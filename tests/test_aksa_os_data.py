"""Tests for the projects source: one walk of .projects mapped into the page's data."""

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aksa_os.runner import run_command
from aksa_os.sources.projects import read_projects

TIMEOUT = 5.0
REPOSITORY_ENV = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_CONFIG_PARAMETERS",
)


def completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["git"], returncode, stdout=stdout, stderr=stderr)


class FakeRunner:
    """Stands in for the thin command layer and records what it was asked to run."""

    def __init__(self, result: subprocess.CompletedProcess[str] | Exception):
        self.result = result
        self.calls: list[tuple[list[str], Path, float]] = []

    def __call__(self, command, *, cwd, timeout):
        self.calls.append((list(command), cwd, timeout))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def run_git(directory: Path, *args: str) -> None:
    """Run git for a test's own setup, with an identity and no signing so it works anywhere."""
    identity = ["-c", "user.email=test@example.com", "-c", "user.name=Test", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "-C", str(directory), *identity, *args], check=True, capture_output=True, text=True)


def write_file(directory: Path, name: str, mtime: float | None = None) -> Path:
    """Write one file under a temporary tree, with a fixed change time when given."""
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("content\n")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def test_read_projects_lists_a_git_project_and_a_pyproject_project(tmp_path):
    write_file(tmp_path / "content" / "git-project" / ".git", "HEAD", mtime=200)
    write_file(tmp_path / "content" / "git-project", "main.py", mtime=200)
    write_file(tmp_path / "content" / "pyproject-project", "pyproject.toml", mtime=100)
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    assert source.ok is True
    assert [project.path for project in source.value.projects] == [
        "content/git-project",
        "content/pyproject-project",
    ]
    assert [project.name for project in source.value.projects] == ["git-project", "pyproject-project"]
    assert [project.is_repo for project in source.value.projects] == [True, False]


def test_read_projects_descends_into_a_plain_container(tmp_path):
    write_file(tmp_path / "content" / "alpha", "README.md")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    assert [project.path for project in source.value.projects] == ["content/alpha"]


def test_read_projects_does_not_descend_into_a_project(tmp_path):
    write_file(tmp_path / "top", "README.md")
    write_file(tmp_path / "top" / "nested", "README.md")
    write_file(tmp_path / "top" / "nested", "note.txt")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [project] = source.value.projects
    assert project.path == "top"


def test_read_projects_skips_generated_directories_from_the_file_count(tmp_path):
    project = tmp_path / "app"
    write_file(project, "README.md")
    write_file(project / "src", "app.py")
    write_file(project / "src" / "deep", "lib.py")
    for generated in (".git", ".venv", "node_modules", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache"):
        write_file(project / generated, "ignored.bin")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.file_count == 3


def test_read_projects_reports_the_newest_file_time(tmp_path):
    project = tmp_path / "app"
    write_file(project, "README.md", mtime=1_000)
    write_file(project / "src", "old.py", mtime=500)
    write_file(project / "src", "new.py", mtime=4_000)
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.file_count == 3
    assert found.last_change == datetime.fromtimestamp(4_000, tz=UTC)
    assert found.last_change.tzinfo is UTC


def test_read_projects_leaves_branch_and_dirty_unset_for_a_non_repo(tmp_path):
    write_file(tmp_path / "app", "README.md")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.is_repo is False
    assert found.branch is None
    assert found.dirty is None
    assert runner.calls == []


@pytest.mark.parametrize(
    ("header", "branch"),
    [
        ("## main...origin/main [ahead 1]", "main"),
        ("## main", "main"),
        ("## HEAD (no branch)", "detached"),
        ("## No commits yet on trunk", "trunk"),
    ],
)
def test_read_projects_reads_the_branch_from_the_status_header(tmp_path, header, branch):
    write_file(tmp_path / "repo" / ".git", "HEAD")
    runner = FakeRunner(completed(f"{header}\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.branch == branch


def test_read_projects_counts_every_dirty_file(tmp_path):
    project = tmp_path / "repo"
    write_file(project / ".git", "HEAD")
    status = "## feat/projects...origin/feat/projects [ahead 1]\n M models.py\nA  projects.py\n?? data.py\n"
    runner = FakeRunner(completed(status))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.branch == "feat/projects"
    assert found.dirty == 3
    assert runner.calls == [
        (["git", "--no-optional-locks", "-C", str(project), "status", "--porcelain=v1", "--branch"], project, TIMEOUT)
    ]


def test_read_projects_reports_a_clean_repository(tmp_path):
    write_file(tmp_path / "repo" / ".git", "HEAD")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    [found] = source.value.projects
    assert found.branch == "main"
    assert found.dirty == 0


def test_read_projects_leaves_the_git_index_of_a_real_repository_unchanged(tmp_path, monkeypatch):
    for name in REPOSITORY_ENV:
        monkeypatch.delenv(name, raising=False)
    project = tmp_path / "repo"
    project.mkdir()
    run_git(project, "init", "-q", "-b", "main", ".")
    (project / "main.py").write_text("content\n")
    run_git(project, "add", "main.py")
    run_git(project, "commit", "-qm", "init")
    os.utime(project / "main.py")
    index = project / ".git" / "index"
    before = index.stat().st_mtime_ns

    source = read_projects(tmp_path, run_command, TIMEOUT)

    assert source.ok is True
    [found] = source.value.projects
    assert found.is_repo is True
    assert found.branch == "main"
    assert found.dirty == 0
    assert index.stat().st_mtime_ns == before


@pytest.mark.parametrize(
    "result",
    [
        completed("", returncode=128, stderr="fatal: not a git repository"),
        subprocess.TimeoutExpired(["git"], TIMEOUT),
        FileNotFoundError(2, "No such file or directory"),
    ],
)
def test_read_projects_keeps_a_project_when_git_fails(tmp_path, result):
    write_file(tmp_path / "repo" / ".git", "HEAD")
    write_file(tmp_path / "repo", "main.py")
    runner = FakeRunner(result)

    source = read_projects(tmp_path, runner, TIMEOUT)

    assert source.ok is True
    [found] = source.value.projects
    assert found.path == "repo"
    assert found.file_count == 1
    assert found.branch is None
    assert found.dirty is None


def test_read_projects_does_not_follow_a_symlinked_directory(tmp_path):
    write_file(tmp_path / "elsewhere", "README.md")
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects" / "linked").symlink_to(tmp_path / "elsewhere")
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path / "projects", runner, TIMEOUT)

    assert source.ok is True
    assert source.value.projects == []
    assert runner.calls == []


def test_read_projects_returns_an_empty_view_when_the_root_is_missing(tmp_path):
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path / "absent", runner, TIMEOUT)

    assert source.ok is True
    assert source.value.projects == []
    assert source.source == "Projects"
    assert source.read_at.tzinfo is UTC
    assert runner.calls == []


def test_read_projects_sorts_by_newest_change_then_name(tmp_path):
    write_file(tmp_path / "a", "README.md", mtime=100)
    write_file(tmp_path / "b", "README.md", mtime=300)
    write_file(tmp_path / "c", "README.md", mtime=300)
    runner = FakeRunner(completed("## main\n"))

    source = read_projects(tmp_path, runner, TIMEOUT)

    assert [project.name for project in source.value.projects] == ["b", "c", "a"]

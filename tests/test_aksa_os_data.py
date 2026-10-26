"""Tests for the AKSA OS sources: reads of .projects and .kb mapped into page data."""

import os
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from aksa_os.runner import run_command
from aksa_os.sources.knowledge import read_knowledge
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


def write_page(
    kb: Path,
    area: str,
    name: str,
    *,
    summary: str = "One sentence.",
    tags: str = "[agents]",
    updated: str = "2026-10-19",
    extra: str = "",
    body: str = "",
) -> Path:
    """Write one wiki page with the frontmatter contract and the body given."""
    path = kb / "wiki" / area / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nsummary: {summary}\ntags: {tags}\nupdated: {updated}\n{extra}---\n{body}")
    return path


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under a tree with its content and change time, to prove a reader wrote nothing."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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


def test_read_knowledge_lists_pages_from_two_areas(tmp_path):
    write_page(
        tmp_path,
        "ai",
        "agentic-design.md",
        summary="Rule, skill, and agent compared.",
        updated="2026-10-19",
        body="# Agentic design\n\n**TL;DR** A rule shapes behaviour.\n",
    )
    write_page(
        tmp_path,
        "brand",
        "oneo4-spec.md",
        summary="oneo4 brand specification.",
        updated="2026-10-23",
        body="# OneO4 spec\n",
    )

    source = read_knowledge(tmp_path)

    assert source.ok is True
    assert source.source == "Knowledge"
    assert source.read_at.tzinfo is UTC
    assert [page.path for page in source.value.pages] == [
        "wiki/brand/oneo4-spec.md",
        "wiki/ai/agentic-design.md",
    ]
    assert [page.area for page in source.value.pages] == ["brand", "ai"]
    assert [page.title for page in source.value.pages] == ["OneO4 spec", "Agentic design"]
    assert [page.summary for page in source.value.pages] == [
        "oneo4 brand specification.",
        "Rule, skill, and agent compared.",
    ]
    assert [page.updated for page in source.value.pages] == [date(2026, 10, 23), date(2026, 10, 19)]


@pytest.mark.parametrize("body", ["**TL;DR** No heading here.\n", "# \n\nNo heading text.\n"])
def test_read_knowledge_takes_the_title_from_the_file_stem_without_a_heading(tmp_path, body):
    write_page(tmp_path, "ai", "agentic-design.md", body=body)

    source = read_knowledge(tmp_path)

    [page] = source.value.pages
    assert page.title == "agentic-design"


def test_read_knowledge_ignores_a_heading_inside_a_code_fence(tmp_path):
    write_page(tmp_path, "ai", "commands.md", body="```sh\n# install\n```\n\n# Real title\n")

    source = read_knowledge(tmp_path)

    [page] = source.value.pages
    assert page.title == "Real title"


def test_read_knowledge_sorts_by_newest_update_then_path(tmp_path):
    write_page(tmp_path, "zeta", "older.md", updated="2026-10-01")
    write_page(tmp_path, "beta", "same.md", updated="2026-10-05")
    write_page(tmp_path, "alpha", "same.md", updated="2026-10-05")

    source = read_knowledge(tmp_path)

    assert [page.path for page in source.value.pages] == [
        "wiki/alpha/same.md",
        "wiki/beta/same.md",
        "wiki/zeta/older.md",
    ]


def test_read_knowledge_counts_inbox_items_excluding_gitkeep(tmp_path):
    write_page(tmp_path, "ai", "page.md")
    inbox = tmp_path / "inbox"
    write_file(inbox, "2026-10-20-one.md")
    write_file(inbox, "2026-10-21-two.md")
    write_file(inbox, ".gitkeep")
    write_file(inbox, "notes.txt")

    source = read_knowledge(tmp_path)

    assert source.value.inbox_count == 2


def test_read_knowledge_counts_no_inbox_items_when_the_inbox_is_absent(tmp_path):
    write_page(tmp_path, "ai", "page.md")

    source = read_knowledge(tmp_path)

    assert source.value.inbox_count == 0


def test_read_knowledge_fails_when_the_kb_root_is_missing(tmp_path):
    source = read_knowledge(tmp_path / "absent")

    assert source.ok is False
    assert source.value is None
    assert str(tmp_path / "absent") in source.error
    assert "link_external.py" in source.error


def test_read_knowledge_fails_when_the_wiki_directory_is_missing(tmp_path):
    source = read_knowledge(tmp_path)

    assert source.ok is False
    assert str(tmp_path / "wiki") in source.error
    assert "link_external.py" in source.error


def test_read_knowledge_skips_malformed_pages_and_keeps_the_rest(tmp_path):
    write_page(tmp_path, "ai", "good.md", summary="Good page.")
    write_page(tmp_path, "ai", "no-summary.md", summary="")
    write_page(tmp_path, "ai", "bad-yaml.md", tags="[unclosed")
    (tmp_path / "wiki" / "orphan.md").write_text("---\nsummary: No area.\ntags: [x]\nupdated: 2026-10-19\n---\n")

    source = read_knowledge(tmp_path)

    assert source.ok is True
    assert [page.path for page in source.value.pages] == ["wiki/ai/good.md"]
    assert source.value.skipped == 3


def test_read_knowledge_skips_a_page_it_cannot_read(tmp_path):
    write_page(tmp_path, "ai", "good.md")
    (tmp_path / "wiki" / "ai" / "broken.md").mkdir(parents=True)

    source = read_knowledge(tmp_path)

    assert source.ok is True
    assert [page.path for page in source.value.pages] == ["wiki/ai/good.md"]
    assert source.value.skipped == 1


def test_read_knowledge_leaves_the_kb_tree_unchanged(tmp_path):
    write_page(tmp_path, "ai", "agentic-design.md", body="# Agentic design\n")
    write_file(tmp_path / "inbox", "2026-10-20-one.md")
    before = snapshot(tmp_path)

    source = read_knowledge(tmp_path)

    assert [page.title for page in source.value.pages] == ["Agentic design"]
    assert snapshot(tmp_path) == before

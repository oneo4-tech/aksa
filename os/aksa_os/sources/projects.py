"""Read the projects under .projects: what each holds and, for a repository, its git state."""

import os
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from aksa_os.models import Project, ProjectsView, Source
from aksa_os.runner import CommandRunner

SOURCE = "Projects"
MARKERS = ("config.yaml", "README.md", "pyproject.toml")
GENERATED = frozenset({".git", ".venv", "node_modules", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache"})


def read_projects(root: Path, runner: CommandRunner, timeout: float) -> Source[ProjectsView]:
    """List every project under the root, or an empty view when the root is absent."""
    read_at = datetime.now(UTC)
    if not root.is_dir():
        return Source.success(ProjectsView(projects=[]), source=SOURCE, read_at=read_at)
    projects = []
    for current, dirnames, _ in os.walk(root, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name not in GENERATED)
        keep = []
        for name in dirnames:
            path = Path(current) / name
            if path.is_symlink():
                continue
            if _is_project(path):
                projects.append(_project(path, root, runner, timeout))
            else:
                keep.append(name)
        dirnames[:] = keep
    projects.sort(key=_order)
    return Source.success(ProjectsView(projects=projects), source=SOURCE, read_at=read_at)


def _is_project(path: Path) -> bool:
    """A git repository or a directory carrying one of the project markers."""
    if (path / ".git").exists():
        return True
    return any((path / marker).is_file() for marker in MARKERS)


def _project(path: Path, root: Path, runner: CommandRunner, timeout: float) -> Project:
    file_count, last_change = _measure(path)
    is_repo = (path / ".git").exists()
    branch, dirty = _git_state(path, runner, timeout) if is_repo else (None, None)
    return Project(
        name=path.name,
        path=path.relative_to(root).as_posix(),
        file_count=file_count,
        last_change=last_change,
        is_repo=is_repo,
        branch=branch,
        dirty=dirty,
    )


def _measure(project: Path) -> tuple[int, datetime | None]:
    """Count the regular files under a project and find the newest change time."""
    count = 0
    newest: float | None = None
    for current, dirnames, filenames in os.walk(project, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if name not in GENERATED)
        for name in filenames:
            try:
                info = os.lstat(Path(current) / name)
            except OSError:
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            count += 1
            if newest is None or info.st_mtime > newest:
                newest = info.st_mtime
    return count, datetime.fromtimestamp(newest, tz=UTC) if newest is not None else None


def _git_state(project: Path, runner: CommandRunner, timeout: float) -> tuple[str | None, int | None]:
    """The branch and dirty-file count, or no git state when git cannot answer."""
    command = ["git", "--no-optional-locks", "-C", str(project), "status", "--porcelain=v1", "--branch"]
    try:
        result = runner(command, cwd=project, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None, None
    if result.returncode:
        return None, None
    return _parse_status(result.stdout)


def _parse_status(stdout: str) -> tuple[str | None, int]:
    """The branch from the status header and one dirty file per other line."""
    lines = [line for line in stdout.splitlines() if line]
    branch = None
    if lines and lines[0].startswith("## "):
        branch = _branch(lines[0].removeprefix("## "))
        lines = lines[1:]
    return branch, len(lines)


def _branch(header: str) -> str:
    """The branch name from a status header, or detached when no branch is checked out."""
    text = header.strip()
    if text.startswith("HEAD (no branch)"):
        return "detached"
    if text.startswith("No commits yet on "):
        return text.removeprefix("No commits yet on ").strip()
    return text.split("...")[0].split(" ")[0]


def _order(project: Project) -> tuple[bool, float, str]:
    """Newest change first, projects without a change last, then by name."""
    newest = project.last_change.timestamp() if project.last_change else 0.0
    return (project.last_change is None, -newest, project.name)

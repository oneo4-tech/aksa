"""Read the shell state: the current branch, the worktree count, and the Python version."""

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from aksa_os.models import Source, SystemView
from aksa_os.runner import CommandRunner

SOURCE = "System"
UNKNOWN_BRANCH = "unknown"


def read_system(root: Path, runner: CommandRunner, timeout: float) -> Source[SystemView]:
    """The repository state the shell shows; a git failure says unknown and leaves the rest readable."""
    read_at = datetime.now(UTC)
    view = SystemView(
        branch=_branch(root, runner, timeout),
        worktrees=_worktrees(root / ".worktrees"),
        python=f"{sys.version_info.major}.{sys.version_info.minor}",
    )
    return Source.success(view, source=SOURCE, read_at=read_at)


def _branch(root: Path, runner: CommandRunner, timeout: float) -> str:
    """The checked-out branch, or unknown when git cannot answer."""
    command = ["git", "--no-optional-locks", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"]
    try:
        result = runner(command, cwd=root, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return UNKNOWN_BRANCH
    if result.returncode:
        return UNKNOWN_BRANCH
    return result.stdout.strip() or UNKNOWN_BRANCH


def _worktrees(root: Path) -> int:
    """How many worktree directories sit under .worktrees; a missing directory counts none."""
    if not root.is_dir():
        return 0
    return sum(1 for path in root.iterdir() if path.is_dir())

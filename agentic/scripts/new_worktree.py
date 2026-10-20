"""Create a git worktree under .worktrees/ ready to work in.

Usage: uv run agentic/scripts/new_worktree.py BRANCH [BASE]

Adds .worktrees/<BRANCH with / replaced by -> on the new branch BRANCH, starting
from BASE (default main). A fresh worktree has none of the gitignored setup, so the
script then runs, inside it, link_external.py (the .kb, .projects and .worktrees
links) and sync_vendors.py claude codex (the vendor skill folders); uv creates the
worktree's own virtual environment on the first run.

Stops at the first failing step and exits with its code; git refuses an existing
branch or folder.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def plan(branch: str, base: str) -> tuple[Path, list[tuple[list[str], Path]]]:
    """The worktree path and each (command, working directory) to run, in order."""
    worktree = REPO_ROOT / ".worktrees" / branch.replace("/", "-")
    return worktree, [
        (["git", "worktree", "add", str(worktree), "-b", branch, base], REPO_ROOT),
        (["uv", "run", "agentic/scripts/link_external.py"], worktree),
        (["uv", "run", "agentic/scripts/sync_vendors.py", "claude", "codex"], worktree),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("branch", help="new branch name, such as feat/x")
    parser.add_argument("base", nargs="?", default="main", help="ref to branch from (default main)")
    args = parser.parse_args()

    worktree, steps = plan(args.branch, args.base)
    for command, cwd in steps:
        code = subprocess.run(command, check=False, cwd=cwd).returncode
        if code:
            print(f"error: {' '.join(command)} exited {code}", file=sys.stderr)
            return code
    print(f"\nready: .worktrees/{worktree.name} on {args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

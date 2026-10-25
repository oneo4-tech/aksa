"""Read the open factory runs from GitHub with one gh call."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from aksa_os.models import FactoryRun, FactoryView, Source
from aksa_os.runner import CommandRunner

SOURCE = "GitHub"
COMMAND = [
    "gh",
    "issue",
    "list",
    "--state",
    "open",
    "--limit",
    "50",
    "--json",
    "number,title,labels,url,updatedAt",
]
STAGE_PREFIX = "stage:"
NEEDS_OWNER = "needs:owner"
CLAIMED = "claimed"


def read_factory(runner: CommandRunner, cwd: Path, timeout: float) -> Source[FactoryView]:
    """List every open factory run, or a safe failure that never reaches the route as an exception."""
    read_at = datetime.now(UTC)
    try:
        result = runner(COMMAND, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return Source.failure(f"gh issue list timed out after {timeout:g}s", source=SOURCE, read_at=read_at)
    except OSError as error:
        reason = error.strerror or type(error).__name__
        return Source.failure(f"gh issue list could not run: {reason}", source=SOURCE, read_at=read_at)
    if result.returncode:
        return Source.failure(f"gh issue list exited {result.returncode}", source=SOURCE, read_at=read_at)
    try:
        issues = json.loads(result.stdout)
        runs = sorted((run for issue in issues if (run := _run(issue))), key=lambda run: run.updated_at, reverse=True)
    except (TypeError, ValueError, KeyError):
        return Source.failure("gh issue list returned unreadable JSON", source=SOURCE, read_at=read_at)
    return Source.success(FactoryView(runs), source=SOURCE, read_at=read_at)


def _run(issue: dict) -> FactoryRun | None:
    """One gh issue as the screen shows it, or None when it is not a factory run."""
    labels = {label["name"] for label in issue["labels"]}
    stages = sorted(name.removeprefix(STAGE_PREFIX) for name in labels if name.startswith(STAGE_PREFIX))
    if not stages:
        return None
    return FactoryRun(
        number=issue["number"],
        title=issue["title"],
        stage=stages[0],
        needs_owner=NEEDS_OWNER in labels,
        claimed=CLAIMED in labels,
        url=issue["url"],
        updated_at=datetime.fromisoformat(issue["updatedAt"]),
    )

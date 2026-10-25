"""Run one command and hand back its result, the thin layer sources read through."""

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol


class CommandRunner(Protocol):
    """What a source needs to run a command; tests pass a fake."""

    def __call__(self, command: Sequence[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]: ...


def run_command(command: Sequence[str], *, cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    """Run a command without raising on a non-zero exit, so the caller decides."""
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=timeout)

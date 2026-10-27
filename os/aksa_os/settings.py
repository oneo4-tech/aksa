"""Settings for AKSA OS, derived from where the package sits in the repository."""

from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]


@dataclass(frozen=True)
class Settings:
    """Where AKSA OS reads from, and where it serves."""

    repo_root: Path = REPO_ROOT
    host: str = "127.0.0.1"
    port: int = 8765
    timeout: float = 10.0

    @property
    def kb(self) -> Path:
        return self.repo_root / ".kb"

    @property
    def projects(self) -> Path:
        return self.repo_root / ".projects"

    @property
    def worktrees(self) -> Path:
        return self.repo_root / ".worktrees"

    @property
    def env_file(self) -> Path:
        return self.repo_root / ".env"

    @property
    def local_settings(self) -> Path:
        return self.repo_root / ".local" / "aksa_os.json"

    @property
    def opencode_db(self) -> Path:
        return Path.home() / ".local" / "share" / "opencode" / "opencode.db"

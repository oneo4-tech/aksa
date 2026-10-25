"""The typed values AKSA OS reads and renders."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Source[T]:
    """One read from one source: its value, or a safe error, and when it was read."""

    ok: bool
    value: T | None = None
    error: str | None = None
    source: str = ""
    read_at: datetime | None = None

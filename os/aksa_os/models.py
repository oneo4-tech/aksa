"""The typed values AKSA OS reads and renders."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Self


@dataclass(frozen=True)
class Source[T]:
    """One read from one source: its value, or a safe error, and when it was read."""

    ok: bool
    value: T | None = None
    error: str | None = None
    source: str = ""
    read_at: datetime | None = None

    @classmethod
    def success(cls, value: T, *, source: str = "", read_at: datetime | None = None) -> Self:
        """A read that produced its value."""
        return cls(ok=True, value=value, source=source, read_at=read_at)

    @classmethod
    def failure(cls, error: str, *, source: str = "", read_at: datetime | None = None) -> Self:
        """A read that failed with a message safe to show."""
        return cls(ok=False, error=error, source=source, read_at=read_at)


@dataclass(frozen=True)
class FactoryRun:
    """One open factory issue as the factory screen shows it."""

    number: int
    title: str
    stage: str
    needs_owner: bool
    claimed: bool
    url: str
    updated_at: datetime


@dataclass(frozen=True)
class FactoryView:
    """Every open factory run, most recently updated first."""

    runs: list[FactoryRun]

    @property
    def waiting(self) -> int:
        """How many runs wait on the owner."""
        return sum(run.needs_owner for run in self.runs)


@dataclass(frozen=True)
class Project:
    """One project under .projects as the projects screen shows it."""

    name: str
    path: str
    file_count: int
    last_change: datetime | None
    is_repo: bool
    branch: str | None = None
    dirty: int | None = None


@dataclass(frozen=True)
class ProjectsView:
    """Every project under .projects, most recently changed first."""

    projects: list[Project]


@dataclass(frozen=True)
class KnowledgePage:
    """One wiki page as the knowledge screen shows it."""

    title: str
    area: str
    path: str
    summary: str
    updated: date


@dataclass(frozen=True)
class KnowledgeView:
    """Every wiki page, most recently changed first, and how many items wait in the inbox."""

    pages: list[KnowledgePage]
    inbox_count: int
    skipped: int = 0

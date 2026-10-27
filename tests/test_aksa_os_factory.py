"""Tests for the factory source: one GitHub read mapped into the page's data."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from aksa_os.sources.factory import read_factory

CWD = Path("repo")
ISSUE_LIST = [
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


def completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], returncode, stdout=stdout, stderr=stderr)


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


def issue(number: int, title: str, labels: list[str], updated: str) -> dict:
    return {
        "number": number,
        "title": title,
        "labels": [{"name": name} for name in labels],
        "url": f"https://github.com/oneo4-tech/aksa/issues/{number}",
        "updatedAt": updated,
    }


RUNS = [
    issue(12, "chore(docs): older run", ["stage:plan"], "2026-10-20T09:00:00Z"),
    issue(
        37,
        "feat(os): add AKSA OS read-only cockpit",
        ["stage:build", "needs:owner", "claimed"],
        "2026-10-25T09:00:00Z",
    ),
]


def test_read_factory_runs_one_gh_issue_list():
    runner = FakeRunner(completed(json.dumps(RUNS)))
    read_factory(runner, CWD, 5.0)
    assert runner.calls == [(ISSUE_LIST, CWD, 5.0)]


def test_read_factory_maps_stage_owner_and_claim_flags():
    runner = FakeRunner(completed(json.dumps(RUNS)))
    source = read_factory(runner, CWD, 5.0)
    assert source.ok is True
    [run] = [run for run in source.value.runs if run.number == 37]
    assert run.title == "feat(os): add AKSA OS read-only cockpit"
    assert run.stage == "build"
    assert run.needs_owner is True
    assert run.claimed is True
    assert run.url == "https://github.com/oneo4-tech/aksa/issues/37"
    assert run.updated_at == datetime(2026, 10, 25, 9, 0, tzinfo=UTC)


def test_read_factory_lists_the_most_recently_updated_run_first():
    runner = FakeRunner(completed(json.dumps(RUNS)))
    source = read_factory(runner, CWD, 5.0)
    assert [run.number for run in source.value.runs] == [37, 12]


def test_read_factory_skips_issues_that_are_not_factory_runs():
    runner = FakeRunner(
        completed(
            json.dumps(
                [
                    issue(7, "a content issue, not a run", [], "2026-10-25T09:00:00Z"),
                    issue(8, "a factory run", ["stage:triage"], "2026-10-24T09:00:00Z"),
                ]
            )
        )
    )
    source = read_factory(runner, CWD, 5.0)
    assert [run.number for run in source.value.runs] == [8]


def test_read_factory_fails_safely_when_gh_exits_non_zero():
    runner = FakeRunner(completed("", returncode=1, stderr="token ghp_secret refused"))
    source = read_factory(runner, CWD, 5.0)
    assert source.ok is False
    assert source.value is None
    assert "gh issue list" in source.error
    assert "1" in source.error
    assert "ghp_secret" not in source.error


def test_read_factory_fails_safely_on_a_timeout():
    runner = FakeRunner(subprocess.TimeoutExpired(ISSUE_LIST, 5.0))
    source = read_factory(runner, CWD, 5.0)
    assert source.ok is False
    assert "timed out" in source.error
    assert "5" in source.error


def test_read_factory_fails_safely_on_unreadable_json():
    runner = FakeRunner(completed("not json"))
    source = read_factory(runner, CWD, 5.0)
    assert source.ok is False
    assert source.value is None
    assert "JSON" in source.error

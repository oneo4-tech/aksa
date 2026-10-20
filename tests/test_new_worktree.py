"""Tests for agentic/scripts/new_worktree.py, with commands recorded instead of run."""

import subprocess

import new_worktree as nw
import pytest


@pytest.fixture
def calls(tmp_path, monkeypatch):
    monkeypatch.setattr(nw, "REPO_ROOT", tmp_path)
    recorded = []

    def fake_run(command, check, cwd):
        recorded.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(nw.subprocess, "run", fake_run)
    return recorded


def run(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr("sys.argv", ["new_worktree.py", *argv])
    return nw.main()


def test_adds_worktree_then_links_and_syncs_inside_it(calls, tmp_path, monkeypatch):
    assert run(monkeypatch, "feat/x") == 0
    worktree = tmp_path / ".worktrees" / "feat-x"
    assert calls == [
        (["git", "worktree", "add", str(worktree), "-b", "feat/x", "main"], tmp_path),
        (["uv", "run", "agentic/scripts/link_external.py"], worktree),
        (["uv", "run", "agentic/scripts/sync_vendors.py", "claude", "codex"], worktree),
    ]


def test_base_is_passed_to_git(calls, monkeypatch):
    run(monkeypatch, "fix-y", "origin/main")
    assert calls[0][0][-1] == "origin/main"


def test_stops_at_first_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(nw, "REPO_ROOT", tmp_path)
    calls = []

    def fake_run(command, check, cwd):
        calls.append(command)
        return subprocess.CompletedProcess(command, 128)

    monkeypatch.setattr(nw.subprocess, "run", fake_run)
    assert run(monkeypatch, "feat/x") == 128
    assert len(calls) == 1

"""Tests for agentic/scripts/link_external.py, run against a temporary repo root."""

import os

import link_external as le
import pytest


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(le, "REPO_ROOT", root)
    monkeypatch.setattr(le, "CONFIG", root / "environment.yaml")
    return root


@pytest.fixture
def external(tmp_path):
    target = tmp_path / "external" / "kb"
    target.mkdir(parents=True)
    return target


def write_config(repo, text: str) -> None:
    (repo / "environment.yaml").write_text(text)


def run(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr("sys.argv", ["link_external.py", *argv])
    return le.main()


def test_add_then_up_to_date(repo, external, monkeypatch):
    write_config(repo, f"links:\n  .kb: {external}\n")
    assert run(monkeypatch, "--check") == 1
    assert not (repo / ".kb").is_symlink()
    assert run(monkeypatch) == 0
    assert os.readlink(repo / ".kb") == str(external)
    assert run(monkeypatch, "--check") == 0


def test_dry_run_changes_nothing(repo, external, monkeypatch):
    write_config(repo, f"links:\n  .kb: {external}\n")
    assert run(monkeypatch, "--dry-run") == 0
    assert not (repo / ".kb").is_symlink()


def test_updates_link_to_other_target(repo, external, tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    (repo / ".kb").symlink_to(other)
    write_config(repo, f"links:\n  .kb: {external}\n")
    assert le.sync_links(le.load_links(le.CONFIG), apply=True) == (1, 0)
    assert os.readlink(repo / ".kb") == str(external)
    assert other.is_dir()


def test_real_folder_in_the_way_is_an_error(repo, external, monkeypatch):
    (repo / ".kb").mkdir()
    (repo / ".kb" / "note.md").write_text("keep")
    write_config(repo, f"links:\n  .kb: {external}\n")
    assert run(monkeypatch) == 1
    assert (repo / ".kb" / "note.md").read_text() == "keep"


def test_missing_target_is_an_error(repo, tmp_path, monkeypatch):
    write_config(repo, f"links:\n  .kb: {tmp_path / 'nowhere'}\n")
    assert run(monkeypatch) == 1
    assert not (repo / ".kb").is_symlink()


@pytest.mark.parametrize(
    "text",
    ["links: []\n", "other: {}\n", "links:\n  .kb: relative/path\n", "links:\n  a/b: /tmp\n", "links:\n  ..: /tmp\n"],
    ids=["not-mapping", "no-links", "relative-target", "nested-name", "parent-name"],
)
def test_malformed_config_is_an_error(repo, monkeypatch, text, capsys):
    write_config(repo, text)
    assert run(monkeypatch) == 1
    assert capsys.readouterr().err.startswith("error:")


def test_repo_config_is_valid():
    """The real environment.yaml parses; its targets may not exist on every machine."""
    config = le.Path(le.__file__).resolve().parents[2] / "config" / "environment.yaml"
    assert le.load_links(config)

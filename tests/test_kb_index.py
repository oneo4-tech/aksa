"""Tests for agentic/scripts/kb_index.py, run against a temporary Knowledge Base."""

import kb_index as ki
import pytest

PAGE = "---\nsummary: {summary}\ntags: [ai, agents]\nupdated: 2026-10-19\n---\n**TL;DR** Short.\n"


@pytest.fixture
def kb(tmp_path, monkeypatch):
    (tmp_path / "wiki").mkdir()
    monkeypatch.setattr(ki, "KB", tmp_path)
    return tmp_path


def write_page(kb, rel: str, text: str) -> None:
    path = kb / "wiki" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr("sys.argv", ["kb_index.py", *argv])
    return ki.main()


def test_build_then_up_to_date(kb, monkeypatch):
    write_page(kb, "ai/agentic-design.md", PAGE.format(summary="Rule, skill, and agent compared."))
    write_page(kb, "testing/flaky-tests.md", PAGE.format(summary="Why tests flake."))
    assert run(monkeypatch, "--check") == 1
    assert run(monkeypatch) == 0
    index = (kb / "index.md").read_text()
    assert (
        "## ai\n\n- [agentic-design](wiki/ai/agentic-design.md): Rule, skill, and agent compared. #ai #agents" in index
    )
    assert index.index("## ai") < index.index("## testing")
    assert run(monkeypatch, "--check") == 0


def test_check_detects_stale_index(kb, monkeypatch):
    write_page(kb, "ai/one.md", PAGE.format(summary="First."))
    run(monkeypatch)
    write_page(kb, "ai/one.md", PAGE.format(summary="Changed."))
    assert run(monkeypatch, "--check") == 1


@pytest.mark.parametrize(
    "rel, text",
    [
        ("top-level.md", PAGE.format(summary="Not in a domain.")),
        ("ai/Bad_Name.md", PAGE.format(summary="Bad name.")),
        ("ai/no-frontmatter.md", "**TL;DR** Nothing.\n"),
        ("ai/no-tags.md", "---\nsummary: x\nupdated: 2026-10-19\n---\n"),
        ("ai/bad-date.md", "---\nsummary: x\ntags: [ai]\nupdated: soon\n---\n"),
        ("ai/bad-yaml.md", "---\nsummary: [unclosed\n---\n"),
        ("ai/too-long.md", PAGE.format(summary="Long.") + "x" * ki.MAX_CHARS),
    ],
)
def test_invalid_page_is_an_error_and_index_untouched(kb, monkeypatch, rel, text):
    write_page(kb, rel, text)
    assert run(monkeypatch) == 1
    assert not (kb / "index.md").exists()


def test_missing_wiki_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(ki, "KB", tmp_path)
    assert run(monkeypatch, "--check") == 1

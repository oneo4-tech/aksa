"""Tests for the research-topic skill's check_research.py."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "agentic" / "skills" / "auxiliary" / "research-topic"
spec = importlib.util.spec_from_file_location("check_research", SKILL / "scripts" / "check_research.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)

VALID = """---
topic: Example protocol
date: 2026-10-20
limits: none
---

# Research: Example protocol

## Questions

1. What does the protocol guarantee about ordering?

## Sources

- [K1] `wiki/protocols/example.md`: ordering basics
- [W1] specification: https://example.org/spec (version 2.1)

Knowledge Base pages read with nothing relevant: none

## Foundations

- F1. Messages on one stream are delivered in order [W1, section 4].

## Paradigms

- P1. Per-stream ordering: ordering holds within a stream, not across streams [K1]

## Hypotheses

- H1. Cross-stream ordering needs an application sequence number. Based on: F1, P1. Verify by: section 5 of the spec.

## Gaps and contradictions

- Unanswered: none
- Contradictions: none
"""


def test_valid_file_passes():
    assert cr.check(VALID, []) == []


def test_template_fails_until_filled():
    errors = cr.check((SKILL / "assets" / "research-template.md").read_text(), [])
    assert any("unfilled placeholder" in e for e in errors)


def test_banned_source_type_is_rejected():
    text = VALID.replace("- [W1] specification:", "- [W1] blog post:")
    errors = cr.check(text, [])
    assert any("not a wiki page or an allowed web source type" in e for e in errors)
    assert "F1 cites unregistered [W1]" in errors


def test_untrusted_kb_path_is_rejected():
    errors = cr.check(VALID.replace("`wiki/protocols/example.md`", "`inbox/2026-10-20-example.md`"), [])
    assert any("not a wiki page" in e for e in errors)


def test_uncited_finding_and_unused_source():
    errors = cr.check(VALID.replace(" [W1, section 4]", ""), [])
    assert "F1 cites no source" in errors
    assert "[W1] is registered but never cited" in errors


def test_hypothesis_needs_known_basis_and_verification():
    assert "H1 is based on unknown F9" in cr.check(VALID.replace("Based on: F1, P1.", "Based on: F9."), [])
    errors = cr.check(VALID.replace(" Verify by: section 5 of the spec.", ""), [])
    assert any(e.startswith("H1 needs") for e in errors)


def test_opinion_words_outside_quotes():
    errors = cr.check(VALID.replace("are delivered in order", "should be preferred"), [])
    assert any("opinion word 'should'" in e for e in errors)
    assert cr.check(VALID.replace("are delivered in order", 'are "best effort" in order'), []) == []


def test_em_dash_and_secret():
    assert any("em dash" in e for e in cr.check(VALID.replace("ordering basics", "ordering — basics"), []))
    assert cr.check(VALID, ["2026-10-20"]) == ["contains a value from .env"]


def test_env_values_reads_long_values(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nKEY=short\nTOKEN='abcdefghijk'\n")
    assert cr.env_values(env) == ["abcdefghijk"]
    assert cr.env_values(tmp_path / "missing") == []

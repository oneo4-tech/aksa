"""Tests for agentic/scripts/check_pr_review.py."""

import subprocess
from pathlib import Path

import check_pr_review as cpr

TEMPLATE = (Path(__file__).resolve().parents[1] / ".github" / "pull_request_template.md").read_text()


def test_needs_review_only_for_components():
    assert cpr.needs_review(["AGENTS.md"])
    assert cpr.needs_review(["README.md", "agentic/skills/core/add-kb/SKILL.md"])
    assert not cpr.needs_review(["README.md", "tests/test_x.py", ".github/workflows/check.yml"])


def test_unfilled_template_has_no_result():
    assert cpr.review_result(TEMPLATE) == ""
    assert cpr.review_result("") == ""


def test_filled_section_is_returned_without_comment():
    body = TEMPLATE.replace("## review-component result\n", "## review-component result\n\npass: agentic/x.md\n")
    assert cpr.review_result(body) == "pass: agentic/x.md"


def run(monkeypatch, changed: list[str], body: str) -> int:
    def fake_run(command, capture_output, text, check):
        return subprocess.CompletedProcess(command, 0, stdout="\n".join(changed))

    monkeypatch.setattr(cpr.subprocess, "run", fake_run)
    monkeypatch.setenv("PR_BODY", body)
    return cpr.main(["origin/main"])


def test_main(monkeypatch):
    assert run(monkeypatch, ["README.md"], "") == 0
    assert run(monkeypatch, ["AGENTS.md"], TEMPLATE) == 1
    assert run(monkeypatch, ["AGENTS.md"], "## review-component result\n\npass\n") == 0

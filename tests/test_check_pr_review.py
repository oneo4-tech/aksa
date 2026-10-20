"""Tests for agentic/scripts/check_pr_review.py."""

import subprocess
from pathlib import Path

import check_pr_review as cpr

TEMPLATE = (Path(__file__).resolve().parents[1] / ".github" / "pull_request_template.md").read_text()
SKILL_FILE = "agentic/skills/core/add-kb/references/x.md"


def test_components_groups_skill_files_by_folder():
    paths = ["AGENTS.md", "README.md", SKILL_FILE, "agentic/skills/core/add-kb/SKILL.md", "agentic/rules/x.md"]
    assert cpr.components(paths) == ["AGENTS.md", "agentic/rules/x.md", "agentic/skills/core/add-kb"]
    assert cpr.components(["README.md", "tests/test_x.py", ".github/workflows/check.yml"]) == []


def test_unfilled_template_has_no_result():
    assert cpr.review_result(TEMPLATE) == ""
    assert cpr.review_result("") == ""


def test_filled_section_is_returned_without_comment():
    body = TEMPLATE.replace("## review-component result\n", "## review-component result\n\npass: agentic/x.md\n")
    assert cpr.review_result(body) == "pass: agentic/x.md"


def run(monkeypatch, changed: list[str], body: str, *args: str) -> int:
    def fake_run(command, capture_output, text, check):
        return subprocess.CompletedProcess(command, 0, stdout="\n".join(changed))

    monkeypatch.setattr(cpr.subprocess, "run", fake_run)
    monkeypatch.setenv("PR_BODY", body)
    return cpr.main(["origin/main", *args])


def test_main(monkeypatch):
    assert run(monkeypatch, ["README.md"], "") == 0
    assert run(monkeypatch, ["AGENTS.md"], TEMPLATE) == 1
    assert run(monkeypatch, ["AGENTS.md"], "## review-component result\n\npass\n") == 1
    assert run(monkeypatch, ["AGENTS.md"], "## review-component result\n\nAGENTS.md: pass\n") == 0


def test_every_changed_component_must_be_named(monkeypatch):
    body = "## review-component result\n\nAGENTS.md: pass\n"
    assert run(monkeypatch, ["AGENTS.md", SKILL_FILE], body) == 1
    assert run(monkeypatch, ["AGENTS.md", SKILL_FILE], body + "agentic/skills/core/add-kb: pass\n") == 0


def test_body_file_when_env_is_unset(monkeypatch, tmp_path):
    body = tmp_path / "body.md"
    body.write_text("## review-component result\n\nAGENTS.md: pass\n")
    assert run(monkeypatch, ["AGENTS.md"], "", "--body-file", str(body)) == 0

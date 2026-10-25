"""Tests for the run-testing brief check and plan commands.

The script belongs to the run-testing skill, not agentic/scripts, so it is loaded by path.
"""

import importlib.util
from pathlib import Path

import pytest
import yaml

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "agentic"
    / "skills"
    / "testing"
    / "run-testing"
    / "scripts"
    / "run_testing.py"
)


def load_script():
    spec = importlib.util.spec_from_file_location("run_testing", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_testing = load_script()

DEFAULTS = {
    "client": "Acme Analytics",
    "surfaces": ["api", "ui"],
    "ui_base_url": "https://app.acme.test",
    "api_base_url": "https://api.acme.test",
    "environment": "staging",
}
PROSE = (
    "\n## Background\n\nWhy the engagement exists.\n"
    "\n## Scope\n\nWhat is tested.\n"
    "\n## Out of scope\n\nWhat is not.\n"
    "\n## Known risks\n\nWhat could go wrong.\n"
    "\n## Acceptance criteria\n\nWhat done means.\n"
)


def write_brief(folder: Path, drop: tuple[str, ...] = (), **overrides) -> Path:
    """Write a valid brief unless a field is dropped or overridden."""
    folder.mkdir(parents=True, exist_ok=True)
    data = {**DEFAULTS, "engagement": folder.name, **overrides}
    for field in drop:
        data.pop(field, None)
    (folder / "brief.md").write_text("---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n" + PROSE)
    return folder


def put(folder: Path, artifact: str) -> None:
    """Create an artifact, as a file or as a folder when its name ends with '/'."""
    path = folder / artifact
    if artifact.endswith("/"):
        path.mkdir(parents=True, exist_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n")


def run(capsys, *argv: str) -> tuple[int, str]:
    code = run_testing.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def plan_lines(output: str) -> list[list[str]]:
    return [line.split() for line in output.splitlines() if line.strip()]


def test_valid_brief_passes(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    assert run(capsys, "check", str(folder)) == (0, "")


def test_missing_engagement_folder_is_bad_input(tmp_path, capsys):
    code, output = run(capsys, "check", str(tmp_path / "absent"))
    assert code == 2
    assert "absent" in output


def test_missing_brief_is_bad_input(tmp_path, capsys):
    folder = tmp_path / "acme-checkout"
    folder.mkdir()
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "brief" in output


def test_brief_with_invalid_utf8_is_reported(tmp_path, capsys):
    folder = tmp_path / "acme-checkout"
    folder.mkdir()
    (folder / "brief.md").write_bytes(b"---\nclient: \xff\n---\n")
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert output.startswith("brief:") and len(output.splitlines()) == 1


def test_brief_that_cannot_be_read_is_reported(tmp_path, capsys, monkeypatch):
    folder = write_brief(tmp_path / "acme-checkout")

    def refuse(*args, **kwargs):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(run_testing.Path, "read_text", refuse)
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert output.startswith("brief:") and len(output.splitlines()) == 1


def test_brief_with_byte_order_mark_passes(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    brief = folder / "brief.md"
    brief.write_bytes(b"\xef\xbb\xbf" + brief.read_bytes())
    assert run(capsys, "check", str(folder)) == (0, "")


@pytest.mark.parametrize("field", ["client", "engagement", "surfaces", "environment"])
def test_missing_required_field_is_named(tmp_path, capsys, field):
    folder = write_brief(tmp_path / "acme-checkout", drop=(field,))
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert f"{field}:" in output


@pytest.mark.parametrize("field, value", [("client", ""), ("environment", 12), ("surfaces", "api")])
def test_invalid_required_field_is_named(tmp_path, capsys, field, value):
    folder = write_brief(tmp_path / "acme-checkout", **{field: value})
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert f"{field}:" in output


def test_engagement_must_equal_the_folder_name(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", engagement="other-client")
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "engagement:" in output
    assert "acme-checkout" in output


@pytest.mark.parametrize("surfaces", [[], ["mobile"]])
def test_surfaces_must_be_a_non_empty_subset(tmp_path, capsys, surfaces):
    folder = write_brief(tmp_path / "acme-checkout", surfaces=surfaces)
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "surfaces:" in output


def test_unknown_surface_is_named(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", surfaces=["api", "mobile"])
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "mobile" in output


def test_ui_base_url_is_required_with_ui_surface(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", drop=("ui_base_url",), surfaces=["ui"])
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "ui_base_url:" in output


def test_api_base_url_is_required_with_api_surface(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", drop=("api_base_url",), surfaces=["api"])
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "api_base_url:" in output


def test_api_spec_must_exist_inside_the_engagement(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", api_spec="specs/openapi.yaml")
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "api_spec:" in output
    assert "specs/openapi.yaml" in output

    put(folder, "specs/openapi.yaml")
    assert run(capsys, "check", str(folder)) == (0, "")


@pytest.mark.parametrize("names", [["API_TOKEN", "client_secret"], ["API-TOKEN"], ["1TOKEN"]])
def test_credentials_env_lists_valid_variable_names(tmp_path, capsys, names):
    folder = write_brief(tmp_path / "acme-checkout", credentials_env=names)
    code, output = run(capsys, "check", str(folder))
    assert code == 2
    assert "credentials_env:" in output


def test_credentials_env_accepts_upper_case_names(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", credentials_env=["API_TOKEN", "UI_PASSWORD"])
    assert run(capsys, "check", str(folder)) == (0, "")


def test_plan_lists_six_steps_in_dependency_order(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    code, output = run(capsys, "plan", str(folder))
    assert code == 0
    assert plan_lines(output) == [
        ["write-test-strategy", "docs/test-strategy.md", "pending"],
        ["design-test-cases", "docs/test-cases.md", "pending"],
        ["write-api-tests", "tests/api/", "pending"],
        ["write-ui-tests", "tests/ui/", "pending"],
        ["write-bug-report", "docs/bugs/<id>.md", "pending"],
        ["summarise-test-execution", "docs/execution-summary.md", "pending"],
    ]


def test_existing_artifacts_are_done(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    for artifact in ("docs/test-strategy.md", "tests/api/", "docs/bugs/BUG-1.md"):
        put(folder, artifact)
    code, output = run(capsys, "plan", str(folder))
    assert code == 0
    status = {line[0]: line[2] for line in plan_lines(output)}
    assert status["write-test-strategy"] == "done"
    assert status["write-api-tests"] == "done"
    assert status["write-bug-report"] == "done"
    assert status["design-test-cases"] == "pending"


def test_ui_only_engagement_omits_api_tests(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", surfaces=["ui"], drop=("api_base_url",))
    code, output = run(capsys, "plan", str(folder))
    assert code == 0
    names = [line[0] for line in plan_lines(output)]
    assert "write-api-tests" not in names
    assert names[-2:] == ["write-bug-report", "summarise-test-execution"]


def test_named_workflow_with_missing_input_is_refused(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    code, output = run(capsys, "plan", str(folder), "design-test-cases")
    assert code == 3
    assert "docs/test-strategy.md" in output


def test_named_api_workflow_without_api_surface_is_refused(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout", surfaces=["ui"], drop=("api_base_url",))
    code, output = run(capsys, "plan", str(folder), "write-api-tests")
    assert code == 3
    assert "api" in output


def test_named_workflow_with_its_input_present_runs(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    put(folder, "docs/test-strategy.md")
    code, output = run(capsys, "plan", str(folder), "design-test-cases")
    assert code == 0
    assert plan_lines(output) == [["design-test-cases", "docs/test-cases.md", "pending"]]


EVIDENCE_WORKFLOWS = ("write-bug-report", "summarise-test-execution")


@pytest.mark.parametrize("workflow", EVIDENCE_WORKFLOWS)
@pytest.mark.parametrize("evidence", [(), ("evidence/README.md",)], ids=["empty", "readme-only"])
def test_evidence_workflow_without_evidence_files_is_refused(tmp_path, capsys, workflow, evidence):
    folder = write_brief(tmp_path / "acme-checkout")
    put(folder, "docs/test-cases.md")
    put(folder, "evidence/")
    for artifact in evidence:
        put(folder, artifact)
    code, output = run(capsys, "plan", str(folder), workflow)
    assert code == 3
    assert f"refused: {workflow} cannot run yet; missing evidence/" in output


@pytest.mark.parametrize("workflow", EVIDENCE_WORKFLOWS)
@pytest.mark.parametrize("other", ["evidence/junit.xml", "evidence/run-1/junit.xml", "evidence/run-1/README.md"])
def test_evidence_workflow_with_a_file_beside_the_readme_runs(tmp_path, capsys, workflow, other):
    folder = write_brief(tmp_path / "acme-checkout")
    put(folder, "docs/test-cases.md")
    put(folder, "evidence/README.md")
    put(folder, other)
    code, output = run(capsys, "plan", str(folder), workflow)
    assert code == 0
    assert plan_lines(output)[0][0] == workflow


def test_named_workflow_is_planned_even_when_its_artifact_exists(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    put(folder, "docs/test-strategy.md")
    put(folder, "docs/test-cases.md")
    code, output = run(capsys, "plan", str(folder), "design-test-cases")
    assert code == 0
    assert plan_lines(output) == [["design-test-cases", "docs/test-cases.md", "done"]]


def test_unknown_workflow_is_bad_input(tmp_path, capsys):
    folder = write_brief(tmp_path / "acme-checkout")
    code, output = run(capsys, "plan", str(folder), "write-test-plan")
    assert code == 2
    assert "write-test-plan" in output


def test_plan_rejects_a_bad_engagement_path(tmp_path, capsys):
    code, output = run(capsys, "plan", str(tmp_path / "absent"))
    assert code == 2
    assert "absent" in output

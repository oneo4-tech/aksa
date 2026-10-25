"""Check an engagement brief and plan the run-testing workflow chain.

Usage:
    run_testing.py check <engagement-dir>
    run_testing.py plan <engagement-dir> [workflow ...]

`check` exits 0 when the brief is valid, 2 with one line per missing or invalid
field. `plan` exits 0 with one line per step of the chain in dependency order,
then one `out: <name>: <reason>` line per step it leaves out, 3 when a named
workflow cannot run yet naming its missing inputs, and 2 on bad input. A whole
chain is the core steps plus the optional steps the brief selects; workflows
named on the command line run alone. Neither command writes.
"""

import argparse
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

BRIEF = "brief.md"
EVIDENCE = "evidence/"
SURFACES = ("api", "ui")
CREDENTIAL_NAME = re.compile(r"[A-Z][A-Z0-9_]*")


@dataclass(frozen=True)
class Step:
    """One workflow in the chain, its artifact, what must exist before it runs, and its tier."""

    name: str
    artifact: str
    requires: tuple[str, ...] = ()
    surface: str | None = None
    optional: bool = False


STEPS = (
    Step("review-requirements", "docs/requirements-review.md"),
    Step("write-test-strategy", "docs/test-strategy.md"),
    Step("write-test-plan", "docs/test-plan.md", ("docs/test-strategy.md",)),
    Step("estimate-test-effort", "docs/effort-estimate.md", ("docs/test-plan.md",)),
    Step("design-test-cases", "docs/test-cases.md", ("docs/test-strategy.md",)),
    Step("design-test-data", "docs/test-data.md", ("docs/test-cases.md",)),
    Step("scaffold-test-framework", "tests/conftest.py"),
    Step("write-api-tests", "tests/api/", ("docs/test-cases.md",), surface="api"),
    Step("write-ui-tests", "tests/ui/", ("docs/test-cases.md",), surface="ui"),
    Step("write-contract-tests", "tests/contract/", surface="api", optional=True),
    Step("write-performance-tests", "tests/performance/", ("docs/test-cases.md",), optional=True),
    Step(
        "audit-accessibility",
        "docs/accessibility-audit.md",
        ("docs/test-strategy.md",),
        surface="ui",
        optional=True,
    ),
    Step(
        "test-api-security-basics",
        "docs/security-review.md",
        ("docs/test-strategy.md",),
        surface="api",
        optional=True,
    ),
    Step("test-mobile-app", "tests/mobile/", ("docs/test-cases.md",), surface="ui", optional=True),
    Step("wire-ci-pipeline", "ci/github-actions.yml", ("docs/test-cases.md",), optional=True),
    Step("audit-test-coverage", "docs/coverage-audit.md", ("docs/test-cases.md",)),
    Step("triage-failing-tests", "docs/failure-triage.md", (EVIDENCE,)),
    Step("plan-exploratory-session", "docs/exploratory/", ("docs/test-strategy.md",), optional=True),
    Step("write-bug-report", "docs/bugs/<id>.md", (EVIDENCE,)),
    Step("summarise-test-execution", "docs/execution-summary.md", (EVIDENCE, "docs/test-cases.md")),
    Step("map-traceability", "docs/traceability.md", ("docs/test-cases.md",)),
    Step("verify-acceptance-criteria", "docs/acceptance-criteria.md", ("docs/traceability.md",)),
    Step("write-qa-report", "docs/qa-report.md", ("docs/traceability.md", "docs/acceptance-criteria.md")),
)
WORKFLOWS = {step.name: step for step in STEPS}


class BriefError(ValueError):
    """The brief cannot be read as a mapping of frontmatter fields."""


def parse_brief(text: str) -> dict:
    """The YAML frontmatter of a brief."""
    match = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.DOTALL)
    if match is None:
        raise BriefError("no YAML frontmatter")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise BriefError(f"invalid YAML frontmatter: {error}") from error
    if not isinstance(data, dict):
        raise BriefError("frontmatter must be a mapping of fields")
    return data


def present(value: object) -> bool:
    """A non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def validate_brief(brief: dict, folder_name: str, file_exists: Callable[[str], bool]) -> list[str]:
    """One line per field that is missing or invalid, in the order a brief reads."""
    problems: list[str] = []
    for field in ("client", "engagement", "environment"):
        if not present(brief.get(field)):
            problems.append(f"{field}: missing")
    engagement = brief.get("engagement")
    if present(engagement) and engagement != folder_name:
        problems.append(f"engagement: must equal the folder name '{folder_name}'")

    surfaces = brief.get("surfaces")
    usable: set[str] = set()
    if surfaces is None:
        problems.append("surfaces: missing")
    elif not isinstance(surfaces, list):
        problems.append("surfaces: must be a list of api, ui")
    elif not surfaces:
        problems.append("surfaces: must list at least one of api, ui")
    else:
        usable = {surface for surface in surfaces if surface in SURFACES}
        unknown = [surface for surface in surfaces if surface not in SURFACES]
        if unknown:
            problems.append("surfaces: unknown surface " + ", ".join(f"'{surface}'" for surface in unknown))

    if "ui" in usable and not present(brief.get("ui_base_url")):
        problems.append("ui_base_url: required when surfaces includes ui")
    if "api" in usable and not present(brief.get("api_base_url")):
        problems.append("api_base_url: required when surfaces includes api")

    api_spec = brief.get("api_spec")
    if api_spec not in (None, ""):
        spec_path = PurePosixPath(api_spec) if isinstance(api_spec, str) else None
        if spec_path is None or spec_path.is_absolute() or ".." in spec_path.parts:
            problems.append("api_spec: must be a path inside the engagement folder")
        elif not file_exists(api_spec):
            problems.append(f"api_spec: file not found: {api_spec}")

    names = brief.get("credentials_env")
    if names is not None:
        if not isinstance(names, list):
            problems.append("credentials_env: must be a list of variable names")
        else:
            invalid = [name for name in names if not isinstance(name, str) or not CREDENTIAL_NAME.fullmatch(name)]
            if invalid:
                problems.append("credentials_env: invalid variable name " + ", ".join(f"'{name}'" for name in invalid))
    return problems


def load_brief(engagement: Path) -> tuple[dict, list[str]]:
    """The brief, or the reasons it cannot be used."""
    if not engagement.is_dir():
        return {}, [f"engagement: not a folder: {engagement}"]
    path = engagement / BRIEF
    if not path.is_file():
        return {}, [f"brief: missing: {path}"]
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        return {}, [f"brief: not valid UTF-8: {path}: {error.reason} at byte {error.start}"]
    except OSError as error:
        return {}, [f"brief: cannot read {path}: {error.strerror or error}"]
    try:
        brief = parse_brief(text)
    except BriefError as error:
        return {}, [f"brief: {error}"]
    return brief, validate_brief(brief, engagement.name, lambda spec: (engagement / spec).is_file())


def artifact_exists(engagement: Path, artifact: str) -> bool:
    """An artifact exists when its file does, or a folder artifact holds a file.

    Bug reports are one file per defect in `docs/bugs/`; a folder artifact is a
    directory of files, so an empty folder is not done.
    """
    if artifact == "docs/bugs/<id>.md":
        return any((engagement / "docs" / "bugs").glob("*.md"))
    path = engagement / artifact
    if artifact.endswith("/"):
        return any(child.is_file() for child in path.rglob("*"))
    return path.exists()


def is_done(engagement: Path, step: Step) -> bool:
    """A step is done when its artifact exists."""
    return artifact_exists(engagement, step.artifact)


def missing_inputs(engagement: Path, step: Step, surfaces: set[str]) -> list[str]:
    """Inputs a named workflow needs before it can run, including its surface.

    Evidence needs a file other than the top-level `evidence/README.md`, as the evidence skills do.
    """
    missing = []
    for required in step.requires:
        if required == EVIDENCE:
            evidence = engagement / EVIDENCE
            readme = evidence / "README.md"
            if not any(path.is_file() and path != readme for path in evidence.rglob("*")):
                missing.append(EVIDENCE)
        elif not artifact_exists(engagement, required):
            missing.append(required)
    if step.surface is not None and step.surface not in surfaces:
        missing.append(f"surface '{step.surface}' in surfaces")
    return missing


def selected_workflows(brief: dict) -> set[str]:
    """The optional workflows the brief selects; a missing or non-list field selects none."""
    workflows = brief.get("workflows")
    if not isinstance(workflows, list):
        return set()
    return {name for name in workflows if isinstance(name, str)}


def select_steps(brief: dict, surfaces: set[str], requested: set[str]) -> tuple[list[Step], list[tuple[Step, str]]]:
    """The steps to plan, and the steps left out with their reasons, both in table order."""
    selected = selected_workflows(brief)
    steps: list[Step] = []
    left_out: list[tuple[Step, str]] = []
    for step in STEPS:
        if step.surface is not None and step.surface not in surfaces:
            left_out.append((step, f"surface {step.surface} is not in the brief's surfaces"))
        elif requested and step.name not in requested:
            left_out.append((step, "not named in the request"))
        elif not requested and step.optional and step.name not in selected:
            left_out.append((step, "not selected in the brief's workflows"))
        else:
            steps.append(step)
    return steps, left_out


def command_check(engagement: Path) -> int:
    _, problems = load_brief(engagement)
    for problem in problems:
        print(problem)
    return 2 if problems else 0


def command_plan(engagement: Path, requested: list[str]) -> int:
    brief, problems = load_brief(engagement)
    if problems:
        for problem in problems:
            print(problem)
        return 2

    unknown = [name for name in requested if name not in WORKFLOWS]
    if unknown:
        print("error: unknown workflow: " + ", ".join(unknown), file=sys.stderr)
        print("known workflows: " + ", ".join(WORKFLOWS), file=sys.stderr)
        return 2

    surfaces = {surface for surface in brief["surfaces"] if surface in SURFACES}
    requested_names = set(requested)
    if requested:
        for step in STEPS:
            if step.name not in requested_names:
                continue
            missing = missing_inputs(engagement, step, surfaces)
            if missing:
                print(f"refused: {step.name} cannot run yet; missing {', '.join(missing)}", file=sys.stderr)
                return 3

    steps, left_out = select_steps(brief, surfaces, requested_names)

    for step in steps:
        print(f"{step.name} {step.artifact} {'done' if is_done(engagement, step) else 'pending'}")
    for step, reason in left_out:
        print(f"out: {step.name}: {reason}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="validate the engagement brief")
    check.add_argument("engagement", type=Path, help="engagement folder, such as .projects/testing/<name>")

    plan = commands.add_parser("plan", help="print the steps in dependency order")
    plan.add_argument("engagement", type=Path, help="engagement folder, such as .projects/testing/<name>")
    plan.add_argument("workflows", nargs="*", help="workflows to plan; the default is the whole chain")

    args = parser.parse_args(argv)
    if args.command == "check":
        return command_check(args.engagement)
    return command_plan(args.engagement, args.workflows)


if __name__ == "__main__":
    sys.exit(main())

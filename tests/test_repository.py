"""Repository invariants: path policy, rule index, skill structure, and references."""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATHS_FILE = "config/environment.yaml"
CATEGORIES = {"core", "productivity", "factory", "engineering"}
SKILL_SECTIONS = ["When to use", "Inputs and prerequisites", "Procedure", "Output", "Constraints"]
# Absolute or home-relative paths (D-012). Split so this file does not match itself.
ABSOLUTE_PATH = re.compile("|".join(["/" + "Users/", "/" + "home/", "~" + "/", r"\$" + "HOME", r"[A-Z]:\\"]))
# Backticked repo paths, such as `agentic/rules/x.md`, without placeholders.
REPO_PATH = re.compile(r"`((?:agentic|config|tests|\.githooks|\.github)/[^`<>*\s]+)`")
DECISION = re.compile(r"\bD-\d{3}\b")


def repo_files() -> list[Path]:
    """Tracked and new, not ignored, files that still exist."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def instruction_files() -> list[Path]:
    return [ROOT / "AGENTS.md", *sorted((ROOT / "agentic").rglob("*.md"))]


def skill_files() -> list[Path]:
    return sorted((ROOT / "agentic" / "skills").rglob("SKILL.md"))


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "missing frontmatter"
    return {
        key.strip(): value.strip()
        for key, _, value in (line.partition(":") for line in match.group(1).splitlines())
        if not key.startswith((" ", "#"))
    }


def test_no_absolute_paths_outside_environment_yaml():
    skip = {ROOT / PATHS_FILE, Path(__file__).resolve(), ROOT / "uv.lock"}
    offenders = []
    for path in repo_files():
        if path in skip:
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [
            f"{path.relative_to(ROOT)}:{n}" for n, line in enumerate(text.splitlines(), 1) if ABSOLUTE_PATH.search(line)
        ]
    assert offenders == [], f"absolute paths belong only in {PATHS_FILE}"


def test_rule_index_matches_rule_files():
    agents = (ROOT / "AGENTS.md").read_text()
    index = agents.split("### Rules", 1)[1].split("\n#", 1)[0]
    indexed = set(re.findall(r"`(agentic/rules/[^`]+\.md)`", index))
    on_disk = {str(p.relative_to(ROOT)) for p in (ROOT / "agentic" / "rules").glob("*.md")}
    assert indexed == on_disk


@pytest.mark.parametrize("skill_md", skill_files(), ids=lambda p: p.parent.name)
def test_skill_structure(skill_md):
    text = skill_md.read_text()
    fields = frontmatter(text)
    assert skill_md.parent.parent.name in CATEGORIES
    assert skill_md.parent.parent.parent == ROOT / "agentic" / "skills"
    assert fields.get("name") == skill_md.parent.name
    assert re.fullmatch(r"[a-z]+(-[a-z0-9]+)+", fields["name"]), "verb-object, lowercase hyphenated (D-005)"
    assert fields.get("description")
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    assert [h for h in headings if h in SKILL_SECTIONS] == SKILL_SECTIONS


def test_skill_names_unique():
    names = [p.parent.name for p in skill_files()]
    assert len(names) == len(set(names))


def test_referenced_repo_paths_exist():
    # decisions.md is history: superseded rows keep the paths they named.
    decisions = ROOT / "agentic" / "memory" / "decisions.md"
    missing = [
        f"{path.relative_to(ROOT)}: {ref}"
        for path in instruction_files()
        if path != decisions
        for ref in REPO_PATH.findall(path.read_text())
        if not (ROOT / ref.rstrip("/")).exists()
    ]
    assert missing == []


def test_referenced_decisions_exist():
    recorded = set(DECISION.findall((ROOT / "agentic" / "memory" / "decisions.md").read_text()))
    missing = [
        f"{path.relative_to(ROOT)}: {ref}"
        for path in instruction_files()
        for ref in DECISION.findall(path.read_text())
        if ref not in recorded
    ]
    assert missing == []

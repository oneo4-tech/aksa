"""Repository invariants: path policy, channel URLs, rule index, skill structure, and references."""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATHS_FILE = "config/environment.yaml"
COMPONENTS = ROOT / "agentic" / "rules" / "components.md"
SKILL_TEMPLATE = ROOT / "agentic" / "templates" / "skill-template.md"
# Windows cannot create these names, with or without an extension (D-021).
RESERVED = re.compile(r"(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?", re.IGNORECASE)
# Absolute or home-relative paths (D-012). Split so this file does not match itself.
ABSOLUTE_PATH = re.compile("|".join(["/" + "Users/", "/" + "home/", "~" + "/", r"\$" + "HOME", r"[A-Z]:\\"]))
# A channel URL belongs in its runtime config, never in a tracked file. Split as above.
CHANNEL_URL = "youtube.com" + "/@"
# Backticked repo paths, such as `agentic/rules/x.md`, without placeholders.
REPO_PATH = re.compile(r"`((?:agentic|config|tests|\.githooks|\.github)/[^`<>*\s]+)`")
DECISION = re.compile(r"\bD-\d{3}\b")
DECISIONS = ROOT / "agentic" / "memory" / "decisions.md"
DECISIONS_HISTORY = ROOT / "agentic" / "memory" / "decisions-history.md"


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


def test_no_channel_url_in_tracked_files():
    offenders = []
    for path in repo_files():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        offenders += [
            f"{path.relative_to(ROOT)}:{n}" for n, line in enumerate(text.splitlines(), 1) if CHANNEL_URL in line
        ]
    assert offenders == [], "channel URLs belong in .projects/content/yt-<channel>/channel.yaml"


def test_rule_index_matches_rule_files():
    agents = (ROOT / "AGENTS.md").read_text()
    index = agents.split("### Rules", 1)[1].split("\n#", 1)[0]
    indexed = set(re.findall(r"`(agentic/rules/[^`]+\.md)`", index))
    on_disk = {str(p.relative_to(ROOT)) for p in (ROOT / "agentic" / "rules").glob("*.md")}
    assert indexed == on_disk


def skill_categories() -> set[str]:
    """Categories listed under the Category bullet of components.md."""
    block = COMPONENTS.read_text().split("- Category, exactly one", 1)[1].split("\n- ", 1)[0]
    return set(re.findall(r"^  - `([a-z-]+)`:", block, re.MULTILINE))


def in_listed_category(skill_md: Path) -> bool:
    """A skill's folder sits directly under a category listed in components.md (D-022)."""
    return skill_md.parent.parent.name in skill_categories()


@pytest.mark.parametrize(("category", "accepted"), [("content", True), ("factory", True), ("unlisted", False)])
def test_skill_category_must_be_listed(category, accepted):
    skill_md = ROOT / "agentic" / "skills" / category / "run-example" / "SKILL.md"
    assert in_listed_category(skill_md) is accepted


def skill_sections() -> list[str]:
    """Section headings of the skill template, in order."""
    return re.findall(r"^## (.+)$", SKILL_TEMPLATE.read_text(), re.MULTILINE)


def test_components_lists_template_sections():
    sections_line = next(
        line for line in COMPONENTS.read_text().splitlines() if line.startswith("- Sections, in order:")
    )
    assert re.findall(r"\*\*([^*]+)\*\* \(", sections_line) == skill_sections()


def test_no_windows_reserved_names():
    offenders = [
        str(path.relative_to(ROOT))
        for path in repo_files()
        if any(RESERVED.fullmatch(part) for part in path.relative_to(ROOT).parts)
    ]
    assert offenders == [], "Windows cannot check out these paths (D-021)"


@pytest.mark.parametrize("skill_md", skill_files(), ids=lambda p: p.parent.name)
def test_skill_structure(skill_md):
    text = skill_md.read_text()
    fields = frontmatter(text)
    assert in_listed_category(skill_md)
    assert skill_md.parent.parent.parent == ROOT / "agentic" / "skills"
    assert fields.get("name") == skill_md.parent.name
    assert re.fullmatch(r"[a-z]+(-[a-z0-9]+)+", fields["name"]), "verb-object, lowercase hyphenated (D-005)"
    assert fields.get("description")
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    sections = skill_sections()
    assert [h for h in headings if h in sections] == sections


@pytest.mark.parametrize("skill_md", skill_files(), ids=lambda p: p.parent.name)
def test_skill_folder_structure(skill_md):
    entries = {p.name for p in skill_md.parent.iterdir() if p.name != "__pycache__"}
    assert entries <= {"SKILL.md", "references", "scripts"}, "see the folder structure in components.md"


def test_skill_names_unique():
    names = [p.parent.name for p in skill_files()]
    assert len(names) == len(set(names))


def test_referenced_repo_paths_exist():
    # Superseded rows keep the paths they named.
    missing = [
        f"{path.relative_to(ROOT)}: {ref}"
        for path in instruction_files()
        if path != DECISIONS_HISTORY
        for ref in REPO_PATH.findall(path.read_text())
        if not (ROOT / ref.rstrip("/")).exists()
    ]
    assert missing == []


def test_referenced_decisions_exist():
    recorded = {row[0] for row in decision_rows(DECISIONS) + decision_rows(DECISIONS_HISTORY)}
    missing = [
        f"{path.relative_to(ROOT)}: {ref}"
        for path in instruction_files()
        for ref in DECISION.findall(path.read_text())
        if ref not in recorded
    ]
    assert missing == []


def decision_rows(path: Path) -> list[list[str]]:
    """Cells of each decision row: ID, Date, Kind, Area, Decision, Why, Source, Status."""
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in path.read_text().splitlines()
        if line.startswith("| D-")
    ]


def test_decisions_split_by_status():
    active, history = decision_rows(DECISIONS), decision_rows(DECISIONS_HISTORY)
    ids = [row[0] for row in active + history]
    assert len(ids) == len(set(ids)), "decision ids are unique across both files"
    assert all(row[7] == "active" for row in active), "superseded rows move to decisions-history.md (D-016)"
    assert all(row[7].startswith("superseded by D-") for row in history)


def test_decision_areas_are_listed():
    header = DECISIONS.read_text().split("\n| ID |", 1)[0]
    allowed = set(re.findall(r"`([a-z-]+)`", header.split("- Areas:", 1)[1].split("\n", 1)[0]))
    used = {area.strip() for row in decision_rows(DECISIONS) for area in row[3].split(",")}
    assert used <= allowed, f"unlisted areas: {used - allowed}"

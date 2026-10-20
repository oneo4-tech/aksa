"""Check a research-topic output file against the skill's rules.

Usage: uv run agentic/skills/auxiliary/research-topic/scripts/check_research.py FILE

Checks frontmatter, unfilled placeholders, em dashes, the source registry (wiki
pages and allowed web source types only), citations on every foundation and
paradigm, the basis and verification of every hypothesis, opinion words outside
quotes, and values from the repository's .env (never printed).

Exit 0 when the file passes, 1 when a check fails, 2 when the file cannot be read.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
FRONTMATTER_KEYS = ("topic", "date", "limits")
WEB_TYPES = ("official docs", "source repository", "specification", "release notes", "changelog")
KB_SOURCE = re.compile(r"^- \[(K\d+)\] `wiki/[^`]+\.md`")
WEB_SOURCE = re.compile(rf"^- \[(W\d+)\] (?:{'|'.join(WEB_TYPES)}): https?://\S+")
CITATION = re.compile(r"\[((?:K|W)\d+)\b")
QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”|`[^`]*`")
OPINION = re.compile(
    r"\b(recommend\w*|should|best|better|worse|prefer\w*|ideal\w*|suggest\w*|advis\w*)\b", re.IGNORECASE
)


def sections(body: str) -> dict[str, list[str]]:
    """Lines of each '## ' section, keyed by heading."""
    found: dict[str, list[str]] = {}
    current = None
    for line in body.splitlines():
        if line.startswith("## "):
            current = found.setdefault(line[3:].strip(), [])
        elif current is not None:
            current.append(line)
    return found


def items(lines: list[str], prefix: str) -> list[tuple[str, str]]:
    """(id, line) of each '- <prefix><n>.' item."""
    return [(m.group(1), line) for line in lines if (m := re.match(rf"- ({prefix}\d+)\.", line))]


def check(text: str, secrets: list[str]) -> list[str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return ["file must start with --- frontmatter ---"]
    errors = []
    fields = dict(line.partition(":")[::2] for line in match.group(1).splitlines())
    errors += [f"frontmatter needs '{key}'" for key in FRONTMATTER_KEYS if not fields.get(key, "").strip()]

    for n, line in enumerate(text.splitlines(), 1):
        if "{{" in line:
            errors.append(f"line {n}: unfilled placeholder")
        if "—" in line:
            errors.append(f"line {n}: em dash")

    parts = sections(text[match.end() :])
    if not [line for line in parts.get("Questions", []) if re.match(r"\d+\. ", line)]:
        errors.append("Questions has no numbered question")

    registered = set()
    for line in parts.get("Sources", []):
        if not line.startswith("- ["):
            continue
        source = KB_SOURCE.match(line) or WEB_SOURCE.match(line)
        if source:
            registered.add(source.group(1))
        else:
            errors.append(f"source is not a wiki page or an allowed web source type: {line}")

    findings = items(parts.get("Foundations", []), "F") + items(parts.get("Paradigms", []), "P")
    cited = set()
    for item_id, line in findings:
        refs = set(CITATION.findall(line))
        if not refs:
            errors.append(f"{item_id} cites no source")
        errors += [f"{item_id} cites unregistered [{ref}]" for ref in sorted(refs - registered)]
        cited |= refs
    errors += [f"[{ref}] is registered but never cited" for ref in sorted(registered - cited)]

    finding_ids = {item_id for item_id, _ in findings}
    for item_id, line in items(parts.get("Hypotheses", []), "H"):
        basis = re.search(r"Based on: ([^.]+)\.", line)
        if not basis or not re.search(r"Verify by: \S", line):
            errors.append(f"{item_id} needs 'Based on: <ids>.' and 'Verify by: <test>'")
            continue
        errors += [
            f"{item_id} is based on unknown {ref}"
            for ref in re.findall(r"[A-Z]+\d+", basis.group(1))
            if ref not in finding_ids
        ]

    for heading in ("Foundations", "Paradigms", "Gaps and contradictions"):
        for line in parts.get(heading, []):
            errors += [
                f"{heading}: opinion word '{word}' outside a quote" for word in OPINION.findall(QUOTED.sub("", line))
            ]

    if any(secret in text for secret in secrets):
        errors.append("contains a value from .env")
    return errors


def env_values(path: Path) -> list[str]:
    """Values of at least 8 characters from a .env file, if it exists."""
    if not path.is_file():
        return []
    values = (line.partition("=")[2].strip().strip("\"'") for line in path.read_text().splitlines() if "=" in line)
    return [value for value in values if len(value) >= 8]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = Path(argv[0])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"FAIL {path}: {error}")
        return 2
    errors = check(text, env_values(REPO_ROOT / ".env"))
    if errors:
        print(f"FAIL {path}")
        print("\n".join(f"  - {error}" for error in errors))
        return 1
    print(f"OK   {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

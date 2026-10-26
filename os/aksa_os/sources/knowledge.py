"""Read the Knowledge Base wiki: its pages with their areas and update dates, and the inbox count."""

import re
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

from aksa_os.models import KnowledgePage, KnowledgeView, Source

SOURCE = "Knowledge"
FRONTMATTER = re.compile(r"---\n(.*?)\n---\n", re.DOTALL)
FIX = "run agentic/scripts/link_external.py"


def read_knowledge(root: Path) -> Source[KnowledgeView]:
    """Every wiki page, newest change first, and how many inbox items wait for review."""
    read_at = datetime.now(UTC)
    if not root.is_dir():
        return Source.failure(f"{root} not found; {FIX}", source=SOURCE, read_at=read_at)
    wiki = root / "wiki"
    if not wiki.is_dir():
        return Source.failure(f"{wiki} not found; {FIX}", source=SOURCE, read_at=read_at)
    pages, skipped = [], 0
    for path in sorted(wiki.rglob("*.md")):
        page = _page(path, wiki)
        if page is None:
            skipped += 1
        else:
            pages.append(page)
    pages.sort(key=_order)
    view = KnowledgeView(pages=pages, inbox_count=_inbox_count(root), skipped=skipped)
    return Source.success(view, source=SOURCE, read_at=read_at)


def _page(path: Path, wiki: Path) -> KnowledgePage | None:
    """One page from its frontmatter and first heading, or None when it breaks the contract."""
    parts = path.relative_to(wiki).parts
    if len(parts) != 2:
        return None
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return None
    match = FRONTMATTER.match(text)
    try:
        meta = yaml.safe_load(match.group(1)) if match else None
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None
    summary, tags, updated = meta.get("summary"), meta.get("tags"), meta.get("updated")
    if not isinstance(summary, str) or not summary.strip() or "\n" in summary.strip():
        return None
    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) for tag in tags):
        return None
    if not isinstance(updated, date) or not isinstance(meta.get("sources", []), list):
        return None
    return KnowledgePage(
        title=_title(text, path.stem),
        area=parts[0],
        path=path.relative_to(wiki.parent).as_posix(),
        summary=summary.strip(),
        updated=updated,
    )


def _title(text: str, stem: str) -> str:
    """The first H1 outside a code fence, or the file stem."""
    fenced = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
        elif not fenced and stripped.startswith("# "):
            return stripped[2:].strip()
    return stem


def _inbox_count(root: Path) -> int:
    """How many inbox items wait for review."""
    return sum(1 for path in (root / "inbox").glob("*.md") if path.is_file() and path.name != ".gitkeep")


def _order(page: KnowledgePage) -> tuple[int, str]:
    """Newest update first, then by path."""
    return (-page.updated.toordinal(), page.path)

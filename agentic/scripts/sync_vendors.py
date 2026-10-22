"""Sync aksa's agentic components into the given vendors' repo-level folders.

Usage: uv run agentic/scripts/sync_vendors.py VENDOR [VENDOR ...] [--only KIND ...]
                                             [--copy] [--dry-run | --check] [--force]

VENDOR is one of: claude, opencode, codex, gemini, copilot.
KIND is a component kind (see KINDS); the default syncs every kind. Today the only
kind is skills; the note above SKILL_DIRS lists the kinds planned next.

Components sync only to repo-level vendor folders, never to global home folders.

Skills live at agentic/skills/<category>/<skill>/SKILL.md. Vendors want a flat
<skills_dir>/<skill>/SKILL.md, so the category folder is dropped.

Skills are symlinked, so edits show up live; --copy copies them instead.

Each vendor folder gets a .aksa-sync.json manifest naming the skills this script
owns. Only those are replaced or pruned; a vendor's own skills are never touched.
An unmanaged entry with a skill's name is a conflict: skipped unless --force.

Skills stay vendor-neutral. OpenCode needs extra frontmatter to offer a skill as
a /<name> command and to let agents and other skills load it (OPENCODE_FIELDS), so
opencode always gets copies with any missing fields added; re-sync after edits.
A skill that sets one of those fields to another value is a warning; --check exits 1.
Claude gets run-factory as a rendered copy with `disable-model-invocation: true`;
its other skills remain symlinked.

--dry-run prints the plan. --check does the same and exits 1 if anything is out
of sync. Exit 1 also on conflicts or duplicate skill names.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "agentic" / "skills"
MANIFEST = ".aksa-sync.json"

VENDORS = ("claude", "opencode", "codex", "gemini", "copilot")

# Where each vendor reads the kinds aksa does not sync yet, from memory of vendor docs:
# verify each against current docs before implementing it.
#   instructions: claude CLAUDE.md; codex, opencode, copilot AGENTS.md;
#                 gemini GEMINI.md unless .gemini/settings.json context.fileName names AGENTS.md
#   agents:       claude .claude/agents/<name>.md; opencode .opencode/agent/<name>.md;
#                 copilot .github/agents/<name>.agent.md
#   hooks:        claude and gemini settings.json "hooks"; copilot .github/hooks/;
#                 opencode plugins in .opencode/plugin/
# Project skills folders from each vendor's docs (checked 2026-10-13).
SKILL_DIRS = {
    "claude": ".claude/skills",
    "opencode": ".opencode/skills",
    "codex": ".agents/skills",
    "gemini": ".gemini/skills",
    "copilot": ".github/skills",
}
# Other project folders a vendor also scans: syncing both loads skills twice.
ALSO_READS = {
    "opencode": {".claude/skills", ".agents/skills"},
    "gemini": {".agents/skills"},
    "copilot": {".claude/skills", ".agents/skills"},
}
# Frontmatter OpenCode needs (https://opencode.ai/docs/skills, checked 2026-10-13).
# metadata opencode/slash adds the /<name> command; opencode/autoinvoke keeps the
# skill in the agent's list so agents and other skills can load it.
OPENCODE_FIELDS = {
    "compatibility": "opencode",
    "metadata.opencode/slash": "true",
    "metadata.opencode/autoinvoke": "true",
}
CLAUDE_RUN_FACTORY_FIELDS = {"disable-model-invocation": True}


Render = Callable[[str], str]


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path


def discover_skills() -> tuple[list[Skill], list[str]]:
    """Return skills sorted by name, plus errors (duplicates)."""
    found: dict[str, list[Path]] = {}
    for skill_md in sorted(SKILLS_ROOT.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        # Skip a SKILL.md nested inside another skill (for example an asset).
        if any((p / "SKILL.md").exists() for p in skill_dir.parents if SKILLS_ROOT in p.parents):
            continue
        found.setdefault(skill_dir.name, []).append(skill_dir)
    errors = [
        f"duplicate skill name '{name}': " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in paths)
        for name, paths in found.items()
        if len(paths) > 1
    ]
    skills = [Skill(name, paths[0]) for name, paths in sorted(found.items()) if len(paths) == 1]
    return skills, errors


def read_frontmatter(skill_md: Path) -> dict[str, str]:
    return parse_frontmatter(skill_md.read_text())


def parse_frontmatter(text: str) -> dict[str, str]:
    """Flat keys from simple YAML frontmatter; a nested key reads as 'parent.child'."""
    lines = text.splitlines()
    fields: dict[str, str] = {}
    if not lines or lines[0].strip() != "---":
        return fields
    parent = ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.strip().partition(":")
        if not sep or line.lstrip().startswith("#"):
            continue
        value = value.strip().strip("'\"")
        if line.startswith((" ", "\t")):
            fields[f"{parent}.{key.strip()}"] = value
        else:
            parent = key.strip()
            fields[parent] = value
    return fields


def frontmatter_warnings(skills: list[Skill]) -> list[str]:
    warnings: list[str] = []
    for skill in skills:
        name = read_frontmatter(skill.path / "SKILL.md").get("name")
        if not name:
            warnings.append(f"{skill.name}: SKILL.md has no 'name:' field")
        elif name != skill.name:
            warnings.append(f"{skill.name}: frontmatter name '{name}' differs from folder name")
    return warnings


def opencode_warnings(skills: list[Skill]) -> list[str]:
    """Fields a skill sets to a value other than the one OpenCode needs; sync keeps the skill's value."""
    warnings: list[str] = []
    for skill in skills:
        fields = read_frontmatter(skill.path / "SKILL.md")
        for key, want in OPENCODE_FIELDS.items():
            if key in fields and fields[key].lower() != want:
                warnings.append(f"{skill.name}: frontmatter {key} is {fields[key]!r}, opencode needs {want!r}")
    return warnings


def add_frontmatter_fields(text: str, desired_fields: dict[str, str | bool]) -> str:
    """SKILL.md text with any missing fields added to its frontmatter."""
    existing_fields = parse_frontmatter(text)
    missing = {k: v for k, v in desired_fields.items() if k not in existing_fields}
    if not missing:
        return text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        lines = ["---\n", "---\n", *lines]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("SKILL.md frontmatter has no closing '---'")
    if not lines[end - 1].endswith("\n"):
        lines[end - 1] += "\n"
    # Insert bottom-up so earlier indices stay valid.
    inserts: list[tuple[int, list[str]]] = []
    nested: dict[str, list[str]] = {}
    for key, value in missing.items():
        rendered_value = json.dumps(value) if isinstance(value, str) else str(value).lower()
        parent, _, child = key.rpartition(".")
        if parent:
            nested.setdefault(parent, []).append(f"  {child}: {rendered_value}\n")
        else:
            inserts.append((end, [f"{key}: {rendered_value}\n"]))
    for parent, children in nested.items():
        at = next((i for i in range(1, end) if lines[i].split(":", 1)[0] == parent), None)
        inserts.append((end, [f"{parent}:\n", *children]) if at is None else (at + 1, children))
    for at, new in sorted(inserts, key=lambda item: item[0], reverse=True):
        lines[at:at] = new
    return "".join(lines)


def add_opencode_fields(text: str) -> str:
    """SKILL.md text with any OPENCODE_FIELDS it lacks added to its frontmatter."""
    return add_frontmatter_fields(text, OPENCODE_FIELDS)


def add_claude_run_factory_fields(text: str) -> str:
    """SKILL.md text with Claude's run-factory invocation setting added."""
    return add_frontmatter_fields(text, CLAUDE_RUN_FACTORY_FIELDS)


def tree_hash(root: Path, render: Render | None = None) -> str:
    """Hash of a skill folder; render, if given, is applied to its SKILL.md first."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        data = path.read_bytes()
        if render and path == root / "SKILL.md":
            data = render(data.decode()).encode()
        digest.update(str(path.relative_to(root)).encode())
        digest.update(data)
    return digest.hexdigest()


def link_target(source: Path, target_dir: Path) -> str:
    """Relative link so clones and worktrees stay valid."""
    return os.path.relpath(source, target_dir.resolve())


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def is_current(skill: Skill, target: Path, mode: str, render: Render | None) -> bool:
    if mode == "symlink":
        return target.is_symlink() and target.resolve() == skill.path.resolve()
    return target.is_dir() and not target.is_symlink() and tree_hash(target) == tree_hash(skill.path, render)


def sync_dir(
    target_dir: Path,
    mode: str,
    render: Render | None,
    skills: list[Skill],
    apply: bool,
    force: bool,
    overrides: dict[str, tuple[str, Render | None]] | None = None,
) -> tuple[int, int]:
    """Sync one vendor folder; render, if given, rewrites each copied SKILL.md. Returns (changes, conflicts)."""
    manifest_path = target_dir / MANIFEST
    managed: set[str] = set(json.loads(manifest_path.read_text())["managed"]) if manifest_path.exists() else set()
    changes = conflicts = 0
    owned: set[str] = set()

    for skill in skills:
        target = target_dir / skill.name
        skill_mode, skill_render = (overrides or {}).get(skill.name, (mode, render))
        if is_current(skill, target, skill_mode, skill_render):
            owned.add(skill.name)
            continue
        exists = target.exists() or target.is_symlink()
        if exists and skill.name not in managed and not force:
            print(f"  conflict  {skill.name}: exists and not managed by aksa (use --force)")
            conflicts += 1
            continue
        print(f"  {'update' if exists else 'add':<9} {skill.name}")
        changes += 1
        owned.add(skill.name)
        if apply:
            target_dir.mkdir(parents=True, exist_ok=True)
            remove(target)
            if skill_mode == "symlink":
                target.symlink_to(link_target(skill.path, target_dir), target_is_directory=True)
            else:
                shutil.copytree(skill.path, target, symlinks=True)
                if skill_render:
                    skill_md = target / "SKILL.md"
                    rendered = skill_render(skill_md.read_text())
                    skill_md.unlink()  # Drop a symlinked SKILL.md rather than write through it.
                    skill_md.write_text(rendered)

    for name in sorted(managed - {s.name for s in skills}):
        print(f"  prune     {name}")
        changes += 1
        if apply:
            remove(target_dir / name)

    if apply and (owned or manifest_path.exists()):
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"managed": sorted(owned)}, indent=2) + "\n")
    return changes, conflicts


def sync_skills(vendors: list[str], args: argparse.Namespace, apply: bool) -> tuple[int, bool]:
    """Sync skills to each vendor. Returns (changes, failed): failed means exit 1."""
    skills, errors = discover_skills()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        # Syncing now would prune the clashing skill from every vendor.
        print("Skills not synced: rename the duplicate skill folders first.", file=sys.stderr)
        return 0, True
    for warning in frontmatter_warnings(skills):
        print(f"warning: {warning}", file=sys.stderr)
    field_conflicts = opencode_warnings(skills) if "opencode" in vendors else []
    for warning in field_conflicts:
        print(f"warning: {warning}", file=sys.stderr)

    folders = {SKILL_DIRS[v] for v in vendors}
    for vendor in vendors:
        overlap = sorted(ALSO_READS.get(vendor, set()) & folders)
        if overlap:
            print(f"warning: {vendor} also reads {', '.join(overlap)}, so skills load twice", file=sys.stderr)

    total_changes = total_conflicts = 0
    for vendor in vendors:
        skills_dir = SKILL_DIRS[vendor]
        # OpenCode gets rendered copies; a symlink would serve the source without its fields.
        render = add_opencode_fields if vendor == "opencode" else None
        mode = "copy" if args.copy or render else "symlink"
        overrides = {"run-factory": ("copy", add_claude_run_factory_fields)} if vendor == "claude" else None
        print(f"skills: {vendor} -> {skills_dir} ({mode})")
        changes, conflicts = sync_dir(
            REPO_ROOT / skills_dir, mode, render, skills, apply, args.force, overrides=overrides
        )
        if not changes and not conflicts:
            print("  up to date")
        total_changes += changes
        total_conflicts += conflicts

    verb = "applied" if apply else "pending"
    print(f"{len(skills)} skill(s), {total_changes} change(s) {verb}, {total_conflicts} conflict(s)\n")
    return total_changes, bool(total_conflicts or (args.check and field_conflicts))


# Component kind -> sync function. Add a kind here when its source components exist.
KINDS: dict[str, Callable[[list[str], argparse.Namespace, bool], tuple[int, bool]]] = {
    "skills": sync_skills,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "vendors", nargs="+", choices=VENDORS, metavar="VENDOR", help=f"one or more of: {', '.join(VENDORS)}"
    )
    parser.add_argument(
        "--only", nargs="+", choices=list(KINDS), metavar="KIND", help=f"sync only these kinds: {', '.join(KINDS)}"
    )
    parser.add_argument("--copy", action="store_true", help="copy skills instead of symlinking them")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    group.add_argument("--check", action="store_true", help="like --dry-run, exit 1 if out of sync")
    parser.add_argument("--force", action="store_true", help="replace unmanaged entries that clash with a component")
    args = parser.parse_args()
    vendors = list(dict.fromkeys(args.vendors))
    kinds = list(dict.fromkeys(args.only or KINDS))

    apply = not (args.dry_run or args.check)
    total_changes, failed = 0, False
    for kind in kinds:
        changes, kind_failed = KINDS[kind](vendors, args, apply)
        total_changes += changes
        failed = failed or kind_failed
    return 1 if failed or (args.check and total_changes) else 0


if __name__ == "__main__":
    sys.exit(main())

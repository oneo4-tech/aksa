"""Sync every skill in agentic/skills/ to the given vendors' skills folders.

Usage: python3 agentic/scripts/sync_skills.py VENDOR [VENDOR ...] [--user] [--copy]
                                             [--dry-run | --check] [--force]

VENDOR is one of: claude, opencode, codex, gemini, copilot.
Skills live at agentic/skills/<category>/<skill>/SKILL.md. Vendors want a flat
<skills_dir>/<skill>/SKILL.md, so the category folder is dropped.

Skills are symlinked, so edits show up live; --copy copies them instead.
--user syncs to the vendor's home folder instead of the repo folder.

Each vendor folder gets a .ark-sync.json manifest naming the skills this script
owns. Only those are replaced or pruned; a vendor's own skills are never touched.
An unmanaged entry with a skill's name is a conflict: skipped unless --force.

Syncing to opencode also checks each SKILL.md frontmatter has the fields OpenCode
needs to offer the skill as a /<name> command and to let agents and other skills
load it (see OPENCODE_FIELDS). Missing fields are warnings; --check exits 1.

--dry-run prints the plan. --check does the same and exits 1 if anything is out
of sync. Exit 1 also on conflicts or duplicate skill names.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "agentic" / "skills"
MANIFEST = ".ark-sync.json"

# Skills folders from each vendor's docs (checked 2026-10-13): (project, user).
VENDORS = {
    "claude": (".claude/skills", "~/.claude/skills"),
    "opencode": (".opencode/skills", "~/.config/opencode/skills"),
    "codex": (".agents/skills", "~/.agents/skills"),
    "gemini": (".gemini/skills", "~/.gemini/skills"),
    "copilot": (".github/skills", "~/.copilot/skills"),
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


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path


def resolve_dir(skills_dir: str) -> Path:
    """Expand ~; a relative path is relative to the repo root."""
    path = Path(skills_dir).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path


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
    """Flat keys from simple YAML frontmatter; a nested key reads as 'parent.child'."""
    lines = skill_md.read_text().splitlines()
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
    warnings: list[str] = []
    for skill in skills:
        fields = read_frontmatter(skill.path / "SKILL.md")
        for key, want in OPENCODE_FIELDS.items():
            if fields.get(key, "").lower() != want:
                warnings.append(f"{skill.name}: opencode needs frontmatter {key}: {want!r}")
    return warnings


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def link_target(source: Path, target_dir: Path) -> str:
    """Relative link inside the repo so clones and worktrees stay valid, absolute outside."""
    if target_dir.resolve().is_relative_to(REPO_ROOT):
        return os.path.relpath(source, target_dir.resolve())
    return str(source)


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def is_current(skill: Skill, target: Path, mode: str) -> bool:
    if mode == "symlink":
        return target.is_symlink() and target.resolve() == skill.path.resolve()
    return target.is_dir() and not target.is_symlink() and tree_hash(target) == tree_hash(skill.path)


def sync_dir(target_dir: Path, mode: str, skills: list[Skill], apply: bool, force: bool) -> tuple[int, int]:
    """Sync one vendor folder. Returns (changes, conflicts)."""
    manifest_path = target_dir / MANIFEST
    managed: set[str] = set(json.loads(manifest_path.read_text())["managed"]) if manifest_path.exists() else set()
    changes = conflicts = 0
    owned: set[str] = set()

    for skill in skills:
        target = target_dir / skill.name
        if is_current(skill, target, mode):
            owned.add(skill.name)
            continue
        exists = target.exists() or target.is_symlink()
        if exists and skill.name not in managed and not force:
            print(f"  conflict  {skill.name}: exists and not managed by ark (use --force)")
            conflicts += 1
            continue
        print(f"  {'update' if exists else 'add':<9} {skill.name}")
        changes += 1
        owned.add(skill.name)
        if apply:
            target_dir.mkdir(parents=True, exist_ok=True)
            remove(target)
            if mode == "symlink":
                target.symlink_to(link_target(skill.path, target_dir), target_is_directory=True)
            else:
                shutil.copytree(skill.path, target, symlinks=True)

    for name in sorted(managed - {s.name for s in skills}):
        print(f"  prune     {name}")
        changes += 1
        if apply:
            remove(target_dir / name)

    if apply and (owned or manifest_path.exists()):
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"managed": sorted(owned)}, indent=2) + "\n")
    return changes, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "vendors", nargs="+", choices=list(VENDORS), metavar="VENDOR", help=f"one or more of: {', '.join(VENDORS)}"
    )
    parser.add_argument("--user", action="store_true", help="sync to the vendor's home folder, not the repo")
    parser.add_argument("--copy", action="store_true", help="copy skills instead of symlinking them")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    group.add_argument("--check", action="store_true", help="like --dry-run, exit 1 if out of sync")
    parser.add_argument("--force", action="store_true", help="replace unmanaged entries that clash with a skill")
    args = parser.parse_args()
    vendors = list(dict.fromkeys(args.vendors))

    skills, errors = discover_skills()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        # Syncing now would prune the clashing skill from every vendor.
        print("Nothing synced: rename the duplicate skill folders first.", file=sys.stderr)
        return 1
    for warning in frontmatter_warnings(skills):
        print(f"warning: {warning}", file=sys.stderr)
    missing_fields = opencode_warnings(skills) if "opencode" in vendors else []
    for warning in missing_fields:
        print(f"warning: {warning}", file=sys.stderr)

    if not args.user:
        folders = {VENDORS[v][0] for v in vendors}
        for vendor in vendors:
            overlap = sorted(ALSO_READS.get(vendor, set()) & folders)
            if overlap:
                print(f"warning: {vendor} also reads {', '.join(overlap)}, so skills load twice", file=sys.stderr)

    mode = "copy" if args.copy else "symlink"
    apply = not (args.dry_run or args.check)
    total_changes = total_conflicts = 0
    for vendor in vendors:
        skills_dir = VENDORS[vendor][1 if args.user else 0]
        target_dir = resolve_dir(skills_dir)
        print(f"{vendor} -> {skills_dir} ({mode})")
        changes, conflicts = sync_dir(target_dir, mode, skills, apply, args.force)
        if not changes and not conflicts:
            print("  up to date")
        total_changes += changes
        total_conflicts += conflicts

    verb = "applied" if apply else "pending"
    print(f"\n{len(skills)} skill(s), {total_changes} change(s) {verb}, {total_conflicts} conflict(s)")
    if total_conflicts or (args.check and (total_changes or missing_fields)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

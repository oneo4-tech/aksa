"""Create the repo-root symlinks to external resources listed in agentic/config/environment.yaml.

Usage: uv run agentic/scripts/link_external.py [--dry-run | --check]

environment.yaml maps each link name (a single repo-root entry, such as .kb) to an
absolute target directory. That file is the only place absolute paths live; the
rest of the repository refers to the links by their repo-relative names.

A missing link is added and a link to another target is updated. A real file or
folder where a link should be, or a target that does not exist, is an error and
is left untouched.

--dry-run prints the plan. --check does the same and exits 1 if anything is out
of sync. Exit 1 also on errors.
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "agentic" / "config" / "environment.yaml"


class ConfigError(Exception):
    """environment.yaml is malformed."""


def load_links(config: Path) -> dict[str, Path]:
    """Link name -> absolute target. Raises ConfigError on a malformed config."""
    data = yaml.safe_load(config.read_text()) or {}
    links = data.get("links") if isinstance(data, dict) else None
    if not isinstance(links, dict):
        raise ConfigError(f"{config.name}: 'links' must be a mapping of link name to target")
    result: dict[str, Path] = {}
    for name, target in links.items():
        if not isinstance(name, str) or not isinstance(target, str):
            raise ConfigError(f"{config.name}: link {name!r} must map a name to a path string")
        if Path(name).name != name or name in {".", ".."}:
            raise ConfigError(f"{config.name}: link {name!r} must be a single repo-root entry")
        path = Path(target).expanduser()
        if not path.is_absolute():
            raise ConfigError(f"{config.name}: target of {name!r} must be absolute, got {target!r}")
        result[name] = path
    return result


def sync_links(links: dict[str, Path], apply: bool) -> tuple[int, int]:
    """Create or repair each link. Returns (changes, errors)."""
    changes = errors = 0
    for name, target in links.items():
        link = REPO_ROOT / name
        if link.is_symlink() and os.readlink(link) == str(target):
            if not target.is_dir():
                print(f"  error     {name}: target {target} is not a directory")
                errors += 1
            continue
        if link.exists() and not link.is_symlink():
            print(f"  error     {name}: a real file or folder is in the way, move it first")
            errors += 1
            continue
        if not target.is_dir():
            print(f"  error     {name}: target {target} is not a directory, create it first")
            errors += 1
            continue
        print(f"  {'update' if link.is_symlink() else 'add':<9} {name} -> {target}")
        changes += 1
        if apply:
            if link.is_symlink():
                link.unlink()
            link.symlink_to(target, target_is_directory=True)
    return changes, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    group.add_argument("--check", action="store_true", help="like --dry-run, exit 1 if out of sync")
    args = parser.parse_args()

    try:
        links = load_links(CONFIG)
    except (OSError, ConfigError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    apply = not (args.dry_run or args.check)
    changes, errors = sync_links(links, apply)
    if not changes and not errors:
        print("  up to date")
    verb = "applied" if apply else "pending"
    print(f"\n{len(links)} link(s), {changes} change(s) {verb}, {errors} error(s)")
    return 1 if errors or (args.check and changes) else 0


if __name__ == "__main__":
    sys.exit(main())

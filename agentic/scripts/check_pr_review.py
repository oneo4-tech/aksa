"""Fail a pull request that changes components without a review-component result naming them.

Usage: uv run agentic/scripts/check_pr_review.py BASE_REF [--body-file FILE]

CI passes the pull request body in the PR_BODY environment variable; run locally
with --body-file instead. When the diff from BASE_REF touches AGENTS.md or
agentic/, the body's "## review-component result" section
(.github/pull_request_template.md) must name every changed component: a skill
by its folder, such as agentic/skills/core/add-kb, and any other component by
its file path.

Exit 0 when the check passes or no component changed, 1 when the result is
missing or leaves a component out.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SECTION = "## review-component result"


def components(paths: list[str]) -> list[str]:
    """Changed components: skill folders for skill files, the path itself otherwise."""
    found = set()
    for path in paths:
        parts = path.split("/")
        if parts[:2] == ["agentic", "skills"] and len(parts) > 4:
            found.add("/".join(parts[:4]))
        elif path == "AGENTS.md" or path.startswith("agentic/"):
            found.add(path)
    return sorted(found)


def review_result(body: str) -> str:
    """Text of the review section, without HTML comments; empty when absent."""
    if SECTION not in body:
        return ""
    section = re.split(r"^## ", body.split(SECTION, 1)[1], maxsplit=1, flags=re.MULTILINE)[0]
    return re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL).strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", help="ref the pull request merges into, such as origin/main")
    parser.add_argument("--body-file", type=Path, help="pull request body, when PR_BODY is not set")
    args = parser.parse_args(argv)

    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{args.base}...HEAD"], capture_output=True, text=True, check=True
    )
    changed = components(diff.stdout.splitlines())
    if not changed:
        print("no component changed")
        return 0
    body = os.environ.get("PR_BODY") or (args.body_file.read_text() if args.body_file else "")
    result = review_result(body)
    missing = [component for component in changed if component not in result]
    if missing:
        print(f"name each changed component in the '{SECTION}' section of the pull request body:")
        print("\n".join(f"  - {component}" for component in missing))
        return 1
    print(f"review-component result names all {len(changed)} changed component(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Fail a pull request that changes components without a review-component result.

Usage: uv run agentic/scripts/check_pr_review.py BASE_REF

Run in CI on pull requests, with the pull request body in the PR_BODY environment
variable. When the diff from BASE_REF touches AGENTS.md or agentic/, the body's
"## review-component result" section (.github/pull_request_template.md) must hold
text beyond the template's HTML comment.

Exit 0 when the check passes or no component changed, 1 when the result is missing.
"""

import os
import re
import subprocess
import sys

SECTION = "## review-component result"


def needs_review(paths: list[str]) -> bool:
    """True when a changed path is a component."""
    return any(path == "AGENTS.md" or path.startswith("agentic/") for path in paths)


def review_result(body: str) -> str:
    """Text of the review section, without HTML comments; empty when absent."""
    if SECTION not in body:
        return ""
    section = re.split(r"^## ", body.split(SECTION, 1)[1], maxsplit=1, flags=re.MULTILINE)[0]
    return re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL).strip()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{argv[0]}...HEAD"], capture_output=True, text=True, check=True
    )
    if not needs_review(diff.stdout.splitlines()):
        print("no component changed")
        return 0
    if not review_result(os.environ.get("PR_BODY", "")):
        print(f"components changed: fill the '{SECTION}' section of the pull request body (AGENTS.md, Components)")
        return 1
    print("review-component result present")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

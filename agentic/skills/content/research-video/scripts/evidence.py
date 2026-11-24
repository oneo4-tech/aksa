"""Check each claim's quote against its live source page, and link the page at the quote.

Usage: uv run agentic/skills/content/research-video/scripts/evidence.py CHANNEL N

Reads videos/<N>/citations.json in the channel workspace: a JSON list of claims, each
with these fields (REQUIRED, written by research-video):

  id      C1, C2, ...: unique, cited by research.md and the script
  claim   the claim as the script makes it
  url     the https source page
  quote   the line on that page that backs the claim, copied exactly

For each claim it loads the source page in the system Chrome through Playwright, checks
that the quote is on the page's rendered text exactly, with only runs of whitespace
normalised to one space, and writes back into the file:

  link     the url with a text fragment that opens the page at the quote and highlights it
  found    true when the quote is on the page
  checked  when it was checked, ISO 8601 UTC
  error    only when the page did not load

Each page is loaded once. It prints JSON (claims, found, the ids not found). Gate 2 of
content_issue.py refuses the video while any claim is not found (gate_problems).

Exit codes: 0 every quote found, 1 a page, browser, or file error, 2 bad input (an
invalid citations file or channel), 3 refused (a quote not found on its page).
"""

import argparse
import datetime
import json
import re
import sys
import urllib.parse
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

# A quote longer than START + END words links by its first and last words, as text-fragment
# textStart,textEnd; a shorter one links whole.
START, END = 4, 3
LOAD_TIMEOUT_MS = 60_000
RENDER_WAIT_MS = 1_500
CLAIM_ID = re.compile(r"C[1-9][0-9]*")
TEXT = ["claim", "quote"]


class BadInput(Exception):
    """A missing or invalid citations file or channel: exit 2."""


class PageError(Exception):
    """A source page that did not load: its claims are not found, and the run exits 1."""


class BrowserError(Exception):
    """Chrome did not start: exit 1."""


def claim_problems(claims) -> list[str]:
    """Every missing or invalid field of a citations list, as 'C1: field: problem'."""
    if not (isinstance(claims, list) and claims):
        return ["citations.json: must be a non-empty list of claims"]
    problems = []
    ids = [claim.get("id") for claim in claims if isinstance(claim, dict)]
    for index, claim in enumerate(claims, 1):
        if not isinstance(claim, dict):
            problems.append(f"claim {index}: must be a JSON object")
            continue
        name = claim.get("id")
        if not (isinstance(name, str) and CLAIM_ID.fullmatch(name)):
            problems.append(f"claim {index}: id: must be C followed by a number, such as C1")
            name = f"claim {index}"
        for field in [*TEXT, "url"]:
            if field not in claim:
                problems.append(f"{name}: {field}: missing")
            elif field in TEXT and not (isinstance(claim[field], str) and claim[field].strip()):
                problems.append(f"{name}: {field}: must be a non-empty string")
        url = claim.get("url")
        if "url" in claim and not (isinstance(url, str) and url.startswith("https://") and len(url) > 8):
            problems.append(f"{name}: url: must be an https:// link")
    repeated = sorted({i for i in ids if isinstance(i, str) and ids.count(i) > 1})
    return problems + [f"{name}: id: used by more than one claim" for name in repeated]


def normalise(text: str) -> str:
    """Runs of whitespace, including non-breaking spaces and line breaks, as one space."""
    return re.sub(r"\s+", " ", text).strip()


def _encode(words: list[str]) -> str:
    # A text directive reserves "-", "," and "&", so each is percent-encoded with everything else.
    return urllib.parse.quote(" ".join(words), safe="").replace("-", "%2D")


def fragment_link(url: str, quote: str) -> str:
    """The url with a text fragment that opens the page scrolled to the quote and highlights it."""
    words = normalise(quote).split(" ")
    if len(words) > START + END:
        directive = f"{_encode(words[:START])},{_encode(words[-END:])}"
    else:
        directive = _encode(words)
    return f"{url}{'' if '#' in url else '#'}:~:text={directive}"


def check(claims: list[dict], pages: dict[str, str | PageError], now: datetime.datetime) -> list[dict]:
    """Each claim with its link, whether its quote is on its page, when that was checked, and
    the error of a page that did not load."""
    checked = now.isoformat(timespec="seconds")
    results = []
    for claim in claims:
        page = pages[claim["url"]]
        result = {k: v for k, v in claim.items() if k != "error"} | {
            "link": fragment_link(claim["url"], claim["quote"]),
            "found": isinstance(page, str) and normalise(claim["quote"]) in normalise(page),
            "checked": checked,
        }
        if isinstance(page, PageError):
            result["error"] = str(page)
        results.append(result)
    return results


def gate_problems(claims) -> list[str]:
    """Why a video's citations cannot pass gate 2: an invalid file, or any claim not checked,
    changed since it was checked, or not found on its page. Empty when every claim was found."""
    if problems := claim_problems(claims):
        return problems
    for claim in claims:
        name = claim["id"]
        if not isinstance(claim.get("found"), bool) or "checked" not in claim:
            problems.append(f"{name}: never checked; run evidence.py")
        elif claim.get("link") != fragment_link(claim["url"], claim["quote"]):
            problems.append(f"{name}: url or quote changed since checked; run evidence.py again")
        elif not claim["found"]:
            error = f" ({claim['error']})" if "error" in claim else ""
            problems.append(f"{name}: quote not found on {claim['url']}{error}")
    return problems


def summary(results: list[dict]) -> dict:
    """The claims found and the ids of those not found."""
    missing = [claim["id"] for claim in results if not claim["found"]]
    return {"claims": len(results), "found": len(results) - len(missing), "not_found": missing}


# Thin shell: the citations file and the browser.

Fetch = Callable[[list[str]], dict[str, str | PageError]]


def chrome(urls: list[str]) -> dict[str, str | PageError]:
    """Each page's rendered text, loaded in the system Chrome through Playwright."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    pages: dict[str, str | PageError] = {}
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="chrome")
        except PlaywrightError as error:
            raise BrowserError(f"Chrome did not start; install Google Chrome ({str(error).splitlines()[0]})") from None
        page = browser.new_page()
        for url in urls:
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
                if response is not None and response.status >= 400:
                    pages[url] = PageError(f"HTTP {response.status}")
                    continue
                page.wait_for_timeout(RENDER_WAIT_MS)  # let script-rendered pages fill in
                pages[url] = page.inner_text("body")
            except PlaywrightError as error:
                pages[url] = PageError(str(error).splitlines()[0])
        browser.close()
    return pages


def citations_path(workspace: Path, number: int) -> Path:
    return workspace / "videos" / str(number) / "citations.json"


def read_claims(path: Path) -> list[dict]:
    try:
        claims = json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: no citations.json; research-video writes it") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None
    if problems := claim_problems(claims):
        raise BadInput(f"{path}:\n  " + "\n  ".join(problems))
    return claims


def main(
    argv: list[str] | None = None,
    fetch: Fetch = chrome,
    root: Path = REPO_ROOT,
    now: Callable[[], datetime.datetime] = lambda: datetime.datetime.now(datetime.UTC),
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        path = citations_path(youtube_channel.load(args.channel, root).workspace, args.number)
        claims = read_claims(path)
        pages = fetch(sorted({claim["url"] for claim in claims}))
        results = check(claims, pages, now())
        path.write_text(json.dumps(results, indent=1) + "\n")
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (BrowserError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary(results), indent=1))
    failed = [claim for claim in results if "error" in claim]
    for claim in failed:
        print(f"error: {claim['id']}: {claim['url']}: {claim['error']}", file=sys.stderr)
    missing = [claim for claim in results if not claim["found"] and "error" not in claim]
    for claim in missing:
        print(f"refused: {claim['id']}: quote not found on {claim['url']}", file=sys.stderr)
    return 1 if failed else 3 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

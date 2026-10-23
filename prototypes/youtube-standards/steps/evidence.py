"""PROTOTYPE: evidence capture for a citation dossier.

For each claim: load the source page in Chrome, confirm the exact quote is on the page, highlight it, screenshot the
viewport, save a text snapshot with its SHA-256, and build a text-fragment link that opens the page at the quote.

uv run --no-project --with playwright steps/evidence.py -> out/evidence/<id>.png, <id>.txt, evidence.json
"""

import hashlib
import json
import re
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "out" / "evidence"
CLAIMS = [
    (
        "C1",
        "https://playwright.dev/docs/test-agents",
        "Playwright comes with three Playwright Test Agents out of the box",
    ),
    (
        "C2",
        "https://github.com/microsoft/playwright/releases/tag/v1.56.0",
        "three custom agent definitions designed to guide LLMs through the core process of building a Playwright test",
    ),
    (
        "C3",
        "https://playwright.dev/docs/test-agents",
        "executes the test suite and automatically repairs failing tests",
    ),
    (
        "C4",
        "https://playwright.dev/docs/test-agents",
        "Re-runs the test until it passes or until guardrails stop the loop",
    ),
    (
        "C5",
        "https://playwright.dev/docs/test-agents",
        "a skipped test if the healer believes that functionality is broken",
    ),
    (
        "C7",
        "https://developsense.com/blog/2015/03/oracles-are-about-problems-not-correctness",
        "an oracle is a means by which we recognize a problem when we encounter one in testing",
    ),
    (
        "C8",
        "https://www.satisfice.com/blog/archives/856",
        "Checking is the mechanistic process of verifying propositions about the product",
    ),
    (
        "C9",
        "https://playwright.dev/docs/test-agents",
        "should be regenerated whenever Playwright is updated to pick up new tools and instructions",
    ),
]
MARK = """quote => {
  const norm = s => s.replace(/\\s+/g, ' ');
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const head = quote.slice(0, 30);
  let node;
  while ((node = walker.nextNode())) {
    const i = norm(node.textContent).indexOf(head);
    if (i < 0) continue;
    const el = node.parentElement;
    el.style.outline = '6px solid #ff2e88'; el.style.background = '#ffe06688';
    el.scrollIntoView({ block: 'center' });
    return true;
  }
  return false;
}"""


def fragment(url: str, quote: str) -> str:
    words = quote.split()
    start, end = " ".join(words[:4]), " ".join(words[-3:])
    return f"{url}#:~:text={urllib.parse.quote(start)},{urllib.parse.quote(end)}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        for cid, url, quote in CLAIMS:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            text = re.sub(r"\s+", " ", page.inner_text("body"))
            found = quote in text
            marked = page.evaluate(MARK, quote) if found else False
            page.screenshot(path=str(OUT / f"{cid}.png"))
            (OUT / f"{cid}.txt").write_text(text)
            rows.append(
                {
                    "claim": cid,
                    "url": url,
                    "quote": quote,
                    "found_exact": found,
                    "highlighted": marked,
                    "link": fragment(url, quote),
                    "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
                    "checked": datetime.now(UTC).isoformat(timespec="seconds"),
                }
            )
            print(cid, "found" if found else "NOT FOUND", url)
        browser.close()
    (OUT / "evidence.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()

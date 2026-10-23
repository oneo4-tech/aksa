"""PROTOTYPE: record a browser UI test with Playwright (system Chrome). -> out/capture/playwright.mp4"""

import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "capture"
VID = OUT / "pw-raw"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(VID),
        record_video_size={"width": 1920, "height": 1080},
    )
    page = ctx.new_page()
    page.goto((HERE / "content" / "checkout.html").as_uri())
    page.wait_for_timeout(800)
    page.locator("#price").press_sequentially("100", delay=120)
    page.locator("#pct").press_sequentially("10", delay=120)
    page.wait_for_timeout(400)
    page.locator("#apply").hover()
    page.wait_for_timeout(400)
    page.locator("#apply").click()
    page.wait_for_timeout(600)
    total = page.locator("#total")
    total.evaluate("e => e.style.outline = '6px solid #cf222e'")
    print("UI shows:", total.inner_text(), "| expected: Total: 90.00")
    page.wait_for_timeout(2500)
    ctx.close()
    browser.close()

webm = next(VID.glob("*.webm"))
subprocess.run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(webm),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        str(OUT / "playwright.mp4"),
    ],
    check=True,
)
shutil.rmtree(VID)

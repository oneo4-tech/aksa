"""Media test for the brand-channel skill's branding.py: every asset rendered in the real Chrome with the real
fonts. Marked media; it runs locally and is skipped in CI (#28)."""

import json
import os
import struct
from pathlib import Path

import pytest
from test_branding import SIZES, branding, folder
from test_youtube_channel import workspace

ISSUE = "https://github.com/oneo4-tech/aksa/issues/28"
pytestmark = [
    pytest.mark.media,
    pytest.mark.skipif(os.environ.get("CI") == "true", reason=f"CI has no Chrome or fonts; run locally ({ISSUE})"),
]
BOXES = (
    "[...document.querySelectorAll('text')].map(t => { const b = t.getBBox(); return [b.x, b.y, b.width, b.height]; })"
)


@pytest.fixture(scope="module")
def tools():
    """Skip, naming what is missing, unless the fonts and Chrome are here."""
    fonts = Path(os.environ.get(branding.FONTS_VARIABLE) or branding.FONTS_DIR)
    missing = [f"font {name}" for name in branding.FONTS.values() if not (fonts / name).is_file()]
    if missing:
        pytest.skip(f"missing {', '.join(missing)} (README, Setup)")
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        try:
            playwright.chromium.launch(channel="chrome").close()
        except Error:
            pytest.skip("Google Chrome is not installed (README, Setup)")


def test_every_asset_renders_at_its_youtube_size_under_its_limit(tmp_path, tools, capsys):
    workspace(tmp_path)
    assert branding.main(["example"], root=tmp_path) == 0
    report = {asset["name"]: asset for asset in json.loads(capsys.readouterr().out)["assets"]}
    for name, size in SIZES.items():
        data = (folder(tmp_path) / f"{name}.png").read_bytes()
        assert struct.unpack(">II", data[16:24]) == size, name
        assert report[name]["limit"] is None or len(data) < report[name]["limit"], name
    if out := os.environ.get("BRANDING_OUT"):  # keep the renders to look at
        for name in SIZES:
            Path(out, f"{name}.png").write_bytes((folder(tmp_path) / f"{name}.png").read_bytes())


def test_banner_lines_measured_in_chrome_sit_inside_the_safe_area(tmp_path, tools, capsys):
    workspace(tmp_path)
    assert branding.main(["example"], root=tmp_path) == 0
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        tab = browser.new_page(viewport={"width": 2048, "height": 1152})
        tab.set_content(branding.page((folder(tmp_path) / "banner.svg").read_text(), branding.font_css()))
        assert tab.evaluate(branding.FONTS_LOADED) is True
        boxes = tab.evaluate(BOXES)
        browser.close()
    left, top = (2048 - 1235) / 2, (1152 - 338) / 2
    assert len(boxes) == 2
    for x, y, width, height in boxes:
        assert left <= x and x + width <= left + 1235
        assert top <= y and y + height <= top + 338


def test_ffmpeg_turns_a_gemini_png_into_a_full_hd_backdrop_jpeg(tmp_path):
    """The real ffmpeg on a 1376x768 PNG (Gemini's 16:9 size): a 1920x1080 JPEG, cropped to fill."""
    import shutil
    import subprocess

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is not installed (README, Setup)")
    png = tmp_path / "art.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=1376x768", "-frames:v", "1", str(png)],
        check=True,
    )
    data = branding.ffmpeg_jpeg(png.read_bytes())
    assert data[:2] == b"\xff\xd8"
    (tmp_path / "out.jpg").write_bytes(data)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(tmp_path / "out.jpg")],
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == "1920,1080"

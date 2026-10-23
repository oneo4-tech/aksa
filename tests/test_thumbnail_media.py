"""Media test for the design-thumbnail skill's thumbnail.py: each layout composed in the real Chrome from fake
art. Marked media; it runs locally and is skipped in CI (#28)."""

import json
import os
import struct
import zlib
from pathlib import Path

import pytest
from test_thumbnail import SUBJECT, TEXT, answer, thumbnail, video

ISSUE = "https://github.com/oneo4-tech/aksa/issues/28"
pytestmark = [
    pytest.mark.media,
    pytest.mark.skipif(os.environ.get("CI") == "true", reason=f"CI has no Chrome or fonts; run locally ({ISSUE})"),
]


@pytest.fixture(scope="module")
def tools():
    """Skip, naming what is missing, unless the fonts and Chrome are here."""
    fonts = Path(os.environ.get(thumbnail.FONTS_VARIABLE) or thumbnail.FONTS_DIR)
    missing = [f"font {name}" for name in thumbnail.FONTS.values() if not (fonts / name).is_file()]
    if missing:
        pytest.skip(f"missing {', '.join(missing)} (README, Setup)")
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        try:
            playwright.chromium.launch(channel="chrome").close()
        except Error:
            pytest.skip("Google Chrome is not installed (README, Setup)")


def disc(side=512):
    """A PNG of a warm disc on the channel background, standing in for Gemini's art."""

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    rows = []
    for y in range(side):
        row = bytearray(b"\0")
        for x in range(side):
            inside = (x - side / 2) ** 2 + (y - side / 2) ** 2 < (side / 3) ** 2
            row += bytes((230, 120, 60) if inside else (15, 15, 15))
        rows.append(bytes(row))
    header = struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0)
    body = zlib.compress(b"".join(rows))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", body) + chunk(b"IEND", b"")


def pixels(data):
    """Width and height of PNG or JPEG bytes."""
    if data.startswith(b"\x89PNG"):
        return struct.unpack(">II", data[16:24])
    at = 2
    while at < len(data):
        marker, length = data[at + 1], struct.unpack(">H", data[at + 2 : at + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[at + 5 : at + 9])
            return width, height
        at += 2 + length
    raise AssertionError("no JPEG frame header")


@pytest.mark.parametrize("layout", thumbnail.LAYOUTS)
def test_each_layout_composes_at_the_youtube_size_under_the_upload_limit(tmp_path, tools, monkeypatch, capsys, layout):
    folder = video(tmp_path)
    monkeypatch.setenv(thumbnail.KEY_VARIABLE, "fake-key-not-real")
    argv = ["example", "14", "--text", TEXT, "--subject", SUBJECT, "--layout", layout]
    assert thumbnail.main(argv, post=lambda body, key: answer(disc()), root=tmp_path) == 0
    report = json.loads(capsys.readouterr().out)
    data = (folder / report["file"]).read_bytes()
    assert pixels(data) == (3840, 2160)
    assert len(data) == report["bytes"] <= thumbnail.LIMIT
    if out := os.environ.get("THUMBNAIL_OUT"):  # keep the result to look at
        Path(out, f"{layout}{Path(report['file']).suffix}").write_bytes(data)

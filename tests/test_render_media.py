"""Media test for the render-video skill's render.py: a two-scene fixture rendered twice with the real
whisper-cli, Chrome, and ffmpeg. Marked media; it runs locally and is skipped in CI (#28)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from test_render import NUMBER, SCENES, files, render

ISSUE = "https://github.com/oneo4-tech/aksa/issues/28"
pytestmark = [
    pytest.mark.media,
    pytest.mark.skipif(
        os.environ.get("CI") == "true", reason=f"CI has no Chrome, ffmpeg, whisper-cli, or fonts; run locally ({ISSUE})"
    ),
]
TERMINAL = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}


@pytest.fixture(scope="module")
def tools():
    """Skip, naming what is missing, unless every tool, the whisper model, the fonts, and Chrome are here."""
    missing = [name for name in ["ffmpeg", "ffprobe", "whisper-cli"] if not shutil.which(name)]
    model = Path(os.environ.get(render.MODEL_VARIABLE) or render.WHISPER_MODEL)
    fonts = Path(os.environ.get(render.FONTS_VARIABLE) or render.FONTS_DIR)
    missing += [] if model.is_file() else [f"whisper model {model.name}"]
    missing += [f"font {name}" for name in render.FONTS.values() if not (fonts / name).is_file()]
    if missing:
        pytest.skip(f"missing {', '.join(missing)} (README, Setup)")
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        try:
            playwright.chromium.launch(channel="chrome").close()
        except Error:
            pytest.skip("Google Chrome is not installed (README, Setup)")


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, capture_output=True, text=True).stdout


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-count_frames", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(out)["streams"]


def frame_hashes(path):
    """One md5 per decoded frame."""
    lines = ffmpeg("-i", str(path), "-f", "framemd5", "-").splitlines()
    return [line.split(",")[-1].strip() for line in lines if not line.startswith("#")]


@pytest.mark.parametrize("kind, size", [("long-form", (1920, 1080)), ("short", (1080, 1920))])
def test_two_scenes_render_at_the_frame_size_with_identical_frames_on_two_renders(tmp_path, tools, kind, size):
    folder = files(tmp_path, scenes=[SCENES[1], TERMINAL], kind=kind, seconds=(1.5, 1.5), demo=True)
    # A 1920x1080 recording stands in for the VHS tape's demo.mp4; render only cuts and fits it.
    ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=30:duration=4",
        "-pix_fmt",
        "yuv420p",
        str(folder / "demo.mp4"),
    )
    renders = []
    for _ in range(2):
        assert render.main(["example", str(NUMBER)], root=tmp_path) == 0
        report = json.loads((folder / "render" / "scenes.json").read_text())
        renders.append([frame_hashes(folder / s["file"]) for s in report["scenes"]])
        for scene in report["scenes"]:
            streams = probe(folder / scene["file"])
            assert [s["codec_type"] for s in streams] == ["video"]  # silent: T13 adds the sound
            video = streams[0]
            assert (video["width"], video["height"], video["r_frame_rate"]) == (*size, "30/1")
            assert int(video["nb_read_frames"]) == scene["frames"]
    assert [s["source"] for s in report["scenes"]] == ["html", "demo"]
    assert renders[0] == renders[1]

"""Media tests for the render-video skill's render.py and assemble.py: a two-scene fixture rendered twice with
the real whisper-cli, Chrome, and ffmpeg. Marked media; they run locally and are skipped in CI (#28)."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from test_assemble import assemble
from test_render import NUMBER, SCENES, files, render
from test_youtube_channel import CONFIG

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


SAYS = ["The test mocks the discount. // So the assert only checks the fake.", "Run it... and it passes anyway."]


def loudness(path):
    """Integrated loudness (LUFS) and true peak (dBTP) of a file's audio, from ffmpeg's EBU R128 meter."""
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stderr
    summary = log[log.rindex("Summary:") :]
    lufs, peak = re.search(r"I: +(-?[\d.]+) LUFS", summary), re.search(r"Peak: +(-?[\d.]+) dBFS", summary)
    return float(lufs[1]), float(peak[1])


@pytest.mark.parametrize("kind, size", [("long-form", (1920, 1080)), ("short", (1080, 1920))])
def test_two_scenes_assemble_with_captions_from_the_script_at_the_channels_loudness(tmp_path, tools, kind, size):
    if not shutil.which("say"):
        pytest.skip(f"macOS say is missing; it speaks the fixture's narration ({ISSUE})")
    scenes = [SCENES[1] | {"say": SAYS[0]}, TERMINAL | {"say": SAYS[1]}]
    folder = files(tmp_path, scenes=scenes, kind=kind, demo=True)
    for index, say in enumerate(SAYS, 1):  # real speech, so whisper times real words
        text = assemble.caption_words(say)
        wav = folder / "narration" / f"{index:02d}.wav"
        subprocess.run(["say", "-o", str(wav), "--data-format=LEI16@24000", " ".join(text)], check=True)
    ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=30:duration=8",
        "-pix_fmt",
        "yuv420p",
        str(folder / "demo.mp4"),
    )
    music = folder.parents[1] / "music"
    music.mkdir()
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-ac", "2", str(music / "bed.mp3"))  # loops
    finals = []
    for _ in range(2):
        assert render.main(["example", str(NUMBER)], root=tmp_path) == 0
        assert assemble.main(["example", str(NUMBER)], root=tmp_path) == 0
        final = folder / "render" / "final.mp4"
        finals.append(frame_hashes(final))
        streams = probe(final)
        video = next(s for s in streams if s["codec_type"] == "video")
        assert (video["width"], video["height"]) == size
        assert any(s["codec_type"] == "audio" for s in streams)
        lufs, peak = loudness(final)
        print(f"{kind}: {lufs} LUFS, true peak {peak} dBTP")
        assert abs(lufs - CONFIG["loudness"]["lufs"]) <= 1 and peak <= CONFIG["loudness"]["true_peak"]
    srt = folder / "render" / "final.srt"
    if kind == "long-form":
        texts = [" ".join(block.splitlines()[2:]) for block in srt.read_text().strip().split("\n\n")]
        assert " ".join(texts) == " ".join(w for say in SAYS for w in assemble.caption_words(say))
    else:
        assert not srt.exists()
    assert finals[0] == finals[1]

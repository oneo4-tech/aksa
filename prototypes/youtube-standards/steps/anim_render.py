"""PROTOTYPE: render content/anim-scene.html frame by frame with Playwright, then mux narration and music.

uv run --no-project --with playwright steps/anim_render.py  -> out/anim/animated.mp4
"""

import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "anim"
FPS, SECONDS = 30, 23.0

frames = OUT / "frames"
frames.mkdir(parents=True, exist_ok=True)
start = time.time()
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto((HERE / "content" / "anim-scene.html").as_uri())
    page.evaluate("document.fonts.ready")
    for i in range(int(FPS * SECONDS)):
        page.evaluate(f"seek({i / FPS})")
        page.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=92)
    browser.close()
shot = time.time() - start
subprocess.run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames / "%05d.jpg"),
        "-i",
        str(OUT / "voice.wav"),
        "-i",
        str(HERE / "out" / "audio" / "ambient.mp3"),
        "-filter_complex",
        (
            "[2:a]aresample=48000,volume=-30dB,afade=t=out:st=21:d=2[m];[1:a]aresample=48000[v];"
            "[v][m]amix=inputs=2:duration=first:normalize=0[a]"
        ),
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-t",
        str(SECONDS),
        str(OUT / "animated-raw.mp4"),
    ],
    check=True,
)
subprocess.run(
    ["sh", str(HERE / "steps" / "loudnorm.sh"), str(OUT / "animated-raw.mp4"), str(OUT / "mix.wav"), "-14", "-1"],
    check=True,
)
subprocess.run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(OUT / "animated-raw.mp4"),
        "-i",
        str(OUT / "mix.wav"),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        str(OUT / "animated.mp4"),
    ],
    check=True,
)
print(f"frames {shot:.0f}s, total {time.time() - start:.0f}s")

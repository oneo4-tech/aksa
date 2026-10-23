"""PROTOTYPE: three caption styles burned into the same Short. -> out/captions/<style>.mp4

uv run --no-project --with pillow steps/captions.py
Wording comes from the script; timing from whisper-cli (phrases from -ml 32, words from -ml 1).
"""

import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out" / "captions"
SRC = Path("out/ref")
MODEL = Path.home() / ".cache/whisper/ggml-base.en.bin"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
W, H = 1080, 1920


def run(*cmd: str) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def cues(max_len: int) -> list[tuple[float, float, str]]:
    base = OUT / f"ml{max_len}"
    run(
        "whisper-cli",
        "-m",
        str(MODEL),
        "-f",
        str(HERE / SRC / "short1-clean.wav"),
        "-ojf",
        "-ml",
        str(max_len),
        "-sow",
        "-of",
        str(base),
    )
    data = json.loads(Path(f"{base}.json").read_text())
    rows = []
    for seg in data["transcription"]:
        text = seg["text"].strip()
        if re.search(r"\w", text):
            rows.append((seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000, text))
    return rows


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def yellow(text: str) -> Image.Image:
    font = ImageFont.truetype(BOLD, 66)
    img = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(wrap(d, text, font, W - 160)[:3]):
        d.text(
            ((W - d.textlength(ln, font=font)) / 2, 10 + i * 88),
            ln,
            font=font,
            fill="#ffd33d",
            stroke_width=6,
            stroke_fill="black",
        )
    return img


def boxed(text: str) -> Image.Image:
    font = ImageFont.truetype(BOLD, 52)
    img = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, font, int(W * 0.9) - 60)[:3]
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        x, y = (W - tw) / 2, 10 + i * 74
        d.rounded_rectangle((x - 18, y - 8, x + tw + 18, y + 64), 10, fill=(0, 0, 0, 215))
        d.text((x, y), ln, font=font, fill="#ffffff")
    return img


def karaoke(words: list[str], current: int) -> Image.Image:
    font = ImageFont.truetype(BOLD, 74)
    img = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    text = " ".join(words)
    x = (W - d.textlength(text, font=font)) / 2
    for i, w in enumerate(words):
        fill = "#00e5ff" if i == current else "#ffffff"
        d.text((x, 20), w, font=font, fill=fill, stroke_width=7, stroke_fill="black")
        x += d.textlength(w + " ", font=font)
    return img


def burn(name: str, overlays: list[tuple[float, float, Image.Image]], y: int) -> None:
    work = OUT / name
    work.mkdir(parents=True, exist_ok=True)
    inputs, chain, last = [], [], "0:v"
    for k, (a, b, img) in enumerate(overlays):
        png = work / f"{k:03d}.png"
        img.save(png)
        inputs += ["-i", str(png)]
        chain.append(f"[{last}][{k + 1}:v]overlay=0:{y}:enable='between(t,{a:.2f},{b:.2f})'[v{k}]")
        last = f"v{k}"
    run(
        "ffmpeg",
        "-y",
        "-i",
        str(HERE / SRC / "short1-clean.mp4"),
        *inputs,
        "-filter_complex",
        ";".join(chain),
        "-map",
        f"[{last}]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(OUT / f"{name}.mp4"),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    phrases = cues(32)
    burn("a-yellow-outline", [(a, b, yellow(t)) for a, b, t in phrases], 1380)
    burn("b-white-box", [(a, b, boxed(t)) for a, b, t in phrases], 1380)
    words = cues(1)
    groups = [words[i : i + 3] for i in range(0, len(words), 3)]
    overlays = []
    for g in groups:
        texts = [w[2] for w in g]
        for j, (a, b, _) in enumerate(g):
            overlays.append((a, b, karaoke(texts, j)))
    burn("c-word-highlight", overlays, 1300)


if __name__ == "__main__":
    main()

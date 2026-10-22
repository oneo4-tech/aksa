"""PROTOTYPE: assemble slides + one narration engine into a video, caption it with whisper-cli.

uv run --with pillow steps/edit.py <scenes.json> <engine>
-> out/<video>/<engine>.mp4, <engine>.srt; Shorts (tall) get captions burned in.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
MODEL = Path.home() / ".cache/whisper/ggml-base.en.bin"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
PAD = 0.6


def run(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def duration(path: Path) -> float:
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)))


def srt_cues(srt: Path) -> list[tuple[float, float, str]]:
    def sec(t: str) -> float:
        h, m, s = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    cues = []
    for block in srt.read_text().strip().split("\n\n"):
        lines = block.splitlines()
        a, b = lines[1].split(" --> ")
        cues.append((sec(a), sec(b), " ".join(lines[2:]).strip()))
    return cues


def caption_png(text: str, width: int, out: Path) -> None:
    font = ImageFont.truetype(FONT, 64)
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if font.getlength(trial) > width - 160 and line:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    h = 90 * len(lines) + 40
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        x = (width - font.getlength(ln)) / 2
        d.text((x, 20 + i * 90), ln, font=font, fill="#ffd33d", stroke_width=6, stroke_fill="black")
    img.save(out)


def main() -> None:
    scenes_file, engine = Path(sys.argv[1]), sys.argv[2]
    video = json.loads(scenes_file.read_text())
    w, h = map(int, video["format"].split("x"))
    base = HERE / "out" / video["id"]
    work = base / f"work-{engine}"
    work.mkdir(exist_ok=True)
    start = time.time()

    segs = []
    for i, _ in enumerate(video["scenes"]):
        audio, slide, seg = base / engine / f"{i:02d}.wav", base / "slides" / f"{i:02d}.png", work / f"{i:02d}.mp4"
        d = duration(audio) + PAD
        run(
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(slide),
            "-i",
            str(audio),
            "-t",
            f"{d:.2f}",
            "-vf",
            f"scale={w}:{h},fade=in:d=0.25,fade=out:st={d - 0.25:.2f}:d=0.25,format=yuv420p",
            "-af",
            "apad",
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            str(seg),
        )
        segs.append(seg)
    (work / "list.txt").write_text("".join(f"file '{s.name}'\n" for s in segs))
    joined = work / "joined.mp4"
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "list.txt"), "-c", "copy", str(joined))
    edit_s = time.time() - start

    t = time.time()
    wav = work / "joined.wav"
    run("ffmpeg", "-y", "-i", str(joined), "-ar", "16000", "-ac", "1", str(wav))
    run("whisper-cli", "-m", str(MODEL), "-f", str(wav), "-osrt", "-ml", "36", "-sow", "-of", str(base / engine))
    srt = base / f"{engine}.srt"
    caption_s = time.time() - t

    final = base / f"{engine}.mp4"
    if h > w:
        t = time.time()
        cues = [c for c in srt_cues(srt) if re.search(r"\w", c[2])]
        inputs, chain, last = [], [], "0:v"
        for k, (a, b, text) in enumerate(cues):
            png = work / f"cap{k:03d}.png"
            caption_png(text, w, png)
            inputs += ["-i", str(png)]
            chain.append(f"[{last}][{k + 1}:v]overlay=0:1380:enable='between(t,{a:.2f},{b:.2f})'[v{k}]")
            last = f"v{k}"
        run(
            "ffmpeg",
            "-y",
            "-i",
            str(joined),
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
            str(final),
        )
        caption_s += time.time() - t
    else:
        joined.replace(final)

    timing = {
        "video": video["id"],
        "engine": engine,
        "edit_seconds": round(edit_s, 1),
        "caption_seconds": round(caption_s, 1),
        "length_seconds": round(duration(final), 1),
    }
    (base / f"{engine}.timing.json").write_text(json.dumps(timing))
    print(json.dumps(timing))


main()

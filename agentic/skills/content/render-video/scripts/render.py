"""Render a video's scenes into silent clips: animated HTML scenes timed from the narration, and the VHS demo.

Usage: uv run agentic/skills/content/render-video/scripts/render.py CHANNEL N

Reads, in the channel workspace's videos/<N>/:

  script.json        written by write-video-script: type (long-form or short) and scenes, each
                     with kind (title, points, code, terminal), heading, and visual or code
  narration/NN.wav   written by narrate-video, one per scene, NN from 01
  demo.mp4           the VHS recording from build-video-demo, when the video has one
  demo.json          from build-video-demo: folder, the demo's folder in the demo repository
                     clone (channel.yaml demos.path), read for the files code scenes show

and writes render/scenes/NN.mp4, one silent H.264 clip per scene at FPS frames a second,
1920x1080 for a long-form and 1080x1920 for a Short, and render/scenes.json, which it also
prints: type, width, height, fps, and per scene its kind, source (html or demo), file,
narration, seconds, frames, and lead (where the narration starts in the clip).

Timing: whisper-cli (-ml 1 -sow -ojf, the base.en model as narrate-video uses) gives each
narration word its start time. A scene lasts LEAD + its narration + TAIL, rounded up to
whole frames. Each on-screen item (a title word, a point, a terminal line) appears at the
start of the first of its words heard after the previous item's; an item none of whose
words is heard appears at its share of the narration (item i of n at i/n). A code scene
types its file in, then focuses the line naming the word heard, dimming the rest, and
holds each focus at least FOCUS_HOLD seconds.

Picture: references/<kind>.html, one template per scene kind, with references/scene.css and
references/scene.js, the neon-terminal theme coloured from channel.yaml palette. The
scene's cues are inlined as JSON; every animation is a Web Animation, so window.seek(t)
sets any frame exactly. The system Chrome, through Playwright with software raster
(CHROME_ARGS), seeks and screenshots each frame, and ffmpeg encodes them. Fonts are the local files FONTS in RENDER_FONTS, else
.cache/fonts in the home folder (README, Setup), embedded in the page: nothing loads from
the network, so two renders give identical frames.

Terminal scenes play demo.mp4 when it exists: in script order, each from where the
previous one ended, for its own length, fitted inside the frame on the palette background
and fading in and out like the drawn scenes; past the recording's end it shows the last
second, its final frame held. Without demo.mp4, terminal scenes are drawn from visual.

Needs Google Chrome, ffmpeg, ffprobe, whisper-cli with its model, and the fonts (README, Setup).

Exit codes: 0 every scene rendered, 1 a tool or file error, 2 bad input (an invalid script
or channel, or a missing narration or demo file).
"""

import argparse
import base64
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import wave
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

REFERENCES = Path(__file__).resolve().parents[1] / "references"
FPS = 30
SIZES = {"long-form": (1920, 1080), "short": (1080, 1920)}
KINDS = ["title", "points", "code", "terminal"]
LEAD = 0.4  # seconds of picture before the narration starts
TAIL = 0.6  # and after it ends
FADE = 0.3  # every clip fades in and out (style guide: fade transitions)
TYPE_PER_CHAR = 0.012  # code typing speed, seconds a character, as the prototype
TYPE_SHARE = 0.4  # typing takes at most this share of the narration
FOCUS_HOLD = 1.2  # a code focus stays at least this long before it moves
JPEG_QUALITY = 92
# Software raster: GPU raster gave slightly different pixels run to run; sRGB keeps palette colours exact.
CHROME_ARGS = ["--disable-gpu", "--force-color-profile=srgb"]
CRF = 18
FONTS = {"Space Grotesk": "SpaceGrotesk.ttf", "Fira Code": "FiraCode.ttf"}
FONTS_VARIABLE = "RENDER_FONTS"
FONTS_DIR = Path.home() / ".cache" / "fonts"
MODEL_VARIABLE = "WHISPER_MODEL"
WHISPER_MODEL = Path.home() / ".cache" / "whisper" / "ggml-base.en.bin"
PLACEHOLDERS = ["/*{{fonts}}*/", "/*{{css}}*/", "/*{{cues}}*/", "/*{{js}}*/"]
WORD = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")
NAME = re.compile(r"[a-z]+")
STOP = {"the", "and", "for", "with", "that", "this", "are", "was", "you", "not", "but", "its", "has"}
# Names too common in code to point at one line; a spoken "assert" still focuses its line.
CODE_WORDS = {"return", "import", "from", "with", "self", "none", "true", "false", "lambda", "yield"}


class BadInput(Exception):
    """A missing or invalid script, narration, or demo file, or channel: exit 2."""


class ToolError(Exception):
    """Chrome, ffmpeg, ffprobe, whisper-cli, its model, or a font missing or failing: exit 1."""


def words_from(transcript) -> list[dict]:
    """Each heard word, lowercased, with its start and end in seconds, from whisper-cli -ojf JSON."""
    try:
        segments = transcript["transcription"]
        heard = []
        for segment in segments:
            start, end = segment["offsets"]["from"] / 1000, segment["offsets"]["to"] / 1000
            heard += [{"word": w, "start": start, "end": end} for w in WORD.findall(segment["text"].lower())]
        return heard
    except (KeyError, TypeError, AttributeError):
        raise ToolError("whisper-cli wrote JSON without transcription offsets and text") from None


def frame_count(seconds: float) -> int:
    return math.ceil(round(seconds * FPS, 6))


def seek_times(frames: int) -> list[float]:
    return [index / FPS for index in range(frames)]


def scene_frames(narration: float) -> int:
    return frame_count(LEAD + narration + TAIL)


def _keys(text: str) -> set[str]:
    words = WORD.findall(text.lower())
    return {w for w in words if len(w) >= 3 and w not in STOP} or set(words)


def cue_times(items: list[str], words: list[dict], narration: float) -> list[float]:
    """When each item appears, in seconds from the clip's start: at its first heard word, else its share."""
    times, position = [], 0
    for index, item in enumerate(items):
        keys = _keys(item)
        hit = next((j for j in range(position, len(words)) if words[j]["word"] in keys), None)
        if hit is None:
            at = LEAD + narration * index / len(items)
        else:
            at, position = LEAD + words[hit]["start"], hit + 1
        times.append(round(max([at, *times[-1:]]), 3))
    return times


def focus_cues(lines: list[str], words: list[dict]) -> list[dict]:
    """The code line to focus and when: the first line naming a heard word, held FOCUS_HOLD seconds."""
    names = [{n for n in NAME.findall(line.lower()) if len(n) >= 4 and n not in CODE_WORDS} for line in lines]
    focus, current, last = [], None, -math.inf
    for word in words:
        line = next((i for i, found in enumerate(names) if word["word"] in found), None)
        at = LEAD + word["start"]
        if line is None or line == current or at - last < FOCUS_HOLD:
            continue
        focus.append({"line": line, "at": round(at, 3)})
        current, last = line, at
    return focus


def items(scene: dict) -> list[str]:
    """The on-screen items a scene reveals one by one: title words, points, or terminal lines."""
    if scene["kind"] == "title":
        return scene["visual"].split()
    lines = [line.strip() for line in scene["visual"].splitlines() if line.strip()]
    return [line.lstrip("-*• ").strip() for line in lines] if scene["kind"] == "points" else lines


def palette(config: dict) -> dict:
    """The theme colours from channel.yaml palette."""
    colours = config["palette"]
    return {"background": colours["background"], "text": colours["name"], "accent": colours["suffix"]}


def scene_cues(scene: dict, index: int, words: list[dict], narration: float, size, config: dict, code: str | None):
    """Everything the scene's template needs to build its animations, as JSON-ready data."""
    frames = scene_frames(narration)
    cues = {
        "kind": scene["kind"],
        "scene": index,
        "width": size[0],
        "height": size[1],
        "fps": FPS,
        "seconds": frames / FPS,
        "lead": LEAD,
        "narration": narration,
        "fade": FADE,
        "brand": config["name"],
        "heading": scene["heading"],
        "palette": palette(config),
    }
    if scene["kind"] == "code":
        lines = code.expandtabs(4).rstrip("\n").splitlines()
        typing = min(sum(len(line) for line in lines) * TYPE_PER_CHAR, narration * TYPE_SHARE)
        return cues | {
            "file": scene["code"],
            "lines": lines,
            "typing": round(typing, 3),
            "focus": focus_cues(lines, words),
        }
    shown = items(scene)
    return cues | {"items": [{"text": t, "at": at} for t, at in zip(shown, cue_times(shown, words, narration))]}


def plan(script: dict, narrations: list[float], heard: list[list[dict]], config: dict, codes: dict, demo):
    """Each scene's clip: how long, drawn as HTML (with its cues) or cut from the demo (from where).

    demo is the recording's length in seconds, or None when the video has none.
    """
    size, scenes, demo_at = SIZES[script["type"]], [], 0.0
    for index, (scene, narration, words) in enumerate(zip(script["scenes"], narrations, heard), 1):
        frames = scene_frames(narration)
        entry = {"scene": index, "kind": scene["kind"], "frames": frames, "seconds": frames / FPS}
        if scene["kind"] == "terminal" and demo is not None:
            entry |= {"source": "demo", "start": round(min(demo_at, max(demo - 1.0, 0.0)), 3)}
            demo_at += frames / FPS
        else:
            code = codes.get(scene.get("code")) if scene["kind"] == "code" else None
            entry |= {"source": "html", "cues": scene_cues(scene, index, words, narration, size, config, code)}
        scenes.append(entry)
    return scenes


def page(cues: dict, fonts_css: str, references: Path = REFERENCES) -> str:
    """The scene's HTML: its kind's template with the theme, fonts, cues, and shared script inlined."""
    html = (references / f"{cues['kind']}.html").read_text()
    if missing := [p for p in PLACEHOLDERS if p not in html]:
        raise ToolError(f"references/{cues['kind']}.html lacks {', '.join(missing)}")
    # <, >, and & escaped so no text in the cues can end the script element.
    data = json.dumps(cues, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    parts = {
        "/*{{fonts}}*/": fonts_css,
        "/*{{css}}*/": (references / "scene.css").read_text(),
        "/*{{cues}}*/": f"const CUES = {data};\n",
        "/*{{js}}*/": (references / "scene.js").read_text(),
    }
    for placeholder, text in parts.items():
        html = html.replace(placeholder, text)
    return html


def font_css(files: dict[str, bytes]) -> str:
    """@font-face rules embedding each font file, so the page never asks the network for a font."""
    rules = []
    for family, data in files.items():
        source = f"url(data:font/ttf;base64,{base64.b64encode(data).decode()}) format('truetype')"
        rules.append(f"@font-face {{ font-family: '{family}'; src: {source}; font-weight: 300 700; }}")
    return "\n".join(rules)


def encode_command(frames: Path, out: Path) -> list[str]:
    """ffmpeg encoding numbered JPEG frames into a silent H.264 clip at FPS."""
    return [
        "ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"),
        "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF), "-pix_fmt", "yuv420p", "-an", str(out),
    ]  # fmt: skip


def clip_command(demo: Path, start: float, seconds: float, size, background: str, out: Path) -> list[str]:
    """ffmpeg cutting seconds of the VHS recording from start, fitted into size, faded in and out."""
    width, height = size
    filters = ",".join(
        [
            f"fps={FPS}",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x{background.lstrip('#')}",
            "setsar=1",
            f"tpad=stop_mode=clone:stop_duration={seconds:.3f}",
            f"fade=t=in:st=0:d={FADE}",
            f"fade=t=out:st={seconds - FADE:.3f}:d={FADE}",
        ]
    )
    return [
        "ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(demo), "-vf", filters,
        "-t", f"{seconds:.3f}", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF),
        "-pix_fmt", "yuv420p", str(out),
    ]  # fmt: skip


def script_problems(script) -> list[str]:
    """Every field render needs that is missing or invalid, as 'field: problem'."""
    if not isinstance(script, dict):
        return ["script.json: must be a JSON object"]
    problems = [] if script.get("type") in SIZES else ["type: must be long-form or short"]
    scenes = script.get("scenes")
    if not (isinstance(scenes, list) and scenes):
        return problems + ["scenes: must be a non-empty list"]
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or scene.get("kind") not in KINDS:
            problems.append(f"scene {index}: kind: must be title, points, code, or terminal")
            continue
        for field in ["heading", "code" if scene["kind"] == "code" else "visual"]:
            if not (isinstance(scene.get(field), str) and scene[field].strip()):
                problems.append(f"scene {index}: {field}: must be a non-empty string")
    return problems


# Thin shell: whisper-cli, Chrome, ffmpeg, ffprobe, and the video's files.

Transcribe = Callable[[Path], dict]
Shoot = Callable[[str, tuple[int, int], int, Path], None]
Run = Callable[[list[str]], None]
Probe = Callable[[Path], float]


def tool(command: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise ToolError(f"{command[0]} not found; install it (README, Setup)") from None
    except subprocess.CalledProcessError as error:
        raise ToolError(f"{command[0]} failed: {error.stderr.strip()[:400]}") from None


def ffmpeg(command: list[str]) -> None:
    tool(command)


def ffprobe(path: Path) -> float:
    """The length of a media file in seconds."""
    out = tool(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout
    try:
        return float(out.strip())
    except ValueError:
        raise ToolError(f"ffprobe gave no length for {path.name}") from None


def whisper(wav: Path) -> dict:
    """whisper-cli's word-level JSON for wav: one segment per word."""
    model = Path(os.environ.get(MODEL_VARIABLE) or WHISPER_MODEL)
    if not model.is_file():
        raise ToolError(f"whisper model {model.name} missing; download it (README, Setup) or set {MODEL_VARIABLE}")
    with tempfile.TemporaryDirectory() as scratch:
        prefix = Path(scratch) / "words"
        tool(["whisper-cli", "-m", str(model), "-f", str(wav), "-ml", "1", "-sow", "-ojf", "-of", str(prefix), "-np"])
        try:
            return json.loads(prefix.with_suffix(".json").read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ToolError(f"whisper-cli wrote no readable JSON for {wav.name} ({error})") from None


def chrome(html: str, size: tuple[int, int], frames: int, folder: Path) -> None:
    """Each frame of the page, seeked to its time in the system Chrome, as folder/NNNNN.jpg."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="chrome", args=CHROME_ARGS)
        except PlaywrightError as error:
            raise ToolError(f"Chrome did not start; install Google Chrome ({str(error).splitlines()[0]})") from None
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(html)
            if tab.evaluate("window.ready") is not True:
                raise ToolError("the scene's fonts did not load in Chrome; check the font files (README, Setup)")
            for index, at in enumerate(seek_times(frames)):
                tab.evaluate(f"seek({at})")
                tab.screenshot(path=str(folder / f"{index:05d}.jpg"), type="jpeg", quality=JPEG_QUALITY)
        except PlaywrightError as error:
            raise ToolError(f"Chrome failed on the scene ({str(error).splitlines()[0]})") from None
        finally:
            browser.close()


def read_json(path: Path, missing: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: {missing}") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None


def narration_seconds(path: Path) -> float:
    try:
        with wave.open(str(path)) as audio:
            return audio.getnframes() / audio.getframerate()
    except FileNotFoundError:
        raise BadInput(f"{path}: missing; narrate-video writes it") from None
    except (wave.Error, EOFError) as error:
        raise BadInput(f"{path}: not a readable WAV file ({error})") from None


def read_fonts() -> dict[str, bytes]:
    folder = Path(os.environ.get(FONTS_VARIABLE) or FONTS_DIR)
    try:
        return {family: (folder / name).read_bytes() for family, name in FONTS.items()}
    except FileNotFoundError as error:
        raise ToolError(f"font {Path(error.filename).name} missing in {folder}; install it (README, Setup)") from None


def read_codes(script: dict, video: Path, config: dict, root: Path) -> dict[str, str]:
    """The text of each demo file a code scene shows, from the demo repository clone."""
    shown = sorted({s["code"] for s in script["scenes"] if s["kind"] == "code"})
    if not shown:
        return {}
    record = read_json(video / "demo.json", "missing; build-video-demo writes it")
    if not (isinstance(record, dict) and isinstance(record.get("folder"), str) and record["folder"].strip()):
        raise BadInput(f"{video / 'demo.json'}: folder: must be the demo's folder name")
    folder = root / ".projects" / "content" / config["demos"]["path"] / record["folder"]
    codes = {}
    for name in shown:
        try:
            codes[name] = (folder / name).read_text()
        except FileNotFoundError:
            raise BadInput(f"{folder / name}: missing; build-video-demo builds the files code scenes show") from None
    return codes


def render(video: Path, script: dict, config: dict, root: Path, transcribe, shoot, run, probe) -> dict:
    """Every scene of the video into render/scenes/NN.mp4; the report of what was rendered."""
    wavs = [video / "narration" / f"{index:02d}.wav" for index in range(1, len(script["scenes"]) + 1)]
    narrations = [narration_seconds(wav) for wav in wavs]
    codes = read_codes(script, video, config, root)
    fonts = font_css(read_fonts())
    demo = video / "demo.mp4"
    demo_seconds = probe(demo) if demo.is_file() else None
    heard = [words_from(transcribe(wav)) for wav in wavs]
    scenes = plan(script, narrations, heard, config, codes, demo_seconds)
    out = video / "render" / "scenes"
    out.mkdir(parents=True, exist_ok=True)
    size, background = SIZES[script["type"]], config["palette"]["background"]
    report = []
    for scene in scenes:
        clip = out / f"{scene['scene']:02d}.mp4"
        if scene["source"] == "demo":
            run(clip_command(demo, scene["start"], scene["seconds"], size, background, clip))
        else:
            with tempfile.TemporaryDirectory() as frames:
                shoot(page(scene["cues"], fonts), size, scene["frames"], Path(frames))
                run(encode_command(Path(frames), clip))
        report.append(
            {
                "scene": scene["scene"],
                "kind": scene["kind"],
                "source": scene["source"],
                "file": f"render/scenes/{clip.name}",
                "narration": f"narration/{clip.name.replace('.mp4', '.wav')}",
                "seconds": scene["seconds"],
                "frames": scene["frames"],
                "lead": LEAD,
            }
        )
    return {"type": script["type"], "width": size[0], "height": size[1], "fps": FPS, "scenes": report}


def main(
    argv: list[str] | None = None,
    transcribe: Transcribe = whisper,
    shoot: Shoot = chrome,
    run: Run = ffmpeg,
    probe: Probe = ffprobe,
    root: Path = REPO_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        script = read_json(video / "script.json", "missing; write-video-script writes it")
        if problems := script_problems(script):
            raise BadInput(f"{video / 'script.json'}:\n  " + "\n  ".join(problems))
        report = render(video, script, channel.config, root, transcribe, shoot, run, probe)
        (video / "render" / "scenes.json").write_text(json.dumps(report, indent=1) + "\n")
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

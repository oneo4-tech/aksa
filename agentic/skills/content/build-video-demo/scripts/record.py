"""Record a video's terminal demo as one clip per terminal scene, from the demo folder's VHS tape.

Usage: uv run agentic/skills/content/build-video-demo/scripts/record.py CHANNEL N

Reads, in the channel workspace's videos/<N>/, script.json (its terminal scenes, counted) and
demo.json (folder, the demo's folder in the demo repository clone, channel.yaml demos.path),
and that folder's demo.tape. The tape marks the start of each terminal scene's steps with a
comment line "# scene" (optionally with a label after a colon, such as "# scene: the boundary mutant");
everything before the first marker, the settings, the one Output line, and the hidden setup,
is shared. For the K-th section it writes a tape of the shared part, its Output set to
demo-K.mp4, and that section alone, runs vhs on it from the demo folder, and moves
demo-K.mp4 to videos/<N>/demo-K.mp4, where render-video plays it for the K-th terminal
scene. Each section runs after a fresh setup, so it must not need an earlier section's state.
The full tape still records the whole demo (vhs demo.tape) for a viewer: the markers are
comments to vhs.

Prints each recording written. Exit codes: 0 every section recorded, 1 vhs missing or failing
or a file error, 2 bad input (an invalid channel, a missing or invalid script.json,
demo.json, or demo.tape, or a tape without exactly one Output line before the first
marker), 3 refused: the tape's section count differs from the script's terminal scenes.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

SCENE = re.compile(r"#\s*scene(:.*)?")
OUTPUT = re.compile(r"Output\s+\S+")


class BadInput(Exception):
    """A missing or invalid script, demo record, or tape, or channel: exit 2."""


class Refused(Exception):
    """The tape and the script disagree on the terminal scenes: exit 3."""


class ToolError(Exception):
    """vhs missing or failing: exit 1."""


def split(tape: str) -> tuple[list[str], list[list[str]]]:
    """The shared lines before the first scene marker, and each section's lines after its marker."""
    shared, sections = [], []
    for line in tape.splitlines():
        if SCENE.fullmatch(line.strip()):
            sections.append([])
        elif sections:
            sections[-1].append(line)
        else:
            shared.append(line)
    outputs = [i for i, line in enumerate(shared) if OUTPUT.fullmatch(line.strip())]
    if len(outputs) != 1 or any(OUTPUT.fullmatch(line.strip()) for s in sections for line in s):
        raise BadInput("demo.tape: needs exactly one Output line, before the first '# scene' marker")
    return shared, sections


def section_tapes(tape: str, terminals: int) -> list[str]:
    """One tape per scene section: the shared part with its Output set to demo-K.mp4, then the section."""
    shared, sections = split(tape)
    if len(sections) != terminals:
        raise Refused(
            f"demo.tape has {len(sections)} '# scene' sections but script.json has {terminals} terminal scenes;"
            " mark each terminal scene's steps with one '# scene' line"
        )
    tapes = []
    for k, section in enumerate(sections, 1):
        head = [f"Output demo-{k}.mp4" if OUTPUT.fullmatch(line.strip()) else line for line in shared]
        tapes.append("\n".join(head + section) + "\n")
    return tapes


# Thin shell: vhs and the video's files.

Vhs = Callable[[Path, Path], None]


def vhs(tape: Path, cwd: Path) -> None:
    """Record tape with vhs, run from cwd so the tape's relative paths and Output resolve there."""
    try:
        subprocess.run(["vhs", str(tape)], cwd=cwd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise ToolError("vhs not found; install it (brew install vhs)") from None
    except subprocess.CalledProcessError as error:
        raise ToolError(f"vhs failed on {tape.name}: {(error.stderr or error.stdout).strip()[:400]}") from None


def read_json(path: Path, writer: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: missing; {writer} writes it") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None


def record(channel: str, number: int, root: Path, run: Vhs) -> list[Path]:
    """Every terminal scene's clip into videos/<number>/demo-K.mp4; the paths written."""
    loaded = youtube_channel.load(channel, root)
    video = loaded.workspace / "videos" / str(number)
    script = read_json(video / "script.json", "write-video-script")
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not isinstance(scenes, list):
        raise BadInput(f"{video / 'script.json'}: scenes: must be a list")
    terminals = sum(isinstance(s, dict) and s.get("kind") == "terminal" for s in scenes)
    entry = read_json(video / "demo.json", "build-video-demo")
    if not (isinstance(entry, dict) and isinstance(entry.get("folder"), str) and entry["folder"].strip()):
        raise BadInput(f"{video / 'demo.json'}: folder: must be the demo's folder name")
    folder = root / ".projects" / "content" / loaded.config["demos"]["path"] / entry["folder"]
    try:
        tape = (folder / "demo.tape").read_text()
    except FileNotFoundError:
        raise BadInput(f"{folder / 'demo.tape'}: missing; build-video-demo writes it") from None
    tapes, written = section_tapes(tape, terminals), []
    with tempfile.TemporaryDirectory() as scratch:
        for k, text in enumerate(tapes, 1):
            path = Path(scratch) / f"demo-{k}.tape"
            path.write_text(text)
            run(path, folder)
            target = video / f"demo-{k}.mp4"
            shutil.move(folder / f"demo-{k}.mp4", target)
            written.append(target)
    return written


def main(argv: list[str] | None = None, root: Path = REPO_ROOT, vhs: Vhs = vhs) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        written = record(args.channel, args.number, root, vhs)
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except (ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for path in written:
        print(f"recorded: {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

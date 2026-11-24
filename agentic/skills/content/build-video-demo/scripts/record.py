"""Record a video's terminal demo as one clip per terminal scene, from the demo folder's VHS tape.

Usage: uv run agentic/skills/content/build-video-demo/scripts/record.py CHANNEL N

Run it at the demo stage, and again after narrate-video so each terminal scene follows its narration.

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

A cut Short: when demo.json names "sections" (plan-shorts' cut.py writes them, the long-form tape
section of each of the Short's terminal scenes, in its order), only those sections are kept, in
that order, and the K-th is the Short's K-th terminal scene; N is the Short, so its own
script.json and narration time them and its folder receives demo-K.mp4, replacing the long-form
clips cut.py copied. Everything else, the timing and its refusals, is as for a long-form.

Narration timing: when narrate-video has written videos/<N>/narration/NN.wav for a terminal
scene (NN its scene number), its section is timed from the narration, as render-video plays it
(the narration starting LEAD seconds into the clip). The wav is transcribed with render-video's
whisper; each "# comment" step (a Type line typing "# ...", up to the next one) is cued at the
leading key word of its comment heard after the step before's, else at another of its key words,
as render cues an item; the step starts at the start of the sentence holding that word. The
section's tape gets a leading Sleep and each step's last Sleep (added when the step ends without
one) set so each step starts at its time from the clip's start, which is the shared part's last
Show: typing takes the tape's TypingSpeed (VHS's 50ms default) a character or key press, the
command runs inside the step's last Sleep, and VHS's clip runs VHS_RATE clip seconds a tape second,
so each step's clip time is divided by it. The last step's Sleep holds to the scene's length
(LEAD + narration + TAIL, whole frames) of tape, unscaled, so the clip ends a little short of the
scene (render holds its last frame). A scene without narration records as written.

Prints each recording written. Exit codes: 0 every section recorded, 1 vhs or whisper-cli
missing or failing or a file error, 2 bad input (an invalid channel, a missing or invalid
script.json, demo.json, demo.tape, or narration wav, a tape without exactly one Output line
before the first marker, a narrated section without a "# comment" step, or demo.json sections
not a non-empty list of the tape's section numbers, naming the bad one), 3 refused: the tape's
section count, or a cut Short's named section count, differs from the script's terminal scenes
(naming both counts), a narrated step's comment is unheard (naming the scene and the comment),
or a step or the scene's end comes before the tape can reach it.
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

sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "render-video" / "scripts"))
import render

SCENE = re.compile(r"#\s*scene(:.*)?")
OUTPUT = re.compile(r"Output\s+\S+")
STEP = re.compile(r"""Type(?:@\S+)?\s+(["'`])#\s*(.*?)\1""")  # a "# comment" step's first line, and its comment
SLEEP = re.compile(r"Sleep\s+\S+")
SPEED = re.compile(r"Set\s+TypingSpeed\s+(\S+)")
DURATION = re.compile(r"(\d+(?:\.\d+)?)(ms|s|m)?")
UNITS = {"ms": 0.001, "s": 1, "m": 60, None: 1}
KEYS = r"Enter|Backspace|Delete|Insert|Tab|Space|Escape|Up|Down|Left|Right|PageUp|PageDown|(?:Ctrl|Alt|Shift)\+\S+"
# One VHS command of a line: typed text (each character one TypingSpeed tick), a Sleep, or a key press (one tick).
COMMAND = re.compile(
    rf"""Type(?:@(?P<speed>\S+))?\s+(?P<q>["'`])(?P<text>.*?)(?P=q)|Sleep\s+(?P<sleep>\S+)"""
    rf"|(?:{KEYS})(?:@(?P<key_speed>\S+))?(?:\s+(?P<count>\d+))?"
)
TYPING_SPEED = 0.05  # VHS's default TypingSpeed, 50ms
# Clip seconds a tape second: VHS's clip runs faster than its tape's Sleeps and typing. Measured with vhs 0.12.1 at
# the channel's 1920x1080 tape settings and ffmpeg freezedetect (#86 T1), in two run-to-run groups: 0.964 (pure Sleep
# tapes, typing after "Sleep 10s" at 9.64 s in three runs, and some runs of a four-step typed tape) and 0.983 (most
# runs of that typed tape). It also varies with the mix of typing and Sleep, the screen size, framerate, and load
# (0.92 at 640x360). This rate sits between the groups; re-measure when the media test drifts.
VHS_RATE = 0.974
SENTENCE_END = re.compile(r"""[.!?]["')\]]*$""")


class BadInput(Exception):
    """A missing or invalid script, demo record, or tape, or channel: exit 2."""


class Refused(Exception):
    """The tape and the script disagree on the terminal scenes, or a narrated step is unheard or cannot start in
    time: exit 3."""


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


def seconds(duration: str) -> float:
    match = DURATION.fullmatch(duration)
    if not match:
        raise BadInput(f"demo.tape: '{duration}' is not a VHS duration, such as 500ms or 2s")
    return float(match.group(1)) * UNITS[match.group(2)]


def played(lines: list[str], speed: float) -> float:
    """How long VHS takes over lines: each typed character and key press one tick of speed (or its @ speed), and
    each Sleep its length; settings, comments, and anything else none."""
    total = 0.0
    for line in lines:
        if line.strip().startswith(("#", "Set ", "Output ")):
            continue
        for command in COMMAND.finditer(line):
            if command["sleep"]:
                total += seconds(command["sleep"])
            elif command["q"]:
                total += len(command["text"]) * (seconds(command["speed"]) if command["speed"] else speed)
            else:
                tick = seconds(command["key_speed"]) if command["key_speed"] else speed
                total += int(command["count"] or 1) * tick
    return total


def sentence_split(text: str) -> list[str]:
    """A whisper segment's words as render splits them, the last ending in "." when the segment ends a sentence."""
    words = render.WORD.findall(text.lower())
    if words and SENTENCE_END.search(text.strip()):
        words[-1] += "."
    return words


def step_starts(comments: list[str], words: list[dict], scene: int) -> list[float]:
    """When each "# comment" step starts, in seconds from the clip's start: at the start of the sentence holding its
    leading key word heard after the step before's (else another key word, as render cues an item); refused when
    none is heard."""
    starts, position = [], 0
    for comment in comments:
        hit = render._hit(words, position, render._named(comment))
        if hit is None:
            raise Refused(
                f"scene {scene}: step '# {comment}' is not heard in its narration after the step before it; reword"
                " the comment or the narration so the narrator says its leading word (write-video-script)"
            )
        position = hit + 1
        first = next((j + 1 for j in range(hit - 1, -1, -1) if words[j]["word"].endswith(".")), 0)
        starts.append(round(render.LEAD + words[first]["start"], 3))
    return starts


def narrated(shared: list[str], section: list[str], scene: int, words: list[dict], length: float) -> list[str]:
    """The section with a leading Sleep and each "# comment" step's last Sleep (added when it has none) set so the
    step starts as its sentence starts, the command running inside that Sleep, and the last step holds to length,
    the scene's seconds. The clip starts at the shared part's last Show. Each step's clip start is converted to tape
    time by VHS_RATE; the scene's end stays length of tape, so the clip ends a little short of the scene, never over.
    Refused when a step, or the scene's end, comes before the tape can reach it."""
    speed = next((seconds(m[1]) for line in shared if (m := SPEED.fullmatch(line.strip()))), TYPING_SPEED)
    shows = [i for i, line in enumerate(shared) if line.strip() == "Show"]
    marks = [i for i, line in enumerate(section) if STEP.match(line.strip())]
    if not marks:
        raise BadInput(f"demo.tape: scene {scene}'s section has no '# comment' step to time from its narration")
    steps = [section[a:b] for a, b in zip(marks, marks[1:] + [len(section)])]
    comments = [STEP.match(step[0].strip())[2] for step in steps]
    starts = step_starts(comments, words, scene) + [length]
    out, at = section[: marks[0]], played(shared[shows[-1] + 1 if shows else 0 :] + section[: marks[0]], speed)
    for k, start in enumerate(starts):
        tape = start / VHS_RATE if k < len(steps) else start
        if tape < at:
            what = f"step '# {comments[k]}' starts with its sentence" if k < len(steps) else "the scene ends"
            reached = at * VHS_RATE if k < len(steps) else at
            raise Refused(
                f"scene {scene}: {what} at {start:.2f} s but the tape reaches it at {reached:.2f} s; give the"
                " narration before it more time or shorten the step before it"
            )
        out.append(f"Sleep {round((tape - at) * 1000)}ms")
        if k < len(steps):
            step = steps[k]
            while not step[-1].strip():
                step = step[:-1]
            body = step[:-1] if SLEEP.fullmatch(step[-1].strip()) else step
            out += body
            at = tape + played(body, speed)
    return out


def sections_of(tape: str, terminals: int, named: object = None) -> tuple[list[str], list[list[str]]]:
    """split, keeping only the named sections (1-based, in their order) for a cut Short whose demo record names them;
    bad input when a named section is not in the tape, refused unless one section remains per terminal scene."""
    shared, sections = split(tape)
    if named is None:
        if len(sections) != terminals:
            raise Refused(
                f"demo.tape has {len(sections)} '# scene' sections but script.json has {terminals} terminal scenes;"
                " mark each terminal scene's steps with one '# scene' line"
            )
        return shared, sections
    if not (isinstance(named, list) and named):
        raise BadInput(f"demo.json: sections: {named!r}: must be a non-empty list of demo.tape '# scene' numbers")
    for k in named:
        if type(k) is not int or not 1 <= k <= len(sections):
            raise BadInput(f"demo.json: sections: {k!r} is not a '# scene' section of demo.tape (1 to {len(sections)})")
    if len(named) != terminals:
        raise Refused(
            f"demo.json names {len(named)} sections but script.json has {terminals} terminal scenes; keep one"
            " terminal scene for each long-form scene the Short cut (plan-shorts)"
        )
    return shared, [sections[k - 1] for k in named]


def section_tapes(shared: list[str], sections: list[list[str]], narrations: list[tuple | None]) -> list[str]:
    """One tape per scene section: the shared part with its Output set to demo-K.mp4, then the section, timed from
    its narration (narrated) when it has one: its scene number, heard words, and seconds; else as written."""
    tapes = []
    for k, (section, narration) in enumerate(zip(sections, narrations), 1):
        head = [f"Output demo-{k}.mp4" if OUTPUT.fullmatch(line.strip()) else line for line in shared]
        body = narrated(shared, section, *narration) if narration else section
        tapes.append("\n".join(head + body) + "\n")
    return tapes


# Thin shell: vhs and the video's files.

Vhs = Callable[[Path, Path], None]
Transcribe = Callable[[Path], dict]


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


def narration(video: Path, scene: int, transcribe: Transcribe) -> tuple | None:
    """A terminal scene's scene number, heard words (sentence_split), and seconds (render's LEAD + narration + TAIL,
    whole frames), or None when narrate-video has not written its narration/NN.wav."""
    wav = video / "narration" / f"{scene:02d}.wav"
    if not wav.is_file():
        return None
    length = render.scene_frames(render.narration_seconds(wav)) / render.FPS
    return scene, render.words_from(transcribe(wav), sentence_split), length


def record(channel: str, number: int, root: Path, run: Vhs, transcribe: Transcribe) -> list[Path]:
    """Every terminal scene's clip into videos/<number>/demo-K.mp4; the paths written."""
    loaded = youtube_channel.load(channel, root)
    video = loaded.workspace / "videos" / str(number)
    script = read_json(video / "script.json", "write-video-script")
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not isinstance(scenes, list):
        raise BadInput(f"{video / 'script.json'}: scenes: must be a list")
    terminals = [i for i, s in enumerate(scenes, 1) if isinstance(s, dict) and s.get("kind") == "terminal"]
    entry = read_json(video / "demo.json", "build-video-demo")
    if not (isinstance(entry, dict) and isinstance(entry.get("folder"), str) and entry["folder"].strip()):
        raise BadInput(f"{video / 'demo.json'}: folder: must be the demo's folder name")
    folder = root / ".projects" / "content" / loaded.config["demos"]["path"] / entry["folder"]
    try:
        tape = (folder / "demo.tape").read_text()
    except FileNotFoundError:
        raise BadInput(f"{folder / 'demo.tape'}: missing; build-video-demo writes it") from None
    shared, sections = sections_of(tape, len(terminals), entry.get("sections"))
    narrations = [narration(video, scene, transcribe) for scene in terminals]
    tapes, written = section_tapes(shared, sections, narrations), []
    with tempfile.TemporaryDirectory() as scratch:
        for k, text in enumerate(tapes, 1):
            path = Path(scratch) / f"demo-{k}.tape"
            path.write_text(text)
            run(path, folder)
            target = video / f"demo-{k}.mp4"
            shutil.move(folder / f"demo-{k}.mp4", target)
            written.append(target)
    return written


def main(
    argv: list[str] | None = None, root: Path = REPO_ROOT, vhs: Vhs = vhs, transcribe: Transcribe = render.whisper
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        written = record(args.channel, args.number, root, vhs, transcribe)
    except (BadInput, render.BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except (ToolError, render.ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for path in written:
        print(f"recorded: {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

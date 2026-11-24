"""Give a Short cut from a long-form video the long-form's demo and the citations its scenes use.

Usage: uv run agentic/skills/content/plan-shorts/scripts/cut.py CHANNEL SHORT --from LONGFORM --scenes 2,3

Reads, in the channel workspace, the long-form's videos/<LONGFORM>/:

  demo.json       from build-video-demo: folder and link, the demo the Short reuses
  citations.json  from research-video, every claim verified (evidence.py)
  script.json     from write-video-script: the scenes, numbered from 1, and the claims each states
  demo-K.mp4      build-video-demo's recording of its K-th terminal scene (record.py)
  demo.mp4        an older long-form's single recording, read only when no demo-K.mp4 exists

and writes into the Short's videos/<SHORT>/, which content_issue.py new created:

  demo.json       the long-form's, unchanged, so the Short shows and links the same demo
  citations.json  the long-form's verified claims that the given scenes state, in its order
  demo-J.mp4      the recording of each cut terminal scene, J counting the Short's terminal
                  scenes in the --scenes order, as render-video numbers them
  demo.mp4        the long-form's single recording, when it has no demo-K.mp4

so the Short passes gate 2 and packaging without new research. It never edits the long-form.

It refuses (exit 3) a long-form output missing or invalid, citations not all verified, a demo
without folder or link, scenes that state no claim, a cut terminal scene without its demo-K.mp4
when the long-form has any, a Short folder that does not exist, and a Short that already has
demo.json or citations.json (never overwritten).

Exit codes: 0 written, 1 a file error, 2 bad input (an invalid channel, a scene number not in
the long-form's script, or a Short cut from itself), 3 refused.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
# The citations format is read through the script that writes it, research-video's evidence.py.
sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "research-video" / "scripts"))
import evidence
import youtube_channel

WRITTEN = ["demo.json", "citations.json"]


class BadInput(Exception):
    """A scene number not in the long-form or a Short cut from itself: exit 2."""


class Refused(Exception):
    """A step the owner or another skill must take first: exit 3."""


def scene_numbers(text: str, count: int) -> list[int]:
    """The 1-based scene numbers of text such as '2,3', each within the long-form's count."""
    try:
        numbers = [int(part) for part in text.split(",")]
    except ValueError:
        numbers = []
    if not numbers or any(not 1 <= n <= count for n in numbers):
        raise BadInput(f"--scenes {text!r}: must be scene numbers from 1 to {count}, such as 2,3")
    return numbers


def used_claims(scenes: list[dict], numbers: list[int], claims: list[dict]) -> list[dict]:
    """The claims the numbered scenes state, in the citations' order; refused when none."""
    used = {c for n in numbers for c in scenes[n - 1].get("claims") or []}
    if not used:
        raise Refused(f"scenes {numbers} state no claim; cut scenes with a cited fact, or plan an independent Short")
    return [claim for claim in claims if claim["id"] in used]


def recordings(source: Path, scenes: list[dict], numbers: list[int]) -> list[tuple[Path, str]]:
    """Each recording the Short needs and its name there: the cut terminal scenes' demo-K.mp4
    renumbered in the Short's order, else the single demo.mp4 when the long-form has only that."""
    terminal = [k for k, scene in enumerate(scenes, 1) if scene.get("kind") == "terminal"]
    clips = {n: source / f"demo-{terminal.index(n) + 1}.mp4" for n in terminal}
    if not any(clip.is_file() for clip in clips.values()):
        return [(source / "demo.mp4", "demo.mp4")] if (source / "demo.mp4").is_file() else []
    cut_clips = [clips[n] for n in numbers if n in clips]
    if missing := [clip.name for clip in cut_clips if not clip.is_file()]:
        raise Refused(f"{source}: {', '.join(missing)} missing; record them with build-video-demo's record.py")
    return [(clip, f"demo-{j}.mp4") for j, clip in enumerate(cut_clips, 1)]


def read(path: Path, writer: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise Refused(f"{path}: missing; {writer} writes it") from None
    except json.JSONDecodeError as error:
        raise Refused(f"{path}: not valid JSON ({error})") from None


def cut(channel: str, short: int, long_form: int, scenes: str, root: Path) -> Path:
    """Write the Short's demo and citations from the long-form's; return the Short's folder."""
    if short == long_form:
        raise BadInput(f"#{short} cannot be cut from itself; --from takes the long-form's number")
    videos = youtube_channel.load(channel, root).workspace / "videos"
    source, target = videos / str(long_form), videos / str(short)
    if not target.is_dir():
        raise Refused(f"{target}: missing; file the Short first with content_issue.py new --parent {long_form}")
    for name in WRITTEN:
        if (target / name).exists():
            raise Refused(f"{target / name}: exists; it is never overwritten")
    demo = read(source / "demo.json", "build-video-demo")
    if not (isinstance(demo, dict) and all(isinstance(demo.get(k), str) and demo[k] for k in ("folder", "link"))):
        raise Refused(f"{source / 'demo.json'}: needs folder and link; build-video-demo writes them")
    claims = read(source / "citations.json", "research-video")
    if problems := evidence.gate_problems(claims):
        raise Refused(f"{source / 'citations.json'}: not all verified:\n  " + "\n  ".join(problems))
    script = read(source / "script.json", "write-video-script")
    if not (isinstance(script, dict) and isinstance(script.get("scenes"), list)):
        raise Refused(f"{source / 'script.json'}: needs scenes; write-video-script writes them")
    numbers = scene_numbers(scenes, len(script["scenes"]))
    used = used_claims(script["scenes"], numbers, claims)
    clips = recordings(source, script["scenes"], numbers)
    (target / "demo.json").write_text(json.dumps(demo, indent=1) + "\n")
    (target / "citations.json").write_text(json.dumps(used, indent=1) + "\n")
    for clip, name in clips:
        shutil.copyfile(clip, target / name)
    return target


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("short", type=int, help="the Short's content issue number")
    parser.add_argument("--from", dest="long_form", type=int, required=True, help="the long-form's issue number")
    parser.add_argument("--scenes", required=True, help="the long-form scene numbers the Short cuts, such as 2,3")
    args = parser.parse_args(argv)
    try:
        folder = cut(args.channel, args.short, args.long_form, args.scenes, root)
    except (youtube_channel.ChannelError, BadInput) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 3
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"written: {folder.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

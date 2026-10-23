"""Check a video's script against the channel's writing rules, length target, and citations.

Usage: uv run agentic/skills/content/write-video-script/scripts/check_script.py CHANNEL N

Reads videos/<N>/script.json in the channel workspace, written by write-video-script:

  title       the video's challenge-style title, at most channel.yaml title_max characters
  type        long-form or short, as the content issue's content-type label
  structure   challenge-first, incident-story, or myth-buster
  acronyms    capitalised terms that are not stress, such as ["AI", "CI"]; may be empty
  scenes      a non-empty list, each with:
    kind      title, points, code, or terminal
    heading   the on-screen heading
    visual    on-screen text (title, points, terminal), where code values and digits belong
    code      for a code scene instead of visual: the demo file shown, such as demo/discount.py
    say       the narration: plain words, // for a pause, ... for a hesitation, no other markup
    claims    the citations.json ids (C1, C2, ...) the scene states as fact; may be empty

It refuses (exit 3), naming each problem, a script that has a banned phrase (in the title, a
heading, visual, or say), a title over title_max, and in say: a sentence of 20 words or more,
three long sentences (LONG_WORDS or more) in a row, digits, more than one CAPS word per
sentence other than acronyms, markup other than // and ..., or a word the channel's
pronunciation list respells; a scene claim not in videos/<N>/citations.json or not found on
its source page; or an estimated length outside the type's target.

Length estimate: words in say at BASE_WPM words a minute times the channel's voice.pace (the
narration's playback speed), plus PAUSE_SECONDS per // and HESITATION_SECONDS per .... BASE_WPM
160 sits in the prototype's 150-165 words-a-minute target and its measured run (381 words in
2.1-2.8 minutes); the pause times are the middles of the measured 1.1-1.4 s and 0.5-0.8 s.

It prints JSON (scenes, words, seconds, target_seconds, words_per_minute).

Exit codes: 0 the script passes, 1 a file error, 2 bad input (an invalid script file or
channel), 3 refused (a writing rule, length, or citation problem).
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

BASE_WPM = 160
PAUSE_SECONDS = 1.25
HESITATION_SECONDS = 0.65
MAX_WORDS = 20  # every sentence stays under this
LONG_WORDS = 16  # a long sentence; never three in a row
TARGET_SECONDS = {"long-form": (300, 600), "short": (30, 60)}
STRUCTURES = ["challenge-first", "incident-story", "myth-buster"]
KINDS = ["title", "points", "code", "terminal"]
CLAIM_ID = re.compile(r"C[1-9][0-9]*")
WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")
PAUSE = "//"
HESITATION = re.compile(r"\.\.\.|…")


class BadInput(Exception):
    """A missing or invalid script file or channel: exit 2."""


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _choices(names: list[str]) -> str:
    return ", ".join(names[:-1]) + f", or {names[-1]}"


def format_problems(script) -> list[str]:
    """Every missing or invalid field of a script file, as 'field: problem'."""
    if not isinstance(script, dict):
        return ["script.json: must be a JSON object"]
    problems = []
    if not _text(script.get("title")):
        problems.append("title: must be a non-empty string")
    if script.get("type") not in TARGET_SECONDS:
        problems.append("type: must be long-form or short")
    if script.get("structure") not in STRUCTURES:
        problems.append(f"structure: must be {_choices(STRUCTURES)}")
    acronyms = script.get("acronyms")
    if not (isinstance(acronyms, list) and all(isinstance(a, str) for a in acronyms)):
        problems.append("acronyms: must be a list of strings; may be empty")
    scenes = script.get("scenes")
    if not (isinstance(scenes, list) and scenes):
        return problems + ["scenes: must be a non-empty list"]
    for index, scene in enumerate(scenes, 1):
        name = f"scene {index}"
        if not isinstance(scene, dict):
            problems.append(f"{name}: must be a JSON object")
            continue
        if scene.get("kind") not in KINDS:
            problems.append(f"{name}: kind: must be {_choices(KINDS)}")
        shown = "code" if scene.get("kind") == "code" else "visual"
        for field in ["heading", shown, "say"]:
            if field not in scene:
                problems.append(f"{name}: {field}: missing")
            elif not _text(scene[field]):
                problems.append(f"{name}: {field}: must be a non-empty string")
        claims = scene.get("claims")
        if not (isinstance(claims, list) and all(isinstance(c, str) and CLAIM_ID.fullmatch(c) for c in claims)):
            problems.append(f"{name}: claims: must be a list of claim ids such as C1; may be empty")
    return problems


def spoken(say: str) -> str:
    """The narration without its pause and hesitation markup."""
    return HESITATION.sub(" ", say.replace(PAUSE, " "))


def sentences(say: str) -> list[list[str]]:
    """Each sentence of the narration as its words; a hesitation does not end a sentence."""
    parts = re.split(r"(?<=[.!?])\s+", spoken(say).strip())
    return [words for part in parts if (words := WORD.findall(part))]


def estimate(scenes: list[dict], pace: float) -> tuple[int, int]:
    """Words spoken, and the narration's estimated seconds at the channel's pace."""
    says = [scene["say"] for scene in scenes]
    words = sum(len(WORD.findall(spoken(say))) for say in says)
    pauses = sum(say.count(PAUSE) for say in says)
    hesitations = sum(len(HESITATION.findall(say)) for say in says)
    seconds = words * 60 / (BASE_WPM * pace) + pauses * PAUSE_SECONDS + hesitations * HESITATION_SECONDS
    return words, round(seconds)


def say_problems(say: str, config: dict, acronyms: set[str]) -> list[str]:
    """Writing rule problems of one scene's narration, beyond banned phrases."""
    problems = []
    for words in sentences(say):
        if len(words) >= MAX_WORDS:
            problems.append(f"sentence of {len(words)} words, keep it under {MAX_WORDS}: '{' '.join(words[:6])} ...'")
        caps = [w for w in words if w.isupper() and sum(c.isalpha() for c in w) > 1 and w not in acronyms]
        if len(caps) > 1:
            problems.append(f"{len(caps)} CAPS words in one sentence ({', '.join(caps)}); stress at most one")
    if digits := re.findall(r"\d+(?:[.,:]\d+)*%?", say):
        problems.append(f"digits '{digits[0]}'; write numbers as spoken words, code values go in visual or code")
    if "<" in say or ">" in say:
        problems.append("markup '<'; only // pauses and ... hesitations are allowed")
    for word, respelling in config["pronunciation"].items():
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", say, re.IGNORECASE):
            problems.append(f"'{word}' must be respelled '{respelling}' (pronunciation list)")
    return problems


def rhythm_problems(scenes: list[dict]) -> list[str]:
    """Each place the narration, read straight through, has three long sentences in a row."""
    problems, run = [], 0
    for index, scene in enumerate(scenes, 1):
        for words in sentences(scene["say"]):
            run = run + 1 if len(words) >= LONG_WORDS else 0
            if run == 3:
                problems.append(
                    f"scene {index}: say: three long sentences in a row, ending '{' '.join(words[:6])} ...'"
                )
    return problems


def problems(script: dict, config: dict, pace: float, citations: list[dict] | None) -> list[str]:
    """Every writing rule, length, and citation problem of a well-formed script."""
    found = []
    if not youtube_channel.title_ok(script["title"], config):
        found.append(f"title: {len(script['title'])} characters; at most {config['title_max']}")
    found += [f"title: banned phrase '{p}'" for p in youtube_channel.banned_phrases(script["title"], config)]
    acronyms = set(script["acronyms"])
    by_id = {c.get("id"): c for c in citations or [] if isinstance(c, dict)}
    for index, scene in enumerate(script["scenes"], 1):
        name = f"scene {index}"
        for field in ["heading", "visual", "say"]:
            phrases = youtube_channel.banned_phrases(scene.get(field, ""), config)
            found += [f"{name}: {field}: banned phrase '{p}'" for p in phrases]
        found += [f"{name}: say: {p}" for p in say_problems(scene["say"], config, acronyms)]
        for claim in scene["claims"] if citations is not None else []:
            if claim not in by_id:
                found.append(f"{name}: claims: {claim} not in citations.json")
            elif by_id[claim].get("found") is not True:
                found.append(f"{name}: claims: {claim} not found on its source page; run evidence.py")
    if citations is None and any(scene["claims"] for scene in script["scenes"]):
        found.append("citations.json: missing; research-video writes it")
    found += rhythm_problems(script["scenes"])
    _, seconds = estimate(script["scenes"], pace)
    low, high = TARGET_SECONDS[script["type"]]
    if not low <= seconds <= high:
        found.append(f"length: about {seconds} s; a {script['type']} needs {low}-{high} s")
    return found


# Thin shell: the script and citations files.


def read_json(path: Path, missing: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        if missing:
            raise BadInput(f"{path}: {missing}") from None
        return None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        folder = channel.workspace / "videos" / str(args.number)
        script = read_json(folder / "script.json", "no script.json; write-video-script writes it")
        if bad := format_problems(script):
            raise BadInput(f"{folder / 'script.json'}:\n  " + "\n  ".join(bad))
        citations = read_json(folder / "citations.json", "")
        if citations is not None and not isinstance(citations, list):
            raise BadInput(f"{folder / 'citations.json'}: must be a list of claims")
        pace = channel.config["voice"]["pace"]
        found = problems(script, channel.config, pace, citations)
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    words, seconds = estimate(script["scenes"], pace)
    report = {
        "scenes": len(script["scenes"]),
        "words": words,
        "seconds": seconds,
        "target_seconds": list(TARGET_SECONDS[script["type"]]),
        "words_per_minute": round(BASE_WPM * pace),
    }
    print(json.dumps(report, indent=1))
    for problem in found:
        print(f"refused: {problem}", file=sys.stderr)
    return 3 if found else 0


if __name__ == "__main__":
    sys.exit(main())

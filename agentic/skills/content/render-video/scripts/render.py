"""Render a video's scenes into silent clips: animated HTML scenes timed from the narration, and the VHS demo.

Usage: uv run agentic/skills/content/render-video/scripts/render.py CHANNEL N

Reads, in the channel workspace's videos/<N>/:

  script.json        written by write-video-script: type (long-form or short) and scenes, each
                     with kind and heading and its kind's fields (Scene kinds, below)
  narration/NN.wav   written by narrate-video, one per scene, NN from 01
  demo-K.mp4         the VHS recording of the K-th terminal scene, from build-video-demo's record.py
  demo.mp4           a single VHS recording of every terminal scene, read only when no demo-K.mp4 exists
  demo.json          from build-video-demo: folder, the demo's folder in the demo repository
                     clone (channel.yaml demos.path), read for the files code and split scenes show

and writes render/scenes/NN.mp4, one silent H.264 clip per scene at FPS frames a second,
1920x1080 for a long-form and 1080x1920 for a Short, and render/scenes.json, which it also
prints: type, width, height, fps, and per scene its kind, source (html or demo), file,
narration, seconds, frames, and lead (where the narration starts in the clip). It also writes
render/alignment.md, the alignment report for gate 3: per drawn scene, each on-screen element
(heading, point, word, line, item, role, activity, stake, panel, mark, focus, file, link, takeaway,
action) with its text, cue, heard (when its own words start), lag (cue minus heard), and the
words said from its cue to one second after, in cue order; elements entering with the scene, not
at words (a code view typing in or shown whole, a repo or kit card, a split's hook, a cold open's
split panels, a link whose word is unheard), are listed as frame. A terminal scene played from a
recording is listed as recording, timed by its tape.

Scene kinds and their fields (marks, link_at, takeaways_at, a kit file's at optional; lines counted from 1):

  title, points, terminal  visual: title words, point lines, or terminal lines
  code     code: a demo file; marks: [{"line": 7, "note": "patches the unit", "at": "patch"}]
  split    left, right: {"code": "demo/checkout.py", "label": "The code", "marks": [...]}, marks
           inside their side; hook (optional, 2 to 8 words): "This test has never failed"
  compare  left, right: {"heading": "Checking", "items": ["...", "`assert x == 1`"]}
  kit      "Take it to your agent" on the repo scene's GitHub card: repo: "oneo4-tech/testlab-demos";
           path: "38-ai-test-mutation/ai-kit"; files: [{"path": "AGENTS.md", "use": "Paste into your
           AGENTS.md or CLAUDE.md", "at": "rules"}, ...]; link_at: "description"; takeaways: ["...", ...];
           takeaways_at: "takeaways"
  intro    the long-form hook before the challenge: roles: ["Developers who let AI write tests", "Testers
           who review that code"] (one to three, drawn as role cards); activity: "Spot the bug in two
           AI-written tests" (the challenge line); stake: "They pass in CI." (a callout)
  repo     the GitHub card introducing the AI kit before it is used: repo: "oneo4-tech/testlab-demos";
           path: "38-ai-test-mutation/ai-kit"; files: ["AGENTS.md", "scripts/find_self_mocks.py", ...];
           link_at: "description"
  cta      the like, share, subscribe, and notification beat before the end: actions: ["like", "share",
           "subscribe", "notify"] (each at most once, drawn in that order)

Timing: whisper-cli (-ml 1 -sow -ojf, the base.en model as narrate-video uses) gives each
narration word its start time. A scene lasts LEAD + its narration + TAIL, rounded up to
whole frames. Every on-screen element enters at its own words, never before. A word names a key or code
name when equal to it or sharing its first STEM letters, a numeral by its words ("90" as ninety). A scene's
heading appears at the first word heard in its own narration naming its leading key word (3 letters or more,
not STOP words), else another of its key words ("Bug one: it mocks the coupon logic" at "bug"). Each on-screen
item (a title word, a point, a terminal line, a split panel by its label, a compare item, an intro's roles,
activity, and stake, a kit takeaway) appears at the start of its leading key word (matched whole) heard after
the previous item's in its list, else at the first of its other key words heard after it ("Developers", not
"let" in an earlier question). A compare's two column headings enter together, at the later of their cues, and
each column's items after them, so the sides alternate as narrated. A kit (kit_cues) lights each file, in order,
at the first heard word naming its at (without one, its path's key words) after the previous file's, wipes in
its link at link_at (default LINK_AT; unheard: after the files), and shows its takeaways last, after both: the
first at its takeaways_at word, else at its own word, each cued only by words the takeaway before it lacks, so
none shows at a word read in an earlier one. A cta brings in each action at the first heard word naming it
(CTA_WORDS: like or likes, share, subscribe or subscribed, notification, notifications, or bell) after the
action before's. A heading, item, mark, kit file or takeaway, cta action, or repo file none of whose words is
heard where it is due is refused, naming the scene, the item, and the fix (reword the item or the narration).
No drawn scene is blank for over BLANK_MAX seconds: one with nothing cued by then, and no code typing in or
cold-open split panels, is refused (filled), naming the fix: open the narration on the heading's words, or add
a filler or transition title scene, such as a question in the centre, before it. Each entrance keeps heard, the
time its own words start, beside its cue; after staggering, an element cued more than a frame before its heard
time is refused (aligned, a backstop the rules above never trip), naming the scene and element.

A code scene types its file in within TYPE_MAX seconds (the first scene, the cold open, shows it whole
from its first frame), so the code is whole as the narrator starts on it, and no focus or mark starts
before typing ends; then it focuses the line naming the word heard, dimming the rest, and holds each focus at least FOCUS_HOLD
seconds; a word naming several lines moves the focus only down, to the first at or after it, so a word
heard again does not pull it back up. A code scene shows at most ROWS lines (style guide: 14, 10 on a
Short); a longer file scrolls with the focus, so the focused line and a line of context round it stay
in view. Every line has the same box; the focus band wipes over it and the arrow points at its last
character. Marks replace that word-driven focus: each focuses its line at the first heard word naming
its at word after the previous mark's, with its note in a chip beside the line over
no code; earlier notes stay, dimmed. A split scene shows its two files side by side (stacked on a
Short), SPLIT_ROWS lines in view a side, scrolling as code does; only marks focus its lines. As the
first scene both files are whole from its first frame; later, each panel enters at its label's cue and
its marks no earlier. A split's hook shows big over a veil from the first frame until the narration's first
sentence ends (split_hook, at most HOOK_MAX seconds), then fades while the panels come forward; the heading,
panels, and marks enter no earlier. A kit draws the repo card (entering at the lead, every file dim), lights only the current
file with its use in a callout beside it (below the card on a Short), and lists the numbered takeaways beside
(below) the card. A cta draws flat icons of its own (a thumb up, a share arrow, a bell, and a subscribe pill in
the palette's deep red, syntax, with "Subscribe" in warm white; no YouTube logo), in a row (two by two on a
Short), each entering at its cue, then doing one short move: a press, one pulse, or one bell swing. A repo card
enters at the lead, lists each
file at the first heard word naming its path's leading key word the file before lacks, else another of them,
and wipes in https://github.com/<repo>/tree/main/<path> at link_at (default LINK_AT; unheard: after the
files). `backticked` text in compare items and kit takeaways shows as code.

Picture: references/<kind>.html, one template per scene kind, with references/scene.css and
references/scene.js, the neon-terminal theme coloured from channel.yaml palette. Every drawn
scene keeps the palette background colour; with channel.yaml background (image: a path in the channel workspace,
such as branding/backdrop.jpg; opacity; fit: cover or contain, the default; all validated by youtube_channel.load),
every drawn scene shows that image embedded as a data URI, still and behind everything (backdrop): contain centres
it at 70% of the frame's width (a Short's width inside its padding); cover fills the frame, cropped, under a scrim,
a gradient of the palette background whose least alpha (scrim) keeps the text and accent colours at CONTRAST over
the image's brightest possible pixel, white, at its opacity; panels stay opaque. The
scene's cues are inlined as JSON; every animation is a Web Animation, so window.seek(t)
sets any frame exactly. A Short's scenes draw nothing in its caption band, from CAPTION_TOP of its height
down, where assemble.py burns the captions: their content ends FLOOR_GAP pixels above it. Motion is medium and purposeful, tuned only in MOTION: each element enters
with one short eased-out move at its cue, focus bands and links wipe in, earlier elements dim, and
entrances start at least MOTION stagger seconds apart (staggered). The system Chrome, through Playwright with software raster
(CHROME_ARGS), seeks and screenshots each frame, and ffmpeg encodes them. Fonts are the local files FONTS in RENDER_FONTS, else
.cache/fonts in the home folder (README, Setup), embedded in the page: nothing loads from
the network, so two renders give identical frames.

Terminal scenes play their recordings, fitted inside the frame on the palette background and
fading in and out like the drawn scenes. With demo-K.mp4 files, the K-th terminal scene plays
demo-K.mp4 whole at its own speed: a clip longer than its scene by more than one frame is
refused, so the tape is timed from the narration or the narration lengthened, and a shorter
one holds its final frame. Every terminal scene needs its clip once any exists. Else, with demo.mp4 (an older
recording, or one plan-shorts copied into a cut Short), terminal scenes play it in script
order, each from where the previous one ended, for its own length; past the recording's end
it shows the last second, its final frame held. With neither, terminal scenes are drawn from
visual.

Needs Google Chrome, ffmpeg, ffprobe, whisper-cli with its model, and the fonts (README, Setup).

Exit codes: 0 every scene rendered, 1 a tool or file error, 2 bad input (an invalid script
or channel (youtube_channel.load refuses a missing background image or an invalid opacity or fit), a missing narration or demo file, a terminal clip longer than its scene, an item or heading whose
words are never heard, a scene with nothing to show within BLANK_MAX seconds, or an element cued before its
own words are heard).
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

sys.path.insert(0, str(REPO_ROOT / "agentic" / "skills" / "content" / "narrate-video" / "scripts"))
import narrate

REFERENCES = Path(__file__).resolve().parents[1] / "references"
FPS = 30
SIZES = {"long-form": (1920, 1080), "short": (1080, 1920)}
# A Short's burned captions (assemble.py, references/captions.html) start this share of its height down; its scenes
# draw nothing below FLOOR_GAP pixels above that band, nor does a long-form below FLOOR pixels from its bottom.
CAPTION_TOP = 0.64
FLOOR_GAP, FLOOR = 40, 90
ROWS = {SIZES["long-form"]: 14, SIZES["short"]: 10}  # code lines in view (style guide: at most 14, 10 on a Short)
SPLIT_ROWS = {SIZES["long-form"]: 16, SIZES["short"]: 10}  # code lines in view on each side of a split
KINDS = ["title", "points", "code", "terminal", "split", "compare", "kit", "intro", "repo", "cta"]
# A cta's actions, in the order a script lists them, each with the heard words that bring in its icon.
CTA_WORDS = {"like": {"like", "likes"}, "share": {"share"}, "subscribe": {"subscribe", "subscribed"},
             "notify": {"notification", "notifications", "bell"}}  # fmt: skip
LINK_AT = "description"  # a kit or repo link appears at this word unless the scene names its own link_at
REPO = re.compile(r"[\w.-]+/[\w.-]+")  # a repo card's repo: owner/name
SIDES = ["left", "right"]
TEXT_FIELDS = {"title": ["visual"], "points": ["visual"], "terminal": ["visual"], "code": ["code"], "kit": ["path"],
               "intro": ["activity", "stake"], "repo": ["path"]}  # fmt: skip
LEAD = 0.4  # seconds of picture before the narration starts
TAIL = 0.6  # and after it ends
FADE = 0.3  # every clip fades in and out (style guide: fade transitions)
TYPE_PER_CHAR = 0.012  # code typing speed, seconds a character, as the prototype
TYPE_SHARE = 0.4  # typing takes at most this share of the narration
TYPE_MAX = 0.6  # and at most this long, so the code is whole as the narrator starts on it and no focus waits
# Motion, the one place its intensity is tuned (scene.js reads it as CUES.motion): an element enters over enter
# seconds, eased out, from offset (a share of its size) off its place; a focus band or link wipes in over wipe;
# an earlier element dims over dim; entrances start at least stagger seconds apart.
MOTION = {"enter": 0.4, "offset": 0.08, "wipe": 0.4, "dim": 0.3, "stagger": 0.15}
# The channel's background image (channel.yaml background, validated by youtube_channel.load), embedded by type so
# nothing loads from a network. A cover image gets a scrim of the palette background (scrim()) so text keeps the
# style guide's CONTRAST; the scrim is SCRIM_EDGE darker at the top and bottom edges, where heading and captions sit.
BACKDROP_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
CONTRAST = 4.5
SCRIM_EDGE = 0.2
FOCUS_HOLD = 1.2  # a code focus stays at least this long before it moves
HOOK_MAX = 3.0  # a split's hook leaves by this many seconds into the clip (split_hook)
HOOK_WORDS = (2, 8)  # and has this many words, fewest and most
BLANK_MAX = 1.0  # something besides the background shows within this many seconds of a scene's start (filled)
STEM = 5  # a heard word names a code name sharing its first STEM letters: "rounded" names round
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
# The alignment report's element kinds by the cue field they sit in; a list's items by their scene's kind.
ELEMENT_KINDS = {"roles": "role", "files": "file", "takeaways": "takeaway", "actions": "action", "left": "panel",
                 "right": "panel"}  # fmt: skip
ITEM_KINDS = {"title": "word", "points": "point", "terminal": "line"}
STOP = {"the", "and", "for", "with", "that", "this", "are", "was", "you", "not", "but", "its", "has"}
# Names too common in code to point at one line; a spoken "assert" still focuses its line.
CODE_WORDS = {"return", "import", "from", "with", "self", "none", "true", "false", "lambda", "yield"}


class BadInput(Exception):
    """A missing or invalid script, narration, or demo file, or channel: exit 2."""


class Unheard(BadInput):
    """An on-screen item or heading none of whose words is heard where it is due; plan names its scene."""

    def __init__(self, text: str):
        super().__init__(
            f'"{text}": none of its words is heard after the item before it; reword the item or the narration so'
            " the narrator says it (write-video-script)"
        )


class ToolError(Exception):
    """Chrome, ffmpeg, ffprobe, whisper-cli, its model, or a font missing or failing: exit 1."""


def words_from(transcript, split: Callable[[str], list[str]] | None = None) -> list[dict]:
    """Each heard word, lowercased (or as split gives a segment's words), with its start and end in seconds,
    from whisper-cli -ojf JSON."""
    split = split or (lambda text: WORD.findall(text.lower()))
    try:
        segments = transcript["transcription"]
        heard = []
        for segment in segments:
            start, end = segment["offsets"]["from"] / 1000, segment["offsets"]["to"] / 1000
            heard += [{"word": w, "start": start, "end": end} for w in split(segment["text"])]
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


def cue_times(items: list[str], words: list[dict]) -> list[dict]:
    """Each item with when it appears and when its words are heard, in seconds from the clip's start (_cues)."""
    return _cues(items, words)[0]


def _cues(items, words, position=0, start=LEAD, distinct=False) -> tuple[list[dict], int]:
    """Each item of a list as text, at (when it appears), and heard (when its words start), from heard word position
    and time start, with the position after its last item: at its leading key word heard after the previous item's,
    else at the first of its other key words heard after it; refused (Unheard) when none is. With distinct, an item
    is cued only by its key words the item before it lacks (all of them when it has no other), so a word read in one
    item does not bring in the next."""
    timed, before = [], set()
    for item in items:
        keys = _keys(item)
        keys, before = (keys - before if distinct and keys - before else keys), keys
        first = next((w for w in WORD.findall(item.lower()) if w in keys), None)
        hit = next((j for j in range(position, len(words)) if words[j]["word"] == first), None)
        hit = next((j for j in range(position, len(words)) if words[j]["word"] in keys), None) if hit is None else hit
        if hit is None:
            raise Unheard(item)
        position = hit + 1
        heard = round(LEAD + words[hit]["start"], 3)
        timed.append(
            {"text": item, "at": round(max([heard, start, *[t["at"] for t in timed[-1:]]]), 3), "heard": heard}
        )
    return timed, position


def kit_cues(scene: dict, words: list[dict]) -> dict:
    """The "Take it to your agent" kit on the repo card: each file lit, with its use, at the first heard word after
    the previous file's naming its at (without one, its path's leading key word, else another); the link at its
    link_at word (default LINK_AT; unheard: after the files); and the takeaways last, after both: the first at its
    takeaways_at word, else at its own word, later ones at their own words (distinct, so no takeaway shows at a word
    of the one before). A file or takeaway unheard is refused (Unheard)."""

    def heard_from(cue: str, position: int) -> int | None:
        return _hit(words, position, narrate.spoken_split(cue))

    shown, times, heard, position = scene["files"], [], [], 0
    for file in shown:
        hit = heard_from(file["at"], position) if "at" in file else _hit(words, position, _named(file["path"]))
        if hit is None:
            raise Unheard(file.get("at", file["path"]))
        position = hit + 1
        heard.append(round(LEAD + words[hit]["start"], 3))
        times.append(max([heard[-1], *times[-1:]]))
    hit = heard_from(scene.get("link_at", LINK_AT), 0)
    link = _link(times[-1], None if hit is None else words[hit])
    start = max(times[-1], link["at"])
    position = max(position, next((j for j, w in enumerate(words) if LEAD + w["start"] >= start), len(words)))
    cued = "takeaways_at" in scene and (hit := heard_from(scene["takeaways_at"], position)) is not None
    if cued:
        position, start = hit, max(start, round(LEAD + words[hit]["start"], 3))
    takeaways = _cues(scene["takeaways"], words, position, start, distinct=True)[0]
    if cued:  # a cued list's first item shows at its cue word
        takeaways[0] |= {"at": start, "heard": round(LEAD + words[hit]["start"], 3)}
    return _card(scene, link) | {
        "files": [{"text": f["path"], "use": f["use"], "at": at, "heard": h} for f, at, h in zip(shown, times, heard)],
        "takeaways": takeaways,
    }


def cta_cues(actions: list[str], words: list[dict]) -> list[dict]:
    """Each action's icon at the first heard word after the previous action's that names it (CTA_WORDS), never
    before the action before it; refused (Unheard) when none is."""
    shown, position = [], 0
    for name in actions:
        hit = next((j for j in range(position, len(words)) if words[j]["word"] in CTA_WORDS[name]), None)
        if hit is None:
            raise Unheard(name)
        position = hit + 1
        heard = round(LEAD + words[hit]["start"], 3)
        shown.append({"name": name, "at": max([heard, *[s["at"] for s in shown[-1:]]]), "heard": heard})
    return shown


def _link(after: float, word: dict | None) -> dict:
    """A GitHub card's link cue: at its heard word, or, unheard, MOTION enter seconds after the files (a frame
    element, without heard)."""
    if word is None:
        return {"at": round(after + MOTION["enter"], 3)}
    heard = round(LEAD + word["start"], 3)
    return {"at": heard, "heard": heard}


def _card(scene: dict, link: dict) -> dict:
    """A GitHub card's cues, shared by repo and kit: the card at the lead and its full link at its link cue."""
    path = scene["path"].strip("/")
    return {
        "repo": scene["repo"],
        "path": path,
        "card": {"at": LEAD},
        "link": {"text": f"https://github.com/{scene['repo']}/tree/main/{path}"} | link,
    }


def repo_cues(scene: dict, words: list[dict]) -> dict:
    """A repo card: the card at the lead, each file at the first heard word after the previous file's naming its
    path's leading key word the file before lacks, else another of them (a name by its first STEM letters), refused
    (Unheard) when none is; the link https://github.com/<repo>/tree/main/<path> at its link_at word (default
    LINK_AT), else after the files."""
    shown, position, before = [], 0, set()
    for name in scene["files"]:
        keys = _named(name)
        keys, before = ([k for k in keys if k not in before] or keys), set(keys)
        hit = _hit(words, position, keys)
        if hit is None:
            raise Unheard(name)
        heard = round(LEAD + words[hit]["start"], 3)
        shown.append({"text": name, "at": max([heard, *[s["at"] for s in shown[-1:]]]), "heard": heard})
        position = hit + 1
    names = narrate.spoken_split(scene.get("link_at", LINK_AT))
    link = _link(shown[-1]["at"], next((w for w in words if _heard(w, names)), None))
    return _card(scene, link) | {"files": shown}


def _names(heard: str, name: str) -> bool:
    return heard == name or len(heard) >= STEM and heard[:STEM] == name[:STEM]


def _heard(word: dict, names) -> bool:
    return any(_names(h, n) for h in narrate.spoken_split(word["word"]) for n in names)


def _named(text: str) -> list[str]:
    """text's key words in its order, a numeral by its words: 3 letters or more and not STOP, else all of them."""
    names = narrate.spoken_split(text)
    return [n for n in names if len(n) >= 3 and n not in STOP] or names


def _hit(words: list[dict], position: int, names: list[str]) -> int | None:
    """The first heard word from position naming names' leading one (a name by its first STEM letters), else the
    first naming any of them; None when none is heard."""
    for wanted in (names[:1], names):
        found = next((j for j in range(position, len(words)) if _heard(words[j], wanted)), None)
        if found is not None:
            return found
    return None


def heading_time(heading: str, words: list[dict]) -> float:
    """When the heading appears: at its leading key word heard in its scene, else at the first of its other key
    words (a numeral by its words, a name by its first STEM letters), so it never shows before the narration names
    one; refused (Unheard) when none is heard."""
    hit = _hit(words, 0, _named(heading))
    if hit is None:
        raise Unheard(heading)
    return round(LEAD + words[hit]["start"], 3)


def focus_cues(lines: list[str], words: list[dict]) -> list[dict]:
    """The code line to focus and when, held FOCUS_HOLD seconds: the line naming a heard word, a numeral by its
    words (narrate.py), in reading order: of several, the first at or after the focus, else none."""
    names = [{n for n in narrate.spoken_split(line) if len(n) >= 4 and n not in CODE_WORDS} for line in lines]
    focus, current, last = [], None, -math.inf
    for word in words:
        heard = [w for w in narrate.spoken_split(word["word"]) if len(w) >= 4]
        found = [i for i, line in enumerate(names) if any(_names(h, n) for h in heard for n in line)]
        ahead = [i for i in found if current is None or i >= current]
        line = found[0] if len(found) == 1 else next(iter(ahead), None)
        at = LEAD + word["start"]
        if line is None or line == current or at - last < FOCUS_HOLD:
            continue
        focus.append({"line": line, "at": round(at, 3), "heard": round(at, 3)})
        current, last = line, at
    return focus


def mark_cues(marks: list[dict], words: list[dict]) -> list[dict]:
    """Each mark's focus, in order: at the first heard word after the previous mark's naming its at word (as
    code names, a numeral by its words), refused (Unheard) when none is; line counted from 0."""
    shown, position = [], 0
    for mark in marks:
        hit = _hit(words, position, narrate.spoken_split(mark["at"]))
        if hit is None:
            raise Unheard(mark["at"])
        position = hit + 1
        heard = round(LEAD + words[hit]["start"], 3)
        at = max([heard, *[s["at"] for s in shown[-1:]]])
        shown.append({"line": mark["line"] - 1, "at": at, "note": mark["note"], "heard": heard})
    return shown


def scroll_tops(count: int, focus: list[dict], rows: int) -> list[int]:
    """The first code line in view at each focus: the view scrolls only when the focused line, with a line of
    context round it, would leave it, and never past the file's end."""
    top, tops = 0, []
    for cue in focus:
        top = max(0, min(top, cue["line"] - 1), cue["line"] + 2 - rows)
        top = min(top, max(count - rows, 0))
        tops.append(top)
    return tops


def items(scene: dict) -> list[str]:
    """The on-screen items a scene reveals one by one: title words, points, or terminal lines."""
    if scene["kind"] == "title":
        return scene["visual"].split()
    lines = [line.strip() for line in scene["visual"].splitlines() if line.strip()]
    return [line.lstrip("-*• ").strip() for line in lines] if scene["kind"] == "points" else lines


def palette(config: dict) -> dict:
    """The theme colours from channel.yaml palette; syntax, the deep red, only fills large shapes (a cta's pill)."""
    colours = config["palette"]
    return {"background": colours["background"], "text": colours["name"], "accent": colours["suffix"],
            "syntax": colours["syntax"]}  # fmt: skip


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
        "heading": {"text": scene["heading"]} | dict.fromkeys(["at", "heard"], heading_time(scene["heading"], words)),
        "palette": palette(config),
        "motion": MOTION,
        "floor": round(size[1] * (1 - CAPTION_TOP)) + FLOOR_GAP if size[1] > size[0] else FLOOR,
    }
    if scene["kind"] == "kit":
        return cues | kit_cues(scene, words)
    if scene["kind"] == "repo":
        return cues | repo_cues(scene, words)
    if scene["kind"] == "cta":
        return cues | {"actions": cta_cues(scene["actions"], words)}
    if scene["kind"] == "intro":
        # Roles, then the activity, then the stake, each at its leading key word as the narrator names it.
        timed = cue_times([*scene["roles"], scene["activity"], scene["stake"]], words)
        return cues | {"roles": timed[:-2], "activity": timed[-2], "stake": timed[-1]}
    if scene["kind"] == "compare":
        # Both column headings together, at the later of their cues, so neither shows before its words; then each
        # column's items after its heading's word and no earlier than the headings, so the sides alternate as the
        # narration does (staggered keeps the right heading with the left).
        headings = {side: _cues([scene[side]["heading"]], words) for side in SIDES}
        together = max(timed[0]["at"] for timed, _ in headings.values())
        for side in SIDES:
            timed, position = headings[side]
            cues[side] = {
                "heading": timed[0] | {"at": together},
                "items": _cues(scene[side]["items"], words, position, together)[0],
            }
        return cues
    if scene["kind"] == "split":
        # The cold open shows both files whole from its first frame; a later split brings each panel in as the
        # narration names its label. Only marks focus a split's lines, never before their panel is in.
        # With a hook, nothing else enters before the hook leaves: the heading, the panels, and their marks wait.
        hook = split_hook(scene, words) if "hook" in scene else 0.0
        if "hook" in scene:
            cues["hook"] = {"text": scene["hook"], "at": 0.0, "until": hook}
            cues["heading"]["at"] = max(cues["heading"]["at"], hook)
        enters = [None, None] if index == 1 else cue_times([scene[s]["label"] for s in SIDES], words)
        for side, enter in zip(SIDES, enters):
            spec = scene[side]
            view = code_view(spec["code"], code[side], spec.get("marks") or [], words, narration,
                             rows=SPLIT_ROWS[tuple(size)], typed=False, scene=index)  # fmt: skip
            panel = {} if enter is None else {"at": max(enter["at"], hook), "heard": enter["heard"]}
            view["focus"] = [cue | {"at": max(cue["at"], panel.get("at", 0), hook)} for cue in view["focus"]]
            cues[side] = {"label": spec["label"]} | view | panel
        return cues
    if scene["kind"] == "code":
        return cues | code_view(scene["code"], code, scene.get("marks"), words, narration, rows=ROWS[tuple(size)],
                                typed=index != 1, scene=index)  # fmt: skip
    return cues | {"items": cue_times(items(scene), words)}


def split_hook(scene: dict, words: list[dict]) -> float:
    """When a split's hook leaves: as the narration's first sentence (of say, up to . ! ? or //) ends, its words
    counted as whisper hears them, at most HOOK_MAX seconds into the clip (also when the sentence is unheard)."""
    count = len(WORD.findall(re.split(r"[.!?]|//", scene.get("say", ""))[0].lower()))
    end = LEAD + words[count - 1]["end"] if 0 < count <= len(words) else HOOK_MAX
    return round(min(end, HOOK_MAX), 3)


def code_view(name, code, marks, words, narration, rows, typed, scene) -> dict:
    """A code view's cues: the file's lines, how long typing takes (0: whole from the first frame), the rows in
    view, and each focus with the view's top line; marks, when given (a list, even empty), replace the
    word-driven focus."""
    lines = code.expandtabs(4).rstrip("\n").splitlines()
    typing = min(sum(len(line) for line in lines) * TYPE_PER_CHAR, narration * TYPE_SHARE, TYPE_MAX) if typed else 0
    typing = round(typing, 3)
    if past := [m["line"] for m in marks or [] if m["line"] > len(lines)]:
        raise BadInput(f"scene {scene}: marks: line {past[0]} is past the end of {name} ({len(lines)} lines)")
    focus = focus_cues(lines, words) if marks is None else mark_cues(marks, words)
    # No band, arrow, or note before the code is whole: typing ends at LEAD + typing.
    focus = [cue | {"at": round(max(cue["at"], LEAD + typing), 3)} for cue in focus]
    tops = scroll_tops(len(lines), focus, rows)
    return {
        "file": name,
        "lines": lines,
        "typing": typing,
        "rows": rows,
        "focus": [cue | {"top": top} for cue, top in zip(focus, tops)],
    }


def _entrances(cues: dict) -> list[dict]:
    """Every entrance in a scene's cues: each object with an at time (the heading, an item, a focus, a mark)."""
    return [entrance for _, entrance in _elements(cues)]


def _elements(node, key: str = "") -> list[tuple[str, dict]]:
    """Every entrance in a scene's cues with the field it sits in: ("items", an item), ("focus", a mark), ..."""
    if isinstance(node, dict):
        own = [(key, node)] if isinstance(node.get("at"), (int, float)) else []
        return own + [e for field, value in node.items() for e in _elements(value, field)]
    return [e for value in node for e in _elements(value, key)] if isinstance(node, list) else []


def _element(cues: dict, field: str, entrance: dict) -> tuple[str, str]:
    """An entrance's kind and text for the alignment report and its refusal; one without heard is a frame element."""
    if field == "focus":  # a mark, or a code line focused by a word naming it
        return ("mark", entrance["note"]) if "note" in entrance else ("focus", f"line {entrance['line'] + 1}")
    text = next((entrance[k] for k in ("text", "label", "name") if k in entrance), field)
    if "heard" not in entrance:
        return "frame", text if text == field else f"{field}: {text}"
    if field == "items":
        return ITEM_KINDS.get(cues["kind"], "item"), text
    return ELEMENT_KINDS.get(field, field), text


def aligned(cues: dict, scene: int) -> dict:
    """The cues, refused when an element is cued more than a frame before its own words are heard: a backstop, as
    the cue rules never place one there."""
    for field, entrance in _elements(cues):
        if "heard" in entrance and entrance["at"] < entrance["heard"] - 1 / FPS:
            kind, text = _element(cues, field, entrance)
            raise BadInput(
                f'scene {scene}: {kind} "{text}" is cued at {entrance["at"]:.2f} s, before its words are heard at'
                f" {entrance['heard']:.2f} s; a render.py cue rule is broken (render-video)"
            )
    return cues


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def alignment(script: dict, scenes: list[dict], heard: list[list[dict]]) -> str:
    """The alignment report, Markdown: per scene, each element's kind, text, cue, heard time, lag, and the words said
    from its cue to one second after, in cue order; a terminal scene played from a recording is named only."""
    lines = ["# Narration alignment", "",
             "Each on-screen element's cue against the narration, in seconds from its clip's start: heard is when its",
             "own words start, lag the cue after that, words what the narrator says from the cue to a second after.",
             "A frame element enters with the scene, not at words."]  # fmt: skip
    for spec, scene, words in zip(script["scenes"], scenes, heard):
        title = f'## Scene {scene["scene"]}: {scene["kind"]} "{_cell(spec["heading"])}"'
        if scene["source"] == "demo":
            lines += ["", title, "",
                      (f"recording: plays {scene['clip']} from {scene['start']:.2f} s, timed by its tape"
                       " (build-video-demo record.py).")]  # fmt: skip
            continue
        cues = scene["cues"]
        rows = [(e["at"], *_element(cues, f, e), e.get("heard")) for f, e in _elements(cues)]
        if cues["kind"] == "code":
            typed = cues["typing"] > 0
            rows.append(
                (LEAD if typed else 0.0, "frame", f"{cues['file']} {'types in' if typed else 'shown whole'}", None)
            )
        rows += [(0.0, "frame", f"{cues[s]['label']} shown whole", None) for s in SIDES
                 if cues["kind"] == "split" and "at" not in cues[s]]  # fmt: skip
        lines += ["", title, "",
                  "| Element | Text | Cue | Heard | Lag | Words said |", "|---|---|---|---|---|---|"]  # fmt: skip
        for at, kind, text, said in sorted(rows, key=lambda row: (row[0], row[3] is not None)):
            spoken = " ".join(w["word"] for w in words if at <= round(LEAD + w["start"], 3) <= at + 1)
            timing = "- | -" if said is None else f"{said:.2f} | {at - said:.2f}"
            lines.append(f"| {kind} | {_cell(text)} | {at:.2f} | {timing} | {spoken} |")
    return "\n".join(lines) + "\n"


def staggered(cues: dict) -> dict:
    """The cues with every entrance starting at least MOTION stagger seconds after the one before it, in time
    order, so only one element starts moving at a time; a compare's two column headings start together."""
    follower = cues["right"]["heading"] if cues["kind"] == "compare" else None  # enters with the left heading
    last = -math.inf
    for entrance in sorted((e for e in _entrances(cues) if e is not follower), key=lambda e: e["at"]):
        entrance["at"] = last = round(max(entrance["at"], last + MOTION["stagger"]), 3)
    if follower:
        follower["at"] = cues["left"]["heading"]["at"]
    return cues


def filled(cues: dict, scene: int) -> dict:
    """The cues, refused when nothing shows within BLANK_MAX seconds of the scene's start: no entrance by then
    and no frame element (code typing in from the lead, a cold open's split panels whole from the first frame).
    Nothing is moved early to fill the gap."""
    shown = [e["at"] for e in _entrances(cues)]
    shown += [LEAD] if cues["kind"] == "code" else []
    shown += [0.0 for side in SIDES if cues["kind"] == "split" and "at" not in cues[side]]
    if not shown or min(shown) > BLANK_MAX:
        raise BadInput(
            f"scene {scene}: nothing shows in its first {BLANK_MAX:g} s; open the narration on the heading's words,"
            " or add a filler or transition title scene (such as a question in the centre) before it"
            " (write-video-script)"
        )
    return cues


def _luminance(colour: list[float]) -> float:
    """WCAG relative luminance of sRGB channels from 0 to 1."""
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in colour]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _rgb(colour: str) -> list[float]:
    return [int(colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def scrim(colours: dict, opacity: float) -> float:
    """The least alpha of the palette background drawn over a cover image so the text and accent colours keep
    CONTRAST over its brightest possible pixel, white. Browsers blend in sRGB, so under scrim alpha s each channel
    of that pixel is b + (1 - s) * opacity * (1 - b), b the background's channel; s is the smallest step of 0.01
    giving (L_text + 0.05) / (L_pixel + 0.05) >= CONTRAST for both colours (WCAG luminance L)."""
    background = _rgb(colours["background"])
    texts = [_luminance(_rgb(colours[c])) for c in ("text", "accent")]
    for step in range(101):
        s = step / 100
        pixel = _luminance([b + (1 - s) * opacity * (1 - b) for b in background])
        if all((t + 0.05) / (pixel + 0.05) >= CONTRAST for t in texts):
            return s
    return 1.0


def backdrop(config: dict, workspace: Path) -> dict:
    """The cues for the channel's background image behind every drawn scene, from channel.yaml background (image, a
    path in the channel workspace, opacity, and fit, validated by youtube_channel.load): {"backdrop": {"image": a
    data URI, "opacity", "fit"}}, or {} without one. fit "contain" (the default) centres the image; "cover" fills
    the frame and adds "scrim": the palette background's alpha over it, at least scrim() in the middle and
    SCRIM_EDGE more at the top and bottom edges, a gradient that keeps text at CONTRAST."""
    spec = config.get("background")
    if spec is None:
        return {}
    name = Path(spec["image"])
    data = (workspace / name).read_bytes()
    uri = f"data:{BACKDROP_TYPES[name.suffix.lower()]};base64,{base64.b64encode(data).decode()}"
    shown = {"image": uri, "opacity": spec["opacity"], "fit": spec.get("fit", "contain")}
    if shown["fit"] == "cover":
        middle = scrim(palette(config), spec["opacity"])
        shown["scrim"] = {"middle": middle, "edge": round(min(1.0, middle + SCRIM_EDGE), 3)}
    return {"backdrop": shown}


def fitted(clip: float, seconds: float, scene: int, name: str) -> None:
    """Refuse a terminal clip longer than its scene by more than one frame: it is never sped up to fit."""
    if clip > seconds + 1 / FPS:
        raise BadInput(
            f"scene {scene}: {name} is {clip:.2f} s but the scene is {seconds:.2f} s;"
            " time the scene's section of demo.tape from the narration (build-video-demo record.py)"
            " or lengthen its narration (write-video-script)"
        )


def plan(script: dict, narrations: list[float], heard: list[list[dict]], config: dict, codes: dict, demo, clips=None):
    """Each scene's clip: how long, drawn as HTML (with its cues), or played from a demo recording.

    clips is the length in seconds of each terminal scene's own recording, demo-K.mp4, in order, or None;
    demo is the single recording's length, or None when the video has none.
    """
    size, scenes, demo_at, terminal = SIZES[script["type"]], [], 0.0, 0
    for index, (scene, narration, words) in enumerate(zip(script["scenes"], narrations, heard), 1):
        frames = scene_frames(narration)
        entry = {"scene": index, "kind": scene["kind"], "frames": frames, "seconds": frames / FPS}
        if scene["kind"] == "terminal" and clips:
            terminal += 1
            name = f"demo-{terminal}.mp4"
            fitted(clips[terminal - 1], frames / FPS, index, name)
            entry |= {"source": "demo", "clip": name, "start": 0.0}
        elif scene["kind"] == "terminal" and demo is not None:
            start = round(min(demo_at, max(demo - 1.0, 0.0)), 3)
            entry |= {"source": "demo", "clip": "demo.mp4", "start": start}
            demo_at += frames / FPS
        else:
            code = codes.get(scene.get("code")) if scene["kind"] == "code" else None
            if scene["kind"] == "split":
                code = {side: codes[scene[side]["code"]] for side in SIDES}
            try:
                cues = scene_cues(scene, index, words, narration, size, config, code)
            except Unheard as error:
                raise BadInput(f"scene {index}: {error}") from None
            entry |= {"source": "html", "cues": aligned(staggered(filled(cues, index)), index)}
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
    """ffmpeg cutting seconds of the VHS recording from start, fitted into size, its final frame held to the end,
    faded in and out."""
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
            problems.append(f"scene {index}: kind: must be {', '.join(KINDS[:-1])}, or {KINDS[-1]}")
            continue
        for field in ["heading", *TEXT_FIELDS.get(scene["kind"], [])]:
            if not _text(scene.get(field)):
                problems.append(f"scene {index}: {field}: must be a non-empty string")
        if scene["kind"] == "code":
            problems += [f"scene {index}: {p}" for p in mark_problems(scene)]
        if scene["kind"] == "split":
            problems += [f"scene {index}: {p}" for p in split_problems(scene)]
            hook = scene.get("hook")
            if "hook" in scene and not (_text(hook) and HOOK_WORDS[0] <= len(hook.split()) <= HOOK_WORDS[1]):
                problems.append(f"scene {index}: hook: must be {HOOK_WORDS[0]} to {HOOK_WORDS[1]} words")
        if scene["kind"] == "compare":
            problems += [f"scene {index}: {p}" for p in compare_problems(scene)]
        if scene["kind"] == "intro" and not (_texts(scene.get("roles")) and len(scene["roles"]) <= 3):
            problems.append(f"scene {index}: roles: must be a list of one to three non-empty strings")
        if scene["kind"] in ("kit", "repo"):
            if not (_text(scene.get("repo")) and REPO.fullmatch(scene["repo"])):
                problems.append(f"scene {index}: repo: must be owner/name")
            problems += [
                f"scene {index}: {cue}: must be a non-empty string"
                for cue in ["link_at", "takeaways_at"][: 2 if scene["kind"] == "kit" else 1]
                if cue in scene and not _text(scene[cue])
            ]
        if scene["kind"] == "repo" and not _texts(scene.get("files")):
            problems.append(f"scene {index}: files: must be a non-empty list of non-empty strings")
        if scene["kind"] == "kit":
            problems += [f"scene {index}: {p}" for p in kit_problems(scene)]
        actions = scene.get("actions")
        valid = isinstance(actions, list) and actions and all(isinstance(a, str) and a in CTA_WORDS for a in actions)
        if scene["kind"] == "cta" and not (valid and len(set(actions)) == len(actions)):
            problems.append(f"scene {index}: actions: must be a list of like, share, subscribe, or notify, each once")
    return problems


def kit_problems(scene: dict) -> list[str]:
    """What is wrong with a kit's files (each path, use, and optional at) and takeaways."""
    shown = scene.get("files")
    if not (isinstance(shown, list) and shown):
        problems = ["files: must be a non-empty list of path, use, and optional at"]
    else:
        problems = []
        for number, file in enumerate(shown, 1):
            if not isinstance(file, dict):
                problems.append(f"files {number}: must be an object of path, use, and optional at")
                continue
            problems += [
                f"files {number}: {f}: must be a non-empty string"
                for f in ["path", "use", "at"]
                if (f != "at" or f in file) and not _text(file.get(f))
            ]
    if not _texts(scene.get("takeaways")):
        problems.append("takeaways: must be a non-empty list of non-empty strings")
    return problems


def split_problems(scene: dict) -> list[str]:
    problems = []
    for side in SIDES:
        spec = scene.get(side)
        if not isinstance(spec, dict):
            problems.append(f"{side}: must be an object of code, label, and optional marks")
            continue
        problems += [f"{side}: {f}: must be a non-empty string" for f in ["code", "label"] if not _text(spec.get(f))]
        problems += [f"{side}: {p}" for p in mark_problems(spec)]
    return problems


def compare_problems(scene: dict) -> list[str]:
    problems = []
    for side in SIDES:
        column = scene.get(side)
        if not isinstance(column, dict):
            problems.append(f"{side}: must be an object of heading and items")
            continue
        if not _text(column.get("heading")):
            problems.append(f"{side}: heading: must be a non-empty string")
        if not _texts(column.get("items")):
            problems.append(f"{side}: items: must be a non-empty list of non-empty strings")
    return problems


def _texts(value) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(v) for v in value)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def mark_problems(holder: dict, where: str = "marks") -> list[str]:
    """What is wrong with the optional marks of a code scene or split side."""
    marks = holder.get("marks")
    if marks is None:
        return []
    if not isinstance(marks, list):
        return [f"{where}: must be a list of line, note, and at"]
    problems = []
    for number, mark in enumerate(marks, 1):
        if not isinstance(mark, dict):
            problems.append(f"{where} {number}: must be an object of line, note, and at")
            continue
        line = mark.get("line")
        if not (isinstance(line, int) and not isinstance(line, bool) and line >= 1):
            problems.append(f"{where} {number}: line: must be a line number from 1")
        problems += [
            f"{where} {number}: {f}: must be a non-empty string" for f in ["note", "at"] if not _text(mark.get(f))
        ]
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
    shown = {s["code"] for s in script["scenes"] if s["kind"] == "code"}
    shown = sorted(shown | {s[side]["code"] for s in script["scenes"] if s["kind"] == "split" for side in SIDES})
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
    brand = backdrop(config, video.parents[1])
    terminals = sum(scene["kind"] == "terminal" for scene in script["scenes"])
    clips = [video / f"demo-{k}.mp4" for k in range(1, terminals + 1)]
    if any(clip.is_file() for clip in clips) and (missing := [c.name for c in clips if not c.is_file()]):
        raise BadInput(
            f"{video}: {', '.join(missing)} missing, one recording per terminal scene; record them with"
            " build-video-demo's record.py"
        )
    clip_seconds = [probe(clip) for clip in clips] if clips and clips[0].is_file() else None
    demo = video / "demo.mp4"
    demo_seconds = probe(demo) if clip_seconds is None and demo.is_file() else None
    heard = [words_from(transcribe(wav)) for wav in wavs]
    scenes = plan(script, narrations, heard, config, codes, demo_seconds, clip_seconds)
    out = video / "render" / "scenes"
    out.mkdir(parents=True, exist_ok=True)
    (video / "render" / "alignment.md").write_text(alignment(script, scenes, heard))
    size, background = SIZES[script["type"]], config["palette"]["background"]
    report = []
    for scene in scenes:
        clip = out / f"{scene['scene']:02d}.mp4"
        if scene["source"] == "demo":
            source = video / scene["clip"]
            run(clip_command(source, scene["start"], scene["seconds"], size, background, clip))
        else:
            with tempfile.TemporaryDirectory() as frames:
                shoot(page(scene["cues"] | brand, fonts), size, scene["frames"], Path(frames))
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

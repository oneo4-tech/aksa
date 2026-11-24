"""Check a video's script against the channel's writing rules, length target, and citations.

Usage: uv run agentic/skills/content/write-video-script/scripts/check_script.py CHANNEL N

Reads videos/<N>/script.json in the channel workspace, written by write-video-script:

  title       the video's challenge-style title, at most channel.yaml title_max characters
  type        long-form or short, as the content issue's content-type label
  structure   challenge-first, incident-story, or myth-buster
  acronyms    capitalised terms that are not stress, such as ["AI", "CI"]; may be empty
  scenes      a non-empty list, each with:
    kind      title, intro, points, code, terminal, split, compare, repo, kit, or cta
    heading   the on-screen heading; the renderer shows it from the first of its words the narrator
              says
    say       the narration: plain words, // for a pause, ... for a hesitation, no other markup
    claims    the citations.json ids (C1, C2, ...) the scene states as fact; may be empty
  and by kind what it shows:
    intro     a long-form's first scene, before the cold open: who the video is for and what they do
      roles   ROLES lines (2-3), who the video is for, such as "Testers who review AI-written code"
      activity  one line: what the viewer will do, such as "Spot the bug in two AI-written tests"
      stake   one line: why it matters, such as "They pass, and checkout still overcharges"
    title, points, terminal
      visual  on-screen text, where code values and digits belong; a points scene is prose, never code
    code
      code    the demo file shown, such as demo/checkout.py
      marks   optional: the lines the narration names, [{"line": N, "note": "short label",
              "at": "word"}], N counted from 1; the renderer highlights line N with its note when
              say reaches the word at
    split     the code under test and its tests side by side, the cold open of a code challenge:
      left    {"code": "demo/checkout.py", "label": "The code"}
      right   {"code": "tests/test_checkout.py", "label": "The tests"}
      marks   optional, inside each side ({"code", "label", "marks"}), as for code; render.py
              reads them there
      hook    optional in a long-form, required in a Short: HOOK_WORDS (2-8) words of curiosity,
              such as "This test has never failed", shown large and said in say's first sentence
    compare   two named things side by side, such as testing versus checking:
      left    {"heading": "Checking", "items": ["what it is", "an example", ...]}
      right   {"heading": "Testing", "items": [...]}; each side says what it is, then examples
    repo      the AI kit's GitHub folder, introduced before any scene uses the kit:
      repo    the GitHub repository, owner/name, such as "example-org/example-demos"
      path    the folder in it, such as "12-mocked-tests/ai-kit"
      files   REPO_FILES lines (1-8): the folder's files shown, such as "AGENTS.md"
      link_at optional: the word of say at which the link note appears, default REPO_CUE
              ("description", as in "the link is in the description")
    kit       the "Take it to your agent" beat: the repo card's GitHub animation again, now explaining
              each file of the kit and how the viewer uses it, never repeating an earlier scene:
      repo, path  as a repo scene: the GitHub repository and the kit folder, <n>-<slug>/ai-kit
      files   REPO_FILES entries (1-8) of KIT_FILE {"path": "AGENTS.md", "use": "Paste into your
              AGENTS.md or CLAUDE.md", "at": "rules"}: the file in ai-kit/, one line on how the
              viewer uses it, and the word of say at which its line appears
      link_at optional: the word of say at which the link appears, default REPO_CUE
      takeaways  two to four lines: what the viewer takes from the video
      takeaways_at  optional: the word of say at which the first takeaway appears; absent, each
              shows at its own words, after the files

    cta       the like, share, subscribe, and notification graphics, the very last scene:
      actions ACTIONS names, each once, such as ["like", "share", "subscribe", "notify"]; say
              names each in natural words (like, share, subscribe, notification or bell), never
              a banned phrase such as "smash that like button"

The old "kit": true flag is replaced by kind kit, and the old kit link and snippet by repo, path,
and files; each is refused naming its replacement, so no script keeps two forms.

It refuses (exit 3), naming each problem, a script that has a banned phrase (in the title, a
heading, on-screen text, or say), a title over title_max, and in say: a sentence of 20 words or
more, three long sentences (LONG_WORDS or more) in a row, digits, more than one CAPS word per
sentence other than acronyms, or markup other than // and ...; a scene claim not in
videos/<N>/citations.json or not found on its source page; or an estimated length outside
the type's target. Grammar flags (every on-screen line written as English: the heading, visual lines but
terminal output, split labels, mark notes, roles, activity, stake, compare headings and items, kit use lines and
takeaways; and every narrated sentence), conservative, the writer's grammar pass judging the rest: a doubled word
(DOUBLED, "the the", but "that that" and "had had"); a narrated sentence not starting with a capital letter; an
on-screen line, not code-like, ending on a DANGLING word (an article, conjunction, "of", or possessive; a stranded
preposition such as "for" is left to the pass); and the reduced relative REDUCED, a code noun, a(n), a noun, then
wrote, made, built, generated, or created ("code an AI wrote": write "code written by AI"). Names: say naming a
person in channel.yaml narration_avoid_names (whole words, any case) is refused; the description's References
credit the concept and its source. Scene rules:
  - a long-form (any structure) opens on an intro scene; an intro is only its first scene, and a
    Short has none (its split hook says what is shown in the first two seconds); the intro's say
    shares a key word (KEY_LETTERS letters or more, not in STOP_WORDS) with each roles line and
    with the activity, so it names the audience and the activity;
  - the cold open (scene 2 of a long-form after its intro, else scene 1) of a code challenge
    (structure challenge-first, or any Short) is a split scene, so the viewer can find the bug;
    another cold open is never a title slide, and a points or terminal one has at least
    HOOK_SHARE of its on-screen words (three letters or more) in its say;
  - in a long-form, the first scene using the AI kit (a kit scene, or a terminal scene whose
    heading or say names the kit) comes after a repo scene; in a Short the kit scene's link is
    the introduction, so no repo scene is needed; when videos/<N>/demo.json names the demo
    folder, a repo scene's https://github.com/<repo>/tree/main/<path> is in that folder;
  - a concept, a compare scene or a points scene whose heading is a bare term (one to four
    words, none in FUNCTION_WORDS) with a key word not said in an earlier scene, gives its
    reason first: its scene's first sentence or the previous scene's last has a REASON cue
    (why, so, because, to know, how do we, how can). Other headings (a code, terminal, or
    split scene naming what it shows, or a sentence-like heading) are judged at gate 2: #38's
    six such headings with new words needed no reason, so checking them would refuse sound
    scripts;
  - a points scene with a line that looks like code (a bracket, =, a backtick, or a dot between
    identifiers) is refused: a reveal about code is a code or split scene with marks;
  - a heading comparing two things (versus, vs) is a compare scene, and each compare side has
    at least two items, what it is and an example;
  - a heading term (KEY_LETTERS letters or more, not in STOP_WORDS) is said in this scene's say
    or an earlier one, so the screen never names a term before the narrator;
  - every cue (a mark's at, a kit file's at, takeaways_at, and a repo or kit scene's link_at or
    REPO_CUE) is a word of its scene's say;
  - every scene after the first opens on a bridge from the one before: its first sentence has a
    TRANSITIONS cue (now that, now, next, so, but, here, with that, let us, let's, we have seen,
    first, then, finally, one more, before, after, also, because, instead, again), as a whole word
    anywhere in it; the refusal shows that sentence; whether it truly links is judged at gate 2;
  - a long-form ends on a cta scene, after the bridge and its comment question, showing all four
    ACTIONS; a Short may end on a cta naming subscribe, as its last scene; a cta is never before
    the last scene; its say names each action it shows, in at most CTA_SENTENCES sentences and
    about CTA_SECONDS (8 s a long-form, 4 s a Short, estimated as the length);
  - the last scene's say thanks the viewer (THANKS: thank you or thanks, any case), long-form and
    Short, inside the cta's limits when the last scene is a cta;
  - a Short flows hook, challenge, why it matters, takeaway, and drive: scene 1 is a split with a
    hook whose words are all in say's first sentence, that sentence at most HOOK_SECONDS at the
    channel's pace (estimated as the length); a code or split scene before the kit has marks
    (the challenge); from the challenge to before the kit a sentence has a REASON cue (why it
    matters); no title scene comes before the kit; the last scene, or the one before a closing
    cta, names the full video or breakdown (DRIVE);
  - a kit scene is among the last KIT_FROM_END (a cta not counted), with TAKEAWAYS takeaways; none of its use lines or
    takeaways repeats, word for word (any case or punctuation), a line an earlier scene showed
    (its on-screen text, compare items, or mark notes): the kit explains each file and how to use
    it; when videos/<N>/demo.json names the demo folder, its card shows <demo link>/ai-kit and,
    when that folder exists in the demo clone (channel.yaml demos.path), each file is in it.
say keeps the real words: narrate-video applies the channel's pronunciation list just before
synthesis, so captions taken from the script show them.

Length estimate: words in say at BASE_WPM words a minute times the channel's voice.pace (the
narration's playback speed). BASE_WPM 172 is the measured speed of content issue #38: 13 scenes,
731 words, 49 // and 4 ..., narrated with the channel's designed Gemini voice at pace 0.92 in
278.4 s, about 158 words a minute after pacing. Its pauses and hesitations left no gaps beyond
the voice's sentence breaks (none near the prototype's 1.25 s), so they are inside that speed
and add no time of their own.

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

BASE_WPM = 172
MAX_WORDS = 20  # every sentence stays under this
LONG_WORDS = 16  # a long sentence; never three in a row
TARGET_SECONDS = {"long-form": (300, 600), "short": (30, 60)}
STRUCTURES = ["challenge-first", "incident-story", "myth-buster"]
KINDS = ["title", "intro", "points", "code", "terminal", "split", "compare", "repo", "kit", "cta"]
# A cta's actions, each with the words of say that name it; a long-form shows all four.
ACTIONS = {
    "like": {"like"},
    "share": {"share"},
    "subscribe": {"subscribe"},
    "notify": {"notify", "notification", "bell"},
}
HOOK_WORDS = (2, 8)  # a split's hook line
HOOK_SECONDS = 3  # a Short's first sentence, holding its hook, at the channel's pace
DRIVE = re.compile(r"\bfull (video|breakdown)\b|\bbreakdown\b", re.IGNORECASE)  # a Short's drive to the long video
CTA_SECONDS = {"long-form": 8, "short": 4}  # a cta, the last scene, said in about this long at the channel's pace
CTA_SENTENCES = 2  # a cta's say, at most
THANKS = re.compile(r"\b(thank you|thanks)\b", re.IGNORECASE)  # the last scene's thank-you to the viewer
SIDES = ["left", "right"]
CLAIM_ID = re.compile(r"C[1-9][0-9]*")
WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")
PAUSE = "//"
HESITATION = re.compile(r"\.\.\.|…")
HOOK_SHARE = 2 / 3  # of the cold open's on-screen words that its narration says
KIT_FROM_END = 2  # the kit beat is the last scene or the one before the bridge
TAKEAWAYS = (2, 4)
ROLES = (2, 3)  # an intro's lines naming who the video is for
REPO_FILES = (1, 8)  # a repo card's file lines
KIT_FILE = ("path", "use", "at")  # a kit file: its path in ai-kit/, how the viewer uses it, the word that shows it
REPO_CUE = "description"  # a repo card's link_at when absent: where the link is
KIT_WORD = re.compile(r"\bkit\b", re.IGNORECASE)
REASON = re.compile(r"\b(why|so|because|to know|how do we|how can)\b", re.IGNORECASE)
FUNCTION_WORDS = {"a", "an", "and", "are", "at", "by", "can", "for", "i", "in", "is", "it", "its", "my", "of", "on",
                  "or", "our", "the", "to", "we", "you"}  # fmt: skip
# A bridge from the scene before (owner, fifth review): the first sentence of each scene after the first has one.
TRANSITIONS = ["now that", "now", "next", "so", "but", "here", "with that", "let us", "let's", "we have seen",
               "first", "then", "finally", "one more", "before", "after", "also", "because", "instead", "again"]  # fmt: skip
TRANSITION = re.compile(r"(?<![\w'])(" + "|".join(map(re.escape, TRANSITIONS)) + r")(?![\w'])", re.IGNORECASE)
# Grammar flags (owner, fifth review): cheap patterns that are wrong in any line; the writer's grammar pass judges
# the rest. A word said twice ("the the"; "that that" and "had had" can be right); a line ending on an article,
# conjunction, "of", or a possessive (a stranded "for" or "with" can be right, as in "Who this is for"); and the
# reduced relative "<code noun> a(n) <noun> wrote" (owner: "Review code an AI wrote", write "code written by AI").
DOUBLED = re.compile(r"(?<![\w'])([A-Za-z]+)\s+\1(?![\w'])", re.IGNORECASE)
DOUBLED_OK = {"that", "had"}
DANGLING = {"a", "an", "the", "and", "or", "but", "nor", "of", "my", "your", "our", "their", "its"}
REDUCED = re.compile(
    r"\b(?:code|tests?|functions?|files?|scripts?|changes?|patch(?:es)?|class(?:es)?|suites?|checks?|fix(?:es)?|"
    r"commits?)\s+an?\s+[A-Za-z]+\s+(?:wrote|made|built|generated|created)\b",
    re.IGNORECASE,
)
CODE_LIKE = re.compile(r"[(=`]|[A-Za-z_]\.[A-Za-z_]")
VERSUS = re.compile(r"\b(versus|vs)\b", re.IGNORECASE)
KEY_LETTERS = 4
STOP_WORDS = {
    "about", "after", "again", "before", "being", "does", "each", "every", "from", "have", "here",
    "into", "just", "more", "most", "only", "over", "some", "than", "that", "their", "them", "then",
    "there", "these", "they", "this", "those", "under", "versus", "very", "what", "when", "where",
    "which", "while", "will", "with", "would", "your",
}  # fmt: skip


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
        shown = {
            "code": ["code"],
            "title": ["visual"],
            "points": ["visual"],
            "terminal": ["visual"],
            "intro": ["activity", "stake"],
            "repo": ["path"],
            "kit": ["path"],
        }
        for field in ["heading", *shown.get(scene.get("kind"), []), "say"]:
            if field not in scene:
                problems.append(f"{name}: {field}: missing")
            elif not _text(scene[field]):
                problems.append(f"{name}: {field}: must be a non-empty string")
        problems += [f"{name}: {p}" for p in shown_problems(scene)]
        claims = scene.get("claims")
        if not (isinstance(claims, list) and all(isinstance(c, str) and CLAIM_ID.fullmatch(c) for c in claims)):
            problems.append(f"{name}: claims: must be a list of claim ids such as C1; may be empty")
        if "kit" in scene:
            problems.append(f"{name}: kit: the kit flag is replaced by kind kit; make this beat a kit scene")
    return problems


def _lines(value, least: int = 1) -> bool:
    return isinstance(value, list) and len(value) >= least and all(_text(line) for line in value)


def shown_problems(scene: dict) -> list[str]:
    """Missing or invalid fields of what a split, compare, or kit scene shows, and of marks."""
    kind, problems = scene.get("kind"), []
    if kind == "split":
        for side in SIDES:
            part = scene.get(side)
            if not (isinstance(part, dict) and _text(part.get("code")) and _text(part.get("label"))):
                problems.append(f"{side}: must be {{code, label}}, the file shown and its label")
            elif "marks" in part and not (isinstance(part["marks"], list) and all(map(_mark_ok, part["marks"]))):
                problems.append(f'{side}: marks: each must be {{"line": N from 1, "note": text, "at": word}}')
        if "marks" in scene:
            problems.append("marks: a split's marks go inside its left or right side")
    if kind == "compare":
        for side in SIDES:
            part = scene.get(side)
            if not (isinstance(part, dict) and _text(part.get("heading")) and _lines(part.get("items"))):
                problems.append(f"{side}: must be {{heading, items}}, a heading and a non-empty list of lines")
    if kind == "kit":
        if "link" in scene:
            problems.append("link: replaced by repo and path; the kit scene shows the repo card's GitHub folder")
        if "snippet" in scene or "snippet_at" in scene:
            problems.append(
                "snippet: replaced by files, each {path, use, at}: explain each kit file and how the viewer uses it"
            )
        problems += _repo_problems(scene)
        files = scene.get("files")
        files_ok = isinstance(files, list) and REPO_FILES[0] <= len(files) <= REPO_FILES[1]
        if not (files_ok and all(isinstance(f, dict) and all(_text(f.get(k)) for k in KIT_FILE) for f in files)):
            problems.append(
                f"files: must be {REPO_FILES[0]}-{REPO_FILES[1]} of {{path, use, at}}: each kit file, one line on "
                "how the viewer uses it, and the word of say that shows it"
            )
        if not _lines(scene.get("takeaways"), 0):
            problems.append("takeaways: must be a list of lines")
        cues = [cue for cue in ("link_at", "takeaways_at") if cue in scene]
        problems += [f"{cue}: must be a word of say" for cue in cues if not _text(scene.get(cue))]
    if "hook" in scene:
        hook = scene["hook"]
        if kind != "split":
            problems.append("hook: only a split scene has a hook")
        elif not (isinstance(hook, str) and HOOK_WORDS[0] <= len(WORD.findall(hook)) <= HOOK_WORDS[1]):
            problems.append(f"hook: must be {HOOK_WORDS[0]}-{HOOK_WORDS[1]} words, the curiosity line said first")
    actions = scene.get("actions")
    if kind == "cta" and not (
        isinstance(actions, list) and actions and set(actions) <= set(ACTIONS) and len(set(actions)) == len(actions)
    ):
        problems.append(f"actions: must be a non-empty list of {_choices(list(ACTIONS))}, each once")
    if kind == "intro" and not (_lines(scene.get("roles")) and ROLES[0] <= len(scene["roles"]) <= ROLES[1]):
        problems.append(f"roles: must be {ROLES[0]}-{ROLES[1]} lines: who the video is for")
    if kind == "repo":
        problems += _repo_problems(scene)
        files = scene.get("files")
        if not (_lines(files) and REPO_FILES[0] <= len(files) <= REPO_FILES[1]):
            problems.append(f"files: must be {REPO_FILES[0]}-{REPO_FILES[1]} lines: the folder's files shown")
        if "link_at" in scene and not _text(scene["link_at"]):
            problems.append("link_at: must be a word of say")
    if "marks" in scene and kind != "split":
        if kind != "code":
            problems.append("marks: only code and split scenes have marks")
        elif not (isinstance(scene["marks"], list) and all(map(_mark_ok, scene["marks"]))):
            problems.append('marks: each must be {"line": N from 1, "note": text, "at": word}')
    return problems


def _repo_problems(scene: dict) -> list[str]:
    if not (isinstance(scene.get("repo"), str) and youtube_channel.REPO.fullmatch(scene["repo"])):
        return ["repo: must be a GitHub repository like owner/name"]
    return []


def _mark_ok(mark) -> bool:
    if not isinstance(mark, dict) or not (_text(mark.get("note")) and _text(mark.get("at"))):
        return False
    line = mark.get("line")
    return isinstance(line, int) and not isinstance(line, bool) and line >= 1


def scene_marks(scene: dict) -> list[dict]:
    """A code scene's marks, or both sides' marks of a split."""
    if scene["kind"] == "split":
        return [mark for side in SIDES for mark in scene[side].get("marks", [])]
    return scene.get("marks", [])


def screen_text(scene: dict) -> str:
    """Every on-screen line of a scene but its heading and code files."""
    kind = scene["kind"]
    if kind == "split":
        return "\n".join(scene[side]["label"] for side in SIDES)
    if kind == "compare":
        return "\n".join(line for side in SIDES for line in [scene[side]["heading"], *scene[side]["items"]])
    if kind == "kit":
        uses = [line for f in scene["files"] for line in (f["path"], f["use"])]
        return "\n".join([scene["repo"], scene["path"], *uses, *scene["takeaways"]])
    if kind == "intro":
        return "\n".join([*scene["roles"], scene["activity"], scene["stake"]])
    if kind == "repo":
        return "\n".join([scene["repo"], scene["path"], *scene["files"]])
    if kind == "cta":
        return ""  # graphics of the actions, no text
    return scene.get("visual", "")


def spoken(say: str) -> str:
    """The narration without its pause and hesitation markup."""
    return HESITATION.sub(" ", say.replace(PAUSE, " "))


def sentences(say: str) -> list[list[str]]:
    """Each sentence of the narration as its words; a hesitation does not end a sentence."""
    parts = re.split(r"(?<=[.!?])\s+", spoken(say).strip())
    return [words for part in parts if (words := WORD.findall(part))]


def estimate(scenes: list[dict], pace: float) -> tuple[int, int]:
    """Words spoken, and the narration's estimated seconds at the channel's pace."""
    words = sum(len(WORD.findall(spoken(scene["say"]))) for scene in scenes)
    return words, round(words * 60 / (BASE_WPM * pace))


def say_problems(say: str, acronyms: set[str]) -> list[str]:
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


def _stems(text: str) -> list[str]:
    """Words of three letters or more, lowercased, without a plural s, for loose matching."""
    words = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", text)]
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def _keys(text: str) -> set[str]:
    """The key words of text (KEY_LETTERS letters or more, not STOP_WORDS), as stems."""
    return {w for w in _stems(text) if len(w) >= KEY_LETTERS and w not in STOP_WORDS}


def intro_problems(scenes: list[dict], long_form: bool) -> list[str]:
    """A long-form opens on an intro naming who it is for and what the viewer will do; a Short has none."""
    found = []
    if long_form and scenes[0]["kind"] != "intro":
        found.append(
            "scene 1: kind: a long-form opens on an intro scene: who it is for, what they will do, why it matters"
        )
    for index, scene in enumerate(scenes, 1):
        if scene["kind"] != "intro":
            continue
        if not long_form:
            found.append(f"scene {index}: kind: a Short has no intro; it opens on its split hook")
        elif index > 1:
            found.append(f"scene {index}: kind: an intro is only the first scene of a long-form")
        said = set(_stems(spoken(scene["say"])))
        for line in [*scene["roles"], scene["activity"]]:
            if not _keys(line) & said:
                found.append(
                    f"scene {index}: say: the intro shows '{line}' but does not say it; name each role and the activity"
                )
    return found


def hook_problems(first: dict, challenge: bool, index: int = 1) -> list[str]:
    """Problems of the cold open, scene index: it shows the real artifact and says what is on screen."""
    name = f"scene {index}"
    if challenge and first["kind"] != "split":
        return [f"{name}: kind: a code challenge opens on a split scene: the code under test and its tests"]
    if first["kind"] == "title":
        return [f"{name}: kind: the cold open shows the real code, output, or failing case, never a title slide"]
    if first["kind"] not in ("points", "terminal"):
        return []
    shown, said = _stems(first["visual"]), set(_stems(spoken(first["say"])))
    present = sum(word in said for word in shown)
    if shown and present < HOOK_SHARE * len(shown):
        return [
            f"{name}: visual: {present} of {len(shown)} on-screen words are in say; the cold open says what it shows"
        ]
    return []


def repo_problems(scenes: list[dict], long_form: bool, demo: dict | None) -> list[str]:
    """A long-form introduces the AI kit with a repo scene before the first scene using it (a kit scene, or a
    terminal scene naming the kit); a repo scene shows the demo's folder once demo.json names it."""
    found = []
    for index, scene in enumerate(scenes, 1):
        if scene["kind"] == "repo" and demo:
            url = f"https://github.com/{scene['repo']}/tree/main/{scene['path'].strip('/')}"
            if not (url == demo["link"] or url.startswith(demo["link"] + "/")):
                found.append(
                    f"scene {index}: repo: {scene['repo']}/{scene['path']} is not the demo's folder, {demo['link']}"
                )
    uses = [
        index
        for index, scene in enumerate(scenes, 1)
        if scene["kind"] == "kit"
        or (scene["kind"] == "terminal" and KIT_WORD.search(scene["heading"] + " " + scene["say"]))
    ]
    if long_form and uses and not any(scene["kind"] == "repo" for scene in scenes[: uses[0] - 1]):
        found.append(
            f"scene {uses[0]}: kind: the AI kit is used before a repo scene introduces it; add a repo scene "
            "(the GitHub repo, path, files, and where the link is) before it"
        )
    return found


def short_problems(scenes: list[dict], pace: float) -> list[str]:
    """A Short's flow, each beat bridged by a sentence: the hook (a split with a hook said in a first sentence of at
    most HOOK_SECONDS), the challenge (marks on the bug's line), why it matters (a REASON sentence before the kit, no
    title slide), the takeaway (the kit), and the drive to the long video (the last scene, or the one before a
    closing cta, names the full video or breakdown)."""
    found, first = [], scenes[0]
    opening = _sentence_texts(first["say"])[:1]
    if first["kind"] == "split" and "hook" not in first:
        found.append(
            f"scene 1: hook: a Short opens on a split with a hook of {HOOK_WORDS[0]}-{HOOK_WORDS[1]} words, said in "
            "its first sentence, that makes the viewer curious"
        )
    elif first["kind"] == "split" and opening:
        said = {w.lower() for w in WORD.findall(opening[0])}
        if not {w.lower() for w in WORD.findall(first["hook"])} <= said:
            found.append(f"scene 1: hook: '{first['hook']}' is not said in the first sentence of say")
        if (seconds := len(WORD.findall(opening[0])) * 60 / (BASE_WPM * pace)) > HOOK_SECONDS:
            found.append(
                f"scene 1: say: the first sentence takes about {round(seconds)} s; a Short's hook is said within "
                f"{HOOK_SECONDS} s"
            )
    kits = [index for index, scene in enumerate(scenes, 1) if scene["kind"] == "kit"]
    end = kits[0] if kits else len(scenes) + 1
    challenge = next((i for i, scene in enumerate(scenes[: end - 1], 1) if scene_marks(scene)), None)
    if challenge is None:
        found.append("short: no challenge beat; mark the bug's line in a code or split scene before the kit")
    elif not any(
        REASON.search(text) for scene in scenes[challenge - 1 : end - 1] for text in _sentence_texts(scene["say"])
    ):
        found.append(
            "short: no why-it-matters beat; between the challenge and the kit, say why it matters "
            "(why, so, because, to know, how do we, how can)"
        )
    found += [
        f"scene {index}: kind: a Short has no title slide before the kit; go from the challenge to why it matters"
        for index, scene in enumerate(scenes[: end - 1], 1)
        if scene["kind"] == "title"
    ]
    drive = len(scenes) - 1 if scenes[-1]["kind"] == "cta" and len(scenes) > 1 else len(scenes)
    if not DRIVE.search(spoken(scenes[drive - 1]["say"])):
        found.append(f"scene {drive}: say: a Short ends by driving to the long video; name the full video or breakdown")
    return found


def cta_problems(scenes: list[dict], long_form: bool, pace: float) -> list[str]:
    """A long-form ends on a cta scene of like, share, subscribe, and notification graphics, after the bridge; a Short
    may end on one naming subscribe; each action is said, in at most CTA_SENTENCES sentences and about CTA_SECONDS."""
    found, last = [], len(scenes)
    ctas = [index for index, scene in enumerate(scenes, 1) if scene["kind"] == "cta"]
    if long_form and last not in ctas:
        found.append(
            f"cta: a long-form ends on a cta scene ({', '.join(ACTIONS)}), after the bridge; add it as the last "
            f"scene, at most {CTA_SENTENCES} sentences naming each action naturally"
        )
    limit = CTA_SECONDS["long-form" if long_form else "short"]
    for index in ctas:
        scene, name = scenes[index - 1], f"scene {index}"
        if long_form and set(scene["actions"]) != set(ACTIONS):
            found.append(f"{name}: actions: a long-form's cta shows all four: {', '.join(ACTIONS)}")
        if index != last:
            where = "after the bridge and its comment question" if long_form else "after the drive to the long video"
            found.append(f"{name}: kind: a {'long-form' if long_form else 'Short'}'s cta is its last scene, {where}")
        if not long_form and "subscribe" not in scene["actions"]:
            found.append(f"{name}: actions: a Short's cta names subscribe")
        said = set(_stems(spoken(scene["say"])))
        for action in scene["actions"]:
            if not ACTIONS[action] & said:
                cues = " or ".join(sorted(ACTIONS[action]))
                found.append(f"{name}: say: the cta shows '{action}' but does not say it ({cues})")
        if (count := len(_sentence_texts(scene["say"]))) > CTA_SENTENCES:
            found.append(f"{name}: say: the cta has {count} sentences; keep it to at most {CTA_SENTENCES}")
        if (seconds := round(len(WORD.findall(spoken(scene["say"]))) * 60 / (BASE_WPM * pace))) > limit:
            found.append(f"{name}: say: the cta takes about {seconds} s; keep it to about {limit} s")
    return found


def transition_problems(scenes: list[dict]) -> list[str]:
    """Each scene after the first whose first sentence has no TRANSITIONS cue bridging from the scene before."""
    found = []
    for index, scene in enumerate(scenes[1:], 2):
        first = _sentence_texts(scene["say"])[:1]
        if first and not TRANSITION.search(first[0].replace("\u2019", "'")):
            found.append(
                f"scene {index}: say: no bridge from the scene before; open with a transition cue (now that, now, "
                f"next, so, but, here, let us, ...), such as 'Now that we have seen the bug, let us look at the fix': "
                f"'{first[0].strip()}'"
            )
    return found


def prose_lines(scene: dict) -> list[tuple[str, str]]:
    """Each on-screen line written as English, as (field, line): the heading, then as visual every other line but
    code, terminal output, and the repo and kit cards' repository, folder, and file paths."""
    kind = scene["kind"]
    if kind in ("terminal", "repo"):
        lines = []
    elif kind == "kit":
        lines = [*(f["use"] for f in scene["files"]), *scene["takeaways"]]
    else:
        lines = screen_text(scene).splitlines()
    lines += [mark["note"] for mark in scene_marks(scene)]
    return [("heading", scene["heading"]), *(("visual", line.strip()) for line in lines if line.strip())]


def _phrase_problems(text: str) -> list[str]:
    found = [
        f"doubled word '{m.group(0)}'; say it once" for m in DOUBLED.finditer(text) if m[1].lower() not in DOUBLED_OK
    ]
    found += [
        f"'{m.group(0)}' is a reduced relative; write it in full, such as 'code written by AI'"
        for m in REDUCED.finditer(text)
    ]
    return found


def grammar_problems(index: int, scene: dict) -> list[str]:
    """The grammar flags of one scene: doubled words and reduced relatives in every on-screen line and in say, a line
    ending on a DANGLING word, and a narrated sentence not starting with a capital letter."""
    name, found = f"scene {index}", []
    for field, line in prose_lines(scene):
        found += [f"{name}: {field}: {p}" for p in _phrase_problems(line)]
        words = WORD.findall(line)
        if words and not CODE_LIKE.search(line) and words[-1].lower() in DANGLING:
            found.append(f"{name}: {field}: '{line}' ends on '{words[-1]}'; finish the phrase")
    found += [f"{name}: say: {p}" for p in _phrase_problems(scene["say"].replace(PAUSE, " "))]
    for text in _sentence_texts(scene["say"]):
        if (first := WORD.search(text)) and first.group(0)[0].islower():
            found.append(
                f"{name}: say: '{text.strip()}' does not start with a capital letter; start each sentence with one, "
                "rephrasing a sentence that opens on a lowercase name such as pytest"
            )
    return found


def _sentence_texts(say: str) -> list[str]:
    return [part for part in re.split(r"(?<=[.!?])\s+", spoken(say).strip()) if WORD.search(part)]


def concept(scene: dict, before: set[str]) -> bool:
    """Whether a scene brings in a concept: a compare scene, or a points scene whose heading is a bare term (one to
    four words, no function word) with a key word not said in an earlier scene, such as "Mutation testing"."""
    if scene["kind"] == "compare":
        return True
    words = re.findall(r"[A-Za-z]+", scene["heading"])
    bare = scene["kind"] == "points" and 1 <= len(words) <= 4 and not {w.lower() for w in words} & FUNCTION_WORDS
    return bare and bool(_keys(scene["heading"]) - before)


def context_problems(scenes: list[dict]) -> list[str]:
    """Each concept whose scene's first sentence, and the previous scene's last, give no reason (REASON)."""
    found, before = [], set()
    for index, scene in enumerate(scenes, 1):
        if concept(scene, before):
            first = _sentence_texts(scene["say"])[:1]
            last = _sentence_texts(scenes[index - 2]["say"])[-1:] if index > 1 else []
            if not any(REASON.search(text) for text in first + last):
                found.append(
                    f"scene {index}: say: a new concept with no reason first; open with why it matters (why, so, "
                    "because, to know, how do we) in this scene's first sentence or the previous scene's last"
                )
        before |= set(_stems(spoken(scene["say"])))
    return found


def scene_problems(index: int, scene: dict, said: set[str]) -> list[str]:
    """The scene rules of one scene: code on slides, comparisons, terms named early, and cues; said
    holds the stems of every word narrated up to and including this scene."""
    name, kind, found = f"scene {index}", scene["kind"], []
    if kind == "points":
        for line in scene["visual"].splitlines():
            if CODE_LIKE.search(line):
                found.append(
                    f"{name}: visual: '{line.strip()}' looks like code; show it as a code or split scene with "
                    "marks on the lines it names"
                )
    if VERSUS.search(scene["heading"]) and kind != "compare":
        found.append(
            f"{name}: kind: '{scene['heading']}' compares two things; make it a compare scene, "
            "each side with what it is and an example"
        )
    if kind == "compare":
        for side in SIDES:
            if (count := len(scene[side]["items"])) < 2:
                found.append(
                    f"{name}: {side}: {count} item; a compare side says what it is and gives at least one example"
                )
    for word in re.findall(rf"[A-Za-z]{{{KEY_LETTERS},}}", scene["heading"]):
        if word.lower() not in STOP_WORDS and _stems(word)[0] not in said:
            found.append(
                f"{name}: heading: '{word}' is on screen before the narrator says it; "
                "say it in this scene or an earlier one"
            )
    words = {w.lower() for w in WORD.findall(spoken(scene["say"]))}
    cues = [("marks", m["at"]) for m in scene_marks(scene)]
    if kind == "kit":
        cues += [("files", f["at"]) for f in scene["files"]]
        cues += [("takeaways_at", scene["takeaways_at"])] if "takeaways_at" in scene else []
    if kind in ("repo", "kit"):
        cues.append(("link_at", scene.get("link_at", REPO_CUE)))
    for field, cue in cues:
        if cue.strip().lower() not in words:
            found.append(f"{name}: {field}: '{cue}' is not a word of say; the renderer shows it at that word")
    if kind == "kit" and not TAKEAWAYS[0] <= len(scene["takeaways"]) <= TAKEAWAYS[1]:
        found.append(
            f"{name}: takeaways: {len(scene['takeaways'])}; "
            f"the kit scene shows {TAKEAWAYS[0]}-{TAKEAWAYS[1]} takeaways from the video"
        )
    return found


def _plain_line(line: str) -> str:
    return " ".join(w.lower() for w in WORD.findall(line))


def shown_lines(scene: dict) -> list[str]:
    """Every line a scene shows but its heading and code: its on-screen text and its mark notes."""
    return [*screen_text(scene).splitlines(), *(mark["note"] for mark in scene_marks(scene))]


def kit_problems(index: int, scene: dict, earlier: list[dict], demo: dict | None, kit_dir: Path | None) -> list[str]:
    """A kit scene against the earlier scenes, none of whose lines it repeats, and the demo: its card shows the
    demo's ai-kit folder, and each file is in that folder of the demo clone (kit_dir, None when absent)."""
    found, name = [], f"scene {index}"
    shown = {}
    for number, before in enumerate(earlier, 1):
        for line in shown_lines(before):
            shown.setdefault(_plain_line(line), number)
    for line in [*(f["use"] for f in scene["files"]), *scene["takeaways"]]:
        if (number := shown.get(_plain_line(line))) and _plain_line(line):
            found.append(
                f"{name}: kit: '{line}' repeats a line shown in scene {number}; explain each file and how to use it, "
                "and take away what earlier scenes did not show"
            )
    if demo:
        url = f"https://github.com/{scene['repo']}/tree/main/{scene['path'].strip('/')}"
        if url != demo["link"] + "/ai-kit":
            found.append(f"{name}: path: the kit card must show the demo's AI kit folder, {demo['link']}/ai-kit")
    for file in scene["files"] if kit_dir else []:
        if not (kit_dir / file["path"]).is_file():
            found.append(f"{name}: files: '{file['path']}' is not in the demo's ai-kit folder")
    return found


def problems(
    script: dict, config: dict, pace: float, citations: list[dict] | None, demo=None, kit_dir=None
) -> list[str]:
    """Every writing rule, scene rule, length, and citation problem of a well-formed script; demo is
    demo.json's {folder, link} and kit_dir its ai-kit folder in the demo clone, each None when not known yet."""
    found = []
    if not youtube_channel.title_ok(script["title"], config):
        found.append(f"title: {len(script['title'])} characters; at most {config['title_max']}")
    found += [f"title: banned phrase '{p}'" for p in youtube_channel.banned_phrases(script["title"], config)]
    acronyms = set(script["acronyms"])
    by_id = {c.get("id"): c for c in citations or [] if isinstance(c, dict)}
    said: set[str] = set()
    for index, scene in enumerate(script["scenes"], 1):
        name = f"scene {index}"
        for field, text in [("heading", scene["heading"]), ("visual", screen_text(scene)), ("say", scene["say"])]:
            phrases = youtube_channel.banned_phrases(text, config)
            found += [f"{name}: {field}: banned phrase '{p}'" for p in phrases]
        said |= set(_stems(spoken(scene["say"])))
        found += scene_problems(index, scene, said)
        if scene["kind"] == "kit":
            found += kit_problems(index, scene, script["scenes"][: index - 1], demo, kit_dir)
        found += [f"{name}: say: {p}" for p in say_problems(scene["say"], acronyms)]
        found += grammar_problems(index, scene)
        found += [
            f"{name}: say: names a person ('{person}'); narration never names people, so credit the concept and its "
            "source in the description's References"
            for person in youtube_channel.phrases_in(scene["say"], config.get("narration_avoid_names", []))
        ]
        for claim in scene["claims"] if citations is not None else []:
            if claim not in by_id:
                found.append(f"{name}: claims: {claim} not in citations.json")
            elif by_id[claim].get("found") is not True:
                found.append(f"{name}: claims: {claim} not found on its source page; run evidence.py")
    if citations is None and any(scene["claims"] for scene in script["scenes"]):
        found.append("citations.json: missing; research-video writes it")
    found += rhythm_problems(script["scenes"])
    scenes, long_form = script["scenes"], script["type"] == "long-form"
    challenge = script["structure"] == "challenge-first" or not long_form
    found += intro_problems(scenes, long_form)
    opening = 2 if long_form and scenes[0]["kind"] == "intro" and len(scenes) > 1 else 1
    found += hook_problems(scenes[opening - 1], challenge, opening)
    found += repo_problems(scenes, long_form, demo)
    found += context_problems(scenes)
    found += transition_problems(scenes)
    found += cta_problems(scenes, long_form, pace)
    if not THANKS.search(spoken(scenes[-1]["say"])):
        found.append(f"scene {len(scenes)}: say: the last scene thanks the viewer; say thank you or thanks")
    found += [] if long_form else short_problems(scenes, pace)
    if not any(scene["kind"] == "kit" for scene in [s for s in scenes if s["kind"] != "cta"][-KIT_FROM_END:]):
        found.append("kit: no kit scene in the last two; end with the Take it to your agent beat")
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


def demo_kit(folder: Path, config: dict, root: Path) -> tuple[dict | None, Path | None]:
    """demo.json's {folder, link} once build-video-demo wrote it, and its ai-kit folder in the demo clone if present."""
    demo = read_json(folder / "demo.json", "")
    if not (isinstance(demo, dict) and _text(demo.get("folder")) and _text(demo.get("link"))):
        return None, None
    kit_dir = root / ".projects" / "content" / config["demos"]["path"] / demo["folder"] / "ai-kit"
    return demo, kit_dir if kit_dir.is_dir() else None


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
        demo, kit_dir = demo_kit(folder, channel.config, root)
        pace = channel.config["voice"]["pace"]
        found = problems(script, channel.config, pace, citations, demo, kit_dir)
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

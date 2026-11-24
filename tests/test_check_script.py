"""Tests for the write-video-script skill's scripts/check_script.py, through main with a tmp workspace."""

import json
import sys
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/write-video-script/scripts"))
import check_script

NUMBER = 12
# CONFIG: pace 0.92, banned_phrases ["in this video"], title_max 60; its pronunciation list (pytest) is
# applied at narration, so say keeps the real word.
WPM = check_script.BASE_WPM * CONFIG["voice"]["pace"]

# Twenty-five words in four sentences: short, medium, short, medium; the first bridges from the scene before (now).
SAY = (
    "Now both tests pass. "
    "I can break the code in one keystroke and neither one notices. "
    "Spot the bug. "
    "The bug is in the tests."
)
CITATIONS = [
    {"id": "C1", "claim": "The healer reruns a test.", "url": "https://example.com/a", "quote": "q", "found": True},
    {"id": "C2", "claim": "A check verifies.", "url": "https://example.com/b", "quote": "q", "found": False},
]


def scene(**fields):
    base = {
        "kind": "points",
        "heading": "Spot the bug",
        "visual": "Both tests pass. Spot the bug.",
        "say": SAY,
        "claims": [],
    }
    return base | fields


def split(**fields):
    """The cold open of a code challenge: the code under test and its tests side by side, its hook said first."""
    base = {
        "kind": "split",
        "heading": "Spot the bug",
        "hook": "Both tests pass",
        "left": {"code": "demo/checkout.py", "label": "The code"},
        "right": {
            "code": "tests/test_checkout.py",
            "label": "The tests",
            "marks": [{"line": 4, "note": "checks the fake", "at": "bug"}],
        },
        "say": SAY,
        "claims": [],
    }
    return base | fields


KIT_FILES = [
    {"path": "AGENTS.md", "use": "Paste into your agents file", "at": "code"},
    {"path": "skills/check-test-can-fail/SKILL.md", "use": "Your agent runs it after writing tests", "at": "tests"},
]


# A Short's why-it-matters beat (seventeen words), its drive to the long video (eight words), and its thank-you to the
# viewer when the kit beat is its last scene (three words).
WHY_SAY = "So why does it matter? Because a coupon can overcharge customers, and both the tests stay green."
DRIVE = " The full breakdown is in the linked video."
THANKS = " Thanks for watching."


def why(**fields):
    return scene(heading="Why it matters", visual="Customers pay more\nThe tests stay green", say=WHY_SAY) | fields


def kit(**fields):
    """The Take it to your agent beat: the kit's GitHub card, each file with how to use it, and the takeaways."""
    base = {
        "kind": "kit",
        "heading": "Break the code",
        "repo": "example-org/example-demos",
        "path": "12-mocked-tests/ai-kit",
        "files": KIT_FILES,
        "link_at": "code",
        "takeaways": ["Ask what would make the test fail.", "Break the code on purpose."],
        "say": SAY + DRIVE + THANKS,
        "claims": [],
    }
    return base | fields


def compare(**fields):
    base = {
        "kind": "compare",
        "heading": "Tests versus the bug",
        "left": {"heading": "Tests", "items": ["Pass on green code", "total_cents(1000) == 1080"]},
        "right": {"heading": "Bug", "items": ["Hides in the mock", "tax client returns 0"]},
        "say": "So why do green tests miss it? " + SAY,
        "claims": [],
    }
    return base | fields


INTRO_SAY = (
    "Do you let an AI assistant write your tests? Or do you review its code? // "
    "Developers and testers, this challenge is for you. // "
    "Today you spot the bug in two unit tests. // They pass while customers pay too much."
)


def intro(**fields):
    """A long-form's first scene: who the video is for, what the viewer will do, and why it matters."""
    base = {
        "kind": "intro",
        "heading": "Is this for you?",
        "roles": ["Developers who let AI write tests", "Testers who review AI code"],
        "activity": "Spot the bug in two unit tests",
        "stake": "They pass while customers pay too much",
        "say": INTRO_SAY,
        "claims": [],
    }
    return base | fields


REPO_SAY = (
    "Now I have built an AI kit for this problem. // It is on my GitHub, and the link is in the description. " + SAY
)


def repo(**fields):
    """The scene that introduces the AI kit's GitHub folder before any scene uses the kit."""
    base = {
        "kind": "repo",
        "heading": "An AI kit for this problem",
        "repo": "example-org/example-demos",
        "path": "12-mocked-tests/ai-kit",
        "files": ["AGENTS.md", "skills/check-test-can-fail/SKILL.md"],
        "say": REPO_SAY,
        "claims": [],
    }
    return base | fields


# Two sentences, twenty words with the thank-you: about eight seconds at the channel's pace.
CTA_SAY = (
    "Before you go, like and share this with a tester. // Subscribe, turn on the bell, and thank you for watching."
)


def cta(**fields):
    """The like, share, subscribe, and notification graphics: a long-form's last scene, after the bridge."""
    base = {
        "kind": "cta",
        "heading": "Like, share, subscribe",
        "actions": ["like", "share", "subscribe", "notify"],
        "say": CTA_SAY,
        "claims": [],
    }
    return base | fields


DEMO_LINK = "https://github.com/example-org/example-demos/tree/main/12-mocked-tests"
KIT = kit()
CTA = cta()
SHORT_CTA = cta(
    actions=["subscribe"], heading="Subscribe", say="Subscribe for the next challenge. // Thanks for watching."
)
WHY = why()
SPLIT = split()
INTRO = intro()
REPO = repo()


REPO_AT = 39  # the repo card's index in long_form: scene 40


def long_form(middle, structure="challenge-first", first=None):
    """A long-form of about six minutes: the intro, first (default the split), middle, the repo card, the kit, the
    bridge, and the cta."""
    scenes = [INTRO, first or SPLIT, *middle] + [scene()] * (37 - len(middle)) + [REPO, KIT, scene(), CTA]
    return script(scenes, type="long-form", structure=structure)


def script(scenes=None, **fields):
    """A Short of four scenes, one hundred and three words: about thirty-nine seconds at the channel's pace: the split
    hook and challenge, a scene, why it matters, and the kit beat driving to the long video and thanking the viewer."""
    base = {
        "title": "Spot the Bug: the test that tests nothing",
        "type": "short",
        "structure": "challenge-first",
        "acronyms": ["AI"],
        "scenes": scenes if scenes is not None else [split(claims=["C1"]), scene(), WHY, KIT],
    }
    return base | fields


def files(root, data=None, citations=CITATIONS):
    folder = workspace(root) / "videos" / str(NUMBER)
    folder.mkdir(parents=True, exist_ok=True)
    if data is not None:
        (folder / "script.json").write_text(data if isinstance(data, str) else json.dumps(data))
    if citations is not None:
        (folder / "citations.json").write_text(json.dumps(citations))
    return folder


def run(root, capsys):
    code = check_script.main(["example", str(NUMBER)], root=root)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_a_script_under_the_writing_rules_passes_with_its_length_estimate(tmp_path, capsys):
    files(tmp_path, script())
    code, out, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")
    report = json.loads(out)
    assert report["words"] == 103 and report["target_seconds"] == [30, 60]
    assert report["seconds"] == round(103 * 60 / WPM)


def test_pauses_and_hesitations_are_not_words_and_sit_inside_the_measured_speed(tmp_path, capsys):
    paused = SAY.replace("Spot the bug.", "Spot the bug. // Look... closely.")
    files(tmp_path, script([split(say=paused), scene(say=paused), WHY, kit(say=paused + DRIVE + THANKS)]))
    code, out, _ = run(tmp_path, capsys)
    report = json.loads(out)
    assert code == 0 and report["words"] == 3 * 27 + 17 + 8 + 3
    assert report["seconds"] == round((3 * 27 + 17 + 8 + 3) * 60 / WPM)


def test_the_estimate_matches_the_measured_narration_of_content_issue_38():
    # #38: 13 scenes, 731 words, 49 // pauses, 4 ... hesitations; narrated at pace 0.92 in 278.4 s.
    marks = ["word //"] * 49 + ["word ..."] * 4 + ["word"] * (731 - 53)
    scenes = [{"say": " ".join(marks[i::13])} for i in range(13)]
    counted, seconds = check_script.estimate(scenes, 0.92)
    assert counted == 731
    assert abs(seconds - 278.4) <= 0.1 * 278.4


LONG = "This sentence runs long enough to count as a long one under the rhythm rule here."
TWENTY = "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty."


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"say": "In this video we break a test. " + SAY}, "scene 1: say: banned phrase 'in this video'"),
        ({"heading": "In this video"}, "scene 1: heading: banned phrase 'in this video'"),
        ({"visual": "In this video"}, "scene 1: visual: banned phrase 'in this video'"),
        ({"say": TWENTY + " " + SAY}, "scene 1: say: sentence of 20 words"),
        ({"say": "It costs 90 dollars. " + SAY}, "scene 1: say: digits '90'"),
        ({"say": "This is NOT a REAL test. " + SAY}, "scene 1: say: 2 CAPS words in one sentence (NOT, REAL)"),
        ({"say": "Wait <short pause> now. " + SAY}, "scene 1: say: markup '<'"),
        ({"say": " ".join([LONG] * 3) + " " + SAY}, "scene 1: say: three long sentences in a row"),
        ({"claims": ["C9"]}, "scene 1: claims: C9 not in citations.json"),
        ({"claims": ["C2"]}, "scene 1: claims: C2 not found on its source page"),
    ],
)
def test_a_scene_breaking_a_writing_rule_is_refused_naming_it(tmp_path, capsys, change, problem):
    files(tmp_path, script([scene(**change), scene(), WHY, KIT], structure="myth-buster"))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    "say",
    [
        "Now this is NOT a test. " + SAY,
        "So AI wrote this, and it is NOT a test. " + SAY,
        "Now wait // and look... closely. " + SAY,
        "Run pytest now. " + SAY,
    ],
)
def test_one_stressed_word_listed_acronyms_pause_markup_and_real_words_are_allowed(tmp_path, capsys, say):
    files(tmp_path, script([SPLIT, scene(say=say, visual="The total is 1080 cents", heading="Bug 1"), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


def test_digits_and_code_stay_allowed_in_a_code_scene(tmp_path, capsys):
    code_scene = {"kind": "code", "heading": "The tests", "code": "demo/test_discount_ai.py", "say": SAY, "claims": []}
    files(tmp_path, script([SPLIT, code_scene, WHY, KIT]))
    assert run(tmp_path, capsys)[0] == 0


# The hook (owner, gate 3 of #38): the cold open shows the real artifact and says what is on screen.


def incident_story(first):
    """A long-form incident story of about six minutes whose cold open, after the intro, is first."""
    return long_form([], "incident-story", first)


@pytest.mark.parametrize(
    ("first", "problem"),
    [
        (
            scene(kind="title", visual="Both tests pass. Spot the bug."),
            "scene 2: kind: the cold open shows the real code, output, or failing case, never a title slide",
        ),
        (
            scene(visual="Two green tests. Zero protection."),
            "scene 2: visual: 1 of 5 on-screen words are in say; the cold open says what it shows",
        ),
    ],
)
def test_a_cold_open_that_does_not_show_and_say_the_artifact_is_refused(tmp_path, capsys, first, problem):
    files(tmp_path, incident_story(first))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    "first",
    [
        scene(
            kind="terminal", visual="$ pytest -q tests\n2 passed", say="Now run pytest. // Both tests passed. " + SAY
        ),
        {"kind": "code", "heading": "Spot the bug", "code": "tests/test_checkout.py", "say": SAY, "claims": []},
        scene(visual="Both TESTS pass: spot the bug"),
        SPLIT,
    ],
)
def test_an_incident_story_cold_open_showing_what_it_says_passes(tmp_path, capsys, first):
    files(tmp_path, incident_story(first))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# The hook (owner, second gate 3 of #38): a code challenge opens on the code and its tests side by side,
# so the viewer can find the bug.


@pytest.mark.parametrize(
    "first",
    [
        {"kind": "code", "heading": "Spot the bug", "code": "tests/test_checkout.py", "say": SAY, "claims": []},
        scene(
            kind="terminal", visual="$ pytest -q tests\n2 passed", say="Now run pytest. // Both tests passed. " + SAY
        ),
        scene(),
    ],
)
@pytest.mark.parametrize(
    ("data", "index"),
    [
        (lambda first: script([first, scene(), WHY, KIT]), 1),
        (lambda first: script([first, scene(), WHY, KIT], structure="myth-buster"), 1),
        (lambda first: long_form([], first=first), 2),
    ],
)
def test_a_code_challenge_or_short_cold_open_that_is_not_a_split_is_refused(tmp_path, capsys, first, data, index):
    files(tmp_path, data(first))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene {index}: kind: a code challenge opens on a split scene: the code under test and its tests" in err


# Reveals about code (owner, second gate 3 of #38): marked in the code, never a points slide of code.


@pytest.mark.parametrize(
    "line",
    ["patch.object swaps an attribute", "assert result == 90", "apply_discount(100, 10)", "Uses `return_value`"],
)
def test_a_points_scene_showing_code_is_refused_pointing_to_marks(tmp_path, capsys, line):
    files(tmp_path, script([SPLIT, scene(visual="Both tests pass\n" + line), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 2: visual: '{line}' looks like code; show it as a code or split scene with marks" in err


def test_a_code_scene_with_marks_on_the_lines_it_names_passes(tmp_path, capsys):
    marked = {
        "kind": "code",
        "heading": "Bug one",
        "code": "tests/test_checkout.py",
        "marks": [{"line": 5, "note": "patches the function under test", "at": "break"}],
        "say": SAY,
        "claims": [],
    }
    files(tmp_path, script([SPLIT, marked, WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    ("bad", "problem"),
    [
        (
            split(right={"code": "t.py", "label": "The tests", "marks": [{"line": 4, "note": "n", "at": "cucumber"}]}),
            "scene 1: marks: 'cucumber'",
        ),
        (kit(link_at="cucumber"), "scene 4: link_at: 'cucumber'"),
    ],
)
def test_a_cue_word_not_in_the_scene_narration_is_refused(tmp_path, capsys, bad, problem):
    scenes = [bad, scene(), WHY, KIT] if bad["kind"] == "split" else [SPLIT, scene(), scene(), bad]
    files(tmp_path, script(scenes))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem + " is not a word of say; the renderer shows it at that word" in err


# Comparisons (owner, second gate 3 of #38): side by side, each side with an example.


@pytest.mark.parametrize("heading", ["Tests versus checks", "Mocks vs fakes", "Unit VS. integration"])
def test_a_comparison_that_is_not_a_compare_scene_is_refused(tmp_path, capsys, heading):
    files(tmp_path, script([SPLIT, scene(heading=heading, say=heading + ". " + SAY), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 2: kind: '{heading}' compares two things; make it a compare scene" in err


def test_a_compare_scene_with_an_example_each_side_passes(tmp_path, capsys):
    files(tmp_path, script([SPLIT, compare(), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


def test_a_compare_side_without_an_example_is_refused(tmp_path, capsys):
    one_sided = compare(right={"heading": "Bug", "items": ["Hides in the mock"]})
    files(tmp_path, script([SPLIT, one_sided, WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 2: right: 1 item; a compare side says what it is and gives at least one example" in err


# Terms (owner, second gate 3 of #38): the screen never names a term before the narrator does.


def test_a_heading_term_not_yet_said_is_refused(tmp_path, capsys):
    files(tmp_path, script([SPLIT, scene(heading="Mutation testing"), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 2: heading: 'Mutation' is on screen before the narrator says it" in err
    assert "'testing'" in err


def test_a_heading_term_said_in_its_scene_or_earlier_passes(tmp_path, capsys):
    said = SAY + " Mutation testing breaks the code."
    scenes = [split(say=said), scene(heading="Mutation testing"), why(heading="Mutations in the tests"), KIT]
    files(tmp_path, script(scenes))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# The AI kit (owner, gate 3 of #38): every video ends by handing the viewer's agent the rules; the fourth
# gate 3 made the kit scene the repo card's GitHub animation, explaining each file and how to use it.


@pytest.mark.parametrize(
    "scenes",
    [
        [SPLIT, scene(), scene(), scene()],
        [SPLIT, scene(), KIT, scene(), scene()],
    ],
)
def test_a_script_without_the_kit_beat_near_its_end_is_refused(tmp_path, capsys, scenes):
    files(tmp_path, script(scenes))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "kit: no kit scene in the last two; end with the Take it to your agent beat" in err


def test_the_kit_beat_may_be_the_one_before_the_bridge(tmp_path, capsys):
    drive = scene(
        heading="Watch the full breakdown", say="Next, watch the full breakdown in the linked video. " + SAY + THANKS
    )
    files(tmp_path, script([SPLIT, WHY, kit(say=SAY), drive]))
    assert run(tmp_path, capsys)[0] == 0


@pytest.mark.parametrize("count", [1, 5])
def test_a_kit_scene_without_two_to_four_takeaways_is_refused(tmp_path, capsys, count):
    files(tmp_path, script([SPLIT, scene(), WHY, kit(takeaways=[f"Takeaway {i}." for i in range(count)])]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 4: takeaways: {count}; the kit scene shows 2-4 takeaways from the video" in err


def demo_folder(root, kit_files=("AGENTS.md", "skills/check-test-can-fail/SKILL.md")):
    """The video's demo record and its AI kit in the demo clone, as build-video-demo leaves them."""
    folder = workspace(root) / "videos" / str(NUMBER)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "demo.json").write_text(json.dumps({"folder": "12-mocked-tests", "link": DEMO_LINK}))
    kit_folder = root / ".projects" / "content" / CONFIG["demos"]["path"] / "12-mocked-tests" / "ai-kit"
    kit_folder.mkdir(parents=True)
    for name in kit_files:
        (kit_folder / name).parent.mkdir(parents=True, exist_ok=True)
        (kit_folder / name).write_text("# kit file\n")


def test_a_kit_whose_files_are_in_the_demo_kit_passes(tmp_path, capsys):
    demo_folder(tmp_path)
    files(tmp_path, script())
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


def test_a_kit_file_not_in_the_demo_kit_is_refused(tmp_path, capsys):
    demo_folder(tmp_path, kit_files=["AGENTS.md"])
    files(tmp_path, script())
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 4: files: 'skills/check-test-can-fail/SKILL.md' is not in the demo's ai-kit folder" in err


def test_a_kit_card_outside_the_demo_kit_folder_is_refused(tmp_path, capsys):
    demo_folder(tmp_path)
    files(tmp_path, script([SPLIT, scene(), WHY, kit(path="12-mocked-tests")]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 4: path: the kit card must show the demo's AI kit folder, {DEMO_LINK}/ai-kit" in err


def test_a_kit_link_word_defaults_to_description(tmp_path, capsys):
    bare = {k: v for k, v in KIT.items() if k != "link_at"}
    files(tmp_path, script([SPLIT, scene(), WHY, bare]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 4: link_at: 'description' is not a word of say" in err


def test_a_kit_file_cue_not_in_say_is_refused(tmp_path, capsys):
    cued = kit(files=[{"path": "AGENTS.md", "use": "Paste into your agents file", "at": "cucumber"}])
    files(tmp_path, script([SPLIT, scene(), WHY, cued]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 4: files: 'cucumber' is not a word of say" in err


# The kit does not repeat (owner, fourth gate 3 of #38): it explains each file, never a line already shown.


@pytest.mark.parametrize(
    ("earlier", "kit_scene", "line"),
    [
        (
            scene(visual="Paste into your agents file"),
            KIT,
            "Paste into your agents file",
        ),
        (
            {
                "kind": "code",
                "heading": "Bug one",
                "code": "t.py",
                "marks": [{"line": 2, "note": "Break the code on purpose", "at": "break"}],
                "say": SAY,
                "claims": [],
            },
            KIT,
            "Break the code on purpose.",
        ),
        (
            compare(right={"heading": "Bug", "items": ["Hides in the mock", "Ask what would make the test FAIL"]}),
            KIT,
            "Ask what would make the test fail.",
        ),
    ],
)
def test_a_kit_repeating_a_line_shown_earlier_is_refused(tmp_path, capsys, earlier, kit_scene, line):
    files(tmp_path, script([SPLIT, earlier, scene(), kit_scene]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 4: kit: '{line}' repeats a line shown in scene 2" in err


def test_a_title_over_title_max_is_refused(tmp_path, capsys):
    files(tmp_path, script(title="x" * 61))
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and "title: 61 characters; at most 60" in err


@pytest.mark.parametrize(
    ("data", "problem"),
    [
        (script([SPLIT, KIT]), "a short needs 30-60 s"),
        (script([SPLIT] + [scene()] * 6 + [KIT]), "a short needs 30-60 s"),
        (script([scene()] * 7 + [KIT], type="long-form"), "a long-form needs 300-600 s"),
    ],
)
def test_a_script_outside_its_content_type_length_is_refused(tmp_path, capsys, data, problem):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and problem in err


def test_a_long_form_of_five_to_ten_minutes_passes(tmp_path, capsys):
    files(tmp_path, long_form([], "myth-buster", first=scene()))
    code, out, err = run(tmp_path, capsys)
    assert (code, err) == (0, "") and 300 <= json.loads(out)["seconds"] <= 600


def test_a_challenge_first_long_form_with_intro_split_and_repo_card_passes(tmp_path, capsys):
    files(tmp_path, long_form([]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# The intro (owner, third gate 3 of #38): a long-form says who it is for and what the viewer will do before
# the challenge; a Short keeps its two-second split hook.


@pytest.mark.parametrize("structure", ["challenge-first", "incident-story", "myth-buster"])
def test_a_long_form_without_an_intro_first_is_refused(tmp_path, capsys, structure):
    data = long_form([], structure)
    data["scenes"] = data["scenes"][1:] + [scene()]
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 1: kind: a long-form opens on an intro scene: who it is for, what they will do, why it matters" in err


def test_a_challenge_first_long_form_whose_second_scene_is_not_the_split_is_refused(tmp_path, capsys):
    files(tmp_path, long_form([], first=scene()))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 2: kind: a code challenge opens on a split scene" in err


@pytest.mark.parametrize(
    ("data", "problem"),
    [
        (script([intro(), SPLIT, WHY, KIT]), "scene 1: kind: a Short has no intro; it opens on its split hook"),
        (long_form([intro()]), "scene 3: kind: an intro is only the first scene of a long-form"),
    ],
)
def test_an_intro_in_a_short_or_after_the_first_scene_is_refused(tmp_path, capsys, data, problem):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    ("change", "line"),
    [
        ({"roles": ["Developers who let AI write tests", "Product managers"]}, "Product managers"),
        ({"activity": "Rank three mocking libraries"}, "Rank three mocking libraries"),
    ],
)
def test_an_intro_whose_say_does_not_name_a_role_or_the_activity_is_refused(tmp_path, capsys, change, line):
    data = long_form([])
    data["scenes"][0] = intro(**change)
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 1: say: the intro shows '{line}' but does not say it; name each role and the activity" in err


# The repo card (owner, third gate 3 of #38): introduce the AI kit on GitHub before any scene uses it.


@pytest.mark.parametrize(
    "use",
    [
        scene(kind="terminal", heading="The kit runs the check", visual="$ python3 ai-kit/scripts/check.py"),
        scene(kind="terminal", heading="The check", visual="$ make check", say="The kit flags both tests. " + SAY),
    ],
)
def test_a_long_form_using_the_kit_before_a_repo_card_is_refused(tmp_path, capsys, use):
    data = long_form([use])
    data["scenes"].remove(REPO)
    data["scenes"].insert(REPO_AT, scene())
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 3: kind: the AI kit is used before a repo scene introduces it" in err


def test_a_long_form_with_no_kit_terminal_needs_the_repo_card_before_its_kit_scene(tmp_path, capsys):
    data = long_form([])
    data["scenes"].remove(REPO)
    data["scenes"].insert(REPO_AT, scene())
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene {REPO_AT + 2}: kind: the AI kit is used before a repo scene introduces it" in err


def test_a_short_needs_no_repo_card_its_kit_link_introduces_the_kit(tmp_path, capsys):
    files(tmp_path, script())
    assert run(tmp_path, capsys)[0] == 0


def test_a_repo_card_matching_the_demo_passes_and_one_elsewhere_is_refused(tmp_path, capsys):
    demo_folder(tmp_path)
    files(tmp_path, long_form([]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")
    data = long_form([])
    data["scenes"][REPO_AT] = repo(path="99-other/ai-kit")
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 40: repo: example-org/example-demos/99-other/ai-kit is not the demo's folder, {DEMO_LINK}" in err


def test_a_repo_card_link_word_not_in_say_is_refused(tmp_path, capsys):
    data = long_form([])
    data["scenes"][REPO_AT] = repo(say=SAY)
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 40: link_at: 'description' is not a word of say" in err


# Concept context (owner, third gate 3 of #38): say why a concept matters before introducing it.


@pytest.mark.parametrize(
    "concept",
    [
        compare(say=SAY),
        scene(heading="Mutation testing", say="Mutation testing seeds faults. " + SAY),
    ],
)
def test_a_concept_without_a_reason_first_is_refused(tmp_path, capsys, concept):
    files(tmp_path, script([SPLIT, concept, WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 2: say: a new concept with no reason first; open with why it matters" in err


@pytest.mark.parametrize(
    ("before", "concept"),
    [
        (SPLIT, compare()),
        (SPLIT, scene(heading="Mutation testing", say="So how do we know a test can fail? Mutation testing. " + SAY)),
        (split(say=SAY + " That is why we need a better question."), compare(say=SAY)),
        (SPLIT, scene(heading="Mutation testing", say="Because mutation testing seeds faults. " + SAY)),
    ],
)
def test_a_concept_whose_reason_comes_first_passes(tmp_path, capsys, before, concept):
    files(tmp_path, script([before, concept, WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    "plain",
    [
        scene(heading="The question nobody asked", say="Here is the question nobody asked. " + SAY),
        {
            "kind": "code",
            "heading": "Bug two: the type",
            "code": "t.py",
            "say": "Now bug two, the type. " + SAY,
            "claims": [],
        },
    ],
)
def test_a_heading_that_is_not_a_bare_term_needs_no_reason(tmp_path, capsys, plain):
    files(tmp_path, script([SPLIT, plain, WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# Like, share, subscribe (owner, fourth gate 3 of #38): graphics, said naturally; the fifth review put them at the
# very end, after the bridge, and made them short: two sentences, about eight seconds (a Short's about four).


def test_a_long_form_ending_on_its_cta_after_the_bridge_passes(tmp_path, capsys):
    files(tmp_path, long_form([]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    "move",
    [
        lambda scenes: scenes.remove(CTA),
        lambda scenes: scenes.insert(-1, scenes.pop()),
        lambda scenes: scenes.insert(REPO_AT - 2, scenes.pop()),
    ],
)
def test_a_long_form_not_ending_on_its_cta_is_refused(tmp_path, capsys, move):
    data = long_form([])
    move(data["scenes"])
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "cta: a long-form ends on a cta scene (like, share, subscribe, notify), after the bridge" in err


def test_a_long_form_cta_before_its_last_scene_is_named(tmp_path, capsys):
    data = long_form([])
    data["scenes"].insert(-1, data["scenes"].pop())
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 42: kind: a long-form's cta is its last scene, after the bridge and its comment question" in err


@pytest.mark.parametrize(
    ("say", "problem"),
    [
        (
            "Before you go, give it a like. // Share it with a tester. // Subscribe, and turn on the bell.",
            "scene 43: say: the cta has 3 sentences; keep it to at most 2",
        ),
        (
            (
                "Before you go, if this challenge helped you today, give it a like and share it with a tester on "
                "your team. // Subscribe, and turn on the bell for notifications."
            ),
            "scene 43: say: the cta takes about 11 s; keep it to about 8 s",
        ),
    ],
)
def test_a_long_form_cta_over_two_sentences_or_eight_seconds_is_refused(tmp_path, capsys, say, problem):
    data = long_form([])
    data["scenes"][-1] = cta(say=say)
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


def test_a_long_form_cta_without_all_four_actions_is_refused(tmp_path, capsys):
    data = long_form([])
    data["scenes"][-1] = cta(actions=["like", "subscribe"])
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 43: actions: a long-form's cta shows all four: like, share, subscribe, notify" in err


@pytest.mark.parametrize(
    ("say", "action"),
    [
        ("Before you go, give it a like. // Share it, and subscribe for more.", "notify"),
        ("Before you go, share it with a tester. // Subscribe, and turn on the bell.", "like"),
    ],
)
def test_a_cta_whose_say_does_not_name_each_action_is_refused(tmp_path, capsys, say, action):
    data = long_form([])
    data["scenes"][-1] = cta(say=say, heading="Share and subscribe")
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene 43: say: the cta shows '{action}' but does not say it" in err


def test_a_short_cta_over_four_seconds_is_refused(tmp_path, capsys):
    ending = cta(
        actions=["subscribe"],
        heading="Subscribe",
        say="Next, subscribe for a brand new spot the bug challenge every single week.",
    )
    files(tmp_path, script([SPLIT, scene(), WHY, KIT, ending]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 5: say: the cta takes about 5 s; keep it to about 4 s" in err


def test_a_short_may_end_on_a_cta_naming_subscribe(tmp_path, capsys):
    files(tmp_path, script([SPLIT, scene(), WHY, KIT, SHORT_CTA]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    ("scenes", "problem"),
    [
        (
            [SPLIT, scene(), cta(actions=["subscribe"], heading="Subscribe", say="Subscribe now. " + SAY), KIT],
            "scene 3: kind: a Short's cta is its last scene",
        ),
        (
            [SPLIT, scene(), scene(), KIT, cta(actions=["like"], heading="Like", say="Give it a like.")],
            "scene 5: actions: a Short's cta names subscribe",
        ),
    ],
)
def test_a_short_cta_not_last_or_without_subscribe_is_refused(tmp_path, capsys, scenes, problem):
    files(tmp_path, script(scenes))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


# The Short flow (owner, fourth gate 3 of #38): curiosity in the first three seconds, then challenge, why it
# matters, the takeaway, and a drive to the long video for the full breakdown.


@pytest.mark.parametrize(
    ("first", "problem"),
    [
        (
            {k: v for k, v in SPLIT.items() if k != "hook"},
            "scene 1: hook: a Short opens on a split with a hook of 2-8 words, said in its first sentence",
        ),
        (split(hook="Nobody reads these tests"), "scene 1: hook: 'Nobody reads these tests' is not said in"),
        (
            split(hook="Both tests pass", say="Both tests pass on every single run in our pipeline today. " + SAY),
            "scene 1: say: the first sentence takes about 4 s; a Short's hook is said within 3 s",
        ),
    ],
)
def test_a_short_without_a_hook_said_in_its_first_three_seconds_is_refused(tmp_path, capsys, first, problem):
    files(tmp_path, script([first, scene(), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    ("scenes", "problem"),
    [
        (
            [split(right={"code": "tests/test_checkout.py", "label": "The tests"}), scene(), WHY, KIT],
            "short: no challenge beat; mark the bug's line in a code or split scene",
        ),
        (
            [SPLIT, scene(), scene(), KIT],
            "short: no why-it-matters beat; between the challenge and the kit, say why it matters",
        ),
        (
            [SPLIT, scene(), WHY, kit(say=SAY)],
            "scene 4: say: a Short ends by driving to the long video; name the full video or breakdown",
        ),
        (
            [SPLIT, WHY, scene(kind="title", visual="Take it to your agent"), KIT],
            "scene 3: kind: a Short has no title slide before the kit",
        ),
    ],
)
def test_a_short_missing_a_beat_of_its_flow_is_refused(tmp_path, capsys, scenes, problem):
    files(tmp_path, script(scenes))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


def test_a_long_form_split_may_have_a_hook_and_needs_none(tmp_path, capsys):
    files(tmp_path, long_form([], first={k: v for k, v in SPLIT.items() if k != "hook"}))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# Transitions (owner, fifth review of #38): each scene after the first opens on a bridge from the one before,
# such as "Now that we have seen the bug, let us look at the fix."


@pytest.mark.parametrize(
    "opening",
    [
        "Now that we have seen the bug, let us look at the fix.",
        "Next, the tests.",
        "So what do the tests check?",
        "But the tests stay green.",
        "Here is the fix.",
        "With that, look at the tests.",
        "Let's look at the tests.",
        "We have seen the code, and the tests come next.",
        "First, the code.",
        "Then the tests run.",
        "Finally, the fix.",
        "One more bug hides in the tests.",
        "Before the fix, look at the tests.",
        "After the fix, both tests fail.",
    ],
)
def test_a_scene_opening_on_a_transition_cue_passes(tmp_path, capsys, opening):
    files(tmp_path, script([SPLIT, scene(say=opening + " " + SAY), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    ("data", "index"),
    [
        (script([SPLIT, scene(say="The tests pass. " + SAY), WHY, KIT]), 2),
        (script([SPLIT, scene(), why(say=WHY_SAY.replace("So why", "Why")), KIT]), 3),
        (long_form([scene(say="The tests pass. " + SAY)]), 3),
    ],
)
def test_a_scene_after_the_first_with_no_bridge_is_refused_showing_its_first_sentence(tmp_path, capsys, data, index):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene {index}: say: no bridge from the scene before; open with a transition cue" in err
    assert "The tests pass." in err or "Why does it matter?" in err


def test_the_first_scene_needs_no_bridge(tmp_path, capsys):
    files(tmp_path, script([split(say="Both tests pass. " + SAY), scene(), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


# Grammar (owner, fifth review of #38): every line on screen and every narrated sentence is natural English;
# "Review code an AI wrote" is wrong, "Review code written by AI" right. The script checks a few cheap patterns;
# the writer's grammar pass judges the rest.


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"say": SAY + " The the bug hides here."}, "scene 2: say: doubled word 'The the'"),
        ({"visual": "Both tests pass\nSpot the the bug"}, "scene 2: visual: doubled word 'the the'"),
        ({"say": SAY + " // now look again."}, "scene 2: say: 'now look again.' does not start with a capital letter"),
        ({"visual": "Both tests pass\nSpot the bug in the"}, "scene 2: visual: 'Spot the bug in the' ends on 'the'"),
        ({"heading": "Spot the bug and"}, "scene 2: heading: 'Spot the bug and' ends on 'and'"),
        ({"say": SAY + " We review code an AI wrote."}, "scene 2: say: 'code an AI wrote' is a reduced relative"),
        ({"heading": "Review tests an agent built"}, "scene 2: heading: 'tests an agent built' is a reduced relative"),
    ],
)
def test_an_ungrammatical_line_or_sentence_is_refused_naming_it(tmp_path, capsys, change, problem):
    files(tmp_path, script([SPLIT, scene(**change), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    "line",
    [
        "Review code written by AI",
        "Who this video is for",
        "I think that that is fine",
        "Tests the AI wrote",
    ],
)
def test_grammatical_lines_and_short_labels_pass(tmp_path, capsys, line):
    files(tmp_path, script([SPLIT, scene(visual="Both tests pass\n" + line), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


@pytest.mark.parametrize(
    ("scene_", "field"),
    [
        (intro(roles=["Developers who let AI write tests", "Testers who review code an AI wrote"]), "visual"),
        (intro(stake="They pass while customers pay the"), "visual"),
        (kit(takeaways=["Break the the code.", "Ask what would make the test fail."]), "visual"),
        (
            split(
                right={"code": "t.py", "label": "The tests", "marks": [{"line": 4, "note": "a mock of", "at": "bug"}]}
            ),
            "visual",
        ),
    ],
)
def test_every_on_screen_line_is_checked(scene_, field):
    assert any(field in p for p in check_script.grammar_problems(1, scene_))


# Names (owner, fifth review of #38): narration never names people; the description's References credit the concept
# and its source. channel.yaml narration_avoid_names lists the names to refuse.

NAMES = {"narration_avoid_names": ["James Bach", "Michael Bolton", "Bolton"]}


@pytest.mark.parametrize("said", ["As James Bach puts it, testing is not checking.", "Bolton calls this checking."])
def test_narration_naming_a_listed_person_is_refused(tmp_path, capsys, said):
    files(tmp_path, script([SPLIT, scene(say=SAY + " " + said), WHY, KIT]))
    workspace(tmp_path, config=CONFIG | NAMES)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert "scene 2: say: names a person ('" in err
    assert "credit the concept and its source in the description's References" in err


def test_a_name_passes_when_the_channel_lists_none(tmp_path, capsys):
    files(tmp_path, script([SPLIT, scene(say=SAY + " Bolton calls this checking."), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


def test_claims_without_a_citations_file_are_refused(tmp_path, capsys):
    files(tmp_path, script(), citations=None)
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and "citations.json: missing; research-video writes it" in err


def test_every_problem_is_named_at_once(tmp_path, capsys):
    files(tmp_path, script([split(say="In this video it costs 90. " + SAY), scene(claims=["C9"]), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert all(p in err for p in ["banned phrase", "digits '90'", "scene 2: claims: C9"])


@pytest.mark.parametrize(
    ("data", "problem"),
    [
        ("{not json", "not valid JSON"),
        (script(scenes=[]), "scenes: must be a non-empty list"),
        (script(type="vlog"), "type: must be long-form or short"),
        (script(structure="listicle"), "structure: must be challenge-first, incident-story, or myth-buster"),
        (script([{"kind": "points", "heading": "h", "visual": "v", "claims": []}]), "scene 1: say: missing"),
        (script([{"kind": "code", "heading": "h", "say": SAY, "claims": []}]), "scene 1: code: missing"),
        (script([scene(claims="C1")]), "scene 1: claims: must be a list of claim ids"),
        (script([scene(kit=True)]), "scene 1: kit: the kit flag is replaced by kind kit"),
        (
            script([scene(kind="slide")]),
            "kind: must be title, intro, points, code, terminal, split, compare, repo, kit, or cta",
        ),
        (script([split(left={"code": "demo/checkout.py"})]), "scene 1: left: must be {code, label}"),
        (
            script([split(left={"code": "demo/checkout.py", "label": "The code", "marks": "line 4"})]),
            "scene 1: left: marks: each",
        ),
        (
            script(
                [split(left={"code": "c.py", "label": "The code", "marks": [{"line": 0, "note": "n", "at": "bug"}]})]
            ),
            "scene 1: left: marks: each",
        ),
        (script([scene(marks=[])]), "scene 1: marks: only code and split scenes have marks"),
        (script([compare(left={"heading": "Tests", "items": []})]), "scene 1: left: must be {heading, items}"),
        (script([kit(link=DEMO_LINK + "/ai-kit")]), "scene 1: link: replaced by repo and path"),
        (script([kit(snippet=["Never mock it."])]), "scene 1: snippet: replaced by files"),
        (script([kit(repo="example-demos")]), "scene 1: repo: must be a GitHub repository like owner/name"),
        (script([kit(path="")]), "scene 1: path: must be a non-empty string"),
        (script([kit(files=[])]), "scene 1: files: must be 1-8 of {path, use, at}"),
        (script([kit(files=[{"path": "AGENTS.md", "use": "Paste it"}])]), "scene 1: files: must be 1-8 of"),
        (script([kit(files=["AGENTS.md"])]), "scene 1: files: must be 1-8 of {path, use, at}"),
        (script([kit(takeaways="Break it")]), "scene 1: takeaways: must be a list of lines"),
        (script([kit(link_at=None)]), "scene 1: link_at: must be a word of say"),
        (script([cta(actions=[])]), "scene 1: actions: must be a non-empty list of like, share, subscribe, or notify"),
        (script([cta(actions=["like", "like"])]), "scene 1: actions: must be a non-empty list of like"),
        (script([cta(actions=["bell"])]), "scene 1: actions: must be a non-empty list of like"),
        (script([split(hook="Look")]), "scene 1: hook: must be 2-8 words"),
        (script([split(hook=" ".join(["word"] * 9))]), "scene 1: hook: must be 2-8 words"),
        (script([scene(hook="Both tests pass")]), "scene 1: hook: only a split scene has a hook"),
        (script([intro(roles=["Developers"])]), "scene 1: roles: must be 2-3 lines"),
        (script([intro(roles=["a", "b", "c", "d"])]), "scene 1: roles: must be 2-3 lines"),
        (script([intro(activity="")]), "scene 1: activity: must be a non-empty string"),
        (script([intro(stake=None)]), "scene 1: stake: must be a non-empty string"),
        (script([repo(repo="example-demos")]), "scene 1: repo: must be a GitHub repository like owner/name"),
        (script([repo(path=" ")]), "scene 1: path: must be a non-empty string"),
        (script([repo(files=[])]), "scene 1: files: must be 1-8 lines"),
        (script([repo(files=[f"f{i}" for i in range(9)])]), "scene 1: files: must be 1-8 lines"),
        (script([repo(link_at=7)]), "scene 1: link_at: must be a word of say"),
    ],
)
def test_an_invalid_script_file_exits_2_naming_the_field(tmp_path, capsys, data, problem):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 2 and problem in err


def test_a_missing_script_exits_2(tmp_path, capsys):
    files(tmp_path)
    code, _, err = run(tmp_path, capsys)
    assert code == 2 and "no script.json" in err


def test_a_split_with_marks_outside_its_sides_is_refused(tmp_path, capsys):
    """render.py reads a split's marks inside each side, so marks on the scene would never show."""
    files(tmp_path, script([split(marks=[{"line": 4, "note": "n", "at": "bug"}]), scene(), WHY, KIT]))
    code, _, err = run(tmp_path, capsys)
    assert code == 2
    assert "scene 1: marks: a split's marks go inside its left or right side" in err


# The thank-you ending (owner, #81): every video, long-form and Short, ends by thanking the viewer in its last
# scene's say, inside row 32's cta limits.


@pytest.mark.parametrize(
    ("data", "ending", "last"),
    [
        (long_form([]), cta(say="Before you go, like and share this. // Subscribe, and turn on the bell."), 43),
        (script(), kit(say=SAY + DRIVE), 4),
        (script([SPLIT, scene(), WHY, KIT, SHORT_CTA]), SHORT_CTA | {"say": "Subscribe for the next challenge."}, 5),
    ],
)
def test_a_last_scene_without_a_thank_you_is_refused_naming_it(tmp_path, capsys, data, ending, last):
    data["scenes"][-1] = ending
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert f"scene {last}: say: the last scene thanks the viewer; say thank you or thanks" in err


@pytest.mark.parametrize("data", [long_form([]), script(), script([SPLIT, scene(), WHY, KIT, SHORT_CTA])])
def test_a_last_scene_thanking_the_viewer_passes_inside_the_cta_limits(tmp_path, capsys, data):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")

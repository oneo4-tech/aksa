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

# Twenty-five words in four sentences: short, medium, short, medium.
SAY = (
    "Both tests pass. "
    "I can break the code in one keystroke and neither of them notices. "
    "Spot the bug. "
    "The bug is in the tests."
)
CITATIONS = [
    {"id": "C1", "claim": "The healer reruns a test.", "url": "https://example.com/a", "quote": "q", "found": True},
    {"id": "C2", "claim": "A check verifies.", "url": "https://example.com/b", "quote": "q", "found": False},
]


def scene(**fields):
    base = {"kind": "points", "heading": "Spot the bug", "visual": "Two green tests", "say": SAY, "claims": []}
    return base | fields


def script(scenes=None, **fields):
    """A Short of four scenes, one hundred words: about forty-one seconds at the channel's pace."""
    base = {
        "title": "Spot the Bug: the test that tests nothing",
        "type": "short",
        "structure": "challenge-first",
        "acronyms": ["AI"],
        "scenes": scenes if scenes is not None else [scene(claims=["C1"]), scene(), scene(), scene()],
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
    assert report["words"] == 100 and report["target_seconds"] == [30, 60]
    assert report["seconds"] == round(100 * 60 / WPM)


def test_pauses_and_hesitations_add_time_but_are_not_words(tmp_path, capsys):
    paused = SAY.replace("Spot the bug.", "Spot the bug. // Look... closely.")
    files(tmp_path, script([scene(say=paused)] * 4))
    code, out, _ = run(tmp_path, capsys)
    report = json.loads(out)
    assert code == 0 and report["words"] == 4 * 27
    expected = 4 * 27 * 60 / WPM + 4 * (check_script.PAUSE_SECONDS + check_script.HESITATION_SECONDS)
    assert report["seconds"] == round(expected)


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
    files(tmp_path, script([scene(**change), scene(), scene(), scene()]))
    code, _, err = run(tmp_path, capsys)
    assert code == 3
    assert problem in err


@pytest.mark.parametrize(
    "say",
    [
        "This is NOT a test. " + SAY,
        "AI wrote this, and it is NOT a test. " + SAY,
        "Wait // and look... closely. " + SAY,
        "Run pytest now. " + SAY,
    ],
)
def test_one_stressed_word_listed_acronyms_pause_markup_and_real_words_are_allowed(tmp_path, capsys, say):
    files(tmp_path, script([scene(say=say, visual="assert result == 90", heading="Bug 1")] + [scene()] * 3))
    code, _, err = run(tmp_path, capsys)
    assert (code, err) == (0, "")


def test_digits_and_code_stay_allowed_in_a_code_scene(tmp_path, capsys):
    code_scene = {"kind": "code", "heading": "The tests", "code": "demo/test_discount_ai.py", "say": SAY, "claims": []}
    files(tmp_path, script([code_scene, scene(), scene(), scene()]))
    assert run(tmp_path, capsys)[0] == 0


def test_a_title_over_title_max_is_refused(tmp_path, capsys):
    files(tmp_path, script(title="x" * 61))
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and "title: 61 characters; at most 60" in err


@pytest.mark.parametrize(
    ("data", "problem"),
    [
        (script([scene()] * 2), "a short needs 30-60 s"),
        (script([scene()] * 8), "a short needs 30-60 s"),
        (script([scene()] * 8, type="long-form"), "a long-form needs 300-600 s"),
    ],
)
def test_a_script_outside_its_content_type_length_is_refused(tmp_path, capsys, data, problem):
    files(tmp_path, data)
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and problem in err


def test_a_long_form_of_five_to_ten_minutes_passes(tmp_path, capsys):
    files(tmp_path, script([scene()] * 40, type="long-form", structure="myth-buster"))
    code, out, _ = run(tmp_path, capsys)
    assert code == 0 and 300 <= json.loads(out)["seconds"] <= 600


def test_claims_without_a_citations_file_are_refused(tmp_path, capsys):
    files(tmp_path, script(), citations=None)
    code, _, err = run(tmp_path, capsys)
    assert code == 3 and "citations.json: missing; research-video writes it" in err


def test_every_problem_is_named_at_once(tmp_path, capsys):
    files(tmp_path, script([scene(say="In this video it costs 90. " + SAY), scene(claims=["C9"])] + [scene()] * 2))
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
        (script([scene(kind="slide")]), "scene 1: kind: must be title, points, code, or terminal"),
        (script([{"kind": "points", "heading": "h", "visual": "v", "claims": []}]), "scene 1: say: missing"),
        (script([{"kind": "code", "heading": "h", "say": SAY, "claims": []}]), "scene 1: code: missing"),
        (script([scene(claims="C1")]), "scene 1: claims: must be a list of claim ids"),
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

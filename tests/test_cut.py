"""Tests for plan-shorts' cut.py, through main(argv, root) against a workspace in a tmp root."""

import json
import sys
from pathlib import Path

import pytest
from test_scaffold import claim
from test_youtube_channel import workspace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/plan-shorts/scripts"))
import cut

DEMO = {
    "folder": "42-mocked-tests",
    "link": "https://github.com/example-org/example-demos/tree/main/42-mocked-tests",
    "proves": "A test that mocks the function under test passes even when the code is broken.",
    "pushed": True,
}
CITATIONS = [claim(1), claim(2), claim(3)]
SCENES = [
    {"kind": "title", "claims": []},
    {"kind": "code", "claims": ["C1"]},
    {"kind": "terminal", "claims": ["C3", "C1"]},
    {"kind": "points", "claims": ["C2"]},
]
ARGV = ["example", "43", "--from", "42", "--scenes", "2,3"]


def video(root, number):
    return root / ".projects" / "content" / "yt-example" / "videos" / str(number)


@pytest.fixture
def root(tmp_path):
    workspace(tmp_path)
    long_form = video(tmp_path, 42)
    long_form.mkdir(parents=True)
    (long_form / "demo.json").write_text(json.dumps(DEMO))
    (long_form / "citations.json").write_text(json.dumps(CITATIONS))
    (long_form / "script.json").write_text(json.dumps({"type": "long-form", "scenes": SCENES}))
    video(tmp_path, 43).mkdir()
    return tmp_path


def read(path):
    return json.loads(path.read_text())


def test_a_cut_short_gets_the_long_forms_demo_and_the_citations_its_scenes_use(root):
    assert cut.main(ARGV, root=root) == 0
    short = video(root, 43)
    assert read(short / "demo.json") == DEMO
    assert read(short / "citations.json") == [CITATIONS[0], CITATIONS[2]]


def test_a_cut_short_gets_the_long_forms_recording_when_it_has_one(root):
    (video(root, 42) / "demo.mp4").write_bytes(b"recording")
    assert cut.main(ARGV, root=root) == 0
    assert (video(root, 43) / "demo.mp4").read_bytes() == b"recording"


def two_terminal_long_form(root):
    """A long-form whose scenes 2 and 4 are terminal, each with its own recording from record.py."""
    scenes = [
        {"kind": "title", "claims": []},
        {"kind": "terminal", "claims": ["C1"]},
        {"kind": "code", "claims": ["C2"]},
        {"kind": "terminal", "claims": ["C3"]},
    ]
    (video(root, 42) / "script.json").write_text(json.dumps({"type": "long-form", "scenes": scenes}))
    (video(root, 42) / "demo-1.mp4").write_bytes(b"first terminal")
    (video(root, 42) / "demo-2.mp4").write_bytes(b"second terminal")


def test_a_cut_short_gets_its_terminal_scenes_recordings_renumbered_in_its_order(root):
    two_terminal_long_form(root)
    assert cut.main(["example", "43", "--from", "42", "--scenes", "4,3,2"], root=root) == 0
    short = video(root, 43)
    assert (short / "demo-1.mp4").read_bytes() == b"second terminal"
    assert (short / "demo-2.mp4").read_bytes() == b"first terminal"
    assert not (short / "demo.mp4").exists()


def test_a_cut_terminal_scene_without_its_recording_is_refused(root, capsys):
    two_terminal_long_form(root)
    (video(root, 42) / "demo-2.mp4").unlink()
    assert cut.main(["example", "43", "--from", "42", "--scenes", "4"], root=root) == 3
    assert "demo-2.mp4" in capsys.readouterr().err
    assert not (video(root, 43) / "demo.json").exists()


@pytest.mark.parametrize("name", ["demo.json", "citations.json", "script.json"])
def test_a_long_form_output_missing_is_refused_naming_it(root, capsys, name):
    (video(root, 42) / name).unlink()
    assert cut.main(ARGV, root=root) == 3
    assert name in capsys.readouterr().err
    assert not (video(root, 43) / "demo.json").exists()


def test_unverified_long_form_citations_are_refused(root, capsys):
    (video(root, 42) / "citations.json").write_text(json.dumps([claim(1), claim(2, found=False), claim(3)]))
    assert cut.main(ARGV, root=root) == 3
    assert "C2" in capsys.readouterr().err
    assert not (video(root, 43) / "citations.json").exists()


def test_a_demo_without_folder_or_link_is_refused(root, capsys):
    (video(root, 42) / "demo.json").write_text(json.dumps({"folder": DEMO["folder"]}))
    assert cut.main(ARGV, root=root) == 3
    assert "link" in capsys.readouterr().err


def test_scenes_that_state_no_cited_fact_are_refused(root, capsys):
    assert cut.main(["example", "43", "--from", "42", "--scenes", "1"], root=root) == 3
    assert "no claim" in capsys.readouterr().err


@pytest.mark.parametrize("scenes", ["0", "5", "2,x", ""])
def test_a_scene_number_outside_the_long_form_is_bad_input(root, capsys, scenes):
    assert cut.main(["example", "43", "--from", "42", "--scenes", scenes], root=root) == 2
    assert "scene" in capsys.readouterr().err


def test_a_short_without_its_folder_is_refused(root, capsys):
    video(root, 43).rmdir()
    assert cut.main(ARGV, root=root) == 3
    assert "content_issue.py new" in capsys.readouterr().err


@pytest.mark.parametrize("name", ["demo.json", "citations.json"])
def test_a_short_that_already_has_its_demo_or_citations_is_never_overwritten(root, capsys, name):
    (video(root, 43) / name).write_text("[]")
    assert cut.main(ARGV, root=root) == 3
    assert name in capsys.readouterr().err
    assert (video(root, 43) / name).read_text() == "[]"


def test_a_short_cut_from_itself_is_bad_input(root):
    assert cut.main(["example", "42", "--from", "42", "--scenes", "2"], root=root) == 2

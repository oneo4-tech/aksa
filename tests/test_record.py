"""Tests for build-video-demo's record.py, through main(argv, root, vhs) with a fake vhs."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from test_youtube_channel import workspace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/build-video-demo/scripts"))
import record

NUMBER = 38
FOLDER = "38-ai-test-mutation"
SETUP = """Output demo.mp4
Set Shell zsh
Set Width 1920

Hide
Type "export PS1='$ ' && clear" Enter
Show
Sleep 500ms
"""
SECTIONS = [
    'Type "./demo/mutate.sh" Enter\nSleep 8s\n',
    'Type "./demo/mutate.sh boundary" Enter\nSleep 8s\n',
    'Type "ai-kit/scripts/mutation_smoke.py" Enter\nSleep 9s\n',
]
TAPE = SETUP + "".join(f"# scene\n{section}" for section in SECTIONS)
TERMINAL = {"kind": "terminal", "heading": "Run it", "visual": "$ ./demo/mutate.sh", "say": "S"}
POINTS = {"kind": "points", "heading": "Why", "visual": "a\nb", "say": "S"}


def demo(root, tape=TAPE, terminals=3):
    """The video's script and demo record, and the demo folder holding its tape; returns (video, folder)."""
    video = workspace(root) / "videos" / str(NUMBER)
    video.mkdir(parents=True)
    scenes = [POINTS] + [TERMINAL] * terminals
    (video / "script.json").write_text(json.dumps({"type": "long-form", "scenes": scenes}))
    (video / "demo.json").write_text(json.dumps({"folder": FOLDER, "link": "https://x", "pushed": False}))
    folder = root / ".projects" / "content" / "example-demos" / FOLDER
    folder.mkdir(parents=True)
    (folder / "demo.tape").write_text(tape)
    return video, folder


class FakeVhs:
    """Records each tape it is given, with its working folder, and writes the tape's Output there."""

    def __init__(self):
        self.tapes = []

    def __call__(self, tape, cwd):
        text = Path(tape).read_text()
        self.tapes.append({"text": text, "cwd": Path(cwd)})
        (Path(cwd) / re.search(r"^Output (\S+)$", text, re.MULTILINE).group(1)).write_bytes(text.encode())


def run(root, vhs, capsys):
    code = record.main(["example", str(NUMBER)], root=root, vhs=vhs)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_each_scene_section_is_recorded_alone_after_the_shared_setup(tmp_path, capsys):
    video, folder = demo(tmp_path)
    vhs = FakeVhs()
    assert run(tmp_path, vhs, capsys)[0] == 0
    assert [t["cwd"] for t in vhs.tapes] == [folder] * 3
    for k, (tape, section) in enumerate(zip(vhs.tapes, SECTIONS), 1):
        assert tape["text"] == SETUP.replace("Output demo.mp4", f"Output demo-{k}.mp4") + section
    # Each recording is moved into the video folder, none left in the public demo folder.
    for k in (1, 2, 3):
        assert (video / f"demo-{k}.mp4").read_text().endswith(SECTIONS[k - 1])
        assert not (folder / f"demo-{k}.mp4").exists()


def test_a_scene_marker_may_carry_a_label(tmp_path, capsys):
    labelled = TAPE.replace("# scene\n", "# scene: a mutant\n", 1)
    demo(tmp_path, tape=labelled)
    assert run(tmp_path, vhs := FakeVhs(), capsys)[0] == 0
    assert len(vhs.tapes) == 3 and "# scene" not in vhs.tapes[0]["text"]


@pytest.mark.parametrize("terminals", [2, 4])
def test_sections_not_matching_the_terminal_scenes_are_refused_naming_both_counts(tmp_path, capsys, terminals):
    video, _ = demo(tmp_path, terminals=terminals)
    code, _, err = run(tmp_path, vhs := FakeVhs(), capsys)
    assert code == 3 and vhs.tapes == []
    assert "3 '# scene' sections" in err and f"{terminals} terminal scenes" in err
    assert not list(video.glob("demo-*.mp4"))


def test_a_tape_without_one_output_line_before_the_first_scene_is_refused(tmp_path, capsys):
    demo(tmp_path, tape=TAPE.replace("Output demo.mp4\n", ""))
    code, _, err = run(tmp_path, vhs := FakeVhs(), capsys)
    assert code == 2 and "Output" in err and vhs.tapes == []


def test_a_missing_tape_is_refused_naming_build_video_demo(tmp_path, capsys):
    _, folder = demo(tmp_path)
    (folder / "demo.tape").unlink()
    code, _, err = run(tmp_path, FakeVhs(), capsys)
    assert code == 2 and "demo.tape" in err and "build-video-demo" in err


def test_a_failing_vhs_is_a_tool_error(tmp_path, capsys):
    demo(tmp_path)

    def broken(tape, cwd):
        raise record.ToolError("vhs failed: no ttyd")

    code, _, err = run(tmp_path, broken, capsys)
    assert code == 1 and "vhs failed" in err


@pytest.mark.media
@pytest.mark.skipif(not shutil.which("vhs"), reason="vhs is missing; brew install vhs (#28)")
def test_real_vhs_records_one_clip_per_section(tmp_path, capsys):
    tape = 'Output demo.mp4\nSet Width 640\nSet Height 360\nHide\nType "clear" Enter\nShow\n'
    tape += '# scene\nType "echo one" Enter\nSleep 300ms\n# scene: two\nType "echo two" Enter\nSleep 300ms\n'
    video, folder = demo(tmp_path, tape=tape, terminals=2)
    assert run(tmp_path, record.vhs, capsys)[0] == 0
    for k in (1, 2):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video / f"demo-{k}.mp4")],
            check=True, capture_output=True, text=True,
        ).stdout  # fmt: skip
        assert float(out) > 0
    assert not list(folder.glob("*.mp4"))

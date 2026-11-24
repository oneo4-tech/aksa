"""Tests for build-video-demo's record.py, through main(argv, root, vhs, transcribe) with a fake vhs and whisper."""

import json
import re
import shutil
import subprocess
import sys
import wave
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


def unheard(wav):
    raise AssertionError(f"transcribed {wav.name} without narration")


def run(root, vhs, capsys, transcribe=unheard):
    code = record.main(["example", str(NUMBER)], root=root, vhs=vhs, transcribe=transcribe)
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


# A narrated terminal scene: TypingSpeed 50ms, each key and typed character one tick.
NARRATED = (
    'Type "# the claim, in one line" Enter\n'  # 25 ticks, 1.25 s
    "Sleep 800ms\n"
    'Type "pytest -q tests" Sleep 300ms Enter\n'  # 16 ticks and 300 ms, 1.1 s: the step takes 3.15 s
    "Sleep 4s\n"
    'Type "# break the boundary" Enter\n'  # 21 ticks, 1.05 s
    "Sleep 500ms\n"
    'Type "./demo/mutate.sh boundary" Enter\n'  # 26 ticks, 1.3 s: the step takes 2.85 s
    "Sleep 6s\n"
)
NARRATED_TAPE = SETUP.replace("Set Width 1920", "Set Width 1920\nSet TypingSpeed 50ms") + "# scene\n" + NARRATED
NARRATED_TAPE += "".join(f"# scene\n{section}" for section in SECTIONS[1:])
# "First, the claim. We run the tests. Now we break the boundary." The second step's word, break, is mid-sentence.
SAID = [("First,", 0.5), ("the", 0.8), ("claim.", 1.0), ("We", 2.0), ("run", 2.2), ("the", 2.4), ("tests.", 2.6),
        ("Now", 5.0), ("we", 5.2), ("break", 5.4), ("the", 5.6), ("boundary.", 5.8)]  # fmt: skip


def whisper(said):
    """A transcriber hearing said, as whisper-cli -ml 1 -sow -ojf: one segment per word, offsets in milliseconds."""
    segments = [{"offsets": {"from": int(at * 1000), "to": int(at * 1000) + 150}, "text": f" {w}"} for w, at in said]
    return lambda wav: {"transcription": segments}


def narrate(video, scene, seconds):
    """narration/NN.wav for the scene, silent, seconds long."""
    (video / "narration").mkdir(exist_ok=True)
    with wave.open(str(video / "narration" / f"{scene:02d}.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * int(16000 * seconds))


def test_a_narrated_section_starts_each_comment_step_as_its_sentence_starts(tmp_path, capsys):
    video, _ = demo(tmp_path, tape=NARRATED_TAPE)
    narrate(video, 2, 9.0)  # the first terminal scene: 0.4 + 9 + 0.6 = 10 s, 300 frames
    vhs = FakeVhs()
    assert run(tmp_path, vhs, capsys, whisper(SAID))[0] == 0
    # Clip time is narration time + LEAD 0.4: steps start at 0.9 (First) and 5.4 (Now, not break at 5.8).
    # The clip opens on the 0.5 s after Show, so 0.4 s more; each step's last Sleep holds to the next step's start,
    # the last one to the scene's 10 s.
    narrated = NARRATED.replace("Sleep 4s", "Sleep 1350ms").replace("Sleep 6s", "Sleep 1750ms")
    head = NARRATED_TAPE.split("# scene\n")[0].replace("Output demo.mp4", "Output demo-1.mp4")
    assert vhs.tapes[0]["text"] == head + "Sleep 400ms\n" + narrated
    # Scenes without narration record as written.
    assert vhs.tapes[1]["text"].endswith(SECTIONS[1])


def test_a_step_whose_comment_is_never_heard_is_refused_naming_scene_and_comment(tmp_path, capsys):
    video, _ = demo(tmp_path, tape=NARRATED_TAPE.replace("# break the boundary", "# the mutant survives"))
    narrate(video, 2, 9.0)
    code, _, err = run(tmp_path, vhs := FakeVhs(), capsys, whisper(SAID))
    assert code == 3 and vhs.tapes == []
    assert "scene 2" in err and "# the mutant survives" in err


def test_a_step_that_cannot_be_typed_before_the_next_sentence_is_refused(tmp_path, capsys):
    video, _ = demo(tmp_path, tape=NARRATED_TAPE)
    narrate(video, 2, 9.0)
    early = [(w, at - 2.0 if at >= 5.0 else at) for w, at in SAID]  # "Now" at 3.0: the first step needs until 4.05
    code, _, err = run(tmp_path, vhs := FakeVhs(), capsys, whisper(early))
    assert code == 3 and vhs.tapes == []
    assert "scene 2" in err and "# break the boundary" in err


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

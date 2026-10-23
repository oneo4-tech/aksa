"""Tests for the narrate-video skill's scripts/narrate.py, through main with fake Gemini, ffmpeg, and whisper."""

import base64
import json
import shutil
import sys
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/narrate-video/scripts"))
import narrate

NUMBER = 14
KEY = "test-key-never-printed"
# CONFIG: voice Puck, style "warm and conversational", pace 0.92, pronunciation {"pytest": "pie test"}.
SAYS = ["Both tests pass. // Run pytest now.", "Spot the bug... in the tests."]
WAV = b"RIFF fake wav"


def files(root, says=SAYS):
    folder = workspace(root) / "videos" / str(NUMBER)
    folder.mkdir(parents=True, exist_ok=True)
    scenes = [{"kind": "points", "heading": "H", "visual": "V", "say": say, "claims": []} for say in says]
    (folder / "script.json").write_text(json.dumps({"title": "T", "type": "short", "scenes": scenes}))
    return folder


def audio(data=WAV):
    content = [{"type": "audio", "mime_type": "audio/wav", "data": base64.b64encode(data).decode()}]
    return {"steps": [{"type": "model_output", "content": content}]}


class Fakes:
    """Gemini answering every request with audio, ffmpeg copying its input, whisper hearing the script."""

    def __init__(self, heard=None):
        self.bodies, self.keys, self.commands = [], [], []
        self.heard = heard  # scene number -> transcript; others hear their spoken text

    def post(self, body, key):
        self.bodies.append(body)
        self.keys.append(key)
        return audio()

    def run(self, command):
        self.commands.append(command)
        shutil.copy(command[command.index("-i") + 1], command[-1])

    def transcribe(self, wav):
        number = int(Path(wav).stem)
        if self.heard and number in self.heard:
            return self.heard[number]
        return narrate.spoken(SAYS[number - 1], CONFIG["pronunciation"]).replace("//", "").replace("...", ",")


def run(root, capsys, fakes, monkeypatch, key=KEY):
    if key is None:
        monkeypatch.delenv(narrate.KEY_VARIABLE, raising=False)
    else:
        monkeypatch.setenv(narrate.KEY_VARIABLE, key)
    code = narrate.main(
        ["example", str(NUMBER)], post=fakes.post, transcribe=fakes.transcribe, run=fakes.run, root=root
    )
    out = capsys.readouterr()
    return code, out.out, out.err


def test_each_scene_is_requested_with_the_voice_id_and_style_apart_from_the_respelled_text(
    tmp_path, capsys, monkeypatch
):
    files(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, capsys, fakes, monkeypatch)
    assert (code, err) == (0, "")
    assert fakes.keys == [KEY, KEY]
    body = fakes.bodies[0]
    assert body["model"] == "gemini-3.8-flash-tts"
    assert body["response_format"] == {"type": "audio"}
    assert body["generation_config"] == {"speech_config": [{"voice": "Puck"}]}
    content = body["input"][0]["content"][0]
    assert content["text"] == "Both tests pass. // Run pie test now."
    assert content["annotations"] == [{"type": "speech_metadata", "style": "warm and conversational"}]
    assert all("warm" not in b["input"][0]["content"][0]["text"] for b in fakes.bodies)


def test_each_scene_is_written_at_the_channel_pace_with_the_pitch_kept(tmp_path, capsys, monkeypatch):
    folder = files(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, capsys, fakes, monkeypatch)
    assert code == 0
    assert [c[0] for c in fakes.commands] == ["ffmpeg", "ffmpeg"]
    assert all(c[c.index("-af") + 1] == "atempo=0.92" for c in fakes.commands)
    assert [c[-1] for c in fakes.commands] == [str(folder / "narration" / f"0{n}.wav") for n in (1, 2)]
    assert (folder / "narration" / "01.wav").read_bytes() == WAV
    report = json.loads((folder / "narration" / "report.json").read_text())
    assert report["passed"] is True and json.loads(out) == report


@pytest.mark.parametrize(
    ("heard", "problem"),
    [
        ("Both tests pass. Slash slash. Run pie test now.", "heard 'slash'"),
        ("Both tests pass. Short pause. Run pie test now.", "heard 'pause'"),
        ("Both tests pass. <long pause> Run pie test now.", "heard markup '<long pause>'"),
        ("Warm and conversational. Both tests pass. Run pie test now.", "heard the voice style"),
        ("Both tests failed badly. Walk away.", "matched 31% of the script's words; needs 90%"),
    ],
)
def test_spoken_markup_or_a_transcript_off_the_script_is_refused(tmp_path, capsys, monkeypatch, heard, problem):
    folder = files(tmp_path)
    code, _, err = run(tmp_path, capsys, Fakes(heard={1: heard}), monkeypatch)
    assert code == 3
    assert f"refused: scene 1: {problem}" in err
    report = json.loads((folder / "narration" / "report.json").read_text())
    assert report["passed"] is False and report["scenes"][1]["problems"] == []


def test_a_transcript_with_the_real_word_matches_its_respelling(tmp_path, capsys, monkeypatch):
    files(tmp_path)
    code, out, _ = run(tmp_path, capsys, Fakes(heard={1: "Both tests pass, run pytest now!"}), monkeypatch)
    assert code == 0
    assert json.loads(out)["scenes"][0]["match"] == 1.0


def test_a_missing_key_stops_before_any_request(tmp_path, capsys, monkeypatch):
    files(tmp_path)
    fakes = Fakes()
    code, _, err = run(tmp_path, capsys, fakes, monkeypatch, key=None)
    assert code == 1
    assert "GEMINI_API_KEY is not set" in err
    assert fakes.bodies == []


@pytest.mark.parametrize(
    "answer",
    [narrate.ApiError("HTTP 429: quota exceeded"), {"steps": [{"type": "model_output", "content": []}]}],
)
def test_an_api_error_stops_with_the_error_and_never_the_key(tmp_path, capsys, monkeypatch, answer):
    folder = files(tmp_path)

    class Failing(Fakes):
        def post(self, body, key):
            super().post(body, key)
            if isinstance(answer, Exception):
                raise answer
            return answer

    fakes = Failing()
    code, out, err = run(tmp_path, capsys, fakes, monkeypatch)
    assert code == 1
    assert err.startswith("error: scene 1: Gemini") and KEY not in err + out
    assert len(fakes.bodies) == 1 and not (folder / "narration" / "01.wav").exists()


def test_a_script_without_narration_is_bad_input(tmp_path, capsys, monkeypatch):
    files(tmp_path, says=["Fine.", ""])
    code, _, err = run(tmp_path, capsys, Fakes(), monkeypatch)
    assert code == 2
    assert "scene 2: say: must be a non-empty string" in err

"""Tests for the render-video skill's scripts/render.py, through main with fake whisper, Chrome, and ffmpeg."""

import json
import re
import sys
import wave
from pathlib import Path

import pytest
from test_youtube_channel import CONFIG, workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/render-video/scripts"))
import render

NUMBER = 14
CODE = 'def test_discount():\n    with patch("discount.apply") as fake:\n        assert fake() == 90\n'
SCENES = [
    {"kind": "points", "heading": "Two tests", "visual": "Mocks replace code\nThe assert checks the fake", "say": "S"},
    {"kind": "code", "heading": "The test", "code": "demo/discount.py", "say": "S"},
]


def whisper_json(words):
    """whisper-cli -ml 1 -sow -ojf output: one segment per word, offsets in milliseconds."""
    segments = [{"offsets": {"from": 0, "to": 10}, "text": ""}]
    segments += [{"offsets": {"from": int(a * 1000), "to": int(b * 1000)}, "text": f" {w}"} for w, a, b in words]
    return {"transcription": segments}


def write_wav(path, seconds, rate=16000):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(b"\0\0" * int(seconds * rate))


def files(root, scenes=SCENES, kind="long-form", seconds=(2.0, 3.0), demo=False, demo_json=True):
    folder = workspace(root) / "videos" / str(NUMBER)
    (folder / "narration").mkdir(parents=True, exist_ok=True)
    script = {"title": "T", "type": kind, "structure": "challenge-first", "acronyms": [], "scenes": scenes}
    (folder / "script.json").write_text(json.dumps(script))
    for index, length in enumerate(seconds[: len(scenes)], 1):
        write_wav(folder / "narration" / f"{index:02d}.wav", length)
    if demo:
        (folder / "demo.mp4").write_bytes(b"vhs recording")
    if demo_json:
        (folder / "demo.json").write_text(
            json.dumps({"folder": "14-mocked-tests", "link": "https://x", "pushed": True})
        )
        code = root / ".projects" / "content" / "example-demos" / "14-mocked-tests" / "demo"
        code.mkdir(parents=True, exist_ok=True)
        (code / "discount.py").write_text(CODE)
    return folder


class Fakes:
    """whisper hearing the given words, Chrome recording each page, ffmpeg writing its output file."""

    def __init__(self, heard=None, demo_seconds=30.0):
        self.heard = heard or {}  # scene number -> [(word, start, end)]
        self.pages, self.commands, self.demo_seconds = [], [], demo_seconds

    def transcribe(self, wav):
        return whisper_json(self.heard.get(int(Path(wav).stem), []))

    def shoot(self, html, size, frames, folder):
        self.pages.append({"html": html, "size": size, "frames": frames})

    def run(self, command):
        self.commands.append(command)
        Path(command[-1]).write_bytes(b"mp4")

    def probe(self, path):
        return self.demo_seconds


@pytest.fixture
def fonts(tmp_path, monkeypatch):
    folder = tmp_path / "fonts"
    folder.mkdir()
    for name in render.FONTS.values():
        (folder / name).write_bytes(b"font bytes")
    monkeypatch.setenv(render.FONTS_VARIABLE, str(folder))
    return folder


def run(root, fakes, capsys):
    code = render.main(
        ["example", str(NUMBER)],
        transcribe=fakes.transcribe,
        shoot=fakes.shoot,
        run=fakes.run,
        probe=fakes.probe,
        root=root,
    )
    out = capsys.readouterr()
    return code, out.out, out.err


def cues(page):
    return json.loads(re.search(r"const CUES = (.*);\n", page["html"]).group(1))


def test_main_renders_each_scene_into_a_numbered_clip_and_reports_its_length(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    assert [c[-1] for c in fakes.commands] == [str(folder / "render" / "scenes" / f"{n:02d}.mp4") for n in (1, 2)]
    report = json.loads((folder / "render" / "scenes.json").read_text())
    assert report == json.loads(out)
    # Scene length is the narration plus LEAD before and TAIL after, rounded up to whole frames.
    frames = [render.frame_count(render.LEAD + s + render.TAIL) for s in (2.0, 3.0)]
    assert [s["frames"] for s in report["scenes"]] == frames == [p["frames"] for p in fakes.pages]
    assert [s["seconds"] for s in report["scenes"]] == [f / render.FPS for f in frames]
    assert report["scenes"][0] == {
        "scene": 1,
        "kind": "points",
        "source": "html",
        "file": "render/scenes/01.mp4",
        "narration": "narration/01.wav",
        "seconds": frames[0] / render.FPS,
        "frames": frames[0],
        "lead": render.LEAD,
    }
    assert (report["width"], report["height"], report["fps"]) == (1920, 1080, 30)


def test_points_appear_at_the_whisper_time_of_their_first_heard_word(tmp_path, fonts, capsys):
    files(tmp_path)
    fakes = Fakes(heard={1: [("So", 0.2, 0.4), ("mocks", 0.5, 0.9), ("then", 1.0, 1.2), ("assert", 1.4, 1.8)]})
    run(tmp_path, fakes, capsys)
    items = cues(fakes.pages[0])["items"]
    assert items == [
        {"text": "Mocks replace code", "at": round(render.LEAD + 0.5, 3)},
        {"text": "The assert checks the fake", "at": round(render.LEAD + 1.4, 3)},
    ]


def test_a_point_whose_words_are_not_heard_appears_at_its_share_of_the_narration(tmp_path, fonts, capsys):
    files(tmp_path)
    run(tmp_path, fakes := Fakes(), capsys)
    # Nothing heard: point i of n appears at i/n of the 2 s narration, after the lead.
    assert [i["at"] for i in cues(fakes.pages[0])["items"]] == [render.LEAD, round(render.LEAD + 1.0, 3)]


def test_cue_times_never_go_back_in_time():
    words = render.words_from(whisper_json([("assert", 0.2, 0.5)]))
    times = render.cue_times(["assert this", "unheard words", "assert again"], words, 3.0)
    assert times == sorted(times) and times[0] == round(render.LEAD + 0.2, 3)


def test_code_scene_focuses_the_line_whose_name_the_narration_says(tmp_path, fonts, capsys):
    files(tmp_path)
    fakes = Fakes(heard={2: [("patch", 0.5, 0.8), ("assert", 2.5, 2.9)]})
    run(tmp_path, fakes, capsys)
    scene = cues(fakes.pages[1])
    assert scene["file"] == "demo/discount.py"
    assert scene["lines"] == CODE.splitlines()
    assert scene["focus"] == [
        {"line": 1, "at": round(render.LEAD + 0.5, 3)},
        {"line": 2, "at": round(render.LEAD + 2.5, 3)},
    ]


def test_focus_holds_before_moving_again():
    lines = ["patch = 1", "assert x"]
    heard = [("patch", 0.5, 0.6), ("assert", 0.9, 1.0), ("assert", 2.0, 2.1)]
    focus = render.focus_cues(lines, render.words_from(whisper_json(heard)))
    # "assert" at 0.9 s comes within FOCUS_HOLD of the first focus, so only the one at 2.0 s moves it.
    assert focus == [{"line": 0, "at": round(render.LEAD + 0.5, 3)}, {"line": 1, "at": round(render.LEAD + 2.0, 3)}]


@pytest.mark.parametrize("kind", render.KINDS)
def test_each_scene_kind_renders_from_its_own_template_with_the_cues_inlined(tmp_path, fonts, capsys, kind):
    scene = {"kind": kind, "heading": "H", "say": "S"}
    scene |= {"code": "demo/discount.py"} if kind == "code" else {"visual": "one\ntwo"}
    files(tmp_path, scenes=[scene])
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    html = fakes.pages[0]["html"]
    assert f'data-kind="{kind}"' in html
    assert "/*{{" not in html  # every placeholder filled
    # Nothing loads from the network: no remote source, stylesheet, import, or font.
    assert not re.search(r"(src|href)=[\"']?https?:|url\(\s*['\"]?https?:|@import", html)
    assert cues(fakes.pages[0])["kind"] == kind


def test_page_embeds_the_local_fonts_and_the_channel_palette(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[:1])
    run(tmp_path, fakes := Fakes(), capsys)
    html = fakes.pages[0]["html"]
    assert "font-family: 'Space Grotesk'" in html and "font-family: 'Fira Code'" in html
    assert "data:font/ttf;base64," in html
    scene = cues(fakes.pages[0])
    assert scene["palette"]["background"] == CONFIG["palette"]["background"]
    assert scene["palette"]["accent"] == CONFIG["palette"]["suffix"]
    assert scene["brand"] == CONFIG["name"]


def test_code_text_cannot_close_the_cue_script(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[1:])
    clone = tmp_path / ".projects" / "content" / "example-demos" / "14-mocked-tests" / "demo" / "discount.py"
    clone.write_text('print("</script><script>alert(1)</script>")\n')
    run(tmp_path, fakes := Fakes(), capsys)
    assert "</script><script>alert" not in fakes.pages[0]["html"]
    assert cues(fakes.pages[0])["lines"] == ['print("</script><script>alert(1)</script>")']


def test_html_frames_are_encoded_at_thirty_fps_without_audio():
    command = render.encode_command(Path("frames"), Path("01.mp4"))
    assert command[command.index("-framerate") + 1] == "30"
    assert command[command.index("-i") + 1] == str(Path("frames") / "%05d.jpg")
    assert command[command.index("-pix_fmt") + 1] == "yuv420p"
    assert "-an" in command and command[-1] == "01.mp4"


def test_frame_plan_rounds_up_to_whole_frames_and_seeks_each_frame():
    assert render.frame_count(2.0) == 60
    assert render.frame_count(2.01) == 61
    assert render.seek_times(3) == [0.0, 1 / 30, 2 / 30]


def test_terminal_scenes_play_the_vhs_recording_in_order(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}
    folder = files(tmp_path, scenes=[terminal, SCENES[0], terminal], seconds=(2.0, 2.0, 3.0), demo=True)
    fakes = Fakes()
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert len(fakes.pages) == 1  # only the points scene is drawn in Chrome
    clips = [c for c in fakes.commands if str(folder / "demo.mp4") in c]
    first = render.frame_count(render.LEAD + 2.0 + render.TAIL) / render.FPS
    assert [float(c[c.index("-ss") + 1]) for c in clips] == [0.0, round(first, 3)]
    assert [c[-1] for c in clips] == [str(folder / "render" / "scenes" / f"{n:02d}.mp4") for n in (1, 3)]
    report = json.loads((folder / "render" / "scenes.json").read_text())
    assert [s["source"] for s in report["scenes"]] == ["demo", "html", "demo"]


def test_a_terminal_scene_past_the_recordings_end_holds_its_last_second(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}
    files(tmp_path, scenes=[terminal, terminal], seconds=(4.0, 4.0), demo=True)
    run(tmp_path, fakes := Fakes(demo_seconds=3.0), capsys)
    starts = [float(c[c.index("-ss") + 1]) for c in fakes.commands]
    assert starts == [0.0, 2.0]
    assert all("tpad=stop_mode=clone" in c[c.index("-vf") + 1] for c in fakes.commands)


def test_terminal_scenes_without_a_recording_are_drawn_from_their_visual(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q\n1 passed", "say": "S"}
    files(tmp_path, scenes=[terminal])
    run(tmp_path, fakes := Fakes(), capsys)
    assert [i["text"] for i in cues(fakes.pages[0])["items"]] == ["$ pytest -q", "1 passed"]


def test_a_short_renders_upright_and_fits_the_recording_inside(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}
    files(tmp_path, scenes=[SCENES[0], terminal], kind="short", demo=True)
    run(tmp_path, fakes := Fakes(), capsys)
    assert fakes.pages[0]["size"] == (1080, 1920)
    filters = fakes.commands[-1][fakes.commands[-1].index("-vf") + 1]
    assert "scale=1080:1920:force_original_aspect_ratio=decrease" in filters
    assert "pad=1080:1920" in filters


def test_missing_narration_is_refused_naming_narrate_video(tmp_path, fonts, capsys):
    files(tmp_path, seconds=(2.0,))
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "narration/02.wav" in err and "narrate-video" in err


def test_a_code_scene_without_the_demo_record_is_refused_naming_build_video_demo(tmp_path, fonts, capsys):
    files(tmp_path, demo_json=False)
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "demo.json" in err and "build-video-demo" in err


def test_a_script_with_an_unknown_kind_is_refused(tmp_path, fonts, capsys):
    files(tmp_path, scenes=[{"kind": "chart", "heading": "H", "visual": "V", "say": "S"}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "scene 1: kind" in err


def test_missing_fonts_stop_before_chrome_with_the_setup_hint(tmp_path, fonts, capsys):
    files(tmp_path)
    (fonts / render.FONTS["Fira Code"]).unlink()
    fakes = Fakes()
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 1 and "FiraCode.ttf" in err and "README" in err
    assert fakes.pages == []

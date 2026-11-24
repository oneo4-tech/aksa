"""Tests for the render-video skill's scripts/render.py, through main with fake whisper, Chrome, and ffmpeg."""

import base64
import itertools
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
    {"kind": "points", "heading": "Two tests", "visual": "Mocks replace code\nThe assert checks the fake",
     "say": "Two tests. Mocks replace code, and the assert checks the fake."},
    {"kind": "code", "heading": "Look closer", "code": "demo/discount.py", "say": "Look closer at the code."},
]  # fmt: skip


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


def files(root, scenes=SCENES, kind="long-form", seconds=(2.0, 3.0), demo=False, demo_json=True, clips=0):
    folder = workspace(root) / "videos" / str(NUMBER)
    (folder / "narration").mkdir(parents=True, exist_ok=True)
    script = {"title": "T", "type": kind, "structure": "challenge-first", "acronyms": [], "scenes": scenes}
    (folder / "script.json").write_text(json.dumps(script))
    for index, length in enumerate(seconds[: len(scenes)], 1):
        write_wav(folder / "narration" / f"{index:02d}.wav", length)
    if demo:
        (folder / "demo.mp4").write_bytes(b"vhs recording")
    for k in range(1, clips + 1):
        (folder / f"demo-{k}.mp4").write_bytes(b"vhs recording of one terminal scene")
    if demo_json:
        (folder / "demo.json").write_text(
            json.dumps({"folder": "14-mocked-tests", "link": "https://x", "pushed": True})
        )
        code = root / ".projects" / "content" / "example-demos" / "14-mocked-tests" / "demo"
        code.mkdir(parents=True, exist_ok=True)
        (code / "discount.py").write_text(CODE)
    return folder


class Fakes:
    """whisper hearing the given words (by default each scene's say, a word every 0.3 s), Chrome recording each page,
    ffmpeg writing its output file."""

    def __init__(self, heard=None, demo_seconds=30.0, lengths=None):
        self.heard = heard or {}  # scene number -> [(word, start, end)]
        self.pages, self.commands, self.demo_seconds = [], [], demo_seconds
        self.lengths = lengths or {}  # recording file name -> its length in seconds

    def transcribe(self, wav):
        number = int(Path(wav).stem)
        if number in self.heard:
            return whisper_json(self.heard[number])
        say = json.loads((Path(wav).parents[1] / "script.json").read_text())["scenes"][number - 1]["say"]
        return whisper_json([(w["word"], w["start"], w["end"]) for w in said(say)])

    def shoot(self, html, size, frames, folder):
        self.pages.append({"html": html, "size": size, "frames": frames})

    def run(self, command):
        self.commands.append(command)
        Path(command[-1]).write_bytes(b"mp4")

    def probe(self, path):
        return self.lengths.get(Path(path).name, self.demo_seconds)


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


def test_points_appear_at_the_whisper_time_of_their_leading_word(tmp_path, fonts, capsys):
    files(tmp_path)
    heard = [("two", 0.0, 0.1), ("tests", 0.1, 0.2), ("So", 0.2, 0.4), ("mocks", 0.5, 0.9), ("then", 1.0, 1.2),
             ("assert", 1.4, 1.8)]  # fmt: skip
    fakes = Fakes(heard={1: heard})
    run(tmp_path, fakes, capsys)
    items = cues(fakes.pages[0])["items"]
    assert items == [
        {"text": "Mocks replace code", "at": round(render.LEAD + 0.5, 3), "heard": round(render.LEAD + 0.5, 3)},
        {"text": "The assert checks the fake", "at": round(render.LEAD + 1.4, 3), "heard": round(render.LEAD + 1.4, 3)},
    ]


def test_a_point_cues_at_its_leading_word_not_an_earlier_key_word(tmp_path, fonts, capsys):
    # Content issue #38: items came in at a common key word said before their own words.
    files(tmp_path, scenes=SCENES[:1])
    heard = [("two", 0.1, 0.2), ("tests", 0.3, 0.4), ("code", 0.5, 0.6), ("mocks", 0.9, 1.0), ("assert", 1.4, 1.5)]
    run(tmp_path, fakes := Fakes(heard={1: heard}), capsys)
    assert cues(fakes.pages[0])["items"][0]["at"] == round(render.LEAD + 0.9, 3)


UNHEARD = [
    (SCENES[0], "Two tests. Mocks replace code.", "The assert checks the fake"),
    ({"kind": "title", "heading": "Your turn", "visual": "Comment below", "say": "S"}, "Comment below.", "Your turn"),
    (SCENES[1] | {"marks": [{"line": 2, "note": "n", "at": "patch"}]}, "Look closer at the code.", "patch"),
    ({"kind": "cta", "heading": "Like it", "actions": ["like", "share"], "say": "S"}, "Like it.", "share"),
    ({"kind": "repo", "heading": "The kit", "repo": "o/r", "path": "k", "files": ["AGENTS.md", "tools/run.py"],
      "say": "S"}, "The kit holds agents rules.", "tools/run.py"),
    ({"kind": "kit", "heading": "Your kit", "repo": "o/r", "path": "k", "takeaways": ["Mock less"],
      "files": [{"path": "AGENTS.md", "use": "Paste it", "at": "rules"}]}, "Your kit. Mock less.", "rules"),
]  # fmt: skip


@pytest.mark.parametrize("scene, say, item", UNHEARD)
def test_an_item_none_of_whose_words_is_heard_is_refused_naming_the_scene_item_and_fix(
    tmp_path, fonts, capsys, scene, say, item
):
    files(tmp_path, scenes=[SCENES[0], scene | {"say": say}], seconds=(2.0, 2.0))
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 2 and fakes.commands == [], err
    assert "scene 2:" in err and f'"{item}"' in err, err
    assert "reword" in err and "write-video-script" in err


def test_render_writes_an_alignment_report_of_each_elements_cue_heard_time_and_words(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}
    folder = files(tmp_path, scenes=[*SCENES, terminal], seconds=(2.0, 3.0, 2.0), clips=1)
    # "mocks" at 0.05 s: the first point is heard at 0.45 s but staggered after the heading to 0.55 s.
    heard = [("two", 0.0, 0.05), ("mocks", 0.05, 0.3), ("replace", 0.3, 0.5), ("code", 0.5, 0.7), ("and", 0.7, 0.8),
             ("the", 0.8, 0.9), ("assert", 1.4, 1.6), ("checks", 1.6, 1.8)]  # fmt: skip
    code, _, err = run(tmp_path, Fakes(heard={1: heard}, lengths={"demo-1.mp4": 1.0}), capsys)
    assert code == 0, err
    report = (folder / "render" / "alignment.md").read_text()
    scenes = re.split(r"^## ", report, flags=re.MULTILINE)[1:]
    assert [s.splitlines()[0] for s in scenes] == ['Scene 1: points "Two tests"', 'Scene 2: code "Look closer"',
                                                  'Scene 3: terminal "Run it"']  # fmt: skip
    assert "| heading | Two tests | 0.40 | 0.40 | 0.00 | two mocks replace code and the |" in scenes[0]
    assert "| point | Mocks replace code | 0.55 | 0.45 | 0.10 | replace code and the |" in scenes[0]
    assert "| point | The assert checks the fake | 1.80 | 1.80 | 0.00 | assert checks |" in scenes[0]
    assert "| frame | demo/discount.py types in | 0.40 | - | - | look closer at the |" in scenes[1]
    assert "recording" in scenes[2] and "demo-1.mp4" in scenes[2] and "|" not in scenes[2]


def test_an_element_cued_before_its_words_are_heard_is_refused_naming_the_scene_and_element(
    tmp_path, fonts, capsys, monkeypatch
):
    # A backstop: the cue rules never place an element before its words, so a fault is injected after them.
    def early(cues):
        cues["items"][1]["at"] = cues["items"][1]["heard"] - 0.5
        return cues

    monkeypatch.setattr(render, "staggered", early)
    files(tmp_path, scenes=SCENES[:1])
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 2 and fakes.commands == [], err
    assert 'scene 1: point "The assert checks the fake"' in err and "before its words" in err, err


def test_cue_times_never_go_back_in_time():
    # "checks", the second item's leading word, is said before the first item's: the second waits for "again".
    words = render.words_from(whisper_json([("checks", 0.1, 0.2), ("assert", 0.2, 0.5), ("again", 0.6, 0.8)]))
    times = [cue["at"] for cue in render.cue_times(["assert this", "checks again"], words)]
    assert times == [round(render.LEAD + 0.2, 3), round(render.LEAD + 0.6, 3)]


def test_code_scene_focuses_the_line_whose_name_the_narration_says(tmp_path, fonts, capsys):
    files(tmp_path)
    fakes = Fakes(heard={2: [("look", 0.0, 0.1), ("patch", 0.8, 1.0), ("assert", 2.5, 2.9)]})  # "patch" once typed in
    run(tmp_path, fakes, capsys)
    scene = cues(fakes.pages[1])
    assert scene["file"] == "demo/discount.py"
    assert scene["lines"] == CODE.splitlines()
    assert [{"line": c["line"], "at": c["at"]} for c in scene["focus"]] == [
        {"line": 1, "at": round(render.LEAD + 0.8, 3)},
        {"line": 2, "at": round(render.LEAD + 2.5, 3)},
    ]


def test_the_cold_opens_code_is_shown_whole_and_later_code_scenes_type_in(tmp_path, fonts, capsys):
    # Content issue #38: the cold open (scene 1, the real artifact) was half typed in its first seconds.
    files(tmp_path, scenes=[SCENES[1], SCENES[0], SCENES[1]], seconds=(3.0, 2.0, 3.0))
    run(tmp_path, fakes := Fakes(), capsys)
    assert cues(fakes.pages[0])["typing"] == 0
    assert cues(fakes.pages[2])["typing"] > 0


@pytest.mark.parametrize("kind, rows", [("long-form", 14), ("short", 10)])
def test_a_code_file_longer_than_the_view_scrolls_so_each_focused_line_stays_in_view(
    tmp_path, fonts, capsys, kind, rows
):
    # Content issue #38 scene 11: 17 lines over the style guide's 14; the bottom lines were cut off.
    fruit = "apple berry cherry damson elder figgy grape guava kiwis lemon mango melon olive peach pears plums"
    code = "\n".join([f"{name} = {i}" for i, name in enumerate(fruit.split())] + ["zebra = 16"]) + "\n"
    files(tmp_path, kind=kind)
    (tmp_path / ".projects/content/example-demos/14-mocked-tests/demo/discount.py").write_text(code)
    heard = [("look", 0.0, 0.1), ("apple", 0.3, 0.4), ("zebra", 1.6, 1.8), ("cherry", 2.9, 3.0)]
    fakes = Fakes(heard={2: heard})
    run(tmp_path, fakes, capsys)
    scene = cues(fakes.pages[1])
    assert scene["rows"] == rows
    # The view moves only when the focus would leave it, keeping a line of context round the focused line.
    assert [(c["line"], c["top"]) for c in scene["focus"]] == [(0, 0), (16, 17 - rows), (2, 1)]
    for cue in scene["focus"]:
        assert cue["top"] <= cue["line"] < cue["top"] + rows


def test_a_code_file_within_the_view_never_scrolls(tmp_path, fonts, capsys):
    files(tmp_path)
    fakes = Fakes(heard={2: [("look", 0.0, 0.1), ("patch", 0.5, 0.8), ("assert", 2.5, 2.9)]})
    run(tmp_path, fakes, capsys)
    scene = cues(fakes.pages[1])
    assert scene["rows"] == 14 and [c["top"] for c in scene["focus"]] == [0, 0]


def test_focus_holds_before_moving_again():
    lines = ["patch = 1", "assert x"]
    heard = [("patch", 0.5, 0.6), ("assert", 0.9, 1.0), ("assert", 2.0, 2.1)]
    focus = render.focus_cues(lines, render.words_from(whisper_json(heard)))
    # "assert" at 0.9 s comes within FOCUS_HOLD of the first focus, so only the one at 2.0 s moves it.
    assert [(c["line"], c["at"]) for c in focus] == [(0, round(render.LEAD + 0.5, 3)), (1, round(render.LEAD + 2.0, 3))]


def test_focus_follows_the_narration_down_the_code():
    # Content issue #38 scene 3: the focus stayed on line 1, since "percent" and "price" name it first.
    lines = [
        "def apply_discount(price: float, percent: float) -> float:",
        '    """Price after a percent discount."""',
        "    if not 0 <= percent <= 100:",
        '        raise ValueError("percent must be 0-100")',
        "    return round(price * (1 - percent / 100), 2)",
    ]
    say = (
        "First, the code these tests are meant to protect. It is a small function called apply discount. It takes"
        " a price and a percent. It refuses any percent below zero or above one hundred. Then it returns the"
        " discounted price, rounded to two decimal places. Ten percent off a hundred should give ninety. Simple"
        " enough that an assistant should test it well."
    )
    said = render.WORD.findall(say.lower())
    heard = [(w, i * 0.4, i * 0.4 + 0.3) for i, w in enumerate(said)]
    focus = render.focus_cues(lines, render.words_from(whisper_json(heard)))
    at = {w: round(render.LEAD + i * 0.4, 3) for i, w in reversed(list(enumerate(said)))}
    moves = [cue["line"] for cue in focus]
    assert (focus[0]["line"], focus[0]["at"]) == (0, at["apply"])
    assert moves in ([0, 2, 4], [0, 3, 4]), focus
    assert at["refuses"] <= focus[1]["at"] <= at["hundred"] and at["returns"] <= focus[2]["at"] <= at["rounded"]


KIND_FIELDS = {
    "title": {"visual": "one two"},
    "points": {"visual": "one\ntwo"},
    "terminal": {"visual": "$ one\ntwo"},
    "code": {"code": "demo/discount.py"},
    "split": {
        "left": {"code": "demo/discount.py", "label": "L"},
        "right": {"code": "tests/test_discount.py", "label": "R"},
    },
    "compare": {"left": {"heading": "A", "items": ["a"]}, "right": {"heading": "B", "items": ["`b`"]}},
    "kit": {
        "repo": "o/r",
        "path": "14-x/ai-kit",
        "files": [{"path": "AGENTS.md", "use": "Paste it", "at": "rules"}],
        "takeaways": ["b"],
    },
    "intro": {"roles": ["Developers", "Testers"], "activity": "Spot the bug", "stake": "They pass"},
    "cta": {"actions": ["like", "subscribe"]},
    "repo": {"repo": "o/r", "path": "14-x/ai-kit", "files": ["AGENTS.md"]},
}


def spoken(scene):
    """A narration saying every word of the scene's fields in order, so each item is heard."""
    fields = {k: v for k, v in scene.items() if k not in ("kind", "say")}
    return " ".join(render.WORD.findall(json.dumps(fields).replace("\\n", " ").lower()))


@pytest.mark.parametrize("kind", render.KINDS)
def test_each_scene_kind_renders_from_its_own_template_with_the_cues_inlined(tmp_path, fonts, capsys, kind):
    scene = {"kind": kind, "heading": "H"} | KIND_FIELDS[kind]
    scene["say"] = spoken(scene)
    split_files(tmp_path, [scene])
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


def test_without_clips_terminal_scenes_play_the_single_recording_in_order(tmp_path, fonts, capsys):
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


def test_without_clips_a_terminal_scene_past_the_recordings_end_holds_its_last_second(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}
    files(tmp_path, scenes=[terminal, terminal], seconds=(4.0, 4.0), demo=True)
    run(tmp_path, fakes := Fakes(demo_seconds=3.0), capsys)
    starts = [float(c[c.index("-ss") + 1]) for c in fakes.commands]
    assert starts == [0.0, 2.0]
    assert all("tpad=stop_mode=clone" in c[c.index("-vf") + 1] for c in fakes.commands)


TERMINAL = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q", "say": "S"}


def scene_seconds(narration):
    return render.frame_count(render.LEAD + narration + render.TAIL) / render.FPS


def test_each_terminal_scene_plays_its_own_clip_whole_and_holds_its_last_frame(tmp_path, fonts, capsys):
    # Content issue #38: one demo.mp4 cut across three terminal scenes showed the kit steps in the boundary scene.
    folder = files(tmp_path, scenes=[TERMINAL, SCENES[0], TERMINAL], seconds=(2.0, 2.0, 3.0), demo=True, clips=2)
    fakes = Fakes(lengths={"demo-1.mp4": 1.5, "demo-2.mp4": 2.0})
    assert run(tmp_path, fakes, capsys)[0] == 0
    clips = [c for c in fakes.commands if "-ss" in c]
    assert [c[c.index("-i") + 1] for c in clips] == [str(folder / "demo-1.mp4"), str(folder / "demo-2.mp4")]
    assert [float(c[c.index("-ss") + 1]) for c in clips] == [0.0, 0.0]
    for command in clips:
        filters = command[command.index("-vf") + 1]
        assert "setpts" not in filters and "tpad=stop_mode=clone" in filters
    assert [c[-1] for c in clips] == [str(folder / "render" / "scenes" / f"{n:02d}.mp4") for n in (1, 3)]


@pytest.mark.parametrize("over", [1.1 / render.FPS, 1.5, 2.0, 30.0])
def test_a_clip_longer_than_its_scene_is_refused_naming_the_scene_both_lengths_and_the_fix(
    tmp_path, fonts, capsys, over
):
    # Content issue #38: a clip longer than its scene was played at 1.5x, out of step with the narration.
    files(tmp_path, scenes=[SCENES[0], TERMINAL], seconds=(2.0, 2.0), clips=1)
    seconds = scene_seconds(2.0)
    fakes = Fakes(lengths={"demo-1.mp4": seconds + over})
    code, _, err = run(tmp_path, fakes, capsys)
    assert code == 2 and fakes.commands == []
    assert "scene 2" in err and "demo-1.mp4" in err
    assert f"{seconds + over:.2f} s" in err and f"{seconds:.2f} s" in err
    assert "demo.tape" in err and "record.py" in err and "write-video-script" in err


def test_a_clip_at_most_one_frame_longer_than_its_scene_plays_at_its_own_speed(tmp_path, fonts, capsys):
    files(tmp_path, scenes=[TERMINAL], seconds=(2.0,), clips=1)
    fakes = Fakes(lengths={"demo-1.mp4": scene_seconds(2.0) + 0.9 / render.FPS})
    assert run(tmp_path, fakes, capsys)[0] == 0
    assert "setpts" not in fakes.commands[0][fakes.commands[0].index("-vf") + 1]


def test_a_missing_clip_for_a_terminal_scene_is_refused_naming_record(tmp_path, fonts, capsys):
    files(tmp_path, scenes=[TERMINAL, TERMINAL], seconds=(2.0, 2.0), clips=1)
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 2 and "demo-2.mp4" in err and "record.py" in err and fakes.commands == []


def test_terminal_scenes_without_a_recording_are_drawn_from_their_visual(tmp_path, fonts, capsys):
    terminal = {"kind": "terminal", "heading": "Run it", "visual": "$ pytest -q\n1 passed",
                "say": "Run it with pytest, and it passed."}  # fmt: skip
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


@pytest.mark.parametrize(
    "heading, heard, at",
    [
        # Content issue #38 scene 7: "Mutation testing" was on screen before the narrator introduced the term.
        ("Testing versus checking", [("testing", 0.6, 0.9)], 0.6),
        # Never before the narration names one of its words: "there is" does not bring in "Mutation testing".
        ("Mutation testing", [("there", 0.2, 0.4), ("is", 0.5, 0.6), ("mutation", 1.3, 1.7), ("testing", 1.8, 2.1)],
         1.3),
        # Its leading word unheard: at another of its key words, a name by its first letters.
        ("Testing mutations", [("mutation", 0.9, 1.2)], 0.9),
        # Owner, #28 gate 3 (third review): "Bug one: it mocks the coupon logic" shows at "Bug".
        ("Bug one: it mocks the coupon logic", [("bug", 0.3, 0.5), ("one", 0.5, 0.7), ("mocks", 1.6, 1.9)], 0.3),
    ],
)  # fmt: skip
def test_a_heading_appears_at_the_first_heard_key_word_of_its_own_scene(heading, heard, at):
    words = render.words_from(whisper_json(heard))
    assert render.heading_time(heading, words) == round(render.LEAD + at, 3)


def test_a_heading_cues_at_its_leading_key_word_not_an_earlier_one(tmp_path, fonts, capsys):
    scene = {"kind": "title", "heading": "Mutation testing", "visual": "Break it", "say": "S"}
    files(tmp_path, scenes=[scene])
    heard = [("testing", 0.1, 0.3), ("mutation", 0.5, 0.8), ("break", 0.9, 1.0), ("it", 1.0, 1.1)]
    run(tmp_path, fakes := Fakes(heard={1: heard}), capsys)
    assert cues(fakes.pages[0])["heading"]["at"] == round(render.LEAD + 0.5, 3)


MARKS = [
    {"line": 2, "note": "patches the function under test", "at": "patch"},
    {"line": 3, "note": "checks the fake's answer", "at": "90"},
]


def test_code_marks_focus_their_line_with_a_note_at_their_cue_word_instead_of_word_focus(tmp_path, fonts, capsys):
    # Content issue #38 scenes 3 and 5: the bugs were told in text slides, not highlighted in the code.
    files(tmp_path, scenes=[SCENES[0], SCENES[1] | {"marks": MARKS}])
    # "assert" names line 3 but is no mark's cue; "ninety" is the numeral 90 in words.
    heard = [("look", 0.0, 0.1), ("patch", 0.8, 1.0), ("assert", 1.2, 1.3), ("ninety", 2.0, 2.3)]
    run(tmp_path, fakes := Fakes(heard={2: heard}), capsys)
    assert cues(fakes.pages[1])["focus"] == [
        {
            "line": 1,
            "at": round(render.LEAD + 0.8, 3),
            "note": MARKS[0]["note"],
            "top": 0,
            "heard": round(render.LEAD + 0.8, 3),
        },
        {
            "line": 2,
            "at": round(render.LEAD + 2.0, 3),
            "note": MARKS[1]["note"],
            "top": 0,
            "heard": round(render.LEAD + 2.0, 3),
        },
    ]


def test_a_mark_past_the_files_end_is_refused_naming_the_scene_and_file(tmp_path, fonts, capsys):
    files(tmp_path, scenes=[SCENES[1] | {"marks": [{"line": 9, "note": "n", "at": "patch"}]}])
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 2 and "scene 1" in err and "line 9" in err and "demo/discount.py" in err
    assert fakes.pages == []


@pytest.mark.parametrize(
    "marks, problem",
    [
        ("line 2", "marks: must be a list"),
        ([{"line": 0, "note": "n", "at": "a"}], "marks 1: line: must be a line number from 1"),
        ([{"line": 2, "note": "", "at": "a"}], "marks 1: note: must be a non-empty string"),
        ([{"line": 2, "note": "n"}], "marks 1: at: must be a non-empty string"),
    ],
)
def test_an_invalid_mark_is_refused_naming_its_field(tmp_path, fonts, capsys, marks, problem):
    files(tmp_path, scenes=[SCENES[1] | {"marks": marks}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err


def entrances(node):
    """Every entrance time in a scene's cues: the heading's and each item's, focus's, or mark's at."""
    if isinstance(node, dict):
        return ([node["at"]] if isinstance(node.get("at"), (int, float)) else []) + [
            t for value in node.values() for t in entrances(value)
        ]
    return [t for value in node for t in entrances(value)] if isinstance(node, list) else []


def test_entrances_are_staggered_so_only_one_element_starts_moving_at_a_time(tmp_path, fonts, capsys):
    scene = {"kind": "points", "heading": "Mocks", "visual": "Mocks one\nMocks two\nMocks three", "say": "S"}
    files(tmp_path, scenes=[scene], seconds=(3.0,))
    heard = [("mocks", 0.5, 0.6), ("two", 0.55, 0.6), ("three", 0.6, 0.7)]
    run(tmp_path, fakes := Fakes(heard={1: heard}), capsys)
    scene = cues(fakes.pages[0])
    times = sorted(entrances(scene))
    assert len(times) == 4 and times[0] == round(render.LEAD + 0.5, 3)  # the first still starts at its word
    assert all(b - a >= render.MOTION["stagger"] - 1e-9 for a, b in itertools.pairwise(times)), times
    assert render.MOTION["stagger"] == 0.15 and scene["motion"] == render.MOTION


TESTS = "def test_total():\n    with patch.object(checkout, 'apply'):\n        assert total() == 8991\n"
SPLIT = {
    "kind": "split",
    "heading": "Spot the bug",
    "left": {"code": "demo/discount.py", "label": "The code"},
    "right": {"code": "tests/test_discount.py", "label": "The AI's tests", "marks": [MARKS[0]]},
    "say": "Spot the bug. Here is the code, and the AI's tests. Look at the patch.",
}


def split_files(root, scenes, **kwargs):
    folder = files(root, scenes=scenes, **kwargs)
    demo = root / ".projects/content/example-demos/14-mocked-tests"
    (demo / "tests").mkdir(exist_ok=True)
    (demo / "tests" / "test_discount.py").write_text(TESTS)
    return folder


@pytest.mark.parametrize("kind, rows", [("long-form", 16), ("short", 10)])
def test_a_split_scene_shows_two_files_each_with_its_label_and_marks(tmp_path, fonts, capsys, kind, rows):
    # Owner, #28 gate 3: the hook shows the code and its tests side by side.
    split_files(tmp_path, [SPLIT, SPLIT], kind=kind, seconds=(3.0, 3.0))
    heard = [("spot", 0.0, 0.1), ("the", 0.2, 0.3), ("code", 0.4, 0.6), ("patch", 1.0, 1.2), ("tests", 2.0, 2.2)]
    run(tmp_path, fakes := Fakes(heard={1: heard, 2: heard}), capsys)
    first, later = cues(fakes.pages[0]), cues(fakes.pages[1])
    assert first["left"] | {"lines": None} == {
        "label": "The code",
        "file": "demo/discount.py",
        "lines": None,
        "typing": 0,
        "rows": rows,
        "focus": [],
    }
    assert first["left"]["lines"] == CODE.splitlines() and first["right"]["lines"] == TESTS.splitlines()
    # Marks live inside their side and focus only that side's line.
    assert first["right"]["focus"] == [
        {
            "line": 1,
            "at": round(render.LEAD + 1.0, 3),
            "note": MARKS[0]["note"],
            "top": 0,
            "heard": round(render.LEAD + 1.0, 3),
        }
    ]
    # The cold open shows both files whole from the first frame; a later split brings each panel in as the
    # narration names its label.
    assert "at" not in first["left"] and "at" not in first["right"]
    assert later["left"]["at"] == round(render.LEAD + 0.4, 3) and later["right"]["at"] == round(render.LEAD + 2.0, 3)


@pytest.mark.parametrize(
    "side, problem",
    [
        (None, "left: must be an object of code, label, and optional marks"),
        ({"code": "demo/discount.py"}, "left: label: must be a non-empty string"),
        ({"code": "demo/discount.py", "label": "L", "marks": [{"line": 2}]}, "left: marks 1: note"),
    ],
)
def test_an_invalid_split_side_is_refused_naming_its_field(tmp_path, fonts, capsys, side, problem):
    split_files(tmp_path, [SPLIT | {"left": side}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err


def test_a_split_side_mark_past_its_files_end_is_refused(tmp_path, fonts, capsys):
    right = SPLIT["right"] | {"marks": [{"line": 4, "note": "n", "at": "a"}]}
    split_files(tmp_path, [SPLIT | {"right": right}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "scene 1" in err and "line 4" in err and "tests/test_discount.py" in err


COMPARE = {
    "kind": "compare",
    "heading": "Two ways to look",
    "left": {"heading": "Checking", "items": ["Confirms what we expect", "`assert total == 8991`"]},
    "right": {"heading": "Testing", "items": ["Explores what could go wrong", "`mutate one line`"]},
    "say": "S",
}


def test_compare_columns_reveal_each_item_as_the_narration_names_it_alternating_sides(tmp_path, fonts, capsys):
    # Owner, #28 gate 3: testing versus checking compared side by side, with examples.
    files(tmp_path, scenes=[COMPARE], seconds=(4.0,))
    said = [("two", 0.0), ("checking", 0.2), ("testing", 0.6), ("confirms", 1.0), ("explores", 1.4), ("assert", 2.0),
            ("mutate", 2.6)]  # fmt: skip
    run(tmp_path, fakes := Fakes(heard={1: [(w, t, t + 0.2) for w, t in said]}), capsys)
    scene = cues(fakes.pages[0])
    at = {w: round(render.LEAD + t, 3) for w, t in said}
    assert scene["left"] == {
        "heading": {"text": "Checking", "at": at["testing"], "heard": at["checking"]},  # with the right heading
        "items": [
            {"text": "Confirms what we expect", "at": at["confirms"], "heard": at["confirms"]},
            {"text": "`assert total == 8991`", "at": at["assert"], "heard": at["assert"]},
        ],
    }
    assert scene["right"] == {
        "heading": {"text": "Testing", "at": at["testing"], "heard": at["testing"]},
        "items": [
            {"text": "Explores what could go wrong", "at": at["explores"], "heard": at["explores"]},
            {"text": "`mutate one line`", "at": at["mutate"], "heard": at["mutate"]},
        ],
    }


def test_compare_column_headings_enter_together_at_the_later_of_their_words(tmp_path, fonts, capsys):
    # Content issue #38: two headings the owner wanted together entered 0.8 s apart.
    files(tmp_path, scenes=[COMPARE], seconds=(4.0,))
    said = [("two", 0.0), ("checking", 0.2), ("confirms", 0.6), ("testing", 1.0), ("explores", 1.4), ("assert", 2.0),
            ("mutate", 2.6)]  # fmt: skip
    run(tmp_path, fakes := Fakes(heard={1: [(w, t, t + 0.2) for w, t in said]}), capsys)
    scene = cues(fakes.pages[0])
    together = round(render.LEAD + 1.0, 3)  # "testing", the later heading's word
    assert scene["left"]["heading"]["at"] == scene["right"]["heading"]["at"] == together
    # Each column's items after the headings, though "confirms" was said before "testing".
    assert all(i["at"] > together for side in render.SIDES for i in scene[side]["items"]), scene


@pytest.mark.parametrize(
    "side, problem",
    [
        ("Checking", "left: must be an object of heading and items"),
        ({"items": ["a"]}, "left: heading: must be a non-empty string"),
        ({"heading": "H", "items": []}, "left: items: must be a non-empty list of non-empty strings"),
    ],
)
def test_an_invalid_compare_column_is_refused_naming_its_field(tmp_path, fonts, capsys, side, problem):
    files(tmp_path, scenes=[COMPARE | {"left": side}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err


def said(say, step=0.3):
    """A scene's say as heard words, one every step seconds from 0."""
    return [
        {"word": w, "start": i * step, "end": i * step + step} for i, w in enumerate(render.WORD.findall(say.lower()))
    ]


AI_TEST_39 = (
    "from unittest.mock import Mock, patch\n\nfrom demo import checkout\n\nCART = [(2499, 2), (4992, 1)]\n\n\n"
    "def test_order_total_applies_coupon():\n    tax = Mock(rate=Mock(return_value=0.0))\n"
    '    with patch.object(checkout, "apply_coupon", return_value=8991):\n'
    '        total = checkout.order_total(CART, "SAVE10", tax)\n    assert total == 8991\n\n\n'
    "def test_order_total_returns_cents():\n    tax = Mock(rate=Mock(return_value=0.19))\n"
    '    total = checkout.order_total(CART, "SAVE10", tax)\n    assert isinstance(total, int)\n'
)
CODE_39 = {
    "kind": "code",
    "heading": "It fakes the coupon logic",
    "code": "tests/test_checkout_ai.py",
    "marks": [
        {"line": 10, "note": "fakes apply_coupon itself", "at": "patch"},
        {"line": 12, "note": "checks the number it wrote in", "at": "wrote"},
    ],
    "say": "Patch object swaps apply coupon, the coupon logic itself, for a mock. // Return value makes the fake answer"
    " a fixed total. // So the assert checks a number the test wrote in. It fakes the coupon logic. // Delete the"
    " real code, and it still passes.",
}


@pytest.mark.parametrize("marks", [True, False])
def test_a_typed_code_scenes_focus_never_starts_before_its_code_is_visible(marks):
    # Owner, #28 acceptance run (#39 scene 2): the first mark's band lit on an empty panel still typing.
    scene = CODE_39 if marks else {k: v for k, v in CODE_39.items() if k != "marks"}
    cues = render.scene_cues(scene, 2, said(scene["say"]), 18.0, render.SIZES["short"], CONFIG, AI_TEST_39)
    assert 0 < cues["typing"] <= 0.6  # typed in briefly, so the code is whole as the narration starts
    assert cues["focus"]
    assert all(cue["at"] >= cues["lead"] + cues["typing"] for cue in cues["focus"]), cues["focus"]


INTRO = {
    "kind": "intro",
    "heading": "Is this challenge for you?",
    "roles": ["Developers who let AI write their tests", "Testers who review AI-written code"],
    "activity": "Spot the bug in two AI-written unit tests",
    "stake": "They pass in CI, and would still pass if checkout overcharged",
    "say": "Do you let an AI assistant write your unit tests? Or do you review code it wrote? // Then this challenge"
    " is for you. // Developers who let AI write their tests. Testers who review AI-written code. // Today you spot"
    " the bug in two AI-written unit tests. // They pass in CI. And they would still pass if checkout overcharged"
    " your customers.",
}


def test_an_intro_brings_in_its_roles_activity_and_stake_as_the_narrator_names_each():
    # Owner, #28 gate 3 (third review): "Video has no introduction ... Set a proper hook on the roles involved, who
    # is this for, what is the activity involved."
    words = said(INTRO["say"])
    at = {w["word"]: round(render.LEAD + w["start"], 3) for w in reversed(words)}  # a word's first time
    cues = render.scene_cues(INTRO, 1, words, 20.0, render.SIZES["long-form"], CONFIG, None)
    assert [r["text"] for r in cues["roles"]] == INTRO["roles"]
    # Each at its leading key word, not at "let" or "review" in the opening question.
    assert [r["at"] for r in cues["roles"]] == [at["developers"], at["testers"]]
    assert cues["activity"] == {"text": INTRO["activity"], "at": at["spot"], "heard": at["spot"]}
    assert cues["stake"] == {"text": INTRO["stake"], "at": at["they"], "heard": at["they"]}
    assert cues["heading"]["at"] == at["challenge"]


def test_an_intro_item_whose_leading_word_is_unheard_falls_back_to_any_of_its_words():
    words = said("A challenge for anyone who reviews AI code. Spot it. They pass.")
    scene = INTRO | {"roles": ["Reviewers of code"]}
    cues = render.scene_cues(scene, 1, words, 5.0, render.SIZES["short"], CONFIG, None)
    assert cues["roles"][0]["at"] == round(render.LEAD + 7 * 0.3, 3)  # "code", its other key word


@pytest.mark.parametrize(
    "field, value, problem",
    [
        ("roles", [], "roles: must be a list of one to three non-empty strings"),
        ("roles", ["a", "b", "c", "d"], "roles: must be a list of one to three non-empty strings"),
        ("activity", "", "activity: must be a non-empty string"),
        ("stake", None, "stake: must be a non-empty string"),
    ],
)
def test_an_invalid_intro_field_is_refused(tmp_path, fonts, capsys, field, value, problem):
    files(tmp_path, scenes=[INTRO | {field: value}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err


REPO = {
    "kind": "repo",
    "heading": "An AI kit for this problem",
    "repo": "oneo4-tech/testlab-demos",
    "path": "38-ai-test-mutation/ai-kit",
    "files": [
        "AGENTS.md",
        "skills/check-test-can-fail/SKILL.md",
        "scripts/find_self_mocks.py",
        "scripts/mutation_smoke.py",
    ],
    "say": "I have built an AI kit for exactly this problem. // It is on my GitHub, and the link is in the"
    " description. // It holds a rules file, an agent skill, and two scripts: one finds self mocks, one runs a"
    " mutation smoke test. // Let me run the two scripts on these tests.",
}


def test_a_repo_card_enters_first_then_lists_its_files_as_named_and_wipes_in_its_link_at_link_at():
    # Owner, #28 gate 3 (third review): introduce the AI kit "as github graphic, before you talk about AI kit".
    words = said(REPO["say"])
    at = {w["word"]: round(render.LEAD + w["start"], 3) for w in reversed(words)}
    cues = render.scene_cues(REPO, 12, words, 12.0, render.SIZES["long-form"], CONFIG, None)
    assert (cues["repo"], cues["path"], cues["card"]) == (REPO["repo"], REPO["path"], {"at": render.LEAD})
    assert cues["link"] == {
        "text": "https://github.com/oneo4-tech/testlab-demos/tree/main/38-ai-test-mutation/ai-kit",
        "at": at["description"],  # link_at defaults to "description"
        "heard": at["description"],
    }
    times = [f["at"] for f in cues["files"]]
    assert [f["text"] for f in cues["files"]] == REPO["files"]
    # AGENTS.md at "agent" (a name by its first letters), the skill at "skill", the first script at "scripts", and
    # the second at "mutation", its first word the script before lacks.
    assert times == [at["agent"], at["skill"], at["scripts"], at["mutation"]]


def test_a_repo_link_whose_cue_is_unheard_follows_the_files():
    words = said("Here is the kit. Agents rules, a skill, scripts to find self mocks, and a mutation smoke script.")
    cues = render.scene_cues(REPO | {"link_at": "github"}, 2, words, 5.0, render.SIZES["short"], CONFIG, None)
    assert cues["link"]["at"] == round(cues["files"][-1]["at"] + render.MOTION["enter"], 3)


@pytest.mark.parametrize(
    "field, value, problem",
    [
        ("repo", "testlab-demos", "repo: must be owner/name"),
        ("path", "", "path: must be a non-empty string"),
        ("files", [], "files: must be a non-empty list of non-empty strings"),
        ("link_at", 2, "link_at: must be a non-empty string"),
    ],
)
def test_an_invalid_repo_field_is_refused(tmp_path, fonts, capsys, field, value, problem):
    files(tmp_path, scenes=[REPO | {field: value}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err


WORDMARK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 12"><path d="M0 6 H90" stroke="#fff"/></svg>'


def branded(root, background, image=True):
    """The fixture channel with background in channel.yaml and its wordmark in branding/."""
    folder = workspace(root, config=CONFIG | {"background": background})
    if image:
        (folder / "branding").mkdir(exist_ok=True)
        (folder / "branding" / "wordmark-example.svg").write_text(WORDMARK)


def test_every_drawn_scene_shows_the_channels_brand_image_faint_and_embedded(tmp_path, fonts, capsys):
    # Owner, #28 gate 3 (third review): "Have the background of slides same color but test lab image with higher
    # opacity."
    files(
        tmp_path,
        scenes=[*SCENES, {"kind": "terminal", "heading": "Run it", "visual": "$ pytest", "say": "Run it: pytest."}],
        seconds=(2.0, 3.0, 2.0),
    )
    branded(tmp_path, {"image": "branding/wordmark-example.svg", "opacity": 0.1})
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 0 and len(fakes.pages) == 3, err
    data = "data:image/svg+xml;base64," + base64.b64encode(WORDMARK.encode()).decode()
    for page in fakes.pages:
        assert cues(page)["backdrop"] == {"image": data, "opacity": 0.1, "fit": "contain"}
        assert cues(page)["palette"]["background"] == CONFIG["palette"]["background"]  # the colour is unchanged


def test_without_a_background_no_brand_image_is_drawn(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[:1])
    run(tmp_path, fakes := Fakes(), capsys)
    assert "backdrop" not in cues(fakes.pages[0])


@pytest.mark.parametrize(
    "background, problem",
    [
        ({"image": "branding/wordmark-example.svg", "opacity": 0.9}, "background.opacity: must be a number above 0"),
        ({"image": "branding/wordmark-example.svg", "opacity": True}, "background.opacity: must be a number above 0"),
        ({"image": "", "opacity": 0.1}, "background.image: must be an image"),
        ({"image": "../x.svg", "opacity": 0.1}, "background.image: must be an image"),
        ({"image": "branding/wordmark.gif", "opacity": 0.1}, "background.image: must be an image"),
        ("wordmark", "background: must be a mapping of image, opacity"),
    ],
)  # fmt: skip
def test_an_invalid_background_is_refused_before_rendering(tmp_path, fonts, capsys, background, problem):
    files(tmp_path, scenes=SCENES[:1])
    branded(tmp_path, background)
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 2 and problem in err and fakes.pages == []


def test_a_missing_brand_image_is_refused_naming_brand_channel(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[:1])
    branded(tmp_path, {"image": "branding/wordmark-example.svg", "opacity": 0.1}, image=False)
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "wordmark-example.svg" in err and "brand-channel" in err


def luminance(colour):
    """WCAG relative luminance of an sRGB colour given as three 0-1 channel values."""
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in colour]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def rgb(hex_colour):
    return [int(hex_colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def contrast(a, b):
    light, dark = sorted([luminance(a), luminance(b)], reverse=True)
    return (light + 0.05) / (dark + 0.05)


PHOTO = CONFIG | {"palette": CONFIG["palette"] | {"background": "#0F0F0F", "name": "#F2EFE6", "suffix": "#00E5FF"}}


@pytest.mark.parametrize("opacity", [0.05, 0.15, 0.3, 0.35])
def test_a_cover_backdrop_gets_a_scrim_keeping_text_and_accent_at_four_and_a_half_to_one_over_white(tmp_path, opacity):
    # Owner, #28 gate 3 (fourth review): "Background image is not about oneo4 test lab, rather a test lab image".
    (tmp_path / "branding").mkdir()
    (tmp_path / "branding" / "backdrop.jpg").write_bytes(b"jpeg bytes")
    config = PHOTO | {"background": {"image": "branding/backdrop.jpg", "opacity": opacity, "fit": "cover"}}
    shown = render.backdrop(config, tmp_path)["backdrop"]
    assert shown["image"] == "data:image/jpeg;base64," + base64.b64encode(b"jpeg bytes").decode()
    assert (shown["opacity"], shown["fit"]) == (opacity, "cover")
    # The image's brightest pixel, white, at its opacity over the palette background, under the scrim's lightest
    # (middle) stop of the palette background: warm white text and the cyan accent keep 4.5:1.
    scrim, background = shown["scrim"]["middle"], rgb(PHOTO["palette"]["background"])
    pixel = [b + (1 - scrim) * opacity * (1 - b) for b in background]
    for text in (PHOTO["palette"]["name"], PHOTO["palette"]["suffix"]):
        assert contrast(rgb(text), pixel) >= 4.5, (text, scrim)
    assert 0 <= scrim <= shown["scrim"]["edge"] <= 1
    lighter = [b + (1 - (scrim - 0.01)) * opacity * (1 - b) for b in background]
    assert scrim == 0 or contrast(rgb(PHOTO["palette"]["suffix"]), lighter) < 4.5  # no darker than it needs


def test_a_backdrop_without_fit_is_contained_and_unscrimmed(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[:1])
    branded(tmp_path, {"image": "branding/wordmark-example.svg", "opacity": 0.1})
    run(tmp_path, fakes := Fakes(), capsys)
    shown = cues(fakes.pages[0])["backdrop"]
    assert shown["fit"] == "contain" and "scrim" not in shown


def test_a_cover_backdrop_reaches_every_drawn_scene(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES, seconds=(2.0, 3.0))
    branded(tmp_path, {"image": "branding/wordmark-example.svg", "opacity": 0.1, "fit": "cover"})
    code, _, err = run(tmp_path, fakes := Fakes(), capsys)
    assert code == 0, err
    assert [cues(page)["backdrop"]["fit"] for page in fakes.pages] == ["cover", "cover"]


CODES = {"demo/discount.py": CODE, "tests/test_discount.py": TESTS}


@pytest.mark.parametrize("position", [1, 2])
@pytest.mark.parametrize("kind", render.KINDS)
def test_a_drawn_scene_whose_words_come_late_shows_only_its_frame_or_is_refused(kind, position):
    # Owner, #28 gate 3 (fourth review): "Avoid displaying blank slide or screen at any time for more than a second";
    # #81: never by showing the heading before its words. Code typing in, a card, or a cold open's split fills it.
    scene = {"kind": kind, "heading": "Heading words", "say": "S"} | KIND_FIELDS[kind]
    late = spoken(scene).split()
    heard = [{"word": w, "start": 6 + i * 0.2, "end": 6.2 + i * 0.2} for i, w in enumerate(late)]
    filler = {"kind": "title", "heading": "One", "visual": "one", "say": "S"}
    script = {"type": "long-form", "scenes": [filler, scene][2 - position :]}
    one = [{"word": "one", "start": 0.1, "end": 0.3}]
    heard = [one] * (position - 1) + [heard]
    if kind in ("code", "kit", "repo") or kind == "split" and position == 1:
        plan = render.plan(script, [12.0] * position, heard, CONFIG, CODES, None)
        assert plan[-1]["cues"]["heading"]["at"] >= render.LEAD + 6  # at its words, not pulled early
    else:
        with pytest.raises(render.BadInput, match=f"scene {position}: nothing shows"):
            render.plan(script, [12.0] * position, heard, CONFIG, CODES, None)


def test_a_drawn_scene_with_nothing_in_its_first_second_is_refused_naming_the_fix(tmp_path, fonts, capsys):
    files(tmp_path, scenes=SCENES[:1])
    heard = [(w["word"], w["start"] + 2.0, w["end"] + 2.0) for w in said(SCENES[0]["say"])]
    code, _, err = run(tmp_path, fakes := Fakes(heard={1: heard}), capsys)
    assert code == 2 and "scene 1:" in err and "1 s" in err and fakes.pages == [], err
    assert "open the narration on the heading's words" in err and "filler or transition title scene" in err


KIT = {
    "kind": "kit",
    "heading": "Take it to your agent",
    "repo": "oneo4-tech/testlab-demos",
    "path": "38-ai-test-mutation/ai-kit",
    "files": [
        {"path": "AGENTS.md", "use": "Paste into your AGENTS.md or CLAUDE.md", "at": "rules"},
        {"path": "skills/check-test-can-fail/SKILL.md", "use": "Your agent runs it after writing tests", "at": "skill"},
        {"path": "scripts/find_self_mocks.py", "use": "Run it on any test file", "at": "first"},
    ],
    "link_at": "description",
    "takeaways": ["Mock collaborators, never the code under test", "Break the code before you trust a test"],
    "takeaways_at": "takeaways",
    "say": "Take it to your agent. Here is how to use each part. // Paste the rules file into your agents file. //"
    " The skill goes in your skills folder. // The first script flags tests that fake the code they test. // The"
    " link is in the description. // The takeaways. Mock collaborators, never the code under test. // And break"
    " the code before you trust a test.",
}


def kit_cues(scene, kind="long-form"):
    words = said(scene["say"])
    at = {w["word"]: round(render.LEAD + w["start"], 3) for w in reversed(words)}  # a word's first time
    return render.scene_cues(scene, 14, words, 20.0, render.SIZES[kind], CONFIG, None), at


def test_a_kit_lights_each_file_with_its_use_then_wipes_in_its_link_and_shows_the_takeaways_last():
    # Owner, #28 gate 3 (fourth review): "produce the same github animation & do not repeat the same information,
    # just explain each of the content & how audience can use it".
    cues, at = kit_cues(KIT)
    assert (cues["repo"], cues["path"], cues["card"]) == (KIT["repo"], KIT["path"], {"at": render.LEAD})
    assert cues["files"] == [
        {"text": f["path"], "use": f["use"], "at": at[w], "heard": at[w]}
        for f, w in zip(KIT["files"], ["rules", "skill", "first"])
    ]
    assert cues["link"] == {
        "text": "https://github.com/oneo4-tech/testlab-demos/tree/main/38-ai-test-mutation/ai-kit",
        "at": at["description"],
        "heard": at["description"],
    }
    assert [t["at"] for t in cues["takeaways"]] == [at["takeaways"], at["break"]]
    assert [t["text"] for t in cues["takeaways"]] == KIT["takeaways"]
    assert "snippet" not in cues  # no AGENTS.md snippet panel


def test_a_kit_whose_link_cue_is_unheard_shows_it_after_the_files_and_ends_on_the_takeaways():
    scene = {k: v for k, v in (KIT | {"link_at": "github"}).items() if k != "takeaways_at"}
    cues, _ = kit_cues(scene)
    files_at = [f["at"] for f in cues["files"]]
    link = cues["link"]["at"]
    assert link == round(files_at[-1] + render.MOTION["enter"], 3)  # after the files
    # Without takeaways_at, the first takeaway waits for its leading word, "mock", heard after the link, not
    # "code" or "test" said after the link in the script's sentence.
    first = min(render.LEAD + w["start"] for w in said(scene["say"]) if w["word"] == "mock")
    assert link < first and cues["takeaways"][0]["at"] == round(first, 3)


@pytest.mark.parametrize(
    "field, value, problem",
    [
        ("repo", "testlab-demos", "repo: must be owner/name"),
        ("path", "", "path: must be a non-empty string"),
        ("files", [], "files: must be a non-empty list of path, use, and optional at"),
        ("files", ["AGENTS.md"], "files 1: must be an object of path, use, and optional at"),
        ("files", [{"path": "AGENTS.md", "use": ""}], "files 1: use: must be a non-empty string"),
        ("files", [{"path": " ", "use": "u"}], "files 1: path: must be a non-empty string"),
        ("files", [{"path": "a", "use": "u", "at": 3}], "files 1: at: must be a non-empty string"),
        ("link_at", 3, "link_at: must be a non-empty string"),
        ("takeaways_at", None, "takeaways_at: must be a non-empty string"),
        ("takeaways", [], "takeaways: must be a non-empty list of non-empty strings"),
    ],
)
def test_an_invalid_kit_field_is_refused(tmp_path, fonts, capsys, field, value, problem):
    files(tmp_path, scenes=[KIT | {field: value}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and f"scene 1: {problem}" in err, err


CTA = {
    "kind": "cta",
    "heading": "Help other testers find this",
    "actions": ["like", "share", "subscribe", "notify"],
    "say": "If this challenge helped, help other testers find it. // A like tells YouTube it is worth showing. //"
    " Share it with the developer who writes tests with AI. // Subscribe, and turn on the bell for notifications,"
    " so you catch the next challenge.",
}


def test_a_cta_brings_in_each_action_as_the_narration_names_it():
    # Owner, #28 gate 3 (fourth review): "Somewhere before the end - show graphics to like, share, subscribe,
    # notification".
    words = said(CTA["say"])
    at = {w["word"]: round(render.LEAD + w["start"], 3) for w in reversed(words)}
    cues = render.scene_cues(CTA, 15, words, 14.0, render.SIZES["long-form"], CONFIG, None)
    assert cues["actions"] == [
        {"name": "like", "at": at["like"], "heard": at["like"]},
        {"name": "share", "at": at["share"], "heard": at["share"]},
        {"name": "subscribe", "at": at["subscribe"], "heard": at["subscribe"]},
        {"name": "notify", "at": at["bell"], "heard": at["bell"]},  # "bell" comes before "notifications"
    ]


@pytest.mark.parametrize(
    "value",
    [[], "like", ["like", "clap"], ["like", "like"], [3]],
)
def test_an_invalid_cta_action_list_is_refused(tmp_path, fonts, capsys, value):
    files(tmp_path, scenes=[CTA | {"actions": value}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    problem = "actions: must be a list of like, share, subscribe, or notify, each once"
    assert code == 2 and f"scene 1: {problem}" in err, err


HOOK = SPLIT | {
    "heading": "Spot the bug",
    "hook": "This test has never failed",
    "say": "This test has never failed. // Not once. And that is the problem. // Here is the code, and the AI's"
    " tests. Can you spot the bug? Look at the patch.",
}


@pytest.mark.parametrize("index", [1, 2])
def test_a_split_hook_shows_from_the_first_frame_until_the_first_sentence_ends_then_the_split_comes_forward(index):
    # Owner, #28 gate 3 (fourth review): the Short "abruptly starts, provide curiosity & generate interest in first 3
    # seconds".
    words = said(HOOK["say"])
    code = {"left": CODE, "right": TESTS}
    cues = render.scene_cues(HOOK, index, words, 8.0, render.SIZES["short"], CONFIG, code)
    until = round(render.LEAD + words[4]["end"], 3)  # "failed", the first sentence's last word
    assert cues["hook"] == {"text": HOOK["hook"], "at": 0.0, "until": until}
    # Nothing else comes in under the hook: the heading, the panels, and their marks wait for it to leave.
    later = [cues["heading"]["at"], *[c["at"] for side in render.SIDES for c in cues[side]["focus"]]]
    later += [cues[side]["at"] for side in render.SIDES if "at" in cues[side]]
    assert all(t >= until for t in later), cues


def test_a_split_hook_over_a_long_first_sentence_leaves_by_three_seconds():
    scene = HOOK | {"say": "This test has never failed in a year of nightly builds on every branch we ship. // Why?"
                    " // Spot the bug in the patch."}  # fmt: skip
    cues = render.scene_cues(
        scene, 1, said(scene["say"]), 8.0, render.SIZES["short"], CONFIG, {"left": CODE, "right": TESTS}
    )
    assert cues["hook"]["until"] == render.HOOK_MAX == 3.0


def test_a_split_without_a_hook_has_none():
    words = said(SPLIT["say"])
    cues = render.scene_cues(SPLIT, 1, words, 4.0, render.SIZES["short"], CONFIG, {"left": CODE, "right": TESTS})
    assert "hook" not in cues


@pytest.mark.parametrize("hook", ["Look", "one two three four five six seven eight nine", "", 3])
def test_a_split_hook_of_other_than_two_to_eight_words_is_refused(tmp_path, fonts, capsys, hook):
    split_files(tmp_path, [HOOK | {"hook": hook}])
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "scene 1: hook: must be 2 to 8 words" in err, err

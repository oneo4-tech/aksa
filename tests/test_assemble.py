"""Tests for the render-video skill's scripts/assemble.py, through main with fake whisper, Chrome, and ffmpeg."""

import json
import re
import sys
from pathlib import Path

import pytest
from test_render import NUMBER, whisper_json, write_wav
from test_youtube_channel import workspace

# A script serving one skill stays in the skill (components.md), outside the pytest pythonpath.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agentic/skills/content/render-video/scripts"))
import assemble

SAYS = ["Mocks replace code. // The assert checks the fake... not the discount.", "Run it and watch it pass."]
FIRST_PASS = {
    "input_i": "-21.40",
    "input_tp": "-6.20",
    "input_lra": "3.10",
    "input_thresh": "-31.90",
    "output_i": "-14.02",
    "output_tp": "-1.00",
    "output_lra": "2.90",
    "output_thresh": "-24.50",
    "normalization_type": "linear",
    "target_offset": "0.10",
}


def files(root, kind="long-form", says=SAYS, seconds=(2.0, 1.5), frames=(90, 75), music=True, scenes=True):
    """A rendered video: script, narration, scene clips with render/scenes.json, and the channel's music bed."""
    space = workspace(root)
    folder = space / "videos" / str(NUMBER)
    (folder / "narration").mkdir(parents=True, exist_ok=True)
    (folder / "render" / "scenes").mkdir(parents=True, exist_ok=True)
    script = {"title": "T", "type": kind, "structure": "challenge-first", "acronyms": []}
    script["scenes"] = [{"kind": "points", "heading": "H", "visual": "V", "say": say} for say in says]
    (folder / "script.json").write_text(json.dumps(script))
    report = []
    for index, (length, count) in enumerate(zip(seconds, frames), 1):
        write_wav(folder / "narration" / f"{index:02d}.wav", length)
        (folder / "render" / "scenes" / f"{index:02d}.mp4").write_bytes(b"mp4")
        report.append(
            {
                "scene": index,
                "kind": "points",
                "source": "html",
                "file": f"render/scenes/{index:02d}.mp4",
                "narration": f"narration/{index:02d}.wav",
                "seconds": count / 30,
                "frames": count,
                "lead": 0.4,
            }
        )
    if scenes:
        width, height = (1920, 1080) if kind == "long-form" else (1080, 1920)
        body = {"type": kind, "width": width, "height": height, "fps": 30, "scenes": report}
        (folder / "render" / "scenes.json").write_text(json.dumps(body))
    if music:
        (space / "music").mkdir(exist_ok=True)
        (space / "music" / "bed.mp3").write_bytes(b"mp3")
    return folder


class Fakes:
    """whisper hearing the given words, Chrome recording each caption page, ffmpeg answering each command."""

    def __init__(self, heard=None, first_pass=FIRST_PASS):
        self.heard = heard or {}  # scene number -> [(word, start, end)]
        self.first_pass, self.pages, self.commands, self.lists = first_pass, [], [], {}

    def transcribe(self, wav):
        return whisper_json(self.heard.get(int(Path(wav).stem), []))

    def snap(self, html, size, count, folder):
        self.pages.append({"html": html, "size": size, "count": count})

    def run(self, command):
        self.commands.append(command)
        for index, arg in enumerate(command):  # concat lists live in a scratch folder: read them now
            if arg == "-i" and command[index + 1].endswith(".txt"):
                self.lists[Path(command[index + 1]).name] = Path(command[index + 1]).read_text()
        if command[-1] == "-":
            return "[Parsed_loudnorm_0 @ 0x1] \n" + json.dumps(self.first_pass, indent=1) + "\n"
        Path(command[-1]).write_bytes(b"out")
        return ""


def run(root, fakes, capsys):
    code = assemble.main(
        ["example", str(NUMBER)], transcribe=fakes.transcribe, snap=fakes.snap, run=fakes.run, root=root
    )
    out = capsys.readouterr()
    return code, out.out, out.err


@pytest.fixture
def fonts(tmp_path, monkeypatch):
    folder = tmp_path / "fonts"
    folder.mkdir()
    for name in assemble.render.FONTS.values():
        (folder / name).write_bytes(b"font bytes")
    monkeypatch.setenv(assemble.render.FONTS_VARIABLE, str(folder))
    return folder


def by_output(fakes, name):
    return next(c for c in fakes.commands if Path(c[-1]).name == name)


def filters(command):
    return command[command.index("-filter_complex") + 1]


def cues(text):
    """(start, end, text) per SRT cue, times in seconds."""

    def seconds(stamp):
        h, m, s = stamp.replace(",", ".").split(":")
        return round(int(h) * 3600 + int(m) * 60 + float(s), 3)

    blocks = [block.splitlines() for block in text.strip().split("\n\n")]
    return [(seconds(b[1].split(" --> ")[0]), seconds(b[1].split(" --> ")[1]), " ".join(b[2:])) for b in blocks]


def states(page):
    return json.loads(re.search(r"const CUES = (.*);\n", page["html"]).group(1))["states"]


def test_scenes_play_in_order_with_each_narration_placed_at_its_lead(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    scenes = folder / "render" / "scenes"
    assert (
        fakes.lists["scenes.txt"] == f"ffconcat version 1.0\nfile '{scenes / '01.mp4'}'\nfile '{scenes / '02.mp4'}'\n"
    )
    mix = by_output(fakes, "mix.wav")
    assert mix[mix.index("-i") + 1] == str(folder / "narration" / "01.wav")
    # Scene 2 starts after scene 1's 90 frames (3 s); each narration starts LEAD 0.4 s into its scene.
    assert re.findall(r"adelay=(\d+):all=1", filters(mix)) == ["400", "3400"]
    assert "apad=whole_dur=5.500" in filters(mix)
    report = json.loads(out)
    assert (report["width"], report["height"], report["seconds"]) == (1920, 1080, 5.5)
    assert report["file"] == "render/final.mp4"


def test_music_bed_loops_under_the_voice_at_the_channels_level(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    fakes = Fakes()
    run(tmp_path, fakes, capsys)
    mix = by_output(fakes, "mix.wav")
    music = mix.index(str(folder.parents[1] / "music" / "bed.mp3"))
    assert mix[music - 3 : music] == ["-stream_loop", "-1", "-i"]
    bed = filters(mix).split(";")[-2]
    assert bed.startswith("[2:a]") and "volume=-24dB" in bed and "atrim=0:5.500" in bed  # CONFIG music_db -24
    assert "amix=inputs=2:duration=shortest:normalize=0" in filters(mix).split(";")[-1]


def test_second_pass_normalises_linearly_from_the_first_pass_measurements_below_the_peak_limit(tmp_path, fonts, capsys):
    """Both passes aim AAC_HEADROOM (0.5 dB) under CONFIG true_peak -1, since AAC encoding lifts peaks."""
    files(tmp_path)
    fakes = Fakes()
    _, out, _ = run(tmp_path, fakes, capsys)
    first = next(c for c in fakes.commands if c[-1] == "-")
    assert first[first.index("-af") + 1] == "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json"
    final = by_output(fakes, "final.mp4")
    assert (
        "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-21.4:measured_TP=-6.2:measured_LRA=3.1:"
        "measured_thresh=-31.9:offset=0.1:linear=true" in filters(final)
    )
    assert final[final.index("-ar") + 1] == "48000"
    assert json.loads(out)["measured"] == {"lufs": -21.4, "true_peak": -6.2}


def test_a_silent_mix_is_refused_naming_the_narration(tmp_path, fonts, capsys):
    files(tmp_path)
    code, _, err = run(tmp_path, Fakes(first_pass=FIRST_PASS | {"input_i": "-inf"}), capsys)
    assert code == 2 and "silent" in err and "narrate-video" in err


def test_long_form_srt_shows_the_scripts_words_without_pause_marks(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    fakes = Fakes()
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    srt = (folder / "render" / "final.srt").read_text()
    assert " ".join(text for _, _, text in cues(srt)) == (
        "Mocks replace code. The assert checks the fake not the discount. Run it and watch it pass."
    )
    assert json.loads(out)["captions"] == "render/final.srt"
    assert fakes.pages == [] and "overlay" not in filters(by_output(fakes, "final.mp4"))


def test_srt_cues_start_at_the_heard_word_in_the_videos_time(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    heard = {
        1: [("mocks", 0.1, 0.4), ("replace", 0.4, 0.8), ("code", 0.8, 1.0), ("the", 1.3, 1.4)],
        2: [("run", 0.2, 0.4), ("it", 0.4, 0.5)],
    }
    run(tmp_path, Fakes(heard=heard), capsys)
    found = cues((folder / "render" / "final.srt").read_text())
    # A cue ends a sentence; scene 1's voice starts at 0.4 s, scene 2's at 3.4 s.
    assert found[0] == (0.5, 1.7, "Mocks replace code.")
    assert found[1][0] == 1.7
    assert found[-1] == (3.6, 4.9, "Run it and watch it pass.")


def test_words_not_heard_take_their_share_of_the_time_between_heard_words():
    starts = assemble.word_starts(["one", "two", "three", "four"], [{"word": "one", "start": 0.0, "end": 0.2}], 2.0)
    assert starts == [0.0, 0.5, 1.0, 1.5]
    # Words after the last heard one share the time to the narration's end.
    heard = [{"word": "one", "start": 0.5, "end": 0.7}]
    assert assemble.word_starts(["one", "two", "three"], heard, 2.0) == [0.5, 1.0, 1.5]


def test_short_captions_show_three_words_with_the_current_word_highlighted(tmp_path, fonts, capsys):
    folder = files(tmp_path, kind="short", says=["One two three four.", "Five six seven."])
    heard = {1: [("one", 0.0, 0.2), ("two", 0.2, 0.4), ("three", 0.4, 0.6), ("four", 0.6, 0.8)], 2: []}
    fakes = Fakes(heard=heard)
    code, out, _ = run(tmp_path, fakes, capsys)
    assert code == 0
    [page] = fakes.pages
    assert page["size"] == (1080, 1920)
    found = states(page)
    assert found[0] == {"words": [], "current": -1}  # blank between narrations
    assert found[1:] == [
        {"words": ["One", "two", "three"], "current": 0},
        {"words": ["One", "two", "three"], "current": 1},
        {"words": ["One", "two", "three"], "current": 2},
        {"words": ["four."], "current": 0},
        {"words": ["Five", "six", "seven."], "current": 0},
        {"words": ["Five", "six", "seven."], "current": 1},
        {"words": ["Five", "six", "seven."], "current": 2},
    ]
    assert page["count"] == len(found)
    # Each state shows from its word's start (frames at 30 fps) to the next word's, blank outside the narration.
    shown = re.findall(r"file '(\d+)\.png'\nduration ([\d.]+)", fakes.lists["captions.txt"])
    frames = [(int(state), round(float(seconds) * 30)) for state, seconds in shown]
    assert frames == [(0, 12), (1, 6), (2, 6), (3, 6), (4, 42), (0, 30), (5, 15), (6, 15), (7, 15), (0, 18)]
    assert sum(f for _, f in frames) == 165
    final = by_output(fakes, "final.mp4")
    assert "overlay=0:0" in filters(final) and "libx264" in final
    assert not (folder / "render" / "final.srt").exists() and json.loads(out)["captions"] == "burned"


def test_long_form_keeps_the_scene_clips_without_re_encoding(tmp_path, fonts, capsys):
    files(tmp_path)
    fakes = Fakes()
    run(tmp_path, fakes, capsys)
    final = by_output(fakes, "final.mp4")
    assert final[final.index("-c:v") + 1] == "copy"
    assert final[final.index("-t") + 1] == "5.500"


def test_missing_scene_report_is_refused_naming_render(tmp_path, fonts, capsys):
    files(tmp_path, scenes=False)
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "scenes.json" in err and "render.py" in err


def test_missing_music_bed_is_refused_naming_where_it_goes(tmp_path, fonts, capsys):
    files(tmp_path, music=False)
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "music/bed.mp3" in err


def test_a_scene_report_not_matching_the_script_is_refused(tmp_path, fonts, capsys):
    folder = files(tmp_path)
    script = json.loads((folder / "script.json").read_text())
    script["scenes"].append(script["scenes"][0])
    (folder / "script.json").write_text(json.dumps(script))
    code, _, err = run(tmp_path, Fakes(), capsys)
    assert code == 2 and "render.py" in err

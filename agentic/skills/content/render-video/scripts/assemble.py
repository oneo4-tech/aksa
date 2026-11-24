"""Assemble a video's rendered scenes and narration into the final video: music, loudness, captions.

Usage: uv run agentic/skills/content/render-video/scripts/assemble.py CHANNEL N

Reads, in the channel workspace:

  videos/<N>/script.json        from write-video-script: type and each scene's say
  videos/<N>/render/scenes.json from render.py: per scene its clip, narration, seconds,
                                frames, and lead (where its narration starts in the clip)
  videos/<N>/narration/NN.wav   from narrate-video
  music/bed.mp3                 the channel's music bed (MUSIC), supplied by the owner
                                (style guide Audio; the Lyria ambient bed, decision 39)

and channel.yaml loudness (lufs, true_peak) and music_db. It writes render/final.mp4 (H.264,
AAC 48 kHz) and, for a long-form, render/final.srt, and prints a report: type, width,
height, seconds, file, captions (the SRT file, or burned), measured (lufs and true_peak of
the written final.mp4, from one more loudnorm pass over it), and mix_before (the mix's
loudness before normalising). The report only states the loudness; it never refuses a miss.

Sound: the scene clips play in order; each narration starts at its scene's start plus its
lead. The music bed loops under the voice at music_db dB, fading out over the last
MUSIC_FADE seconds. Loudness is two-pass EBU R128 (ffmpeg loudnorm): the first pass
measures the mix, the second applies the measured values with linear=true, so the whole
mix gets one gain to lufs (a single pass missed the target by about 1.5 LU in the
prototype), with true peaks AAC_HEADROOM dB below true_peak, since AAC encoding lifts
them a little.

Captions show the script's words, never the transcript's: say with its // pauses and ...
hesitations removed, so captions show real words (the pronunciation respelling is only in
the narration). whisper-cli word timestamps (as render.py) time them: each script word
matched to a heard word starts there, the others share the time between matched words.
Both sides are compared as narrate-video's leak check compares them (narrate.py spoken_split
and comparable), so a script's "fourteen" or "minus one" matches whisper's "14" or "-1".
A long-form gets an SRT file, a cue per sentence of at most CUE_WORDS words and CUE_CHARS
characters. A Short gets burned word-highlight captions: groups of GROUP words in the
lower area clear of the Shorts buttons, the word being said in the accent colour, drawn
from references/captions.html in Chrome (one transparent PNG per state, as render.py
draws scenes: local fonts, software raster, so two runs give identical frames) and
overlaid by ffmpeg.

Needs Google Chrome (Shorts), ffmpeg, whisper-cli with its model, and the fonts (README, Setup).

Exit codes: 0 assembled, 1 a tool or file error, 2 bad input (an invalid script or channel,
a missing or stale scene report, narration, or music bed, or a silent mix).
"""

import argparse
import difflib
import itertools
import json
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import render
from render import FPS, SIZES, BadInput, ToolError, youtube_channel

# Script and heard words are compared as the leak check compares them: through narrate.py.
sys.path.insert(0, str(render.REPO_ROOT / "agentic" / "skills" / "content" / "narrate-video" / "scripts"))
import narrate

MUSIC = Path("music") / "bed.mp3"
MUSIC_FADE = 2.0  # seconds the bed fades out at the end
LRA = 11  # loudnorm loudness range target, as the prototype
# The AAC encoder lifts true peaks (0.1 dB in the media test, 0.52 dB on #38's long-form, 1.01 dB on #39's Short);
# loudnorm aims this far below true_peak so the final file still meets it.
AAC_HEADROOM = 1.5
AUDIO_RATE = 48000
AUDIO_BITRATE = "192k"
CUE_WORDS = 7
CUE_CHARS = 42
GROUP = 3
PAUSES = re.compile(r"//|\.\.\.|…")
SENTENCE_END = (".", "?", "!")
PLACEHOLDERS = ["/*{{fonts}}*/", "/*{{cues}}*/"]


def caption_words(say: str) -> list[str]:
    """The words a caption shows for say: the script's own, pauses and hesitations removed."""
    return PAUSES.sub(" ", say).split()


def _keys(pieces: list[str]) -> list[tuple[str, int]]:
    """Comparable words of pieces (narrate.py), each with the index of the piece it came from."""
    tokens = [(token, index) for index, piece in enumerate(pieces) for token in narrate.spoken_split(piece)]
    keys = narrate.comparable([token for token, _ in tokens])
    return [(key, index) for key, (_, index) in zip(keys, tokens) if key]


def word_starts(words: list[str], heard: list[dict], narration: float) -> list[float]:
    """Each script word's start, seconds into its narration: its heard word's, else its share between them."""
    said, spoken = _keys(words), _keys([h["word"] for h in heard])
    matcher = difflib.SequenceMatcher(None, [k for k, _ in said], [k for k, _ in spoken], autojunk=False)
    starts: list[float | None] = [None] * len(words)
    for block in matcher.get_matching_blocks():
        for k in range(block.size):
            word = said[block.a + k][1]
            if starts[word] is None:
                starts[word] = heard[spoken[block.b + k][1]]["start"]
    if words and starts[0] is None:
        starts[0] = 0.0
    known = [(i, s) for i, s in enumerate(starts) if s is not None] + [(len(words), narration)]
    for (i0, t0), (i1, t1) in itertools.pairwise(known):
        for i in range(i0 + 1, i1):
            starts[i] = t0 + (t1 - t0) * (i - i0) / (i1 - i0)
    return [round(start, 3) for start in starts]


def timeline(scenes: list[dict], says: list[str], heard: list[list[dict]], narrations: list[float]) -> list[dict]:
    """Per scene, in the video's time: where its voice starts and ends, and where each caption word starts."""
    out, frames = [], 0
    for scene, say, words, narration in zip(scenes, says, heard, narrations):
        voice = frames / FPS + scene["lead"]
        shown = caption_words(say)
        starts = word_starts(shown, words, narration)
        out.append(
            {
                "voice": round(voice, 3),
                "end": round(voice + narration, 3),
                "words": [{"text": w, "at": round(voice + s, 3)} for w, s in zip(shown, starts)],
            }
        )
        frames += scene["frames"]
    return out


def _chunks(words: list[dict]) -> list[list[dict]]:
    """Words split into SRT cues: a cue ends at a sentence end, CUE_WORDS words, or CUE_CHARS characters."""
    chunks, current = [], []
    for word in words:
        if current and (len(current) == CUE_WORDS or len(" ".join(w["text"] for w in [*current, word])) > CUE_CHARS):
            chunks.append(current)
            current = []
        current.append(word)
        if word["text"].endswith(SENTENCE_END):
            chunks.append(current)
            current = []
    return chunks + ([current] if current else [])


def _stamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(scenes: list[dict]) -> str:
    """The long-form's SRT: each cue from its first word's start to the next cue's, or its scene's voice end."""
    cues = []
    for scene in scenes:
        chunks = _chunks(scene["words"])
        for index, chunk in enumerate(chunks):
            end = chunks[index + 1][0]["at"] if index + 1 < len(chunks) else scene["end"]
            cues.append((chunk[0]["at"], end, " ".join(w["text"] for w in chunk)))
    return "".join(f"{n}\n{_stamp(a)} --> {_stamp(b)}\n{text}\n\n" for n, (a, b, text) in enumerate(cues, 1))


def caption_states(scenes: list[dict]) -> tuple[list[dict], list[tuple[int, float, float]]]:
    """The Short's caption states (state 0 blank) and when each shows: GROUP words, the said one current."""
    states, spans = [{"words": [], "current": -1}], []
    for scene in scenes:
        words = scene["words"]
        groups = [words[i : i + GROUP] for i in range(0, len(words), GROUP)]
        for g, group in enumerate(groups):
            group_end = groups[g + 1][0]["at"] if g + 1 < len(groups) else scene["end"]
            for j, word in enumerate(group):
                end = group[j + 1]["at"] if j + 1 < len(group) else group_end
                states.append({"words": [w["text"] for w in group], "current": j})
                spans.append((len(states) - 1, word["at"], end))
    return states, spans


def caption_frames(spans: list[tuple[int, float, float]], frames: int) -> list[tuple[int, int]]:
    """(state, frames) covering the whole video at FPS: each span on whole frames, state 0 in the gaps."""
    out, at = [], 0
    for state, start, end in spans:
        first, last = max(min(round(start * FPS), frames), at), min(round(end * FPS), frames)
        if last <= first:
            continue
        if first > at:
            out.append((0, first - at))
        out.append((state, last - first))
        at = last
    return out + ([(0, frames - at)] if frames > at else [])


def _quote(path: str) -> str:
    return "'" + path.replace("'", "'\\''") + "'"


def concat_list(files: list[str], frames: list[int] | None = None) -> str:
    """An ffconcat list of files, each shown for its frames when given (the last repeated, as ffmpeg needs)."""
    if frames is None:
        return "ffconcat version 1.0\n" + "".join(f"file {_quote(f)}\n" for f in files)
    body = "".join(f"file {_quote(f)}\nduration {n / FPS:.6f}\n" for f, n in zip(files, frames))
    return "ffconcat version 1.0\n" + body + f"file {_quote(files[-1])}\n"


def mix_command(voices: list[tuple[Path, float]], music: Path, music_db: float, seconds: float, out: Path):
    """ffmpeg mixing each narration at its start (seconds) with the looped bed at music_db dB."""
    audio = f"aresample={AUDIO_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo"
    inputs = [arg for wav, _ in voices for arg in ["-i", str(wav)]] + ["-stream_loop", "-1", "-i", str(music)]
    count, total, fade = len(voices), f"{seconds:.3f}", min(MUSIC_FADE, seconds / 2)
    parts = [f"[{i}:a]{audio},adelay={round(at * 1000)}:all=1[v{i}]" for i, (_, at) in enumerate(voices)]
    labels = "".join(f"[v{i}]" for i in range(count))
    parts.append(f"{labels}amix=inputs={count}:duration=longest:normalize=0,apad=whole_dur={total}[voice]")
    parts.append(
        f"[{count}:a]{audio},volume={music_db}dB,atrim=0:{total},afade=t=out:st={seconds - fade:.3f}:d={fade:.3f}[bed]"
    )
    parts.append(f"[voice][bed]amix=inputs=2:duration=shortest:normalize=0,atrim=0:{total}[mix]")
    return ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", "[mix]",
            "-c:a", "pcm_f32le", str(out)]  # fmt: skip


def _target(loudness: dict) -> str:
    return f"I={loudness['lufs']}:TP={round(loudness['true_peak'] - AAC_HEADROOM, 2)}:LRA={LRA}"


def measure_command(audio: Path, loudness: dict) -> list[str]:
    """loudnorm measuring a file's audio (the mix, or final.mp4) and printing the values as JSON on stderr."""
    return ["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
            "-af", f"loudnorm={_target(loudness)}:print_format=json", "-f", "null", "-"]  # fmt: skip


def measured(stderr: str) -> dict:
    """The first pass's input_i, input_tp, input_lra, input_thresh, and target_offset, as numbers."""
    start = stderr.rfind("{")
    try:
        values = json.loads(stderr[start : stderr.index("}", start) + 1])
        found = {k: float(values[k]) for k in ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]}
    except (ValueError, KeyError, TypeError):
        raise ToolError("ffmpeg loudnorm printed no measurement JSON") from None
    if found["input_i"] == float("-inf"):
        raise BadInput("the mix is silent: check the narration files (narrate-video) and the music bed")
    return found


def loudnorm_filter(values: dict, loudness: dict) -> str:
    """loudnorm's second pass: the target with the first pass's measurements, one linear gain."""
    return (
        f"loudnorm={_target(loudness)}:measured_I={values['input_i']}:measured_TP={values['input_tp']}:"
        f"measured_LRA={values['input_lra']}:measured_thresh={values['input_thresh']}:"
        f"offset={values['target_offset']}:linear=true"
    )


def final_command(scenes: Path, mix: Path, captions: Path | None, loudnorm: str, seconds: float, out: Path):
    """ffmpeg joining the clips (re-encoded only to burn captions) with the normalised mix."""
    inputs = ["-f", "concat", "-safe", "0", "-i", str(scenes), "-i", str(mix)]
    if captions is None:
        graph, video = f"[1:a]{loudnorm}[a]", ["-map", "0:v", "-c:v", "copy"]
    else:
        inputs += ["-f", "concat", "-safe", "0", "-i", str(captions)]
        graph = f"[2:v]format=rgba[c];[0:v][c]overlay=0:0:eof_action=pass[v];[1:a]{loudnorm}[a]"
        video = ["-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", str(render.CRF), "-pix_fmt", "yuv420p"]
    return ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, *video, "-map", "[a]",
            "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", str(AUDIO_RATE), "-t", f"{seconds:.3f}",
            "-movflags", "+faststart", str(out)]  # fmt: skip


def caption_page(states: list[dict], size, config: dict, fonts_css: str, references: Path = render.REFERENCES) -> str:
    """references/captions.html with the fonts and the states inlined; show(i) draws state i."""
    html = (references / "captions.html").read_text()
    if missing := [p for p in PLACEHOLDERS if p not in html]:
        raise ToolError(f"references/captions.html lacks {', '.join(missing)}")
    cues = {"width": size[0], "height": size[1], "top": render.CAPTION_TOP, "palette": render.palette(config)}
    cues["states"] = states
    data = json.dumps(cues, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return html.replace("/*{{fonts}}*/", fonts_css).replace("/*{{cues}}*/", f"const CUES = {data};\n")


def problems(script, scenes) -> list[str]:
    """Every field assemble needs from script.json and render/scenes.json that is missing or stale."""
    if not (isinstance(script, dict) and script.get("type") in SIZES and isinstance(script.get("scenes"), list)):
        return ["script.json: type and scenes: must be a rendered script (render.py)"]
    found = []
    for index, scene in enumerate(script["scenes"], 1):
        if not (isinstance(scene, dict) and isinstance(scene.get("say"), str) and scene["say"].strip()):
            found.append(f"scene {index}: say: must be a non-empty string")
    report = scenes.get("scenes") if isinstance(scenes, dict) else None
    if not (isinstance(report, list) and len(report) == len(script["scenes"]) and scenes.get("type") == script["type"]):
        found.append("render/scenes.json: does not match script.json; render the scenes again (render.py)")
    return found


# Thin shell: whisper-cli, Chrome, ffmpeg, and the video's files.

Snap = Callable[[str, tuple[int, int], int, Path], None]
Run = Callable[[list[str]], str]


def ffmpeg(command: list[str]) -> str:
    """Run ffmpeg; its stderr, where loudnorm prints its measurement."""
    return render.tool(command).stderr


def chrome(html: str, size: tuple[int, int], count: int, folder: Path) -> None:
    """Each caption state of the page, drawn by show(i) in the system Chrome, as folder/NNNN.png with alpha."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel="chrome", args=render.CHROME_ARGS)
        except PlaywrightError as error:
            raise ToolError(f"Chrome did not start; install Google Chrome ({str(error).splitlines()[0]})") from None
        try:
            tab = browser.new_page(viewport={"width": size[0], "height": size[1]})
            tab.set_content(html)
            if tab.evaluate("window.ready") is not True:
                raise ToolError("the caption font did not load in Chrome; check the font files (README, Setup)")
            for index in range(count):
                tab.evaluate(f"show({index})")
                tab.screenshot(path=str(folder / f"{index:04d}.png"), omit_background=True)
        except PlaywrightError as error:
            raise ToolError(f"Chrome failed on the captions ({str(error).splitlines()[0]})") from None
        finally:
            browser.close()


def assemble(video: Path, workspace: Path, script: dict, scenes: list[dict], config: dict, transcribe, snap, run):
    """The scenes, narration, and music into render/final.mp4 (and final.srt); the report."""
    music = workspace / MUSIC
    if not music.is_file():
        raise BadInput(f"{music}: missing; put the channel's music bed there (style guide Audio)")
    clips = [video / scene["file"] for scene in scenes]
    if missing := [str(c) for c in clips if not c.is_file()]:
        raise BadInput(f"{', '.join(missing)}: missing; render the scenes again (render.py)")
    wavs = [video / scene["narration"] for scene in scenes]
    narrations = [render.narration_seconds(wav) for wav in wavs]
    heard = [render.words_from(transcribe(wav), narrate.spoken_split) for wav in wavs]
    parts = timeline(scenes, [s["say"] for s in script["scenes"]], heard, narrations)
    frames = sum(scene["frames"] for scene in scenes)
    seconds, size = frames / FPS, SIZES[script["type"]]
    out = video / "render"
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        listing, mix = work / "scenes.txt", work / "mix.wav"
        listing.write_text(concat_list([str(c) for c in clips]))
        voices = [(wav, part["voice"]) for wav, part in zip(wavs, parts)]
        run(mix_command(voices, music, config["music_db"], seconds, mix))
        values = measured(run(measure_command(mix, config["loudness"])))
        captions = None
        if script["type"] == "short":
            states, spans = caption_states(parts)
            snap(caption_page(states, size, config, render.font_css(render.read_fonts())), size, len(states), work)
            shown = caption_frames(spans, frames)
            captions = work / "captions.txt"
            captions.write_text(concat_list([f"{state:04d}.png" for state, _ in shown], [n for _, n in shown]))
        loudnorm = loudnorm_filter(values, config["loudness"])
        run(final_command(listing, mix, captions, loudnorm, seconds, out / "final.mp4"))
    final = measured(run(measure_command(out / "final.mp4", config["loudness"])))
    if captions is None:
        (out / "final.srt").write_text(srt(parts))
    return {
        "type": script["type"],
        "width": size[0],
        "height": size[1],
        "seconds": round(seconds, 3),
        "file": "render/final.mp4",
        "captions": "render/final.srt" if captions is None else "burned",
        "measured": {"lufs": final["input_i"], "true_peak": final["input_tp"]},
        "mix_before": {"lufs": values["input_i"], "true_peak": values["input_tp"]},
    }


def main(
    argv: list[str] | None = None,
    transcribe: render.Transcribe = render.whisper,
    snap: Snap = chrome,
    run: Run = ffmpeg,
    root: Path = render.REPO_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        script = render.read_json(video / "script.json", "missing; write-video-script writes it")
        scenes = render.read_json(video / "render" / "scenes.json", "missing; render the scenes first (render.py)")
        if found := problems(script, scenes):
            raise BadInput(f"{video}:\n  " + "\n  ".join(found))
        report = assemble(video, channel.workspace, script, scenes["scenes"], channel.config, transcribe, snap, run)
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Narrate a video's script scene by scene with the channel's voice, then check the audio for leaks.

Usage: uv run --env-file .env agentic/skills/content/narrate-video/scripts/narrate.py CHANNEL N

Reads videos/<N>/script.json in the channel workspace (written by write-video-script; each
scene's say is its narration) and channel.yaml voice.id, voice.style, voice.pace, and
pronunciation. For each scene, in order:

1. Respell: each word of the pronunciation list (word -> respelling, whole words, any case)
   in say becomes its respelling; the script keeps the real words, so captions show them.
   // (a pause) and ... (a hesitation) stay; Gemini pauses on them without speaking them.
2. Synthesise: one Gemini Interactions API request (POST INTERACTIONS) with model MODEL,
   the respelled text, the voice id (a prebuilt name or a designed voice id) in
   generation_config.speech_config, and voice.style only in the text's speech_metadata
   annotation: style text inside the text is spoken aloud. The key is the GEMINI_API_KEY
   environment variable, read from .env by uv run --env-file .env; it is never printed.
3. Pace: ffmpeg atempo=<voice.pace> (tempo changes, pitch kept) writes narration/NN.wav,
   NN the scene number from 01.
4. Leak check: whisper-cli with the base.en model (WHISPER_MODEL, else
   .cache/whisper/ggml-base.en.bin in the home folder) transcribes NN.wav. The scene
   fails when the transcript has a markup word that say lacks (MARKUP_WORDS, such as
   "slash" or "pause"), an angle-bracket tag or //, the voice style, or matches under
   MATCH_MIN of the words.
   Match: difflib ratio of the transcript's words to the respelled text's words, both
   lowercased without punctuation or markup, with the transcript respelled too, so "pytest"
   and "pie test" agree. MATCH_MIN 0.9 allows about two misheard words in a twenty-word
   scene; the prototype's transcripts matched within four words in 381.

It writes narration/report.json and prints it: per scene the file, transcript, match, and
problems; match_min; and passed. Media stays out of git (the workspace ignores *.wav).

Needs ffmpeg and whisper-cli on PATH and the model file (README, Setup).

Exit codes: 0 every scene narrated and clean, 1 a Gemini, tool, or file error, or the key
missing (it stops at the failing scene), 2 bad input (an invalid script file or channel),
3 refused (a scene's audio leaked markup or does not match the script).
"""

import argparse
import base64
import binascii
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "agentic" / "scripts"))
import youtube_channel

INTERACTIONS = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "gemini-3.8-flash-tts"
KEY_VARIABLE = "GEMINI_API_KEY"
MODEL_VARIABLE = "WHISPER_MODEL"
WHISPER_MODEL = Path.home() / ".cache" / "whisper" / "ggml-base.en.bin"
TIMEOUT_SECONDS = 180
MATCH_MIN = 0.9
# Words a voice says when it reads markup aloud; a scene fails when it is heard but not in say.
MARKUP_WORDS = ["slash", "slashes", "pause", "ellipsis", "dot"]
TAG = re.compile(r"<[^<>]*>|//")
WORD = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")


class BadInput(Exception):
    """A missing or invalid script file or channel: exit 2."""


class ApiError(Exception):
    """Gemini failed or answered without audio: exit 1. The message never holds the key."""


class ToolError(Exception):
    """ffmpeg, whisper-cli, or the whisper model missing or failing: exit 1."""


def spoken(say: str, pronunciation: dict[str, str]) -> str:
    """The narration as sent to the voice: each listed word respelled, markup kept."""
    for word, respelling in pronunciation.items():
        say = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", respelling, say, flags=re.IGNORECASE)
    return say


def request_body(text: str, voice: dict) -> dict:
    """The Interactions API request for one scene: style in its own annotation, never in the text."""
    content = {"type": "text", "text": text, "annotations": [{"type": "speech_metadata", "style": voice["style"]}]}
    return {
        "model": MODEL,
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice["id"]}]},
    }


def audio_from(response: dict) -> bytes:
    """The WAV bytes of a response's last audio output."""
    try:
        parts = [
            part
            for step in response["steps"]
            if step.get("type") == "model_output"
            for part in step.get("content", [])
            if part.get("type") == "audio"
        ]
        return base64.b64decode(parts[-1]["data"], validate=True)
    except (KeyError, IndexError, TypeError, AttributeError, binascii.Error):
        raise ApiError("Gemini answered without audio") from None


def pace_command(raw: Path, out: Path, pace: float) -> list[str]:
    """ffmpeg changing the tempo to pace with the pitch kept."""
    return ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"atempo={pace}", str(out)]


def words(text: str, pronunciation: dict[str, str]) -> list[str]:
    """Lowercase words of text after respelling, without punctuation or markup."""
    text = spoken(text.replace("’", "'").replace("‘", "'"), pronunciation)
    return WORD.findall(TAG.sub(" ", text).lower())


def leak_problems(transcript: str, text: str, voice: dict, pronunciation: dict[str, str]) -> tuple[float, list[str]]:
    """The transcript's word match against the spoken text, and every leak it shows."""
    said, heard = words(text, pronunciation), words(transcript, pronunciation)
    match = round(difflib.SequenceMatcher(None, said, heard, autojunk=False).ratio(), 3)
    problems = [f"heard markup '{tag}'" for tag in TAG.findall(transcript)]
    problems += [f"heard '{word}'" for word in MARKUP_WORDS if word in heard and word not in said]
    style = " ".join(words(voice["style"], {}))
    if style and style in " ".join(heard) and style not in " ".join(said):
        problems.append("heard the voice style")
    if match < MATCH_MIN:
        problems.append(f"matched {match:.0%} of the script's words; needs {MATCH_MIN:.0%}")
    return match, problems


def say_problems(script) -> list[str]:
    """Every scene without narration, as 'scene N: say: problem'."""
    scenes = script.get("scenes") if isinstance(script, dict) else None
    if not (isinstance(scenes, list) and scenes):
        return ["scenes: must be a non-empty list"]
    return [
        f"scene {index}: say: must be a non-empty string"
        for index, scene in enumerate(scenes, 1)
        if not (isinstance(scene, dict) and isinstance(scene.get("say"), str) and scene["say"].strip())
    ]


# Thin shell: Gemini, ffmpeg, whisper-cli, and the narration files.

Post = Callable[[dict, str], dict]
Transcribe = Callable[[Path], str]
Run = Callable[[list[str]], None]


def gemini(body: dict, key: str) -> dict:
    """One Interactions API call. The key goes only in the request header."""
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    request = urllib.request.Request(INTERACTIONS, json.dumps(body).encode(), headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read())["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = error.reason
        raise ApiError(f"HTTP {error.code}: {message}") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise ApiError(str(getattr(error, "reason", error))) from None
    except json.JSONDecodeError:
        raise ApiError("answer is not JSON") from None


def tool(command: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise ToolError(f"{command[0]} not found; install it (README, Setup)") from None
    except subprocess.CalledProcessError as error:
        raise ToolError(f"{command[0]} failed: {error.stderr.strip()[:400]}") from None


def ffmpeg(command: list[str]) -> None:
    tool(command)


def whisper(wav: Path) -> str:
    """The plain transcript of wav from whisper-cli with the base.en model."""
    model = Path(os.environ.get(MODEL_VARIABLE) or WHISPER_MODEL)
    if not model.is_file():
        raise ToolError(f"whisper model {model.name} missing; download it (README, Setup) or set {MODEL_VARIABLE}")
    return tool(["whisper-cli", "-m", str(model), "-f", str(wav), "-nt", "-np"]).stdout


def read_script(path: Path) -> dict:
    try:
        script = json.loads(path.read_text())
    except FileNotFoundError:
        raise BadInput(f"{path}: no script.json; write-video-script writes it") from None
    except json.JSONDecodeError as error:
        raise BadInput(f"{path}: not valid JSON ({error})") from None
    if problems := say_problems(script):
        raise BadInput(f"{path}:\n  " + "\n  ".join(problems))
    return script


def narrate(script: dict, config: dict, folder: Path, key: str, post: Post, transcribe: Transcribe, run: Run) -> dict:
    """Each scene synthesised, paced, and transcribed into folder; the leak report."""
    voice, pronunciation = config["voice"], config["pronunciation"]
    folder.mkdir(parents=True, exist_ok=True)
    scenes = []
    with tempfile.TemporaryDirectory() as scratch:
        for index, scene in enumerate(script["scenes"], 1):
            text = spoken(scene["say"], pronunciation)
            try:
                wav = audio_from(post(request_body(text, voice), key))
            except ApiError as error:
                raise ApiError(f"scene {index}: Gemini: {error}") from None
            raw, out = Path(scratch) / f"{index:02d}.wav", folder / f"{index:02d}.wav"
            raw.write_bytes(wav)
            run(pace_command(raw, out, voice["pace"]))
            transcript = transcribe(out).strip()
            match, problems = leak_problems(transcript, text, voice, pronunciation)
            file = f"{folder.name}/{out.name}"
            scenes.append(
                {"scene": index, "file": file, "transcript": transcript, "match": match, "problems": problems}
            )
    return {"scenes": scenes, "match_min": MATCH_MIN, "passed": not any(s["problems"] for s in scenes)}


def main(
    argv: list[str] | None = None,
    post: Post = gemini,
    transcribe: Transcribe = whisper,
    run: Run = ffmpeg,
    root: Path = REPO_ROOT,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("channel")
    parser.add_argument("number", type=int, help="the video's content issue number")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        script = read_script(video / "script.json")
        key = os.environ.get(KEY_VARIABLE)
        if not key:
            raise ApiError(f"{KEY_VARIABLE} is not set: put it in .env and run with uv run --env-file .env")
        report = narrate(script, channel.config, video / "narration", key, post, transcribe, run)
        (video / "narration" / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ApiError, ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=1))
    for scene in report["scenes"]:
        for problem in scene["problems"]:
            print(f"refused: scene {scene['scene']}: {problem}", file=sys.stderr)
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())

"""Narrate a video's script scene by scene with the channel's voice, then check the audio for leaks.

Usage: uv run --env-file .env agentic/skills/content/narrate-video/scripts/narrate.py CHANNEL N [--force]

Reads videos/<N>/script.json in the channel workspace (written by write-video-script; each
scene's say is its narration) and channel.yaml voice.id, voice.style, voice.pace, and
pronunciation. For each scene, in order (Reuse, below, skips steps 2 and 3):

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
   and "pie test" agree. Both sides are also normalised (spoken_split, comparable), since
   scripts spell numbers as words and UK spellings while whisper writes digits and US ones:
   numerals become words ("-1" minus one, "10%" ten percent, "1,205" one thousand two
   hundred five, "59.99" fifty nine point nine nine), "a hundred" is "one hundred", "and"
   after hundred or thousand before a number word is dropped, and -our/-ise/-yse endings
   become -or/-ize/-yze. render-video's assemble.py reuses these to time captions. MATCH_MIN 0.9 allows about two misheard words in a twenty-word
   scene; the prototype's transcripts matched within four words in 381.

Reuse: Gemini TTS allows 100 requests a day, so a rerun synthesises only the scenes whose audio
would change. narration/cache.json maps each scene number to audio_digest, a sha256 of the request
body (model, voice id, style, and the respelled text with its pauses) and the pace; a scene whose
digest matches and whose NN.wav exists keeps its file, and every scene still gets the leak check.
A scene is recorded only once its check passes, so a refused scene and narration from before the
record existed are synthesised again. --force synthesises every scene. It prints "narrated: S
synthesised, R reused" to stderr; a Gemini error (such as HTTP 429, the daily quota) names how
many scenes are still to synthesise, and a rerun after the reset synthesises only those.

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
import hashlib
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
# A numeral as whisper writes it: an optional minus, digits (with thousands commas), decimals, percent.
NUMERAL = re.compile(r"(?<![\w.])(-)?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(%)?(?!\w)")
ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
ONES += ["thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = {10**9: "billion", 10**6: "million", 1000: "thousand", 100: "hundred"}
NUMBER_WORDS = set(ONES + TENS[2:])
# UK endings to their US form, as whisper writes them: behaviour, favourite, organise, analysed.
SPELLINGS = [
    (re.compile(r"(?<=[a-z]{3})our(?=(?:s|ed|ing|ite|ites|able|ful)?$)"), "or"),
    (re.compile(r"(?<=[a-z]{2})is(?=(?:e|es|ed|ing|ation|ations)$)"), "iz"),
    (re.compile(r"(?<=[a-z]{2})ys(?=(?:e|es|ed|ing)$)"), "yz"),
]


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


def audio_digest(text: str, voice: dict) -> str:
    """The sha256 of everything that shapes a scene's audio: the request body and the pace."""
    shaping = {"body": request_body(text, voice), "pace": voice["pace"]}
    return hashlib.sha256(json.dumps(shaping, sort_keys=True).encode()).hexdigest()


def pace_command(raw: Path, out: Path, pace: float) -> list[str]:
    """ffmpeg changing the tempo to pace with the pitch kept."""
    return ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", f"atempo={pace}", str(out)]


def number_words(n: int) -> str:
    """A whole number in words, as said: 105 'one hundred five'."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + (f" {ONES[n % 10]}" if n % 10 else "")
    scale = next(size for size in SCALES if n >= size)
    head, rest = divmod(n, scale)
    return f"{number_words(head)} {SCALES[scale]}" + (f" {number_words(rest)}" if rest else "")


def _numeral(found: re.Match) -> str:
    minus, whole, decimals, percent = found.groups()
    said = number_words(int(whole.replace(",", "")))
    if decimals:
        said += " point " + " ".join(ONES[int(d)] for d in decimals)
    return f" {'minus ' if minus else ''}{said}{' percent' if percent else ''} "


def spoken_split(text: str) -> list[str]:
    """Lowercase words of text with each numeral in words: '-1' minus one, '10%' ten percent."""
    return WORD.findall(NUMERAL.sub(_numeral, text.lower()))


def comparable(tokens: list[str]) -> list[str | None]:
    """Each word in one form for comparing, None for one to skip: 'a hundred' as 'one hundred', the 'and'
    of 'hundred and one' skipped, UK endings in US form. One entry per token, so callers keep positions."""
    out: list[str | None] = []
    for index, token in enumerate(tokens):
        after = tokens[index + 1] if index + 1 < len(tokens) else ""
        before = tokens[index - 1] if index else ""
        if token == "a" and after in SCALES.values():
            token = "one"
        elif token == "and" and before in SCALES.values() and after in NUMBER_WORDS:
            out.append(None)
            continue
        for ending, us in SPELLINGS:
            token = ending.sub(us, token)
        out.append(token)
    return out


def words(text: str, pronunciation: dict[str, str]) -> list[str]:
    """Comparable words of text after respelling, without punctuation or markup (spoken_split, comparable)."""
    text = spoken(text.replace("’", "'").replace("‘", "'"), pronunciation)
    return [word for word in comparable(spoken_split(TAG.sub(" ", text))) if word]


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


def read_cache(path: Path) -> dict:
    """The recorded audio digest per scene number; empty when the record is missing or unreadable."""
    try:
        cache = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return cache if isinstance(cache, dict) else {}


def narrate(
    script: dict,
    config: dict,
    folder: Path,
    key: str,
    post: Post,
    transcribe: Transcribe,
    run: Run,
    force: bool = False,
) -> tuple[dict, int]:
    """Each changed scene synthesised and paced, every scene transcribed; the leak report and the synthesised count."""
    voice, pronunciation = config["voice"], config["pronunciation"]
    folder.mkdir(parents=True, exist_ok=True)
    cache_path = folder / "cache.json"
    cache = read_cache(cache_path)
    texts = [spoken(scene["say"], pronunciation) for scene in script["scenes"]]
    digests = [audio_digest(text, voice) for text in texts]
    stale = [
        force or cache.get(str(index)) != digest or not (folder / f"{index:02d}.wav").is_file()
        for index, digest in enumerate(digests, 1)
    ]
    scenes = []
    with tempfile.TemporaryDirectory() as scratch:
        for index, (text, digest) in enumerate(zip(texts, digests, strict=True), 1):
            raw, out = Path(scratch) / f"{index:02d}.wav", folder / f"{index:02d}.wav"
            if stale[index - 1]:
                try:
                    wav = audio_from(post(request_body(text, voice), key))
                except ApiError as error:
                    left = sum(stale[index - 1 :])
                    raise ApiError(
                        f"scene {index}: Gemini: {error}; {left} scenes still to synthesise, "
                        "a rerun synthesises only those"
                    ) from None
                raw.write_bytes(wav)
                run(pace_command(raw, out, voice["pace"]))
            transcript = transcribe(out).strip()
            match, problems = leak_problems(transcript, text, voice, pronunciation)
            if problems:
                cache.pop(str(index), None)
            else:
                cache[str(index)] = digest
            cache_path.write_text(json.dumps(cache, indent=1) + "\n")
            file = f"{folder.name}/{out.name}"
            scenes.append(
                {"scene": index, "file": file, "transcript": transcript, "match": match, "problems": problems}
            )
    report = {"scenes": scenes, "match_min": MATCH_MIN, "passed": not any(s["problems"] for s in scenes)}
    return report, sum(stale)


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
    parser.add_argument("--force", action="store_true", help="synthesise every scene, even unchanged ones")
    args = parser.parse_args(argv)
    try:
        channel = youtube_channel.load(args.channel, root)
        video = channel.workspace / "videos" / str(args.number)
        script = read_script(video / "script.json")
        key = os.environ.get(KEY_VARIABLE)
        if not key:
            raise ApiError(f"{KEY_VARIABLE} is not set: put it in .env and run with uv run --env-file .env")
        report, synthesised = narrate(
            script, channel.config, video / "narration", key, post, transcribe, run, args.force
        )
        (video / "narration" / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    except (BadInput, youtube_channel.ChannelError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (ApiError, ToolError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=1))
    print(f"narrated: {synthesised} synthesised, {len(report['scenes']) - synthesised} reused", file=sys.stderr)
    for scene in report["scenes"]:
        for problem in scene["problems"]:
            print(f"refused: scene {scene['scene']}: {problem}", file=sys.stderr)
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())

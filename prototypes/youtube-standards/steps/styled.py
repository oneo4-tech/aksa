"""PROTOTYPE: Gemini 3.8 TTS with speech_metadata style and inline tags (Interactions API).

uv run --no-project steps/styled.py -> out/voice/style-<name>.wav
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "voice"
TEXT = (
    "Here are two unit tests an AI assistant wrote for me. <short pause> Both pass. Both are green. <short pause> "
    "And I can break the code they test in ONE keystroke, without either of them noticing. <long pause> "
    "Your job for the next few minutes: spot the bug. <short pause> Not in the code. <short pause> In the TESTS."
)
STYLES = {
    "calm": "calm, curious and unhurried, like a senior tester explaining to a peer; measured pace",
    "confident": "confident and energetic, crisp delivery, slightly faster pace, a hint of playful challenge",
    "warm": "warm and conversational, friendly mentor tone, relaxed natural pace with clear articulation",
}


def tts(text: str, voice: str, style: str | None, out: Path) -> dict:
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    body = {
        "model": "gemini-3.8-flash-tts",
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code} {e.read().decode()[:400]}")
    audio = [c for s in data["steps"] if s["type"] == "model_output" for c in s["content"] if c["type"] == "audio"][-1]
    out.write_bytes(base64.b64decode(audio["data"]))
    return {k: v for k, v in audio.items() if k != "data"}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(tts(TEXT, "Charon", None, OUT / "style-tags-only.wav"))
    for name, style in STYLES.items():
        tts(TEXT, "Charon", style, OUT / f"style-{name}.wav")

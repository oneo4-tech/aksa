"""PROTOTYPE: one sample paragraph in many Gemini TTS voices, plus pace variants.

uv run --no-project steps/voices.py   (GEMINI_API_KEY exported) -> out/voice/<voice>.wav
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MODEL = "gemini-3.8-flash-tts"
TEXT = (
    "Here are two unit tests an AI assistant wrote for me. Both pass. Both are green. "
    "And I can break the code they test in one keystroke without either of them noticing. "
    "Your job for the next few minutes: spot the bug. Not in the code. In the tests."
)
VOICES = [
    "Charon",
    "Kore",
    "Puck",
    "Fenrir",
    "Orus",
    "Iapetus",
    "Algieba",
    "Achird",
    "Sadaltager",
    "Schedar",
    "Aoede",
    "Leda",
    "Sulafat",
    "Rasalgethi",
]


def tts(text: str, voice: str, out: Path) -> None:
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    for attempt in range(4):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=180))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(30)
                continue
            sys.exit(f"{voice}: {e.code} {e.read().decode()[:300]}")
    pcm = base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)


def main() -> None:
    out = HERE / "out" / "voice"
    out.mkdir(parents=True, exist_ok=True)
    words = len(TEXT.split())
    rows = []
    for v in VOICES:
        f = out / f"{v}.wav"
        if not f.exists():
            tts(TEXT, v, f)
        secs = float(
            subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        rows.append({"voice": v, "seconds": round(secs, 1), "wpm": round(words / secs * 60)})
        print(rows[-1], file=sys.stderr)
    (out / "voices.json").write_text(json.dumps(rows))


if __name__ == "__main__":
    main()

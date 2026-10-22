"""PROTOTYPE: narrate each scene with one engine; write out/<video>/<engine>/NN.wav and timing.

uv run steps/narrate.py <scenes.json> <engine>   engine: say | gemini-<model>
Needs GEMINI_API_KEY in the environment for gemini engines.
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STYLE = os.environ.get("TTS_STYLE", "")


def gemini(model: str, text: str, out: Path) -> None:
    body = {
        "contents": [{"parts": [{"text": STYLE + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}},
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    for attempt in range(4):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=180))
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 429 and attempt < 3:
                print("  rate limited, waiting 30s", file=sys.stderr)
                time.sleep(30)
                continue
            sys.exit(f"gemini {e.code}: {msg}")
    pcm = base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)


def say(text: str, out: Path) -> None:
    subprocess.run(["say", "-v", "Samantha", "--data-format=LEI16@24000", "-o", str(out), text], check=True)


def main() -> None:
    scenes_file, engine = Path(sys.argv[1]), sys.argv[2]
    video = json.loads(scenes_file.read_text())
    out_dir = HERE / "out" / video["id"] / engine
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    for i, scene in enumerate(video["scenes"]):
        out = out_dir / f"{i:02d}.wav"
        if engine == "say":
            say(scene["say"], out)
        else:
            gemini(engine.removeprefix("gemini-"), scene["say"], out)
        print(f"  {engine} scene {i} ok", file=sys.stderr)
    timing = {"step": "narrate", "engine": engine, "video": video["id"], "seconds": round(time.time() - start, 1)}
    (out_dir / "timing.json").write_text(json.dumps(timing))
    print(json.dumps(timing))


main()

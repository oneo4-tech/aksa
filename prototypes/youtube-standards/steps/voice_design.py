"""PROTOTYPE: design three custom Gemini voices (stored in the project, 1 year TTL) and render the sample paragraph.

uv run --no-project steps/voice_design.py -> out/voice/designed-<name>.wav, out/voice/designed.json (voice ids)
"""

import base64
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location("styled", Path(__file__).with_name("styled.py"))
styled = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styled)
OUT = Path(__file__).resolve().parent.parent / "out" / "voice"
DESIGNS = {
    "architect": (
        "male",
        "en-IN",
        (
            "A calm, authoritative senior software architect in his mid-40s with a light Indian "
            "English accent, measured pace, explaining a subtle bug to a respected peer."
        ),
    ),
    "mentor": (
        "male",
        "en-US",
        (
            "A warm, curious software tester in his early 30s, friendly mentor energy, relaxed natural "
            "pace, clear articulation, a hint of playful challenge."
        ),
    ),
    "lead": (
        "female",
        "en-GB",
        "A crisp, confident QA lead in her late 30s, precise articulation, calm authority, dry wit, steady pace.",
    ),
}
TEXT = (
    "Here are two unit tests an AI assistant wrote for me. // Both pass. Both are green. // And I can break the code "
    "they test in ONE keystroke... without either of them noticing."
)


def create(name: str, gender: str, lang: str, prompt: str) -> str:
    body = {
        "store": True,
        "voice": {
            "model": "gemini-3.8-flash-tts",
            "type": "prompted",
            "display_name": f"OneO4TestLab prototype {name}",
            "gender": gender,
            "language_code": lang,
            "prompted": {"input": prompt},
        },
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/voices",
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        sys.exit(f"{name}: {e.code} {e.read().decode()[:400]}")
    (OUT / f"designed-{name}-preview.wav").write_bytes(base64.b64decode(data["sample_audio"]["data"]))
    return data["id"] if "id" in data else data["name"].rsplit("/", 1)[-1]


ids = {}
for name, (gender, lang, prompt) in DESIGNS.items():
    ids[name] = create(name, gender, lang, prompt)
    styled.tts(TEXT, ids[name], styled.STYLES["warm"], OUT / f"designed-{name}.wav")
    print(name, ids[name])
(OUT / "designed.json").write_text(json.dumps(ids, indent=1))

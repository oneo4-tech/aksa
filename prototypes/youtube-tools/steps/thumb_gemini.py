"""PROTOTYPE: generate a thumbnail with a Gemini image model from the brief.

uv run steps/thumb_gemini.py <model>   -> out/thumbs/<model>.png
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BRIEF = (
    "YouTube thumbnail, 16:9, 1280x720, dark GitHub-style background. Left: a bright green rounded badge reading "
    "exactly '2 PASSED' in bold monospace, slightly tilted. Below it, huge bold text 'TESTS' in white and 'NOTHING' "
    "in red. Right: a glowing red cartoon bug crawling out of a green checkmark. High contrast, readable at small "
    "size, no other text, no faces, no logos."
)


def main() -> None:
    model = sys.argv[1]
    body = {"contents": [{"parts": [{"text": BRIEF}]}], "generationConfig": {"responseModalities": ["IMAGE"]}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    start = time.time()
    try:
        data = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        sys.exit(f"{model}: {e.code} {e.read().decode()[:300]}")
    parts = data["candidates"][0]["content"]["parts"]
    image = next(p["inlineData"] for p in parts if "inlineData" in p)
    out = HERE / "out" / "thumbs" / f"{model}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(image["data"]))
    print(json.dumps({"step": "thumbnail", "engine": model, "seconds": round(time.time() - start, 1)}))


main()

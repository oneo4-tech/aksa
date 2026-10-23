"""PROTOTYPE: background music bed with a Lyria model. uv run --no-project steps/music.py <model> <name> <prompt>"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

model, name, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
    {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
)
start = time.time()
try:
    data = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(f"{model}: {e.code} {e.read().decode()[:400]}")
cand = data["candidates"][0]
if "content" not in cand:
    sys.exit(f"{model}: no content: {json.dumps(data)[:600]}")
parts = cand["content"]["parts"]
out = Path(__file__).resolve().parent.parent / "out" / "audio"
out.mkdir(parents=True, exist_ok=True)
for p in parts:
    if "inlineData" in p:
        ext = p["inlineData"]["mimeType"].split("/")[-1].replace("mpeg", "mp3")
        (out / f"{name}.{ext}").write_bytes(base64.b64decode(p["inlineData"]["data"]))
        print(
            json.dumps({"music": name, "mime": p["inlineData"]["mimeType"], "seconds": round(time.time() - start, 1)})
        )
    elif "text" in p:
        print("text:", p["text"][:200])

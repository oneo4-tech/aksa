"""PROTOTYPE: text-free thumbnail art in several styles with Gemini 3.1 Flash Image. -> out/thumbs/art-<style>.png"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "thumbs"
SUBJECT = (
    "a smug red software bug crawling out from behind a large glowing green checkmark. Absolutely no text, "
    "letters, or numbers. Solid flat background color #0b0f14, centered subject with margin around it"
)
STYLES = {
    "glossy-cartoon": "Glossy cartoon illustration, soft red rim glow, strong contrast: ",
    "flat-vector": "Flat vector illustration, bold shapes, two-tone shading, clean thick outlines, no gradients: ",
    "clay-3d": "3D clay render, soft studio lighting, playful toy-like materials, subtle depth of field: ",
}

for name, style in STYLES.items():
    body = {"contents": [{"parts": [{"text": style + SUBJECT}]}], "generationConfig": {"responseModalities": ["IMAGE"]}}
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image:generateContent",
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        sys.exit(f"{name}: {e.code} {e.read().decode()[:300]}")
    part = next(p for p in data["candidates"][0]["content"]["parts"] if "inlineData" in p)
    (OUT / f"art-{name}.png").write_bytes(base64.b64decode(part["inlineData"]["data"]))
    print(name, "ok")

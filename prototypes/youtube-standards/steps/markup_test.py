"""PROTOTYPE: which pause markup does Gemini 3.8 TTS speak aloud? -> out/voice/markup-<name>.wav"""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("styled", Path(__file__).with_name("styled.py"))
styled = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styled)
OUT = Path(__file__).resolve().parent.parent / "out" / "voice"
LINE = "Both pass. {p} Both are green. {p} Now break the code."
for name, mark in {
    "short-pause": "<short pause>",
    "long-pause": "<long pause>",
    "bracket": "[pause]",
    "slashes": "//",
    "ellipsis": "...",
}.items():
    styled.tts(LINE.format(p=mark), "Puck", styled.STYLES["warm"], OUT / f"markup-{name}.wav")

"""PROTOTYPE: narration for the animated scene in the owner's picks (Puck, warm, 0.92 pace). -> out/anim/voice.wav"""

import importlib.util
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location("styled", Path(__file__).with_name("styled.py"))
styled = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styled)

OUT = Path(__file__).resolve().parent.parent / "out" / "anim"
TEXT = (
    "Here's a test an AI wrote for me. <short pause> Let's run it. <short pause> "
    "Green. Passing. <short pause> Now look closer... "
    "It patches the very function it's testing, with a fake that returns ninety. "
    "Then it checks for ninety. <short pause> The real code NEVER runs."
)
OUT.mkdir(parents=True, exist_ok=True)
styled.tts(TEXT, "Puck", styled.STYLES["warm"], OUT / "voice-raw.wav")
subprocess.run(
    ["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "voice-raw.wav"), "-af", "atempo=0.92", str(OUT / "voice.wav")],
    check=True,
)

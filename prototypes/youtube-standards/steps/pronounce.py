"""PROTOTYPE: jargon pronunciation, plain vs respelled, one voice. -> out/voice/pron-plain.wav, pron-respelled.wav"""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("v", Path(__file__).with_name("voices.py"))
PLAIN = (
    "Run pytest in CI. Parse the YAML config, check the regex, then call the async OAuth endpoint "
    "with a JWT. Mock the SQL query and assert on the JSON. The CLI exits with a non-zero code."
)
RESPELLED = (
    "Run pie-test in C.I. Parse the yamel config, check the rej-ex, then call the ay-sink oh-auth endpoint "
    "with a J.W.T. Mock the sequel query and assert on the jay-son. The C.L.I. exits with a non-zero code."
)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
out = Path(__file__).resolve().parent.parent / "out" / "voice"
out.mkdir(parents=True, exist_ok=True)
v.tts(PLAIN, "Charon", out / "pron-plain.wav")
v.tts(RESPELLED, "Charon", out / "pron-respelled.wav")

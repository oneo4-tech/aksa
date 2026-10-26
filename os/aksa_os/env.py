"""Parse a .env file into a mapping. Keys stay server-side and no error carries a value."""

import re
from pathlib import Path

KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
EXPORT = "export "


def read_env(path: Path) -> dict[str, str]:
    """Every key and value in the file; a missing or unreadable file reads as empty."""
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return {}
    return parse_env(text)


def parse_env(text: str) -> dict[str, str]:
    """Parse the file's lines, skipping blanks, comments, and malformed entries."""
    values = {}
    for line in text.splitlines():
        entry = _entry(line)
        if entry is not None:
            key, value = entry
            values[key] = value
    return values


def _entry(line: str) -> tuple[str, str] | None:
    """One key and value from a line, or None when the line carries none."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith(EXPORT):
        text = text.removeprefix(EXPORT).lstrip()
    key, separator, value = text.partition("=")
    key = key.strip()
    if not separator or not KEY.match(key):
        return None
    return key, _value(value.strip())


def _value(text: str) -> str:
    """The value without its surrounding quotes, or with an unquoted inline comment removed."""
    if text[:1] in ("'", '"'):
        quote = text[0]
        end = text.find(quote, 1)
        if end != -1:
            inner = text[1:end]
            if quote == '"':
                inner = inner.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
            return inner
    return text.split(" #")[0].strip()

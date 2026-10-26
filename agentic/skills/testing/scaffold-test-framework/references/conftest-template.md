# Test scaffold template

Read before writing in Procedure steps 4 to 6. Copy each block into the engagement folder and replace every `<...>` placeholder with the engagement's value. Nothing here is copied into aksa's own files.

## pyproject.toml

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
  "jsonschema>=4.22",
  "playwright>=1.46",
  "pytest>=8.2",
  "pytest-playwright>=0.5",
  "ruff>=0.6",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: runs against the client's application under test"]

[tool.ruff]
line-length = 120

[tool.ruff.lint.isort]
known-first-party = ["pages"]
```

- The dependencies serve both suites: `httpx` and `jsonschema` for the API, `playwright` and `pytest-playwright` for the UI, and `pytest` and `ruff` for both.
- One `live` marker serves both suites, so its description names neither; a plain `pytest` run includes the live tests.
- `known-first-party` keeps the `from pages.<module>` imports in the UI suite in their own group, so `ruff check` sorts them apart from `playwright`.
- On an explicit rerun, add only a dependency or setting that is missing and keep every other entry, such as one a suite added.

## tests/conftest.py

```python
"""Shared test setup for this engagement.

Load the values named in the brief's `credentials_env` from `.env` at run time,
without printing them. A variable already set in the environment wins, so
`uv run --env-file .env pytest` and a plain `uv run pytest` both work.
"""

import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_env_file(path: Path) -> None:
    """Set each name in the file that the environment does not already have."""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if name:
            os.environ.setdefault(name, value)


def pytest_configure(config) -> None:
    """Load `.env` before collection imports a suite's conftest."""
    if ENV_FILE.is_file():
        load_env_file(ENV_FILE)
```

- The root conftest loads the file once, before collection imports each suite's own conftest, so a suite's import-time `os.environ` read already sees the values.
- `os.environ.setdefault` never overrides a value the owner set, so `uv run --env-file .env pytest` keeps working.
- A missing `.env` is skipped, so `--collect-only` passes without one. An unreadable `.env` fails with its path.
- No name or value is printed, logged, or written to a report.
- Suite fixtures stay in each suite's own `conftest.py`; this file holds only the shared `.env` loading.
- On an explicit rerun, replace the file with this block and report the change.

## tests/ui/pages/README.md

```md
# Page objects

The one home for this engagement's UI page objects. The UI suite imports them as
`pages.<module>` from its own folder, so a page object kept anywhere else cannot be
imported. One module per page the UI cases visit, each a subclass of `BasePage`
with the page's path, its locators, and the actions the cases name. Keep locators
and actions in a page object and assertions in the test.
```

- Write this README only when the brief's `surfaces` includes `ui`; with no `ui` surface, write no page-object folder.
- It sits in `.projects/testing/<engagement>/tests/ui/pages/`, where `write-ui-tests` writes and imports the page objects, so the engagement has one home for them.

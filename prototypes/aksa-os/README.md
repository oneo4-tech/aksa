# AKSA OS overview prototype

**PROTOTYPE. Never merge. Wipe me.**

Question: which overview layout and HUD language should AKSA OS use, and does the aksa palette carry the Jarvis feel?

This reads real local data and writes nothing:

- open factory issues through `gh`
- project folders under `.projects`
- Knowledge Base pages under `.kb/wiki`
- Claude Code usage through the macOS Keychain OAuth endpoint
- OpenRouter credits through its API
- OpenCode local spend from its SQLite database
- Google AI Studio as a manual value (no API exists)

## Run

From the worktree root:

```sh
uv run --with fastapi --with uvicorn --with jinja2 --with requests \
    python prototypes/aksa-os/app.py
```

Open http://127.0.0.1:8765.

Refresh reads everything again. There is no background polling.

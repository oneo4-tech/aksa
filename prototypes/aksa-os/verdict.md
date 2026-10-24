**Prototype:** `prototype/aksa-os-look`, run from `.worktrees/prototype-aksa-os-look` with `uv run --with fastapi --with uvicorn --with jinja2 --with requests python prototypes/aksa-os/app.py`, then open http://127.0.0.1:8765

**Question:** Which overview layout and HUD language should AKSA OS use, and does the aksa palette carry the Jarvis feel?

**Answer:** Keep the overview as built: a left command rail, a central HUD core with live counts, a hero and four stat tiles, a factory run list, and a right rail with credits, projects, and recent KB pages. The aksa palette with cyan telemetry and the red prototype banner carries the Jarvis feel without the literal cyan and gold.

**Why:** Real data made the cockpit legible at a glance. The core reads as Jarvis while the red brand band keeps it aksa. The credits panel proved the mixed sources work: Claude Code, OpenRouter, and OpenCode live, Google AI Studio manual. Surprises: the worktree needed a local `.env` link for OpenRouter; the factory list had to sort on ISO timestamps before humanising them; the right rail is taller than the main column, so the page scrolls.

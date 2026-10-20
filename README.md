# aksa

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory. It keeps agentic components (rules, skills, agents, memory, scripts, templates) in one vendor-neutral place and syncs them to Claude Code, OpenCode, Codex, Gemini CLI, and Copilot.

Agents start from [`AGENTS.md`](AGENTS.md), which also holds the repository map.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and git.

```sh
uv sync                                   # Python and dev tools
cp .env.example .env                      # then fill in keys
git config core.hooksPath .githooks       # pre-commit checks
```

Point the external links at this machine: edit `config/environment.yaml` (the only file with absolute paths), then:

```sh
uv run agentic/scripts/link_external.py   # creates .kb, .projects, .worktrees
uv run agentic/scripts/sync_vendors.py claude codex   # .claude/skills and .agents/skills
uv run agentic/scripts/kb_index.py        # .kb/index.md from the wiki pages
```

Start parallel work in its own worktree, set up the same way: `uv run agentic/scripts/new_worktree.py <branch>`.

The Knowledge Base (`.kb`) is its own git repository with `inbox/`, `raw/`, `wiki/`, and `outputs/`; see `agentic/rules/knowledge.md`.

## Checks

```sh
uv run pytest            # scripts and repository invariants
uv run ruff check .
uv run ruff format --check .
```

The pre-commit hook and CI (`.github/workflows/check.yml`) run the same checks; the hook also checks the vendor sync. On pull requests that change components, `.github/workflows/review.yml` requires a filled **review-component result** section.

## Where things are decided

- Terms: `agentic/memory/vocabulary.md`
- Decisions: `agentic/memory/decisions.md` (superseded: `agentic/memory/decisions-history.md`)
- Memory and Knowledge Base: `agentic/rules/knowledge.md`
- Component standards: `agentic/rules/components.md`

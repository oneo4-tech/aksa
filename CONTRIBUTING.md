# Contributing to aksa

## Quick Start

1. Read [`AGENTS.md`](AGENTS.md) — it's the agent entry point and repository map
2. Install dependencies:
   ```bash
   uv sync
   cp .env.example .env        # then fill in your keys
   git config core.hooksPath .githooks
   ```
3. Run checks locally:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

## Workflow: Software Factory

All tracked changes follow the **Software Factory** ([`agentic/rules/factory.md`](agentic/rules/factory.md)):

1. Open a **Factory Work Request** issue (use the issue template)
2. Factory runs through stages:
   - `stage:triage` → route or close
   - `stage:concept` → settle decisions, feasibility (gate G0)
   - `stage:define` → write & approve requirement (gate G1)
   - `stage:spec` → design approach, interfaces, tests (gate G2)
   - `stage:plan` → task checklist, integration branch (gate G3)
   - `stage:build` → implement & verify each task
   - `stage:ship` → PR ready for owner merge
3. Each stage gate requires **owner approval** before proceeding

## Component Changes

Before creating or changing any **agentic component** (rules, skills, agents, memory, scripts, templates):
- Read [`agentic/rules/components.md`](agentic/rules/components.md)
- Run the `review-component` skill (enforced by CI on PRs)

## Code Standards

- **Python**: `ruff` (line-length 120), `pytest` for tests
- **Commits**: Conventional commits (enforced by commit-msg hook)
- **Pre-commit**: Runs all checks + vendor sync verification
- **No absolute paths**: Use repo-relative paths; only `config/environment.yaml` holds machine paths

## Memory & Knowledge Base

- Agreed terms: `agentic/memory/vocabulary.md`
- Agreed decisions: `agentic/memory/decisions.md`
- Changes only via `add-memory` / `add-kb` skills
- Knowledge Base: `.kb/` (separate git repo with `inbox/`, `raw/`, `wiki/`, `outputs/`)

## Pull Requests

- Fill the PR template (includes `review-component` result section)
- CI runs: `check.yml` (lint, test, format) + `review.yml` (component review gate)
- No direct pushes to `main` — always via PR

## Questions?

Open a **Question/Help** issue or check the [wiki](https://github.com/oneo4-tech/aksa/wiki) (when enabled).
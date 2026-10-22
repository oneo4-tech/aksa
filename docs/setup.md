# Setup

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- git
- GitHub CLI (`gh`) — for factory operations

## Installation

```bash
# Clone
git clone https://github.com/oneo4-tech/aksa.git
cd aksa

# Install Python deps & dev tools
uv sync

# Environment
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

# Git hooks (pre-commit checks, pre-push guard for main)
git config core.hooksPath .githooks
```

## External Resources

aksa uses three external git repositories (symlinked at repo root):

| Symlink | Purpose | Managed By |
|---------|---------|------------|
| `.kb/` | Knowledge Base (wiki, inbox, raw, outputs) | `link_external.py`, `kb_index.py` |
| `.projects/` | Project workspace | `link_external.py` |
| `.worktrees/` | Git worktrees for parallel work | `new_worktree.py` |

Configure machine-specific paths in `config/environment.yaml` (the **only** file with absolute paths), then:

```bash
# Create symlinks
uv run agentic/scripts/link_external.py

# Verify
uv run agentic/scripts/link_external.py --check
```

## Vendor Sync

Sync skills to your editor/agent:

```bash
# Claude Code + OpenCode/Codex/Gemini/Copilot
uv run agentic/scripts/sync_vendors.py claude codex

# Verify
uv run agentic/scripts/sync_vendors.py --check
```

## Knowledge Base Index

Build the wiki index from frontmatter:

```bash
uv run agentic/scripts/kb_index.py

# Verify
uv run agentic/scripts/kb_index.py --check
```

## Worktrees (Parallel Work)

Create a worktree for a branch (sets up symlinks + vendor folders):

```bash
uv run agentic/scripts/new_worktree.py feature/my-feature
cd ../.worktrees/feature-my-feature
# Work independently, same setup
```

## Verification

```bash
# All checks (run by pre-commit & CI)
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Editor Integration

| Editor | Setup |
|--------|-------|
| **Claude Code** | Skills at `.claude/skills/` (auto-synced) |
| **OpenCode** | Skills at `.agents/skills/` (auto-synced) |
| **VS Code** | `.vscode/` has workspace settings & tasks |
| **Other** | Point to `.agents/skills/` or `.claude/skills/` |
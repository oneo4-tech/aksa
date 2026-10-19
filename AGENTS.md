# AKSA

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory.

Instructions for AI agents working in this repository.

## Always-on rules

- **Repository root:** Work from the repository root so repository guidance and hooks apply.
- **Domain records:** Treat `agentic/memory/vocabulary.md` and `agentic/memory/decisions.md` as authoritative. Use agreed terms; do not add terms or reverse active decisions without the owner's agreement and the documented change process.
- **External resources:** reach them only through their gitignored repo-root symlinks: `.kb` (external knowledge base), `.projects` (project workspace), `.worktrees` (git worktrees). Do not commit their contents. Their targets live in `agentic/config/environment.yaml`; run `uv run agentic/scripts/link_external.py` to create or repair the links.
- **Paths:** no absolute or machine-specific paths anywhere in the repository except `agentic/config/environment.yaml`. Use repository-relative paths and the symlinks above.
- **Worktrees:** create every git worktree under `.worktrees/`.
- **Writing style:** Prefer concise wording and quality over development cost. Do not use em dashes in responses or written artifacts.

## Rule index

Read a rule when its condition applies. Keep this index aligned with the rule files.

- `agentic/rules/agentic-design.md`: read before creating, materially changing, placing, or reviewing an agentic component. It defines component boundaries, placement, and review expectations.

## Repository map

- `.vscode/`: workspace settings, extensions, and tasks.
- `agentic/`: agentic components and their shared guidance.
  - `config/`: environment settings; `environment.yaml` holds all external absolute paths.
  - `agents/`: specialized agents, when present.
  - `memory/`: internal decisions and agreed vocabulary.
  - `rules/`: persistent, topic-specific guidance.
  - `scripts/`: deterministic and reusable operations.
  - `skills/`: task-specific procedures, organized by category.
  - `templates/`: starting structures for components.
- `tests/`: pytest tests for `agentic/scripts/`; run `uv run pytest`.
- `.kb`, `.projects`, `.worktrees`: gitignored symlinks to external resources; contents are not stored in this repository.
- `pyproject.toml` and `uv.lock`: Python project metadata and locked dependencies.

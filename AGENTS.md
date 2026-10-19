# AKSA

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory.

This file is the root rule (D-007), always loaded. It holds the rules every agent always follows, a map of the repository, and where to find context on demand.

## Always-on rules

- **Repository root:** work from the repository root so guidance, hooks, and relative paths resolve.
- **Agreed records:** use terms as defined in `agentic/memory/vocabulary.md` and follow active decisions in `agentic/memory/decisions.md`. Do not add terms or reverse decisions without the owner's agreement and the change process at the top of each file.
- **Memory and knowledge:** retrieve facts about aksa with `get-memory` and domain knowledge with `get-kb`; change them only through their add, review, and repair skills (`agentic/rules/knowledge.md`). Vendor auto-memory holds personal preferences only (D-019).
- **Components:** before creating, changing, or reviewing a rule, skill, agent, memory, script, or template, read `agentic/rules/components.md`. Accept the change only after the `review-component` skill passes.
- **Paths:** no absolute or machine-specific paths anywhere except `config/environment.yaml` (D-012). Use repository-relative paths and the external resource symlinks.
- **External resources:** reach `.kb`, `.projects`, and `.worktrees` only through their repo-root symlinks, and never commit their contents. Create every git worktree under `.worktrees/`.
- **Secrets:** keys live in the gitignored `.env`. Never print, copy, or commit their values; `.env.example` lists names only.
- **Checks:** before committing, `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` must pass; the pre-commit hook and CI run the same. After adding or renaming a skill, run `uv run agentic/scripts/sync_vendors.py claude codex`.
- **Writing style:** concise wording; quality over development cost; no em dashes in responses or written artifacts.

## Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs. Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity first

Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that wasn't requested.
- No error handling for impossible scenarios; handle real failures explicitly.
- If 200 lines could be 50, rewrite it.
- Ask: "Would a senior engineer call this overcomplicated?" If yes, simplify.

## Repository map

- `AGENTS.md`: this root rule. `README.md`: human setup and checks.
- `agentic/`: the agentic components.
  - `rules/`: topic-specific rules, indexed below.
  - `skills/<category>/<skill>/`: task procedures, synced to vendor folders (`.claude/skills` for Claude; `.agents/skills` for Codex, Gemini, Copilot, and OpenCode).
  - `agents/`: specialized agents, when present.
  - `memory/`: agreed vocabulary, active decisions, and superseded decisions.
  - `scripts/`: deterministic operations shared across components.
  - `templates/`: starting structures for rules, skills, and agents.
- `config/`: repository settings read by scripts; `environment.yaml` maps the external symlinks to this machine.
- `tests/`: pytest tests for the scripts and repository invariants.
- `.githooks/`: tracked hooks; enable once per clone with `git config core.hooksPath .githooks`.
- `.github/workflows/`: CI running the pre-commit checks.
- `.claude/settings.json`: shared Claude permissions and the session-start sync check.
- `.vscode/`: workspace settings, extensions, and agent CLI tasks.
- `.kb`, `.projects`, `.worktrees`: gitignored symlinks to the external Knowledge Base (its own git repository), project workspace, and git worktrees.
- `pyproject.toml`, `uv.lock`: Python project metadata and locked dependencies.

## On-demand context

Load each item when its condition applies, not up front.

### Rules

- `agentic/rules/components.md`: creating, changing, placing, or reviewing any component.
- `agentic/rules/knowledge.md`: retrieving from, adding to, reviewing, or repairing Memory or the Knowledge Base.

### Memory

- `agentic/memory/vocabulary.md`: when a term's meaning matters or a new term seems needed.
- `agentic/memory/decisions.md`: before a change that may touch an agreed decision; grep by area.
- `agentic/memory/decisions-history.md`: only to learn why a decision changed.
- `.kb/index.md`: the entry point to trusted domain knowledge; read it before any `.kb` page.

### Skills and templates

- Skills are offered by name through the vendor folders; their sources are in `agentic/skills/`.
- Start a new rule, skill, or agent from its file in `agentic/templates/`.

### Scripts

- `agentic/scripts/link_external.py`: create or repair the external symlinks from `config/environment.yaml`; `--check` verifies.
- `agentic/scripts/sync_vendors.py`: sync skills to vendor folders; `--check` verifies.
- `agentic/scripts/kb_index.py`: rebuild `.kb/index.md` from wiki page frontmatter; `--check` validates.

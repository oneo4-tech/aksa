# AKSA

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory.

This file is the root rule (D-007), always loaded. It holds the rules every agent always follows, a map of the repository, and where to find context on demand.

## Always-on rules

- **Repository root:** work from the repository root so guidance, hooks, and relative paths resolve.
- **Agreed records:** use terms as defined in `agentic/memory/vocabulary.md` and follow active decisions in `agentic/memory/decisions.md`. Do not add terms or reverse decisions without the owner's agreement and the change process at the top of each file. When a request conflicts with an active decision, name the decision and ask before building.
- **Memory and knowledge:** retrieve facts about aksa with `get-memory` and domain knowledge with `get-kb`; change them only through their add, review, and repair skills (`agentic/rules/knowledge.md`). Vendor auto-memory holds personal preferences only (D-019).
- **Components:** before creating, changing, or reviewing a rule, skill, agent, memory, script, or template, read `agentic/rules/components.md`. Accept the change only after the `review-component` skill passes.
- **Software work:** every change to code or components runs as a Software Factory run, started or resumed with `run-factory` (`agentic/rules/factory.md`); a release runs through `release-version` (D-038).
- **Paths:** no absolute or machine-specific paths anywhere except `config/environment.yaml` (D-012). Use repository-relative paths and the external resource symlinks.
- **External resources:** reach `.kb`, `.projects`, and `.worktrees` only through their repo-root symlinks, and never commit their contents. Create every git worktree with `uv run agentic/scripts/new_worktree.py <branch>`, which places it under `.worktrees/` and sets up its links and vendor folders.
- **Secrets:** keys live in the gitignored `.env`. Never print, copy, or commit their values; `.env.example` lists names only.
- **Checks:** `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` must pass before committing. Before each commit, run `uv run ruff format .` and `uv run ruff check --fix .`, which fix most failures. The pre-commit hook runs the checks and the vendor sync check on every commit, and CI on every push, so run the checks by hand only while fixing a failure or when a skill's procedure runs them, such as `review-component`. After adding or renaming a skill, run `uv run agentic/scripts/sync_vendors.py claude codex`. A pull request that changes components needs its **review-component result** section to name every changed component; CI checks it, and `uv run agentic/scripts/check_pr_review.py origin/main --body-file <file>` checks a draft body locally.
- **Writing style:** concise wording; quality over development cost; no em dashes in responses or written artifacts.

## Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs. Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- When the owner is not present: guess a choice that is cheap to undo and list it under "Decisions for the owner" in the report and the pull request description; keep it there until the owner answers. Block on a choice that is hard to undo.
- Always ask first, even when it is cheap to undo, before overriding an earlier explicit owner instruction or changing what others see: pull request or issue text, other people's branches, `main`, and merges. Two things need no approval: pushing to the session's own feature branch, and keeping its pull request's **review-component result** and **Decisions for the owner** sections current. In a factory run, landing verified tasks on the run's integration branch and changing its own factory issue need no approval either (D-028).

## Simplicity first

Write the minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that wasn't requested.
- No error handling for impossible scenarios; handle real failures explicitly.
- If 200 lines could be 50, rewrite it.
- Ask: "Would a senior engineer call this overcomplicated?" If yes, simplify.

## Repository map

- `AGENTS.md`: this root rule. `README.md`: human setup and checks. `CHANGELOG.md`: release notes, written only by `release-version` from the first release on.
- `agentic/`: the agentic components.
  - `rules/`: topic-specific rules, indexed below.
  - `skills/<category>/<skill>/`: task procedures, synced to vendor folders (`.claude/skills` for Claude; `.agents/skills` for Codex, Gemini, Copilot, and OpenCode).
  - `agents/`: specialized agents, when present.
  - `memory/`: agreed vocabulary, active decisions, and superseded decisions.
  - `scripts/`: deterministic operations shared across components.
  - `templates/`: starting structures for rules, skills, and agents.
- `config/`: repository settings read by scripts; `environment.yaml` maps the external symlinks to this machine, and `factory.yaml` holds the Software Factory labels and type prefixes.
- `tests/`: pytest tests for the scripts and repository invariants.
- `.githooks/`: tracked hooks, the pre-commit checks and the pre-push guard for `main`; enable once per clone with `git config core.hooksPath .githooks`.
- `.github/workflows/`: CI running the pre-commit checks (`check.yml`) and the pull request review check (`review.yml`). `.github/pull_request_template.md`: pull request sections, including the `review-component` result.
- `.claude/settings.json`: shared Claude permissions and the session-start sync check.
- `.vscode/`: workspace settings, extensions, and agent CLI tasks.
- `.kb`, `.projects`, `.worktrees`: gitignored symlinks to the external Knowledge Base (its own git repository), project workspace, and git worktrees.
- `pyproject.toml`, `uv.lock`: Python project metadata and locked dependencies.

## On-demand context

Load each item when its condition applies, not up front.

### Rules

- `agentic/rules/coding.md`: writing, changing, or reviewing code or tests.
- `agentic/rules/components.md`: creating, changing, placing, or reviewing any component.
- `agentic/rules/factory.md`: working on a factory run: its factory issue, any of its stages, or any `factory` skill.
- `agentic/rules/git.md`: creating a branch, worktree, commit, or pull request, or merging.
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
- `agentic/scripts/new_worktree.py`: create a git worktree under `.worktrees/` with its links and vendor folders set up.
- `agentic/scripts/check_pr_review.py`: in CI, fail a pull request that changes components without a `review-component` result.
- `agentic/scripts/kb_index.py`: rebuild `.kb/index.md` from wiki page frontmatter; `--check` validates.
- `agentic/scripts/factory_issue.py`: the only writer of factory issue labels and bodies; `status` reads a run, `labels` syncs the label set.

# AKSA

`aksa` (Sanskrit for central axis) is an AI workflow operating system with an agent harness and software factory.

This file is the root rule (D-007), always loaded. It holds the binding rules every agent always follows, agent principles for guidance, a map of the repository, and where to find context on demand.

## Binding Rules (always enforced)

- **Repository root:** work from the repository root so guidance, hooks, and relative paths resolve.
- **Agreed records:** use terms from `agentic/memory/vocabulary.md` and decisions from `agentic/memory/decisions.md`; change them only through their agreed process.
- **Memory and knowledge:** retrieve with `get-memory`/`get-kb`; change only via `add-memory`, `add-kb`, `review-kb`, `repair-kb` (`agentic/rules/knowledge.md`).
- **Components:** before creating/changing/reviewing any component, read `agentic/rules/components.md`; accept only after `review-component` passes.
- **Software work:** every change to code or components runs as a factory run (`run-factory` / `release-version`) — `agentic/rules/factory.md` (D-038).
- **Factory intake:** start or resume a run only for explicit tracked-software change intent or a direct factory request, including naming an issue or asking to view/continue the queue. Read-only analysis, explanations, and temporary deliverables are not Software Work Requests and must not create an issue.
- **Paths:** no absolute/machine paths except `config/environment.yaml` (D-012); use repo-relative paths and symlinks.
- **External resources:** reach `.kb`, `.projects`, `.worktrees` only through repo-root symlinks; never commit their contents; create worktrees via `uv run agentic/scripts/new_worktree.py` (D-012, D-039).
- **Secrets:** keys in `.env` (gitignored); never print/copy/commit; `.env.example` lists names only.
- **Checks:** `uv run pytest`, `ruff check`, `ruff format --check` must pass before commit; pre-commit runs them; run by hand only when fixing or per skill procedure.
- **Temporary files:** write temporary files to `.temp/` (gitignored); never create `*_test.txt`, `test_*.txt`, or similar in the repo root.
- **Writing style:** concise wording, sacrifice grammer if needed, avoid verbiage; quality over development cost; no em dashes.

## Agent Principles (guidance, not enforced)

### Think before coding
State assumptions; present alternatives; push back on complexity; stop when unclear; guess cheap-to-undo choices when owner absent (list under "Decisions for the owner"); ask before overriding owner instructions or shared artifacts (PRs, issues, main). In factory runs: landing verified tasks and updating the factory issue need no approval (D-040).

### Simplicity first
Minimum code that solves the problem. No speculative features/abstractions/config. Handle real failures explicitly. Rewrite 200→50 lines. "Would a senior engineer call this overcomplicated?"

## Repository Map

- `AGENTS.md`: this root rule. `README.md`: human setup and checks. `CHANGELOG.md`: release notes, written only by `release-version` from the first release on.
- `agentic/`: the agentic components.
  - `rules/`: topic-specific rules, indexed below.
  - `skills/<category>/<skill>/`: task procedures, synced to vendor folders (`.claude/skills` for Claude; `.agents/skills` for Codex, Gemini, Copilot, and OpenCode).
  - `agents/`: specialized agents, when present.
  - `memory/`: agreed vocabulary, active decisions, and superseded decisions.
  - `scripts/`: deterministic operations shared across components.
  - `templates/`: starting structures for rules, skills, and agents.
- `config/`: repository settings read by scripts; `environment.yaml` maps the external symlinks to this machine, `factory.yaml` holds the Software Factory labels and type prefixes, and `content.yaml` the content labels, stages, and gates.
- `tests/`: pytest tests for the scripts and repository invariants.
- `.githooks/`: tracked hooks, the pre-commit checks and the pre-push guard for `main`; enable once per clone with `git config core.hooksPath .githooks`.
- `.github/workflows/`: CI running the pre-commit checks (`check.yml`) and the pull request review check (`review.yml`). `.github/pull_request_template.md`: pull request sections, including the `review-component` result.
- `.claude/settings.json`: shared Claude permissions and the session-start sync check.
- `.vscode/`: workspace settings, extensions, and agent CLI tasks.
- `.kb`, `.projects`, `.worktrees`: gitignored symlinks to the external Knowledge Base (its own git repository), project workspace, and git worktrees.
- `pyproject.toml`, `uv.lock`: Python project metadata and locked dependencies.

## On-Demand Context

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

### Skills and Templates

- Skills are offered by name through the vendor folders; their sources are in `agentic/skills/`.
- Start a new rule, skill, or agent from its file in `agentic/templates/`.

### Scripts

- `agentic/scripts/link_external.py`: create or repair the external symlinks from `config/environment.yaml`; `--check` verifies.
- `agentic/scripts/sync_vendors.py`: sync skills to vendor folders; `--check` verifies.
- `agentic/scripts/new_worktree.py`: create a git worktree under `.worktrees/` with its links and vendor folders set up.
- `agentic/scripts/check_pr_review.py`: in CI, fail a pull request that changes components without a `review-component` result.
- `agentic/scripts/kb_index.py`: rebuild `.kb/index.md` from wiki page frontmatter; `--check` validates.
- `agentic/scripts/factory_issue.py`: the only writer of factory issue labels and bodies; `status` reads a run, `labels` syncs the label set.
- `agentic/scripts/github_issues.py`: the thin `gh` layer for issues and labels, imported by the issue scripts; not a command.
- `agentic/scripts/content_issue.py`: the only writer of content issue labels and bodies; `new` files a video, `stage` and `gate` move it, `status` reads one or a channel's queue.
- `agentic/scripts/youtube_channel.py`: load a channel's `channel.yaml` and `style-guide.md` from `.projects/content/yt-<channel>/`; `check` validates, `init` sets up its media-ignoring git workspace.
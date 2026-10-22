# aksa

**AI workflow operating system** with an agent harness and software factory.

`aksa` (Sanskrit for *central axis*) keeps agentic components — rules, skills, agents, memory, scripts, templates — in one vendor-neutral place and syncs them to **Claude Code**, **OpenCode**, **Codex**, **Gemini CLI**, and **Copilot**.

---

## Why aksa?

| Problem | aksa's Answer |
|---------|---------------|
| Agents drift, forget context, reinvent patterns | Persistent **memory** (vocabulary + decisions) + **knowledge base** (wiki) |
| Every tool has its own config format | **Single source** in `agentic/`, synced to all vendors via `sync_vendors.py` |
| Ad-hoc changes, no review gate | **Software Factory** with gated stages (triage → concept → define → spec → plan → build → ship) |
| Components lack standards | `agentic/rules/components.md` + `review-component` skill enforced in CI |

---

## Quick Start

```bash
# 1. Install deps (requires uv + git)
uv sync
cp .env.example .env          # add your API keys
git config core.hooksPath .githooks

# 2. Link external resources (Knowledge Base, projects, worktrees)
uv run agentic/scripts/link_external.py

# 3. Sync skills to your editors
uv run agentic/scripts/sync_vendors.py claude codex

# 4. Build Knowledge Base index
uv run agentic/scripts/kb_index.py

# 5. Run checks
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

---

## Repository Map

```
aksa/
├── AGENTS.md              # Root rule — agent entry point & repo map
├── README.md              # This file
├── CHANGELOG.md           # Release notes (from release-version)
├── CONTRIBUTING.md        # How to contribute
├── LICENSE                # MIT
├── mkdocs.yml             # Documentation config
├── pyproject.toml         # Python project (uv)
├── uv.lock                # Locked dependencies
├── .env.example           # Environment template
├── .gitignore
├── .githooks/             # Pre-commit, pre-push, commit-msg hooks
├── .github/
│   ├── workflows/         # CI: check, review, CodeQL, docs
│   ├── dependabot.yml     # Automated dependency updates
│   └── ISSUE_TEMPLATE/    # Factory request, bug, question
├── agentic/               # Core agentic components
│   ├── agents/            # Specialized agents
│   ├── memory/            # vocabulary.md, decisions.md, decisions-history.md
│   ├── rules/             # coding, components, factory, git, knowledge
│   ├── scripts/           # Deterministic ops (link, sync, factory_issue, etc.)
│   ├── skills/            # Task procedures (core/, factory/, auxiliary/)
│   └── templates/         # Starters for rules, skills, agents
├── config/
│   ├── environment.yaml   # Machine-specific paths (only absolute paths allowed)
│   └── factory.yaml       # Factory labels & type prefixes
├── docs/                  # MkDocs source (this site)
├── tests/                 # Pytest for scripts & invariants
└── .kb, .projects, .worktrees/  # Symlinks to external git repos (gitignored)
```

---

## Core Concepts

### Software Factory
All tracked changes run as a **factory run** — an issue that moves through stages with gates requiring owner approval. See [Factory](factory.md).

### Memory & Knowledge Base
- **Vocabulary** (`agentic/memory/vocabulary.md`): agreed terms
- **Decisions** (`agentic/memory/decisions.md`): active architectural choices
- **Knowledge Base** (`.kb/`): wiki with `inbox/`, `raw/`, `wiki/`, `outputs/`
- Changes only via `add-memory` / `add-kb` skills

### Components
Rules, skills, agents, scripts, templates — each has a standard structure and must pass `review-component`.

### Vendor Sync
One command syncs `agentic/skills/` to:
- `.claude/skills/` (Claude Code)
- `.agents/skills/` (OpenCode, Codex, Gemini, Copilot)

---

## Links

- [Setup Guide](setup.md)
- [Architecture](architecture.md)
- [Software Factory](factory.md)
- [Rules Reference](rules.md)
- [Skills Catalog](skills.md)
- [Memory & Knowledge Base](knowledge.md)
- [Scripts Reference](scripts.md)
- [Contributing](../CONTRIBUTING.md)

---

## License

MIT — see [LICENSE](../LICENSE).
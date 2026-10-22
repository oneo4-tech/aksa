# Rules Reference

Rules are binding constraints in `agentic/rules/`. Every agent loads `AGENTS.md` (root rule) which references these.

## Rule Files

| File | Purpose | When Loaded |
|------|---------|-------------|
| `coding.md` | Code style, testing, patterns | Writing/changing/reviewing code |
| `components.md` | Component structure, review process | Creating/changing/reviewing components |
| `factory.md` | Software Factory stages, gates, labels | Any factory run |
| `git.md` | Branching, commits, PRs, merging | Git operations |
| `knowledge.md` | Memory & KB retrieval, add/review/repair | Using memory or KB |

## Loading Rules

Rules are **on-demand** — load only when the condition applies (not upfront). The root rule `AGENTS.md` lists each with its trigger condition.

## Component Rules (`components.md`)

Defines standards for all agentic components:

| Component Type | Location | Template |
|----------------|----------|----------|
| Rule | `agentic/rules/` | `agentic/templates/rule.md` |
| Skill | `agentic/skills/{core,factory,auxiliary}/` | `agentic/templates/skill.md` |
| Agent | `agentic/agents/` | `agentic/templates/agent.md` |
| Memory | `agentic/memory/` | — |
| Script | `agentic/scripts/` | — |
| Template | `agentic/templates/` | — |

### Review Process

Before accepting any new/changed component:
1. Read `agentic/rules/components.md`
2. Run `review-component` skill
3. CI enforces this on PRs (`.github/workflows/review.yml`)

## Memory Rules (`knowledge.md`)

- **Vocabulary**: `agentic/memory/vocabulary.md` — agreed terms
- **Decisions**: `agentic/memory/decisions.md` — active decisions
- **History**: `agentic/memory/decisions-history.md` — superseded decisions
- **KB**: `.kb/wiki/` — domain knowledge (separate repo)

### Retrieval
- `get-memory` — lookup term/decision
- `get-kb` — query Knowledge Base (reads index first)

### Changes
- `add-memory` — new/changed term or decision
- `add-kb` — capture domain knowledge (writes to inbox)
- `review-kb` — approve inbox items into wiki
- `repair-kb` / `repair-memory` — periodic cleanup

## Factory Rules (`factory.md`)

See [Factory](factory.md) for stages, gates, labels, and skills.

## Git Rules (`git.md`)

- Conventional commits (enforced by commit-msg hook)
- Branch naming: `<type>/<short-desc>` (e.g., `feat/factory-task-validation`)
- PR required for `main` (branch protection)
- Worktrees via `new_worktree.py`
- No rebasing (merge conflicts resolved via `resolve-merge-conflicts`)

## Coding Rules (`coding.md`)

- Python: `ruff` (line-length 120), `pytest`
- Type hints where useful
- No speculative abstractions
- Handle real failures explicitly
- Simplicity: "Would a senior engineer call this overcomplicated?"

## Adding a New Rule

1. Copy `agentic/templates/rule.md` → `agentic/rules/<name>.md`
2. Follow structure: purpose, when loaded, binding rules, guidance
3. Add to `AGENTS.md` "On-Demand Context" section
4. Run `review-component` before committing
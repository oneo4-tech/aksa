# Architecture

## High-Level

```
┌─────────────────────────────────────────────────────────────┐
│                        aksa Repository                       │
├─────────────────────────────────────────────────────────────┤
│  AGENTS.md  ──► Root rule, repo map, binding rules          │
├─────────────────────────────────────────────────────────────┤
│  agentic/                                                    │
│  ├── agents/        # Specialized agents (when present)     │
│  ├── memory/        # vocabulary.md, decisions.md           │
│  ├── rules/         # Topic-specific rules (coding, etc.)   │
│  ├── scripts/       # Deterministic operations              │
│  ├── skills/        # Task procedures (core/factory/aux)    │
│  └── templates/     # Starters for new components           │
├─────────────────────────────────────────────────────────────┤
│  config/                                                    │
│  ├── environment.yaml  # Machine paths (only absolute paths)│
│  └── factory.yaml      # Factory labels & type prefixes     │
├─────────────────────────────────────────────────────────────┤
│  External (symlinked, separate git repos)                   │
│  ├── .kb/           # Knowledge Base                        │
│  ├── .projects/     # Project workspace                     │
│  └── .worktrees/    # Parallel git worktrees                │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale | Reference |
|----------|-----------|-----------|
| **Single source for components** | Vendor-neutral; sync to all tools | `agentic/rules/components.md` |
| **Software Factory for all changes** | Gated stages, owner approval, traceability | `agentic/rules/factory.md` |
| **Memory = vocabulary + decisions** | Explicit, reviewable, versioned | `agentic/rules/knowledge.md` |
| **Knowledge Base as separate repo** | Independent history, can be shared | `agentic/rules/knowledge.md` |
| **Worktrees for parallel work** | Isolated environments, same setup | `agentic/scripts/new_worktree.py` |
| **No absolute paths in repo** | Portability; only `config/environment.yaml` | `AGENTS.md` (D-012) |
| **Pre-commit + CI parity** | Catch issues early, enforce standards | `.githooks/`, `.github/workflows/check.yml` |
| **Component review gate** | Quality bar for agentic components | `.github/workflows/review.yml` |

## Data Flow

```
User Request
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Factory    │────►│  Concept    │────►│   Define    │
│  Intake     │     │  (G0)       │     │  (G1)       │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Spec     │────►│    Plan     │
                    │   (G2)      │     │   (G3)      │
                    └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Build    │────►│    Ship     │
                    │  (tasks)    │     │  (PR merge) │
                    └─────────────┘     └─────────────┘
```

## Extension Points

1. **New Rules**: Add to `agentic/rules/` + follow `components.md`
2. **New Skills**: Add to `agentic/skills/{core,factory,auxiliary}/`
3. **New Agents**: Add to `agentic/agents/`
4. **New Scripts**: Add to `agentic/scripts/` + tests in `tests/`
5. **New Templates**: Add to `agentic/templates/`
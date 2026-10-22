# Memory & Knowledge Base

Two distinct systems for persistent, reviewable knowledge.

---

## Memory (`agentic/memory/`)

**Purpose**: Agreed terms and decisions that govern the project.

| File | Content | Updated By |
|------|---------|------------|
| `vocabulary.md` | Defined terms with canonical meanings | `add-memory` |
| `decisions.md` | Active architectural/process decisions | `add-memory` |
| `decisions-history.md` | Superseded decisions with rationale | `add-memory` (on reversal) |

### Vocabulary Entry
```markdown
## term-name
**Definition**: Precise meaning in aksa context.
**See also**: related-term, other-term
**Decisions**: D-XXX, D-YYY
```

### Decision Entry
```markdown
## D-XXX: Short Title
**Status**: Active | Superseded by D-YYY
**Area**: factory | git | components | ...
**Decision**: What was decided.
**Rationale**: Why.
**Alternatives considered**: ...
**Implications**: ...
```

### Retrieval
```bash
# Via skills (preferred)
get-memory "term-name"
get-memory "D-XXX"

# Direct files
cat agentic/memory/vocabulary.md
cat agentic/memory/decisions.md
```

### Changes
Only via `add-memory` skill:
- New term / clarified definition
- New decision / reversal / supersession
- Records change in `decisions-history.md` automatically

---

## Knowledge Base (`.kb/`)

**Purpose**: Domain knowledge, research, references — separate git repo.

### Structure
```
.kb/
├── inbox/      # New items awaiting review (add-kb writes here)
├── raw/        # Source documents (PDFs, URLs, exports)
├── wiki/       # Approved, curated pages (review-kb moves here)
└── outputs/    # Research reports, syntheses (research-topic writes here)
```

### Wiki Page Format
```markdown
---
title: Page Title
tags: [tag1, tag2]
updated: 2026-10-22
---

# Page Title

Content...
```

### Index
`.kb/index.md` — auto-generated from wiki frontmatter by `kb_index.py`.

### Workflow
```
add-kb          review-kb           kb_index.py
    │               │                    │
    ▼               ▼                    ▼
.inbox/  ──approve──► .wiki/  ──rebuild──► .kb/index.md
    │               │
    │            drop/skip
    ▼               ▼
  (stays)       (discarded)
```

### Skills
| Skill | Action |
|-------|--------|
| `add-kb` | Write item to `inbox/` + source to `raw/` |
| `review-kb` | Owner walkthrough: approve→wiki, drop, or skip |
| `get-kb` | Query: reads index → fetches relevant wiki pages |
| `research-topic` | Deep research → writes to `outputs/` |
| `repair-kb` | Cleanup: dedupe, reorganize, fix index |

### External Repo
`.kb/` is a **separate git repository** (symlinked via `link_external.py`). Its contents are never committed to aksa.

---

## When to Use Which

| Need | Use |
|------|-----|
| "What does X mean in aksa?" | `get-memory` → vocabulary |
| "Why did we choose Y?" | `get-memory` → decisions |
| "Research best practices for Z" | `research-topic` → KB outputs |
| "Save this article for later" | `add-kb` → inbox |
| "Curate approved references" | `review-kb` → wiki |
| "Find all pages about testing" | `get-kb` → queries index/wiki |
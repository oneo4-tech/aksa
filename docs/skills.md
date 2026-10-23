# Skills Catalog

Skills are task procedures in `agentic/skills/`. They're synced to vendor folders:
- `.claude/skills/` — Claude Code
- `.agents/skills/` — OpenCode, Codex, Gemini CLI, Copilot

## Categories

### Core Skills (`agentic/skills/core/`)
Fundamental agent capabilities.

| Skill | Purpose |
|-------|---------|
| `add-kb` | Capture domain knowledge to KB inbox |
| `add-memory` | Record agreed term/decision |
| `build-prototype` | Throwaway code for design questions |
| `clarify-response` | Re-explain in Simplified Technical English |
| `create-handoff` | Write self-contained handoff note |
| `define-concept` | Settle decisions, feasibility (G0) |
| `define-requirement` | Write requirement + acceptance criteria (G1) |
| `define-spec` | Design spec: approach, interfaces, tests (G2) |
| `diagnose-bug` | Reproduce, narrow, root cause |
| `find-skills` | Discover/install skills |
| `get-kb` | Query Knowledge Base |
| `get-memory` | Lookup vocabulary/decisions |
| `import-memory` | Import memory from other AI assistants |
| `plan-tasks` | Break spec into vertical task slices (G3) |
| `repair-kb` | Clean up KB wiki |
| `repair-memory` | Clean up memory files |
| `research-topic` | Investigate, gather facts, write foundations |
| `review-component` | Pass/fail on component standards |
| `review-kb` | Walk owner through inbox items |
| `run-factory` | Start/resume factory run (orchestrator) |
| `setup-writing-style` | Learn user's voice from messages/docs |
| `triage-request` | Route factory request or close |

### Factory Skills (`agentic/skills/factory/`)
Software Factory stage execution.

| Skill | Stage | Gate |
|-------|-------|------|
| `implement-task` | Build | — |
| `verify-task` | Build | — |
| `ship-change` | Ship | — |
| `release-version` | Post-ship | — |

### Content Skills (`agentic/skills/content/`)
Content production pipelines outside software delivery (D-041).

| Skill | Purpose |
|-------|---------|
| `run-youtube` | File, resume, or list a channel's videos (`youtube-producer` agent) |
| `scan-video-ideas` | Weekly scan into scored idea cards with competing YouTube videos; one video's card at stage `idea` |
| `research-video` | One video's research from primary sources, with each claim's quote checked on its live page (`citations.json`, required by gate 2) |
| `write-video-script` | One video's `script.json`: scenes in a rotating structure (challenge-first, incident story, myth buster), sized for five to ten minutes or a thirty to sixty second Short, checked against the writing rules and citations |
| `build-video-demo` | One video's runnable demo, passing tests, and VHS tape in `<n>-<slug>/` of the channel's public demo repository clone; returns the description link; pushes or creates the repository only on the owner's yes |
| `narrate-video` | One video's narration, scene by scene, with Gemini 3.8 Flash TTS in the channel's voice, style, pace, and pronunciation into `narration/NN.wav`, refused when a whisper transcript shows spoken markup or misses the script's words |

### Auxiliary Skills (`agentic/skills/auxiliary/`)
Specialized utilities.

| Skill | Purpose |
|-------|---------|
| `built-in-browser` | Use Claude's built-in browser pane |
| `chrome-browser` | Use Claude in Chrome extension |
| `computer-use` | Desktop control via Claude |
| `deep-research` | Multi-source research synthesis |
| `docs` | Create/edit shared documents (Google Docs, Word) |
| `docx` | Word document manipulation |
| `morning` | Render morning brief as HTML |
| `opencode` | OpenCode-specific help |
| `pdf` | PDF operations |
| `pptx` | PowerPoint manipulation |
| `report` | Report OpenCode issues |
| `retrospect-session` | Audit transcript for AI slop/friction |
| `skill-creator` | Create/modify/measure skills |
| `xlsx` | Spreadsheet operations |

## Using Skills

### As Agent
Skills are invoked by name. The agent loads the skill's instructions and follows its procedure.

### As Human (via Agent)
Ask the agent: *"Use the `define-requirement` skill to write a requirement for X"*

### Skill Structure
Each skill has:
```
agentic/skills/<category>/<skill>/
├── skill.yaml       # Metadata (name, description, triggers)
├── instructions.md  # Procedure (what the agent does)
└── resources/       # Optional templates, scripts, examples
```

## Creating a New Skill

1. Choose category: `core/`, `factory/`, or `auxiliary/`
2. Copy `agentic/templates/skill.md` → `agentic/skills/<cat>/<name>/instructions.md`
3. Create `skill.yaml` with metadata
4. Run `review-component` before committing
5. Sync: `uv run agentic/scripts/sync_vendors.py claude codex`

## Skill Discovery

- `find-skills` — search installable skills
- `get-kb` — research if skill exists for a task
- Vendor folders (`.claude/skills/`, `.agents/skills/`) list available skills
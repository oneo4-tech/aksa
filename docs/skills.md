# Skills Catalog

Skills are task procedures in `agentic/skills/<category>/<skill-name>/`, synced to vendor folders:

- `.claude/skills/`: Claude Code
- `.agents/skills/`: Codex, Gemini CLI, Copilot, OpenCode

## Categories

Each skill has exactly one category, by primary purpose, from `agentic/rules/components.md`.

### `core`

Foundational operations that fit no more specific domain.

| Skill | Purpose |
|-------|---------|
| `add-kb` | Capture knowledge or a source to the KB inbox |
| `add-memory` | Record an agreed term or decision |
| `get-kb` | Query the Knowledge Base |
| `get-memory` | Look up vocabulary and decisions |
| `repair-kb` | Clean up and reorganize the KB wiki |
| `repair-memory` | Clean up Memory files |
| `review-component` | Pass or mismatches against the component standard |
| `review-kb` | Walk the owner through KB inbox items |

### `productivity`

Personal work organization.

| Skill | Purpose |
|-------|---------|
| `teach-topic` | Teach a topic over sessions with one lesson per session |

### `factory`

The Software Factory lifecycle, from work request to release.

| Skill | Purpose |
|-------|---------|
| `run-factory` | Start or resume a factory run (orchestrator) |
| `triage-request` | Route a work request or close it |
| `define-concept` | Settle decisions and feasibility (G0) |
| `define-requirement` | Write requirement and acceptance criteria (G1) |
| `define-spec` | Approach, interfaces, tests (G2) |
| `plan-tasks` | Slice into ordered tasks (G3) |
| `implement-task` | Build a task test-first |
| `verify-task` | Independent review, then land the task |
| `diagnose-bug` | Reproduce a bug and find its root cause |
| `resolve-merge-conflicts` | Resolve conflicts by what both sides meant |
| `ship-change` | Update, check, and merge the pull request |
| `release-version` | SemVer release, changelog, tag |

### `auxiliary`

Supporting operations that serve any work.

| Skill | Purpose |
|-------|---------|
| `build-prototype` | Throwaway code for one design question |
| `clarify-response` | Re-explain in Simplified Technical English |
| `create-handoff` | Write a self-contained handoff note |
| `research-topic` | Gather cited facts, KB first |
| `retrospect-session` | Audit a transcript for slop and friction |

### `content`

Content creation and publishing workflows.

| Skill | Purpose |
|-------|---------|
| `draft-newsletter` | Draft a newsletter issue from a video, send on the owner's yes |

### `testing`

Software-testing workflows for a freelance engagement's deliverables.

| Skill | Purpose |
|-------|---------|
| `run-testing` | Validate the brief and run the workflows in order |
| `review-requirements` | Ambiguities, missing criteria, and untestable statements with questions |
| `write-test-strategy` | Scope, risks, approach |
| `write-test-plan` | Schedule, roles, environments, deliverables, criteria, plan risks |
| `estimate-test-effort` | Per-workflow effort range, assumptions, and confidence |
| `design-test-cases` | Test cases from the strategy |
| `design-test-data` | Synthetic data sets and fixtures keyed to cases |
| `scaffold-test-framework` | Per-engagement environment, conftest, and page folder |
| `write-api-tests` | Python `pytest` API tests |
| `write-ui-tests` | Playwright for Python UI tests |
| `write-contract-tests` | `jsonschema` checks derived from the OpenAPI `api_spec` |
| `write-performance-tests` | Locust scenarios from the targets and cases |
| `test-mobile-app` | Playwright mobile web tests for the brief's devices |
| `write-bug-report` | One report per defect from evidence |
| `summarise-test-execution` | Summary of execution evidence |

## Using Skills

Agents offer skills by name and follow the loaded procedure. Ask, for example: *"Use `define-requirement` to write a requirement for X"*.

### Skill Structure

```text
agentic/skills/<category>/<skill-name>/
├── SKILL.md      the procedure, with name and description frontmatter
├── references/   files the procedure reads on demand
└── scripts/      deterministic steps, only when it has them
```

Nothing else sits at the top level.

## Creating a New Skill

1. Choose one category: `core`, `productivity`, `factory`, `auxiliary`, `content`, or `testing`.
2. Copy `agentic/templates/skill-template.md` to `agentic/skills/<category>/<skill-name>/SKILL.md` and fill it in.
3. Run `review-component` and resolve every mismatch.
4. Sync: `uv run agentic/scripts/sync_vendors.py claude codex`.

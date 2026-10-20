# Components

Read before creating, materially changing, placing, or reviewing a component. This is the single standard for components; component kinds are defined in `agentic/memory/vocabulary.md` (D-008). Rules marked **[checked]** are enforced by `tests/test_repository.py`; the rest need judgment during review.

## Choose the kind

- **Rule:** behaviour that applies across tasks. Repository-wide always-on rules go in `AGENTS.md`, the root rule (D-007). Topic-specific guidance goes in one file in `agentic/rules/`.
- **Skill:** a repeatable operation for a specific task. Guidance that serves only that skill stays in the skill.
- **Agent:** only when a distinct goal and role must own an outcome. It reuses rules and skills instead of restating them.
- **Memory:** durable shared context about aksa, never procedure; domain knowledge goes to the Knowledge Base (D-015). Vocabulary and decisions change only by the process at the top of each file; memory never silently changes a decision.
- **Script:** deterministic work or common enablement. A script serving one skill or agent stays inside that component.
- **Template:** a starting structure for a component. It standardizes shape; it does not replace this rule.
- External resources (`.kb`, `.projects`, `.worktrees`) are not components. Reach them through their repo-root symlinks, whose targets live only in `config/environment.yaml` (D-012). The Knowledge Base standard is `agentic/rules/knowledge.md`.

## Placement and structure

| Kind | Location | Start from |
|---|---|---|
| Rule | `agentic/rules/<topic>.md`, indexed in `AGENTS.md` **[checked]** | `agentic/templates/rule-template.md` |
| Skill | `agentic/skills/<category>/<skill-name>/SKILL.md` **[checked]** | `agentic/templates/skill-template.md` |
| Agent | `agentic/agents/<agent-name>.md` | `agentic/templates/agent-template.md` |
| Memory | `agentic/memory/` | the file's own header |
| Script | `agentic/scripts/<name>.py`, with tests in `tests/` | none |
| Template | `agentic/templates/<kind>-template.md` | none |

Repository settings that scripts read, such as `config/environment.yaml`, live in `config/` (D-013); scripts read them rather than copying their values.

## Skills

- Category, exactly one, by primary purpose, from this list **[checked]**:
  - `core`: foundational operations that fit no more specific domain.
  - `productivity`: personal work organization.
  - `factory`: the Software Factory lifecycle and its supporting operations.
  - `engineering`: software development, testing, review, and delivery.
  - `auxiliary`: supporting operations that serve any work, such as research, retrospectives, handoffs, clarifications, and prototypes, and fit no domain above.
- A new category needs a definition the owner has agreed, added to this list before any skill uses it.
- `name` matches the directory, is lowercase hyphenated verb-object (D-005), and is unique across categories, since vendors get a flat folder **[checked]**.
- `description` states when to use the skill and the result it produces **[checked: present]**.
- `description` carries when to use the skill; the body has no separate section for it.
- Sections, in order: **Inputs and prerequisites** (including how to handle missing inputs), **Procedure** (ordered, actionable), **Output** (including how to report failures or blocked work), **Constraints** (approvals, scope limits, applicable decisions, routing to other skills), **Done when** (verifiable conditions checked before reporting completion) **[checked: present and ordered]**.
- Folder structure, nothing else at the top level **[checked]**:

  ```text
  agentic/skills/<category>/<skill-name>/
    SKILL.md      the procedure
    references/   files the procedure reads on demand: output templates, subagent briefs, branch guides
    scripts/      deterministic steps of the procedure, only when it has them
  ```

  `SKILL.md` names each supporting file by its path relative to the skill folder, such as `references/<file>.md`, and states when to read it, so it loads only when a step needs it.
- No checker scripts: a skill states the rules its output must meet as **Done when** conditions, not as a script that validates the output.
- After adding or renaming a skill, run `uv run agentic/scripts/sync_vendors.py claude codex`.

## Writing

- Concise, vendor-neutral (D-004), and specific enough to execute reliably.
- Link to rules, decisions, and shared resources instead of copying them. Referenced repository paths and decisions must exist **[checked]**.
- No absolute or machine-specific paths (D-012) **[checked]**.
- No file or folder named after a Windows reserved device name, such as `aux` or `con` (D-021) **[checked]**.
- Surface errors explicitly; no success-shaped fallbacks.

## Acceptance

A created or materially changed component is accepted only after the `review-component` skill passes.

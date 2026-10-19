# Skill authoring

Read when creating, reviewing, or materially changing a skill.

## Placement

- Store each skill at `agentic/skills/<category>/<skill-name>/SKILL.md`.
- Use exactly one category, chosen by the skill's primary purpose:
  - `core`: reusable foundational operations that do not belong to a more specific domain.
  - `productivity`: personal work organization and productivity workflows.
  - `factory`: the Software Factory lifecycle and its supporting operations.
  - `engineering`: software development, testing, review, and delivery operations.
- Skill names are unique across categories: vendors get a flat folder, so the category is dropped when syncing.
- Keep files, scripts, and assets used only by a skill inside its directory. Shared scripts belong in `agentic/scripts/`.

## Required structure

Create each skill from `agentic/templates/skill-template.md`. Retain its required frontmatter and sections, replacing every placeholder. A skill must:

- Have a concise, unique, lowercase hyphenated `name` in verb-object form (D-005) matching its directory name, and a specific `description` stating when to use it and the result it produces.
- State its purpose and activation conditions in **When to use**.
- Define required information, access, and dependencies in **Inputs and prerequisites**, including how to handle missing inputs.
- Provide an ordered, actionable **Procedure** that covers the skill's responsibilities without duplicating other rules or skills.
- Define the expected **Output** or handoff, including how to report failures or blocked work.
- State relevant **Constraints**, such as approval gates, scope limits, prohibited actions, and applicable rules or decisions.

## Writing

Keep instructions concise, vendor-neutral (D-004), and specific enough to execute reliably. Surface errors explicitly; do not hide failures behind defaults or success-shaped fallbacks. Link to authoritative rules, decisions, and shared resources instead of copying their contents.

## After adding or renaming a skill

Run `uv run agentic/scripts/sync_vendors.py <vendors>` so vendor folders pick it up.

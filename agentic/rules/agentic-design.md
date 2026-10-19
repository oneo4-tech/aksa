# Agentic component design

| Component | Description |
|---|---|
| Rule | Persistent behaviour or constraints that shape how an agent works. |
| Skill | A conditional, task-specific operation with steps an agent follows when invoked. |
| Agent | An operator with a goal and role that owns an outcome and uses rules and skills. |
| Memory | Durable context, such as agreed vocabulary, decisions, or trusted knowledge, that agents can consult. It may be stored inside the repository (`agentic/memory/`) or in an external system reached through a repo-root symlink such as `.kb`. |
| Script | Deterministic executable work or common enablement that agents or skills can run. |
| Template | A reusable starting structure that standardizes creation of another component. |
| Config | Environment settings that agents and scripts read, such as external absolute paths. |

## Choose the component

- Put behaviour that should apply across tasks in `AGENTS.md` or a focused file in `agentic/rules/`. Put repository-wide always-on constraints in `AGENTS.md`; keep topic-specific guidance in one rule file and index it in `AGENTS.md`.
- Put a repeatable operation for a specific task in a skill under `agentic/skills/<category>/<skill-name>/`. Categories: `core` for reusable foundational operations that do not belong to a more specific domain; `productivity` for personal work organization and productivity workflows; `factory` for the Software Factory lifecycle and its supporting operations; `engineering` for software development, testing, review, and delivery operations. Choose one category by the skill's primary purpose. Follow the skill authoring standards below and use `agentic/templates/skill-template.md` when creating a skill. Keep guidance that serves only that skill with the skill.
- Create an agent only when a distinct goal and role need to own an outcome. Reuse applicable rules and skills instead of duplicating their instructions.
- Put durable shared context in `agentic/memory/`, not procedural instructions. Keep agreed vocabulary and decisions in their designated files. Change those files only by following the process stated at the top of each file, and never use memory to silently change an agreed decision.
- External systems are resources, not agentic components. Treat `.kb` as an external memory system, `.projects` as an external project workspace, and `.worktrees` as the location for git worktrees. Use their repo-root symlinks as the stable paths; their targets are recorded only in `agentic/config/environment.yaml`. Follow the relevant domain rules for accessing or changing their contents.
- Put common enablement and deterministic work in reusable scripts under `agentic/scripts/`. Keep scripts that serve only one skill or agent bundled within that component so their ownership and lifecycle stay together.
- Put environment settings in `agentic/config/`. `environment.yaml` is the only file allowed to hold absolute or machine-specific paths; every other component uses repository-relative paths. Read config through a script rather than copying its values.
- Put reusable starting structures in `agentic/templates/`. Templates standardize component structure; they do not replace the rules for authoring or reviewing the component.

## Required review

Before creating or materially changing any agentic component, read this document and use it to choose the component and its location. Every creation must be reviewed against these rules before acceptance. The reviewer must confirm that its purpose and ownership fit the chosen component, that it reuses rather than duplicates existing guidance or operations, that its scope and dependencies are clear, and that it respects active decisions and the component's applicable rules. Resolve any mismatch before accepting the component.

## Skill authoring standards

Read this section when creating, reviewing, or materially changing a skill.

### Placement

- Store each skill at `agentic/skills/<category>/<skill-name>/SKILL.md`.
- Use exactly one category: `core`, `productivity`, `factory`, or `engineering`, chosen by the skill's primary purpose.
- Keep files, scripts, and assets used only by a skill inside its directory. Shared scripts belong in `agentic/scripts/`.

### Required structure

Create each skill from `agentic/templates/skill-template.md`. Retain its required frontmatter and sections, replacing every placeholder. A skill must:

- Have a concise, unique, lowercase hyphenated `name` in verb-object form (for example `record-decision`) matching its directory name, and a specific `description` stating when to use it and the result it produces.
- State its purpose and activation conditions in **When to use**.
- Define required information, access, and dependencies in **Inputs and prerequisites**, including how to handle missing inputs.
- Provide an ordered, actionable **Procedure** that covers the skill's responsibilities without duplicating other rules or skills.
- Define the expected **Output** or handoff, including how to report failures or blocked work.
- State relevant **Constraints**, such as approval gates, scope limits, prohibited actions, and applicable rules or decisions.

Keep instructions concise, vendor-neutral, and specific enough to execute reliably. Surface errors explicitly; do not hide failures behind defaults or success-shaped fallbacks. Link to authoritative rules, decisions, and shared resources instead of copying their contents. Keep skill-specific resources bundled with the skill and explicitly reference shared resources.

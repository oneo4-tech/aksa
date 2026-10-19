# Agentic component design

Components (Rule, Skill, Agent, Memory, Script, Template) are defined in `agentic/memory/vocabulary.md`. This rule decides which component a change needs and where it goes.

## Choose the component

- Put behaviour that should apply across tasks in a rule. Repository-wide always-on constraints go in `AGENTS.md`, the root rule. Topic-specific guidance goes in one file in `agentic/rules/`, created from `agentic/templates/rule-template.md` and indexed in `AGENTS.md`.
- Put a repeatable operation for a specific task in a skill under `agentic/skills/<category>/<skill-name>/`, following `agentic/rules/skill-authoring.md`. Keep guidance that serves only that skill with the skill.
- Create an agent only when a distinct goal and role need to own an outcome. Create it at `agentic/agents/<agent-name>.md` from `agentic/templates/agent-template.md`, and reuse applicable rules and skills instead of duplicating their instructions.
- Put durable shared context in `agentic/memory/`, not procedural instructions. Keep agreed vocabulary and decisions in their designated files. Change those files only by following the process stated at the top of each file, and never use memory to silently change an agreed decision.
- External systems are resources, not components. Treat `.kb` as an external memory system, `.projects` as an external project workspace, and `.worktrees` as the location for git worktrees. Use their repo-root symlinks as the stable paths; their targets are recorded only in `agentic/config/environment.yaml` (D-002). Follow the relevant domain rules for accessing or changing their contents.
- Put common enablement and deterministic work in reusable scripts under `agentic/scripts/`. Keep scripts that serve only one skill or agent bundled within that component so their ownership and lifecycle stay together. Shared settings that scripts read, such as `environment.yaml`, live in `agentic/config/` (D-009); read them through a script rather than copying their values.
- Put reusable starting structures in `agentic/templates/`. Templates standardize component structure; they do not replace the rules for authoring or reviewing the component.

## Required review

Every created or materially changed component must pass the `review-component` skill before acceptance.

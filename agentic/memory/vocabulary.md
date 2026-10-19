# Vocabulary

Agreed terms. Use them as defined. Add a term only after the owner agrees.

| Term | Meaning |
|------|---------|
| Agent | A component: an operator with a goal and role that owns an outcome and uses rules and skills. Lives in `agentic/agents/`. |
| Component | A building block of aksa's agentic system: Rule, Skill, Agent, Memory, Script, or Template indexed from AGENTS.md. External resources (`.kb`, `.projects`, `.worktrees`) are not components. |
| Memory | A component: durable context, such as agreed vocabulary, decisions, or trusted knowledge, that agents consult. Stored in `agentic/memory/` or in an external system reached through a repo-root symlink such as `.kb`. |
| Owner | The Product Owner (PO), who agrees vocabulary and decisions for this repository. |
| Rule | A component: persistent behaviour or constraints that shape how an agent works. `AGENTS.md` is the root rule, always loaded, holding repository-wide rules and the index of conditional rules in `agentic/rules/`. |
| Script | A component: deterministic executable work or common enablement that agents or skills run. Shared scripts live in `agentic/scripts/` and read repository settings from `config/`. |
| Skill | A component: a conditional, task-specific operation with steps an agent follows when invoked. Lives in `agentic/skills/<category>/<skill-name>/`. |
| Software Factory | The part of aksa that takes software work from request to delivery through agents, skills, and rules. Its skills use the `factory` category. |
| Template | A component: a reusable starting structure that standardizes creation of another component. Lives in `agentic/templates/`. |

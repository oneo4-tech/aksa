# Vocabulary

Agreed terms, alphabetical. Use them as defined. Add or change a term only after the owner agrees, using the `add-memory` skill.

| Term | Meaning |
|------|---------|
| Agent | A component: an operator with a goal and role that owns an outcome and uses rules and skills. Lives in `agentic/agents/`. |
| AI slop | Agent output that breaks rules, decisions, or owner preferences, makes unverified claims, adds speculative scope, or wastes tokens. Found by the `retrospect-session` skill. |
| Component | A building block of aksa's agentic system: Rule, Skill, Agent, Memory, Script, or Template indexed from AGENTS.md. External resources (`.kb`, `.projects`, `.worktrees`) are not components. |
| Knowledge Base | An external resource, not a component: curated domain knowledge kept outside the repository in its own git repository and reached through the `.kb` symlink. Only its `wiki/` pages are trusted (D-017). |
| Memory | A component: governed, durable context about aksa itself, namely agreed vocabulary and decisions, that agents consult. Lives in `agentic/memory/` (D-015). |
| Owner | The Product Owner (PO), who agrees vocabulary and decisions for this repository. |
| Rule | A component: persistent behaviour or constraints that shape how an agent works. `AGENTS.md` is the root rule, always loaded, holding repository-wide rules and the index of conditional rules in `agentic/rules/`. |
| Script | A component: deterministic executable work or common enablement that agents or skills run. Shared scripts live in `agentic/scripts/` and read repository settings from `config/`. |
| Skill | A component: a conditional, task-specific operation with steps an agent follows when invoked. Lives in `agentic/skills/<category>/<skill-name>/`. |
| Software Factory | The part of aksa that takes software work from request to delivery through agents, skills, and rules. Its skills use the `factory` category. |
| Template | A component: a reusable starting structure that standardizes creation of another component. Lives in `agentic/templates/`. |

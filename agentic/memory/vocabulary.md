# Vocabulary

Agreed terms, alphabetical. Use them as defined. Add or change a term only after the owner agrees, using the `add-memory` skill.

| Term | Meaning |
|------|---------|
| Agent | A component: an operator with a goal and role that owns an outcome and uses rules and skills. Lives in `agentic/agents/`. |
| AI slop | Agent output that breaks rules, decisions, or owner preferences, makes unverified claims, adds speculative scope, or wastes tokens. Found by the `retrospect-session` skill. |
| Claim | A session's hold on a factory issue while it works on the run: the `claimed` label and a `Factory:` comment naming the session. Taken over only on the owner's yes (D-033). |
| Component | A building block of aksa's agentic system: Rule, Skill, Agent, Memory, Script, or Template indexed from AGENTS.md. External resources (`.kb`, `.projects`, `.worktrees`) are not components. |
| Concept | The factory stage, and the `## Concept` section of a factory issue, where an idea's open decisions are settled one at a time and its feasibility is judged before a requirement is written. |
| Delivery branch | The branch whose single pull request brings a run into `main`: the run's own branch for a small run, its integration branch for a large one. |
| Factory issue | The one GitHub issue that tracks a run from triage to close through its labels, body sections, task checklist, and `Factory:` comments; the only place run state lives (D-024). |
| Finding | A reviewer's statement about a task's change. It blocks only when it cites an unmet acceptance criterion, a broken rule or decision, or a reproduced defect; any other finding is a note, never fixed in the run (D-032). |
| Gate | An owner approval that ends a stage: G0 concept, G1 requirement, G2 spec, G3 plan. The merge into `main`, by the owner or on the owner's explicit yes, ends the run (D-040). |
| Handoff | A self-contained note that lets another tool, agent, or person continue a session's work without its context. Written by the `create-handoff` skill; never stored in Memory or the Knowledge Base. |
| Integration branch | The `int/<n>-<slug>` delivery branch of a large run: its tasks are squash-merged into it, and its pull request brings the run into `main`. |
| Knowledge Base | An external resource, not a component: curated domain knowledge kept outside the repository in its own git repository and reached through the `.kb` symlink. Only its `wiki/` pages are trusted (D-017). |
| Memory | A component: governed, durable context about aksa itself, namely agreed vocabulary and decisions, that agents consult. Lives in `agentic/memory/` (D-015). |
| Owner | The Product Owner (PO), who agrees vocabulary and decisions for this repository. |
| Prototype | Throwaway code that answers one design question by clicking, kept on a never-merged `prototype/<name>` branch. Built by the `build-prototype` skill. |
| Re-pitch | A re-explanation of an earlier agent message: the same claims with the missing context added, in Simplified Technical English. Written by the `clarify-response` skill. |
| Requirement | The agreed what and why of a run: problem, outcome, acceptance criteria each with its test, out of scope, and constraints. The `## Requirement` section of its factory issue, approved at G1. |
| Rule | A component: persistent behaviour or constraints that shape how an agent works. `AGENTS.md` is the root rule, always loaded, holding repository-wide rules and the index of conditional rules in `agentic/rules/`. |
| Run | One work request's way through the Software Factory from triage to close: one factory issue and at most one merged pull request into `main` (D-025). |
| Script | A component: deterministic executable work or common enablement that agents or skills run. Shared scripts live in `agentic/scripts/` and read repository settings from `config/`. |
| Seam | A public entry point where a test checks behaviour, such as a script's command line or a pure function it exposes. |
| Skill | A component: a conditional, task-specific operation with steps an agent follows when invoked. Lives in `agentic/skills/<category>/<skill-name>/`. |
| Software Factory | The part of aksa that takes software work from request to delivery through agents, skills, and rules. Its skills use the `factory` category. |
| Software Work Request (SWR) | A request for software work, as plain text or a GitHub issue, before the factory triages it. |
| Spec | How a large run will be built: approach, interfaces, and the test for each acceptance criterion. The `## Spec` section of its factory issue, approved at G2. |
| Stage | The step of the factory lifecycle a run is in, shown by exactly one `stage:*` label on its factory issue. |
| Task | One slice of a large run: a line of its factory issue's task checklist, built on its own branch, verified, and squash-merged into the integration branch. A small run is a single task. |
| Template | A component: a reusable starting structure that standardizes creation of another component. Lives in `agentic/templates/`. |
| Verdict | The owner's answer to a prototype's question, with what clicking showed, kept in `prototypes/<name>/verdict.md` on the prototype branch. |
| Worktree | A separate git checkout under `.worktrees/`, created by `agentic/scripts/new_worktree.py` with its links and vendor folders set up; a factory run builds in one, one task branch at a time (D-039). |

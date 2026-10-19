---
name: review-component
description: Use before accepting a new or materially changed agentic component (rule, skill, agent, memory, script, or template). Produces a pass or a list of mismatches to resolve.
---

# Review component

## When to use

A component in `AGENTS.md` or `agentic/` has been created or materially changed and must be checked before acceptance.

## Inputs and prerequisites

- The component's path and, for a change, its diff.
- `agentic/rules/agentic-design.md`, `agentic/memory/vocabulary.md`, `agentic/memory/decisions.md`, and any rule specific to the component kind (for a skill, `agentic/rules/skill-authoring.md`).
- If the component's purpose is unclear from its content, ask the author before reviewing.

## Procedure

1. Confirm the component kind fits its purpose and ownership, using `agentic-design.md`.
2. Confirm its location matches the placement for that kind.
3. Search existing rules, skills, agents, and scripts for overlap; it must reuse or link rather than duplicate.
4. Confirm its scope, inputs, and dependencies are stated and that every referenced file, skill, or decision exists.
5. Check active decisions in `decisions.md` and the kind's rules; flag anything that contradicts them.
6. Confirm it uses agreed terms from `vocabulary.md`; flag new terms for the owner instead of adding them.
7. Confirm it holds no absolute or machine-specific paths (D-002).
8. Run `uv run pytest` to apply the automated repository checks.

## Output

Either "pass" with the component path, or a numbered list of mismatches, each naming the check, the location, and the fix. Report a check that could not run as blocked, with the reason; never report it as passed.

## Constraints

- Review only; do not change the component unless the author asks.
- Never accept a component that overrides an active decision; a reversal needs a new decision row.

---
name: review-component
description: Use before accepting a new or materially changed agentic component (rule, skill, agent, memory, script, or template). Produces a pass or a list of mismatches to resolve.
---

# Review component

## Inputs and prerequisites

- The component's path and, for a change, its diff.
- The standard: `agentic/rules/components.md`. Context: `agentic/memory/vocabulary.md` and `agentic/memory/decisions.md`.
- If the component's purpose is unclear from its content, ask the author before reviewing.

## Procedure

1. Run `uv run pytest`. It enforces every rule marked **[checked]** in `components.md`; report each failure as a mismatch.
2. Confirm the kind fits the purpose and ownership, using **Choose the kind** in `components.md`.
3. Search existing rules, skills, agents, and scripts for overlap; the component must reuse or link rather than duplicate.
4. Confirm its scope, inputs, and dependencies are stated, and that the unchecked structure rules for its kind hold.
5. Flag anything that contradicts an active decision in `decisions.md`.
6. Confirm it uses agreed terms from `vocabulary.md`; flag new terms for the owner instead of adding them.

## Output

Either "pass" with the component path, or a numbered list of mismatches, each naming the check, the location, and the fix. Report a check that could not run as blocked, with the reason; never report it as passed. When the change goes to a pull request, put this output in its **review-component result** section (`.github/pull_request_template.md`).

## Constraints

- Review only; do not change the component unless the author asks.
- Never accept a component that overrides an active decision; a reversal needs a new decision row.
- Keep standards in `components.md`; this skill holds only the review procedure.

## Done when

- Every procedure step ran, or is reported as blocked with its reason.
- "pass" is reported only when `uv run pytest` passed and no mismatch remains.

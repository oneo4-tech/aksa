---
name: define-concept
description: Use when a factory run is in stage concept, or the owner wants to think an idea through, settle the decisions behind it, or check whether it is feasible before a requirement is written. Shows what is already known, settles each open decision with the owner one per turn (options, trade-offs, a recommendation), gathers facts and prototypes through helper skills, and ends at gate G0 with a feasibility verdict in the Concept section.
---

# Define concept

## Inputs and prerequisites

- The factory issue in stage `concept` (`uv run agentic/scripts/factory_issue.py status <n>`), with its Request and any earlier Concept section and comments. Another stage: stop and report it.
- What aksa already knows: `get-memory` for decisions and terms in the area, and `get-kb` for domain knowledge.
- The section shape: `references/concept-section.md` in this skill's folder.

## Procedure

1. **Show what is known** before the first question: the `get-memory` and `get-kb` answers on the idea's topic, with their paths. Active decisions are not reopened.
2. **Map the destination:** what the owner wants to reach, what is unknown, and the decisions in the way, as numbered open items. Write the section from `references/concept-section.md` with `factory_issue.py section <n> Concept --file <file>`, and rewrite it as items settle, so a later session resumes from the issue.
3. **Settle one open item per turn** with the owner: the options, their trade-offs, and a recommendation. If no approach is settled, the approach comes first. Look facts up instead of asking:
   - Facts from outside aksa: `research-topic`, run while the interview continues.
   - A question talking cannot settle: `build-prototype`, whose result the owner judges.
   - How it fits aksa: read the code, rules, and skills it touches, and cite their paths.
4. **Record each settled item** in the section right away, with how it was settled: the owner's answer, a research output, or a prototype verdict. A lasting decision about aksa, or an agreed new term, goes under "To record" for the build to add through `add-memory`.
5. **Gate G0.** When no item is open, show the destination, the decisions, what is out of scope or later, and the verdict: feasible; feasible with conditions, each becoming a requirement constraint; or not feasible, with why in one sentence. Ask for the owner's explicit yes. Owner absent: leave the open items with recommendations in the section and follow **Owner in the loop** in `agentic/rules/factory.md`.
6. **Exit:**
   - Feasible: `factory_issue.py stage <n> define --reason "G0 approved by the owner: <verdict>."`
   - Not feasible: comment `Factory: G0: not feasible. <why>`, propose a `not-feasible` row through `add-memory` when the reason is durable, and `gh issue close <n> --reason "not planned"`.
   - Each part out of scope that the owner still wants: a new work request through `factory_issue.py intake`.

## Output

The Concept section with every item settled, out of scope, or later; the G0 result; and the stage moved to `define`, or the issue closed. Report an item still unsettled as blocked, naming it.

## Constraints

- Discovery only: the requirement belongs to `define-requirement`, and the design to `define-spec`.
- One decision per turn. An active decision changes only by a reversal through `add-memory`.
- Research and prototypes run only in this stage (D-026).

## Done when

- Every item in the Concept section is settled, out of scope, or later, each with how it was settled.
- The owner said yes at G0, and the stage is `define`, or the issue is closed as not planned.

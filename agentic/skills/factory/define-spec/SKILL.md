---
name: define-spec
description: Use when a large factory run is in stage spec, or the owner asks to spec, design, or agree the approach, interfaces, or tests of a requirement. Writes the Spec section (approach, interfaces with each real choice designed twice, the test for each acceptance criterion, notes for planning) from the approved requirement, passes gate G2, and moves the run to plan.
---

# Define spec

## Inputs and prerequisites

- The factory issue in stage `spec` (`uv run agentic/scripts/factory_issue.py status <n>`), with its approved Requirement and any Concept section. Another stage: stop and report it.
- The code, rules, and skills the change touches, read directly; seams in `agentic/rules/coding.md`; the component standard in `agentic/rules/components.md`.
- The section shape: `references/spec-section.md` in this skill's folder.

## Procedure

1. **Read the artifacts only:** the Requirement, the Concept decisions, and `get-memory` for the area. A design decision never settled goes back with `factory_issue.py stage <n> concept --reason "<decision>"`, and a requirement that cannot be met as written goes back to `define`. Never settle either here.
2. **Draft the approach and interfaces** from `references/spec-section.md`: the components, modules, and interfaces involved, what each hides, the data shapes, and where state lives. For each real choice, sketch two options and record the pick and why.
3. **Agree the tests** with the owner, one choice per turn: existing seams first, as high and as few as possible. Map every acceptance criterion to the test that proves it; a criterion without one is a gap to settle now.
4. **Add notes for planning:** order hints (a prefactor first; expand, migrate, contract for a wide change), risks, and follow-ups out of scope.
5. **Gate G2.** Show the section and ask for the owner's explicit yes on it and the tests. Owner absent: write the draft and follow **Owner in the loop** in `agentic/rules/factory.md`.
6. **Write and move:** `factory_issue.py section <n> Spec --file <file>`, then `factory_issue.py stage <n> plan --reason "G2 approved by the owner."`, which also names the integration branch.

## Output

The Spec section as approved, and the stage moved to `plan` with the integration branch named. Report a declined gate as blocked, with the owner's open points.

## Constraints

- A synthesis of settled decisions, not a new interview; open decisions go back to concept.
- Refer to the Requirement; never repeat or change it.
- No code beyond a short sketch of an interface.

## Done when

- Every acceptance criterion maps to exactly one agreed test.
- The owner said yes to the section, and `factory_issue.py status <n>` shows stage `plan` with the integration branch named.

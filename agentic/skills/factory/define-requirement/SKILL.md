---
name: define-requirement
description: Use when a factory run is in stage define, or the owner asks to write, draft, or agree the requirement, acceptance criteria, type, or size of a work request. Writes the Requirement section (problem, outcome, acceptance criteria each with its test, out of scope, constraints), proposes the type, size, and title, passes gate G1, and moves the run to spec or build.
---

# Define requirement

## Inputs and prerequisites

- The factory issue in stage `define` (`uv run agentic/scripts/factory_issue.py status <n>`), with its Request and, after concept, its Concept section. Another stage: stop and report it.
- `get-memory` for decisions and terms in the area, and the code the request touches, read to judge the size and the tests.
- The section shape: `references/requirement-section.md` in this skill's folder.

## Procedure

1. **Read the artifacts only:** `gh issue view <n> --comments`, the Concept decisions and conditions, and the decisions they link. A decision the requirement needs that is still open goes back: `factory_issue.py stage <n> concept --reason "<the open decision>"`.
2. **Draft** from `references/requirement-section.md`:
   - Problem: why it matters, in the owner's terms. Outcome: what changes, in a few lines, with no files, modules, or code.
   - Acceptance criteria **AC1** to **ACn**, each checkable on its own and each naming its test: the seam and kind of test (`agentic/rules/coding.md`), or `review-component` for a component change.
   - Out of scope, and constraints, including every condition of a "feasible with conditions" verdict.
   Use agreed terms (`agentic/memory/vocabulary.md`); propose a name for any needed term that has none.
3. **Propose the type, size, and title:** the type is feature, enhancement, fix, or chore (D-030); the size is large when the work needs several reviewable slices or design choices agreed before code, else small; the title is `<prefix>(<scope>): <summary>`, with `!` after the scope for a breaking change.
4. **Gate G1.** Show the section, type, size, and title, and ask for the owner's explicit yes; apply edits and show them again until then. Owner absent: write the draft section and follow **Owner in the loop** in `agentic/rules/factory.md`.
5. **Write and move:** `factory_issue.py section <n> Requirement --file <file>`, then `factory_issue.py set <n> --type <type> --size <size> --title "<title>"`, then `factory_issue.py stage <n> <spec for large, build for small> --reason "G1 approved by the owner."`.

## Output

The Requirement section, labels, and title as approved, and the stage moved. Report a declined gate as blocked, with the owner's open points.

## Constraints

- The what and why only: the how belongs to `define-spec`, and the task split to `plan-tasks`.
- Never settle an open decision here; it goes back to concept.
- The Request section stays as filed.

## Done when

- Every acceptance criterion is checkable and names its test.
- The owner said yes to the exact section, type, size, and title, and `factory_issue.py status <n>` shows them, with stage `spec` or `build` and no problems.

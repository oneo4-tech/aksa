---
name: add-memory
description: Use when the owner agrees a new or changed term, or a new, rejected, or reversed decision about aksa. Records it in agentic/memory/ by the change process and returns the new row.
---

# Add memory

## When to use

The owner has agreed a term or a decision about aksa that should bind future work. Domain knowledge goes to `add-kb` instead (D-015).

## Inputs and prerequisites

- The term and meaning, or the decision: kind, areas, one-sentence decision, one-sentence why, and source (issue, PR, or session).
- The owner's explicit agreement. Without it, propose the row and stop.
- Format and process: the header of `agentic/memory/vocabulary.md` or `agentic/memory/decisions.md`.

## Procedure

1. Run `get-memory` for the term or areas to find duplicates and conflicts. If an existing row already says it, stop and report that row.
2. **Term:** add or change the row in `vocabulary.md`, keeping alphabetical order.
3. **Decision:** take the next id after the highest in `decisions.md` and `decisions-history.md`, and append the row to `decisions.md` with Status `active`. Use only areas listed in its header; propose a new area to the owner instead of inventing one.
4. **Reversal:** set the old row's Status to `superseded by D-n` and move the row unchanged to the bottom of `decisions-history.md` (D-016).
5. Update rules and skills that restate or link the superseded decision.
6. Run `uv run pytest`.

## Output

The added or changed rows with their file paths, and the test result. Report failing tests as blocked with the output.

## Constraints

- Never edit a decision row except its Status; never reuse an id.
- Never record without the owner's agreement.

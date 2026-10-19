---
name: get-memory
description: Use to look up an agreed term or decision about aksa before relying on or changing it. Returns the matching vocabulary and decision rows with their file paths, read with the fewest tokens.
---

# Get memory

## When to use

A task depends on what an aksa term means or what was decided about an area, such as before changing paths, sync, skills, or components.

## Inputs and prerequisites

- A term, area, or keyword. If only a task is given, derive the areas from the area list in the `agentic/memory/decisions.md` header.
- Retrieval order and tiers: `agentic/rules/knowledge.md`.

## Procedure

1. For a term, `grep -iw "<term>" agentic/memory/vocabulary.md`.
2. For a decision, `grep -iw "<area or keyword>" agentic/memory/decisions.md`; try a second keyword before concluding nothing is recorded.
3. Only when asked why a decision changed, grep `agentic/memory/decisions-history.md` for the decision's id.
4. Read whole files only if grep results are ambiguous.

## Output

The matching rows, each with its file path and decision id, or "nothing recorded for <query>" with the queries tried.

## Constraints

- Read only. To record something, use `add-memory`.
- Domain knowledge is in the Knowledge Base; use `get-kb` (D-015).

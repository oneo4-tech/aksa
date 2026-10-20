---
name: repair-memory
description: Use periodically or when Memory feels stale, duplicated, or contradictory. Removes dead weight from agentic/memory/ and returns the changes made and the proposals awaiting the owner.
---

# Repair memory

## Inputs and prerequisites

- `agentic/memory/vocabulary.md`, `agentic/memory/decisions.md`, `agentic/memory/decisions-history.md`, and the standard in `agentic/rules/knowledge.md`.
- The owner available to approve proposals; without them, report proposals only.

## Procedure

1. Run `uv run pytest tests/test_repository.py` and fix mechanical failures, such as a superseded row still in `decisions.md` (move it to `decisions-history.md`, D-016).
2. Find active decisions that overlap, contradict each other, or name paths, scripts, or terms that no longer exist (`grep` the repository).
3. Find vocabulary terms that are unused outside Memory, defined twice, or contradicted by an active decision.
4. Find aksa facts living elsewhere, such as vendor auto-memory or rules, that belong in Memory (D-019), and domain knowledge in Memory that belongs in the Knowledge Base (D-015).
5. Propose each fix to the owner. A decision change is a new consolidating row that supersedes the old ones through `add-memory`; a term change follows the vocabulary process.
6. Apply only approved fixes, then run `uv run pytest`.

## Output

Two lists: changes applied (with file paths and ids), and proposals declined or awaiting the owner. Report failing tests as blocked with the output.

## Constraints

- Mechanical moves only without approval; every change of meaning needs the owner.
- Never delete a decision; superseded rows go to history.

## Done when

- `uv run pytest` passes.
- Every applied change of meaning has the owner's approval, and every proposal is reported as applied, declined, or awaiting the owner.

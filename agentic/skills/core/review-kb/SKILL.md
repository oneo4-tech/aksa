---
name: review-kb
description: Use when the Knowledge Base inbox has items. Walks the owner through each item to approve into the wiki or drop, and returns what was approved, dropped, and skipped.
---

# Review KB

## Inputs and prerequisites

- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- The owner present to decide each item; this skill never approves on its own.
- Page contract: `agentic/rules/knowledge.md`.

## Procedure

1. List `.kb/inbox/` oldest first. For each item, read it and `grep -i` `.kb/index.md` for pages it overlaps.
2. Present the item: summary, sources, and a proposal: a new page `wiki/<domain>/<topic>.md`, a merge into an existing page, or drop (duplicate, wrong, or not durable).
3. Apply the owner's choice:
   - **Approve:** write or merge the page by the contract, with the TL;DR updated, facts stated once, sources kept, and `updated` set to today; split a page that exceeds the size limit. Delete the inbox item. Log `approve`.
   - **Drop:** delete the inbox item and any `raw/` file no other item or page cites. Log `drop`.
   - **Skip:** leave the item.
4. Run `uv run agentic/scripts/kb_index.py` and fix any error it reports.
5. Commit in the Knowledge Base repository (D-018).

## Output

Lists of approved items (with page paths), dropped items, and skipped items, and the index result. Report an index error that could not be fixed as blocked.

## Constraints

- Only the owner approves or drops (D-017).
- Never edit `index.md` by hand.

## Done when

- Every inbox item listed at the start is approved, dropped, or skipped by the owner's choice.
- Each approval and drop has a line in `.kb/log.md`, `uv run agentic/scripts/kb_index.py` reports no error, and the changes are committed in the Knowledge Base repository.

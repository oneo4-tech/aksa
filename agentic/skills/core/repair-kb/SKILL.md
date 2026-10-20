---
name: repair-kb
description: Use periodically or when Knowledge Base lookups return stale, duplicated, or oversized pages. Removes dead weight and reorganizes the wiki, and returns the changes made and the proposals awaiting the owner.
---

# Repair KB

## Inputs and prerequisites

- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- The standard: `agentic/rules/knowledge.md`.
- The owner available to approve proposals; without them, report proposals only.

## Procedure

1. Run `uv run agentic/scripts/kb_index.py --check` and list its errors.
2. Read `.kb/index.md` and find: pages with overlapping summaries or tags (merge), pages over the size limit or covering several topics (split), fragments too small to stand alone (merge), synonym tags or domains (normalize), and pages whose facts are outdated or contradicted by newer pages (update or remove).
3. Find `raw/` files no page or inbox item cites, and inbox items older than 30 days (remind the owner to run `review-kb`).
4. Propose each change to the owner, grouped by kind.
5. Apply approved changes: preserve sources, rewrite links to merged or moved pages (`grep -r "[[<topic>]]" .kb/wiki`), and set `updated` on changed pages. Log each as `repair`.
6. Run `uv run agentic/scripts/kb_index.py` and fix any error, then commit in the Knowledge Base repository (D-018).

## Output

Two lists: changes applied (with page paths), and proposals declined or awaiting the owner, plus the index result.

## Constraints

- Removing or merging content needs the owner's approval; fixing frontmatter format does not.
- Never edit `index.md` by hand or modify files in `raw/`; `outputs/` is out of scope.

## Done when

- `uv run agentic/scripts/kb_index.py --check` passes.
- Every applied change is owner-approved or a frontmatter format fix, and has a `repair` line in `.kb/log.md`.
- No `[[link]]` points to a merged or moved page, and the changes are committed in the Knowledge Base repository.

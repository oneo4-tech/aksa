---
name: add-kb
description: Use to capture domain knowledge, a learning, or a source document for the Knowledge Base. Writes an inbox item (and the source to raw/) for later review-kb, and returns its path.
---

# Add KB

## Inputs and prerequisites

- The knowledge in a few sentences, and any source document or URL.
- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- Layout and inbox item contract: `agentic/rules/knowledge.md`.

## Procedure

1. `grep -i` `.kb/index.md` and `.kb/inbox/` for the topic. If a page already says it, stop and report the page; if an item or page is close, list it under `related`.
2. Copy a source document, unchanged, to `.kb/raw/<YYYY-MM-DD>-<slug>.<ext>`.
3. Write `.kb/inbox/<YYYY-MM-DD>-<slug>.md` by the inbox item contract.
4. Append `- <date> add inbox/<file>: <summary>` to `.kb/log.md`.
5. Commit in the Knowledge Base repository (D-018).

## Output

The inbox item path and a reminder that it becomes trusted only after `review-kb`.

## Constraints

- Never write to `wiki/` or `index.md`; only `review-kb` promotes (D-017).
- Never modify a file in `raw/` once added.
- Facts about aksa go to `add-memory`, not the Knowledge Base (D-015).

## Done when

- The inbox item exists in `.kb/inbox/` by the inbox item contract, and any source document is in `.kb/raw/`.
- `.kb/log.md` has the `add` line, and the change is committed in the Knowledge Base repository.

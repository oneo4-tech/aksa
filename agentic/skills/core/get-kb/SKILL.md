---
name: get-kb
description: Use when a task needs domain knowledge from the Knowledge Base. Returns the relevant facts with the wiki page paths they came from, reading the index first and full pages last.
---

# Get KB

## Inputs and prerequisites

- The question or topic.
- `.kb` linked; if missing, run `uv run agentic/scripts/link_external.py --check` and report the result.
- Retrieval rules: `agentic/rules/knowledge.md`.

## Procedure

1. Search `.kb/index.md`: read it whole while short, otherwise `grep -i` it for keywords and `#tags`. Try synonyms before concluding nothing is there.
2. Shortlist at most five pages. For each, read only the frontmatter and TL;DR with `head -n 12`.
3. Read in full only the pages whose TL;DR does not answer the question.
4. Follow a `[[link]]` only when the answer needs it.

## Output

The answer with the wiki page path behind each fact, or "not in the Knowledge Base" with the queries tried. When nothing is found, say whether the knowledge is worth capturing with `add-kb`.

## Constraints

- Read only. Retrieve only from `wiki/` through `index.md`; never treat `inbox/`, `raw/`, or `outputs/` as trusted (D-017).
- Facts about aksa come from `get-memory`, not the Knowledge Base (D-015).

## Done when

- Every fact in the answer names the `wiki/` page it came from, or the answer is "not in the Knowledge Base" with the queries tried.
- Nothing was changed in `.kb`.

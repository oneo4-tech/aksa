---
name: triage-request
description: Use when a factory run is in stage triage, or the owner asks to triage, sort, or classify a work request. Checks the request for duplicates, earlier rejections, and what exists today, then routes it to concept when discovery is needed or to define, or closes it as a duplicate or won't do on the owner's yes.
---

# Triage request

## Inputs and prerequisites

- The factory issue number. `uv run agentic/scripts/factory_issue.py status <n>` must show stage `triage`; another stage: stop and report it.
- `get-memory` for rejections and decisions in the request's area.

## Procedure

1. **Read the request:** `gh issue view <n> --comments`. Reuse what earlier triage comments established; never ask again what is already answered.
2. **Check for duplicates** by meaning, not only words: `gh issue list --state all --search "<key terms>"`, and the code, rules, and skills (`grep -rn`). An open or closed issue covering the same need is a duplicate candidate.
3. **Check earlier rejections:** `get-memory` for `rejection` and `not-feasible` rows in the area. A match means won't do, citing the row, unless the request brings a new reason.
4. **Check what exists today:** for a bug, try the reported steps once and note whether it reproduces; for a change, find what exists and where.
5. **Recommend one outcome,** with its reason and its action:

   | Outcome | When | Action |
   |---|---|---|
   | Concept | open decisions, unknown feasibility, or research or a prototype needed | `factory_issue.py stage <n> concept --reason "<why>"` |
   | Define | a clear need that needs no discovery | `factory_issue.py stage <n> define --reason "<why>"` |
   | Duplicate | another issue covers it | `gh issue close <n> --duplicate-of <m>` |
   | Won't do | not worth doing, or an earlier rejection holds | `gh issue close <n> --reason "not planned"` |

6. **Decide:** the owner confirms or redirects the route; when the owner is absent, take the recommendation and say so in the comment. Closing needs the owner's explicit yes.
7. **Record and act:** post one comment starting `Factory: triage`, with the outcome, the reason, a guess at the type, and the findings of steps 2 to 4 (where you looked and what you found). Then take the action. For won't do with a durable reason, propose a `rejection` row through `add-memory`.

## Output

The outcome, the triage comment's link, and the new stage, or the closed issue.

## Constraints

- Classify only: no interview and no requirement; unclear ideas go to concept.
- Never close an issue without the owner's explicit yes.
- The type is set at G1 by `define-requirement`; triage only guesses it.

## Done when

- The triage comment records the outcome and where duplicates and rejections were searched.
- `factory_issue.py status <n>` shows stage `concept` or `define`, or the issue is closed with the owner's yes.

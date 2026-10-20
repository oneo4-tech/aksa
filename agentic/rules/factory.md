# Software Factory

Read before working on a factory run: its factory issue, any of its stages, or any `factory` skill. Terms are defined in `agentic/memory/vocabulary.md`; branches, worktrees, commits, and pull requests follow `agentic/rules/git.md`.

## Runs

- A run takes one Software Work Request from triage to close: one factory issue, and at most one merged pull request into `main`, opened at build (D-025). The factory works on the aksa repository only (D-023).
- All run state lives in the factory issue: labels, body sections, the task checklist, and `Factory:` comments (D-024). Never keep run state in local files or vendor memory.
- Labels and the body change only through `uv run agentic/scripts/factory_issue.py`, whose `status` command reads the whole run. Comments, closing the issue, and pull requests use `gh` directly. The label set is in `config/factory.yaml`.
- The `factory-orchestrator` agent runs each run (D-027); start or resume one with `run-factory`.
- A release is not a run: the owner starts it with `release-version`, the only writer of `CHANGELOG.md` (D-035).

## Lifecycle

`concept` runs only when triage routes there; `spec` and `plan` run only for a large run (D-026).

| Stage | Skill | Ends with |
|---|---|---|
| `triage` | `triage-request` | Routed to `concept` when discovery is needed (open decisions, unknown feasibility, research, or a prototype), else to `define`; or closed as a duplicate or won't do on the owner's yes |
| `concept` | `define-concept` | G0: decisions settled and a feasibility verdict; not feasible closes the issue |
| `define` | `define-requirement` | G1: the requirement with how each acceptance criterion is tested, the type, the size, and the title |
| `spec` | `define-spec` | G2: approach, interfaces, and the test for each acceptance criterion |
| `plan` | `plan-tasks` | G3: the task checklist and the pushed integration branch |
| `build` | `implement-task`, then `verify-task`, for each task in order | Every task landed on the delivery branch, with its draft pull request open |
| `ship` | `ship-change` | The pull request ready, the owner's review, the merge on the owner's yes, and closeout |

- Each stage skill runs only in its stage and ends by moving the stage, closing the issue, or stopping for the owner. Stage skills call helpers: `resolve-merge-conflicts` and `diagnose-bug` in build and ship; `research-topic` and `build-prototype` only in concept.
- Tasks run one at a time in checklist order (D-033). A small run is a single task on its delivery branch.
- Moving back to an earlier stage needs a reason; its gate is approved again.

## Owner in the loop

- Gates G0 to G3 and the merge into `main` need the owner's explicit yes, recorded in a `Factory:` comment. Before the merge, the factory asks for the owner's review feedback on the pull request (D-040).
- Also the owner's: closing at triage, the concept interview, new terms and decisions (`add-memory`), a build blocker, a true merge contradiction, a finding still blocking after its confirm pass, and taking over a claim.
- The factory lands verified tasks on the integration branch and changes its own factory issues without asking each time (D-040).
- When the owner is absent, work up to the next point above, then `factory_issue.py set <n> --owner wait --need "<what the owner must do>"`, which posts the need as a `Factory:` comment, release the claim, and stop. The triage route needs no wait; record the guess in the triage comment.
- The wait ends when the owner answers: `factory_issue.py set <n> --owner clear`. Every stage move also removes `needs:owner`.

## Factory issue

- Title: the request's own words until G1, then `<prefix>(<scope>): <summary>` with the type's prefix; a breaking change adds `!` after the scope.
- Labels: exactly one `stage:*`; one `type:*` and one `size:*` from G1; `needs:owner` while waiting for the owner; `claimed` while a session works on it.
- Body sections, in this order, each written by its stage:
  - `## Request`: the request, quoted, never edited.
  - `## Concept`: destination, decisions with how each was settled, items left open or out of scope, and the verdict.
  - `## Requirement`: problem, outcome, acceptance criteria **AC1** to **ACn** each with its test, out of scope, and constraints.
  - `## Spec`: approach, interfaces, the test for each acceptance criterion, and notes for planning.
  - `## Delivery`: the delivery branch, the pull request, and for a large run the task checklist, ticked as tasks land. Written only by `factory_issue.py`.
- Prose sections use `###` headings and no checkboxes, so GitHub counts only tasks.
- Comments start with `Factory:`: stage moves, gate results, verify reports, blockers, needs, claims, the owner's review, and the ship summary.

## Claims

- A session claims the factory issue before working on it and releases the claim whenever it stops (D-033): `factory_issue.py claim <n> --session <id>` and `release`, with `<id>` made once per session as `<host>-<YYYYMMDD-HHMMSS>`.
- A claim held by another session is refused. Show the owner the holder and take over with `--takeover` only on the owner's yes.

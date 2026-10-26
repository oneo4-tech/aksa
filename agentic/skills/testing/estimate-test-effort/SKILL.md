---
name: estimate-test-effort
description: Use when a testing engagement needs an effort estimate, as `run-testing`'s fourth step after the plan or when the owner asks for one. Reads the engagement brief, `docs/test-strategy.md`, and `docs/test-plan.md` and writes `docs/effort-estimate.md` in the brief's `effort_unit`, defaulting to `hours` and saying so, per workflow with assumptions, a range, and a confidence, marking a workflow it cannot estimate as such instead of guessing.
---

# Estimate test effort

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `client`, `engagement`, `effort_unit`, and `workflows`, plus `## Scope` and `## Acceptance criteria`.
- `docs/test-strategy.md` in the same folder, required. It supplies `## Scope`, `## Risks`, `## Approach`, and the workflow sizes those imply. Its shape is `agentic/skills/testing/write-test-strategy/references/test-strategy-template.md`.
- `docs/test-plan.md` in the same folder, required. Its `## Deliverables` supply the workflows to estimate, in order, and its `## Schedule` and `## Open questions` supply the time constraints and the unanswered questions an assumption depends on. Its shape is `agentic/skills/testing/write-test-plan/references/test-plan-template.md`.
- The unit: `effort_unit` from the brief's frontmatter, one of `hours` or `days`. When the field is absent, use `hours` and say in the file that it is the default because the brief names no `effort_unit`; when it holds any other value, stop and name it. Never convert one unit into the other.
- The document shape: `references/effort-estimate-template.md` in this skill's folder, read before writing.
- Missing engagement folder, `brief.md`, `docs/test-strategy.md`, or `docs/test-plan.md`, or a plan whose `## Deliverables` is empty: stop and name the item with the workflow or owner action that supplies it, writing nothing.
- The artifact: `docs/effort-estimate.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full, the strategy, and the plan. Confirm the strategy has `## Scope`, `## Risks` with ids, and `## Approach`, and the plan has `## Deliverables` with one row per workflow, plus `## Schedule`, `## Entry and exit criteria`, and `## Open questions`. Stop on each miss and name it: `write-test-strategy` supplies or completes the strategy, `write-test-plan` the plan, and the owner a missing brief field. Do not estimate, draft, or write anything on a stop.
3. **Settle the unit.** Take the unit as the Inputs state and record whether it came from the brief or is the `hours` default. Note in the file what the estimate excludes, such as client review time, environment procurement, and work outside the brief's `## Scope`; step 5 defines the range and the confidence scale that the Basis section states.
4. **List the workflows to estimate.** Take one row per workflow in the plan's `## Deliverables`, in the plan's order. A deliverable with no workflow named goes to `## Not estimated`, because there is nothing to size.
5. **Estimate each workflow.** For each, take its scope from its deliverable, from the strategy's `## Approach` entries that point at that artifact, and from the endpoints, pages, and flows in the strategy's `## Scope` that it covers.
   - **Assumptions:** name each fact the estimate rests on: the inputs that exist, the number of endpoints, pages, flows, or cases, one execution pass, and each answer in the plan's `## Open questions` it depends on, by its `Q<n>` id. An assumption is written as an assumption, never as a fact.
   - **Range:** give a low and a high in the unit. The low is the work when every assumption holds and one pass is enough; the high is the low plus one rework pass and the time to confirm each open assumption. Never a single number, and no currency.
   - **Confidence:** `high` when the plan and strategy scope the workflow fully and every input exists; `medium` when one assumption is unconfirmed; `low` when a key assumption is unconfirmed or an input the workflow needs is absent.
6. **Mark what cannot be estimated.** A workflow goes to `## Not estimated` with its reason and what would make it estimable, and no number, when its scope is not in the strategy, its deliverable names no artifact, its size depends on an answer that changes it beyond the range, or an input it needs is absent. Never guess, and never give a partial number.
7. **Total the estimated workflows.** Sum the low cells and the high cells over the rows in `## Workflow estimates` only. Name each workflow left out and state that the total is an estimate, not a price and not a delivery date.
8. **Write the document.** Copy the headings of `references/effort-estimate-template.md` into `docs/effort-estimate.md` inside the engagement folder, creating `docs/` when absent, and fill every section, with the header naming the client, the engagement, the unit and its source, the strategy and plan, and the date. Replacing an earlier estimate is allowed only after reading it; report what changed.
9. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/docs/effort-estimate.md`, and when it replaced an earlier version, what changed.
- The unit and whether it came from the brief or is the `hours` default.
- One line per estimated workflow: its low and high in the unit, and its confidence.
- Each workflow left unestimated with its reason, and the total range with the workflows it excludes.
- The assumptions that move the total most, and the plan's `Q<n>` ids they depend on.
- On a stop, each missing item with the workflow or owner action that supplies it, and that nothing was written.
- Never report an estimate that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012); never add engagement files to the repository or commit them, never touch another engagement, and write nothing to the Knowledge Base (D-015).
- Never turn effort into a price, a currency amount, a discount, or a delivery date, and never convert `hours` to `days` or back. A date the client asks for stays in the plan's open questions.
- Never copy a value from the engagement's `.env` into the estimate, a reply, or any other file. Name the `credentials_env` variables only.
- Never run a test suite, a test file, or an API or UI request. This workflow writes a document only.
- Never invent a workflow, a scope item, a count, an assumption, or a number. A workflow the inputs do not size goes to `## Not estimated`; a single number instead of a range is never written.
- Never edit `brief.md`, `docs/test-strategy.md`, `docs/test-plan.md`, or another workflow's artifact; `docs/effort-estimate.md` is this skill's only output.
- This is `run-testing`'s fourth step: it runs after `write-test-plan`, which runs after `write-test-strategy`, and its workflow list comes from the plan's `## Deliverables`. Route a missing strategy to `write-test-strategy`, a missing plan to `write-test-plan`, and a missing brief field to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/effort-estimate.md` exists inside `.projects/testing/<engagement>/` with the four headings of `references/effort-estimate-template.md` in order: Basis, Workflow estimates, Not estimated, Totals.
- The unit line states `hours` or `days`, and when the brief has no `effort_unit` it states that `hours` is the default used because the field is absent.
- `## Workflow estimates` has one row per workflow the estimate sizes, drawn from the plan's `## Deliverables` in order, each with its scope, its assumptions, a low, a high, and a confidence of `high`, `medium`, or `low`; every low is below its high, and no row carries a single number or a currency amount.
- Every workflow the inputs do not size is in `## Not estimated` with its reason and what would make it estimable, and carries no number.
- `## Totals` sums the low and high cells of the estimated rows only, names each excluded workflow, and says the total is an estimate, not a price or a date.
- No credential or token value is in the file or the reply; nothing ran; nothing outside the engagement folder changed; the reply names the artifact, the unit, the total range, and every unestimated workflow.

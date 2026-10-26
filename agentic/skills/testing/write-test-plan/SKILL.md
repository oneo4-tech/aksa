---
name: write-test-plan
description: Use when a testing engagement needs its test plan, as `run-testing`'s third step after the strategy or when the owner asks for one. Reads the engagement brief and `docs/test-strategy.md` and writes `docs/test-plan.md` with schedule, roles, environments, deliverables, entry and exit criteria, risks to the plan, and each unknown value as an open question.
---

# Write test plan

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `client`, `engagement`, `environment`, `surfaces`, `ui_base_url`, `api_base_url`, `credentials_env`, `workflows`, and `key_dates` when present, plus the `## Scope`, `## Out of scope`, `## Known risks`, and `## Acceptance criteria` prose sections.
- `docs/test-strategy.md` in the same folder, required, read in full. It supplies `## Scope`, `## Risks`, `## Approach`, `## Environments`, and `## Entry and exit criteria`. Its shape is `agentic/skills/testing/write-test-strategy/references/test-strategy-template.md`.
- The workflow and artifact list: the step table in `agentic/skills/testing/run-testing/scripts/run_testing.py`, read only. This skill never runs or edits it.
- The document shape: `references/test-plan-template.md` in this skill's folder, read before writing.
- Missing engagement folder or `brief.md`, a brief `## Scope` or `## Acceptance criteria` missing or empty, or a missing `docs/test-strategy.md`: stop and name the item with the workflow or owner action that supplies it, writing nothing.
- The artifact: `docs/test-plan.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full and confirm `## Scope` and `## Acceptance criteria` have content. Read the strategy and confirm `## Scope` has content, `## Risks` has ids, and `## Environments` and `## Entry and exit criteria` have content. Stop on each miss and name it, with `write-test-strategy` as the workflow that supplies a missing or incomplete `docs/test-strategy.md` and the owner as the one who completes the brief. Do not plan, draft, or write anything on a stop.
3. **Start the open questions.** Keep one numbered list, `Q1` upward, for every value the plan needs and the brief, the strategy, and the step table do not give. Record the missing value, the question, who can answer it, and what it affects. A table cell that needs such a value cites its `Q<n>` id; never write a date, name, count, level, or owner the sources do not give, and never `TBD` or an empty cell.
4. **Build the schedule.** Take one milestone per key date in the brief's `key_dates`, keeping its name and date, then the milestones the strategy's `## Entry and exit criteria` and the workflow list imply: brief agreed, environment access, test design, execution, defect triage, and exit review.
   - Use the key date's value as the milestone date. A milestone with no key date takes a `Q<n>` id and is listed under open questions; never estimate a date.
5. **Name the roles.** One row per role the plan needs, from the brief, the strategy, and the workflow list: test lead, client contact, environment owner, and defect owner. Fill `Filled by` with `owner` or `client`; when the plan needs a client-side person or team the brief does not name, cite a `Q<n>` id. Never write a person's name the brief does not give.
6. **List the environments.** Take each environment from the strategy's `## Environments`, with its base URLs and the names in `credentials_env`, never their values. Add its access owner and its test data readiness; an unknown one is a `Q<n>` id.
7. **List the deliverables.** One row per workflow the engagement runs, in the step table's order: the core steps whose `surface` is absent or in the brief's `surfaces`, plus each optional workflow named in the brief's `workflows`. Give each row the workflow name and the artifact path the step table gives. Add no other deliverable.
8. **State entry and exit criteria.** Take the strategy's entry criteria and add the plan's readiness, each with a milestone and the `owner` or `client` who confirms it. Give one exit criterion per acceptance criterion in the brief's `## Acceptance criteria`, in order, with its `AC<n>`, its milestone, and who confirms it. Never weaken a criterion the strategy states.
9. **Name the risks to the plan.** One row per risk to delivering this plan, each with a cause the plan shows: an open question, an unconfirmed key date, a dependency such as environment access, a credential variable, the `api_spec`, or the client's data. These are plan risks, not the product risks in the strategy. Give each an id `P1` to `Pn`, an impact, a likelihood, and a response.
10. **Write the document.** Copy the headings of `references/test-plan-template.md` into `docs/test-plan.md` inside the engagement folder, creating `docs/` when absent, and fill every section, with the header naming the client, the engagement, the environment, the strategy, and the date. Replacing an earlier plan is allowed only after reading it; report what changed.
11. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/docs/test-plan.md`, and when it replaced an earlier version, what changed.
- One line per milestone with its date or its `Q<n>` id, the roles with who fills them, the environments, and the number of deliverables.
- The entry criteria, the exit criteria with their `AC<n>` ids, the `P<n>` risk ids, and every open question with who can answer it and what it affects.
- On a stop, each missing item with the workflow or owner action that supplies it, and that nothing was written.
- Never report a plan that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012); never add engagement files to the repository or commit them, never touch another engagement, and write nothing to the Knowledge Base (D-015).
- Never copy a value from the engagement's `.env` into the plan, a reply, or any other file. Name the `credentials_env` variables only.
- Never run a test suite, a test file, or an API or UI request. This workflow writes a document only; the step table is read, never run or edited.
- Never invent a date, a person, a role assignment, a count, a milestone, or a deliverable. What the brief, the strategy, and the step table do not give is a `Q<n>` row, and the cell cites its id.
- Never edit `brief.md`, `docs/test-strategy.md`, or another workflow's artifact; `docs/test-plan.md` is this skill's only output.
- This is `run-testing`'s third step, after `write-test-strategy`, whose environments and entry and exit criteria it carries into the plan. Route a missing or incomplete strategy to `write-test-strategy`, and a missing brief field to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/test-plan.md` exists inside `.projects/testing/<engagement>/` with the seven headings of `references/test-plan-template.md` in order: Schedule, Roles, Environments, Deliverables, Entry and exit criteria, Risks to the plan, Open questions.
- Every milestone date is a `key_dates` value from the brief or cites a `Q<n>` id, and every such id has a row under Open questions naming who answers it and what it affects; no date, placeholder, or `TBD` appears that the brief does not give.
- Every role has `owner`, `client`, or a `Q<n>` id in its `Filled by` cell, and no person's name appears that the brief does not give.
- Every environment from the strategy's `## Environments` appears with the brief's base URLs and only `credentials_env` variable names, plus its access owner and data readiness.
- Deliverables has one row per workflow the engagement runs, in the step table's order, each with its artifact path; no deliverable is dropped or added.
- Entry criteria and one exit criterion per brief acceptance criterion appear in order, each with a milestone and who confirms it, and none is weaker than the strategy's.
- Every risk to the plan has an id, a cause the plan shows, an impact, a likelihood, and a response.
- No credential or token value is in the file or the reply; nothing ran; nothing outside the engagement folder changed; the reply names the artifact, the open questions, and the milestones without a confirmed date.

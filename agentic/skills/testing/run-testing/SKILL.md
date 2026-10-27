---
name: run-testing
description: Use when the owner asks to run, resume, or plan a freelance testing engagement's workflows, or needs an engagement brief checked before work starts. Validates the brief, plans the dependency chain, runs the pending or named workflows through their own skills, and returns the artifacts each step produced.
---

# Run testing

## Inputs and prerequisites

- The engagement name. Resolve it to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder. The owner starts from `references/brief-template.md`; do not invent client details or fill in a brief for them.
- The check and plan script, `scripts/run_testing.py`, run from the repository root with `uv run`. It reads the brief and writes nothing.
- The workflow skills of the `testing` category, one per step in the plan. The plan has 23 steps in dependency order: the 16 core steps, run when the brief's surfaces apply, and the seven optional steps an engagement selects. Run each step by its own skill; this skill only checks, plans, and hands over.
- The brief's `workflows` field, a list of optional workflow names: `write-contract-tests`, `write-performance-tests`, `audit-accessibility`, `test-api-security-basics`, `test-mobile-app`, `wire-ci-pipeline`, and `plan-exploratory-session`. It selects the optional steps for a whole-chain run; absent or empty means core steps only. A workflow named on the command line runs alone whatever the field says.
- A step is `done` when its artifact exists. A folder artifact, such as the API test folder, counts only when it holds at least one file, recursively; an empty folder is `pending`.
- `evidence/` in the engagement folder, holding what the owner supplies after running a suite. A step that needs evidence stops until the owner adds it; a folder that is empty or holds only `README.md` counts as missing.
- The engagement's `.env`, holding the values for the variable names in `credentials_env`. Read values at run time only.
- Missing engagement folder: stop and report the path, with `references/brief-template.md` as the starting point. Missing or invalid brief: the check names every field, then stop.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If `.projects/testing/<engagement>/` does not exist, stop and report that path; the owner creates it with a brief copied from `references/brief-template.md`. Never create or edit another engagement's folder.
2. **Check the brief first.** From the repository root, run:
   `uv run agentic/skills/testing/run-testing/scripts/run_testing.py check .projects/testing/<engagement>`
   The check reads the required fields and the optional ones: `workflows`, the selection of optional steps, `effort_unit`, `ci_platform`, `accessibility_standard`, `performance_targets`, `mobile_devices`, and `key_dates`. It refuses an invalid value, an unknown or core name in `workflows`, and a selection that needs a field or surface the brief lacks.
   - Exit 0: continue.
   - Exit 2: print every reported line in the reply, name each missing or invalid field, and stop. Do not plan, run a workflow, or write anything.
3. **Plan the chain.** Run the same script with `plan .projects/testing/<engagement>` for the whole chain, or `plan .projects/testing/<engagement> <workflow>...` for named workflows. Each chain line names a step, its artifact, and whether the artifact is `done` or `pending`. A line starting `out: <step>: <reason>` names a step the plan leaves out and why: its surface is not in the brief's surfaces, it is an optional step the brief does not select, or it was not named in the request.
   - Exit 3: the named workflow cannot run yet. Stop, report the missing inputs the script names, and say which workflow or owner action supplies each one; do not invent, stub, or copy an input.
   - Exit 2: report the unknown workflow name or the bad engagement path and stop.
4. **Run the steps.**
   - No workflow named: the chain is the core steps whose surface applies plus the optional steps the brief's `workflows` selects. Take the chain lines in dependency order. A step marked `done` already has its artifact; report it as done and do not rerun it. Run each `pending` step, but first confirm its required inputs exist; when one is missing, stop and name it and the step or owner action that supplies it, as for a named workflow. Report each `out:` line as out with its reason; never run an out step.
   - Workflows named: run exactly those, in the plan's order, even when their artifacts exist; the owner asked for a rerun.
   - Hand each step to that workflow's skill with the engagement folder and the inputs the plan showed. Keep the plan's order: never run a step before the inputs it needs exist. Do not do the workflow's work in this skill.
5. **Collect each result.** Record the artifact the workflow reports and whether it succeeded. A workflow that stops leaves its step `pending`; report it, and do not run a later step whose input it produces.
6. **Offer lessons once, never write them.** When `summarise-test-execution` ran and completed in this run, that step made the run's one offer: report the lessons it offered, what the owner asked to record, and the inbox item `add-kb` returned, and do not offer again. Otherwise, as when the run stopped earlier, did not include that step, or found its artifact `done`, offer reusable lessons from the engagement to the Knowledge Base through `add-kb`, such as a technique worth repeating or a client constraint that generalizes. Write only the lessons the owner asks to record, and report the inbox item `add-kb` returns; with nothing to offer, say so.

## Output

- The brief check result and the plan, then one line per chain step: its name, its artifact, and whether it was already done, ran, or is still pending with the reason. Each `out:` line is reported as out with its reason.
- Every artifact stays inside `.projects/testing/<engagement>/`: documents in `docs/`, test code and the scaffold under `tests/`, data fixtures under `data/`, the CI configuration under `ci/`, and defect reports at `docs/bugs/<id>.md`.
- On a missing or invalid brief, the script's lines, one per field, followed by a stop. On a missing input, the input and the workflow or owner action that supplies it. On a failed workflow, where it stopped and which steps remain pending.
- The lessons offered to the Knowledge Base, by this skill or by `summarise-test-execution`, whether the owner asked to record them, and the inbox item `add-kb` returned.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012), with one exception: lessons the owner asks to record go through `add-kb`, which writes `.kb/inbox/`, `.kb/raw/`, and `.kb/log.md` (D-015, D-017, D-018). Never add engagement files to the repository, commit them, or touch another engagement.
- Never copy a value from the engagement's `.env` into a brief, document, test, commit, or reply. The brief names variables; the values stay in `.env` and are read at run time.
- Never run a workflow out of dependency order, with a missing input, or run one whose earlier step is still pending.
- When workflows are named, run only those and rerun them as asked; in a whole-chain run, run the core steps plus the optional steps the brief's `workflows` selects and never rerun a step whose artifact exists.
- Offer Knowledge Base lessons once per run, through `add-kb` only; never write to `.kb` unasked, and never to its `wiki/` or `index.md` (D-017).
- Use `Engagement` as `agentic/memory/vocabulary.md` defines it. The `testing` category and its workflows are agreed in D-042.

## Done when

- The brief check exited 0 before any workflow ran.
- Every chain line of the plan is reported as already done, run, or still pending with its reason, and every `out:` line is reported as out with its reason; no step was skipped silently.
- Every step reported as run went through its own workflow skill and its artifact exists inside `.projects/testing/<engagement>/`.
- Lessons were offered once in the run, by this skill or by `summarise-test-execution`, never both.
- The reply names the artifacts, any refusal or failure, the lessons offered, and the owner's answer: which lessons to record and the inbox item `add-kb` returned, or that none was recorded.
- Nothing outside the engagement folder changed except the `.kb` files `add-kb` wrote for lessons the owner asked to record; with none asked for, nothing outside the folder changed.

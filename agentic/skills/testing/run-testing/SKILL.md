---
name: run-testing
description: Use when the owner asks to run, resume, or plan a freelance testing engagement's workflows, or needs an engagement brief checked before work starts. Validates the brief, plans the dependency chain, runs the pending or named workflows through their own skills, and returns the artifacts each step produced.
---

# Run testing

## Inputs and prerequisites

- The engagement name. Resolve it to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder. The owner starts from `references/brief-template.md`; do not invent client details or fill in a brief for them.
- The check and plan script, `scripts/run_testing.py`, run from the repository root with `uv run`. It reads the brief and writes nothing.
- The workflow skills of the `testing` category: `write-test-strategy`, `design-test-cases`, `write-api-tests`, `write-ui-tests`, `write-bug-report`, and `summarise-test-execution`. Run each step by its own skill; this skill only checks, plans, and hands over.
- `evidence/` in the engagement folder, holding what the owner supplies after running a suite. A step that needs evidence stops until the owner adds it; a folder that is empty or holds only `README.md` counts as missing.
- The engagement's `.env`, holding the values for the variable names in `credentials_env`. Read values at run time only.
- Missing engagement folder: stop and report the path, with `references/brief-template.md` as the starting point. Missing or invalid brief: the check names every field, then stop.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If `.projects/testing/<engagement>/` does not exist, stop and report that path; the owner creates it with a brief copied from `references/brief-template.md`. Never create or edit another engagement's folder.
2. **Check the brief first.** From the repository root, run:
   `uv run agentic/skills/testing/run-testing/scripts/run_testing.py check .projects/testing/<engagement>`
   - Exit 0: continue.
   - Exit 2: print every reported line in the reply, name each missing or invalid field, and stop. Do not plan, run a workflow, or write anything.
3. **Plan the chain.** Run the same script with `plan .projects/testing/<engagement>` for the whole chain, or `plan .projects/testing/<engagement> <workflow>...` for named workflows. Each line names a step, its artifact, and whether the artifact is `done` or `pending`.
   - Exit 3: the named workflow cannot run yet. Stop, report the missing inputs the script names, and say which workflow or owner action supplies each one; do not invent, stub, or copy an input.
   - Exit 2: report the unknown workflow name or the bad engagement path and stop.
4. **Run the steps.**
   - No workflow named: take the plan lines in dependency order. A step marked `done` already has its artifact; report it as done and do not rerun it. Run each `pending` step, but first confirm its required inputs exist; when one is missing, stop and name it and the step or owner action that supplies it, as for a named workflow.
   - Workflows named: run exactly those, in the plan's order, even when their artifacts exist; the owner asked for a rerun.
   - Hand each step to that workflow's skill with the engagement folder and the inputs the plan showed. Keep the chain's order: strategy, test cases, API tests and UI tests, bug reports, execution summary. Do not do the workflow's work in this skill.
5. **Collect each result.** Record the artifact the workflow reports and whether it succeeded. A workflow that stops leaves its step `pending`; report it, and do not run a later step whose input it produces.
6. **Offer lessons once, never write them.** When `summarise-test-execution` ran and completed in this run, that step made the run's one offer: report the lessons it offered, what the owner asked to record, and the inbox item `add-kb` returned, and do not offer again. Otherwise, as when the run stopped earlier, did not include that step, or found its artifact `done`, offer reusable lessons from the engagement to the Knowledge Base through `add-kb`, such as a technique worth repeating or a client constraint that generalizes. Write only the lessons the owner asks to record, and report the inbox item `add-kb` returns; with nothing to offer, say so.

## Output

- The brief check result and the plan, then one line per step: its name, its artifact, and whether it was already done, ran, or is still pending with the reason.
- Every artifact stays inside `.projects/testing/<engagement>/`: documents in `docs/`, test code in `.projects/testing/<engagement>/tests/api/` and `.projects/testing/<engagement>/tests/ui/`, defect reports at `docs/bugs/<id>.md`, and the execution summary at `docs/execution-summary.md`.
- On a missing or invalid brief, the script's lines, one per field, followed by a stop. On a missing input, the input and the workflow or owner action that supplies it. On a failed workflow, where it stopped and which steps remain pending.
- The lessons offered to the Knowledge Base, by this skill or by `summarise-test-execution`, whether the owner asked to record them, and the inbox item `add-kb` returned.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012), with one exception: lessons the owner asks to record go through `add-kb`, which writes `.kb/inbox/`, `.kb/raw/`, and `.kb/log.md` (D-015, D-017, D-018). Never add engagement files to the repository, commit them, or touch another engagement.
- Never copy a value from the engagement's `.env` into a brief, document, test, commit, or reply. The brief names variables; the values stay in `.env` and are read at run time.
- Never run a workflow out of dependency order, with a missing input, or run one whose earlier step is still pending.
- When workflows are named, run only those and rerun them as asked; in a whole-chain run, never rerun a step whose artifact exists.
- Offer Knowledge Base lessons once per run, through `add-kb` only; never write to `.kb` unasked, and never to its `wiki/` or `index.md` (D-017).
- Use `Engagement` as `agentic/memory/vocabulary.md` defines it. The `testing` category and its workflows are agreed in D-042.

## Done when

- The brief check exited 0 before any workflow ran.
- Every line of the plan is reported as already done, run, or still pending with its reason; no step was skipped silently.
- Every step reported as run went through its own workflow skill and its artifact exists inside `.projects/testing/<engagement>/`.
- Lessons were offered once in the run, by this skill or by `summarise-test-execution`, never both.
- The reply names the artifacts, any refusal or failure, the lessons offered, and the owner's answer: which lessons to record and the inbox item `add-kb` returned, or that none was recorded.
- Nothing outside the engagement folder changed except the `.kb` files `add-kb` wrote for lessons the owner asked to record; with none asked for, nothing outside the folder changed.

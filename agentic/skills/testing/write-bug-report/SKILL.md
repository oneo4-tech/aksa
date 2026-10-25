---
name: write-bug-report
description: Use when a testing engagement needs defect reports, as `run-testing`'s fifth step or when the owner asks for them. Reads the engagement brief and at least one file in `evidence/` and writes one file per defect at `docs/bugs/<id>.md` with reproduction steps, expected and actual results, severity and priority with a one-line rationale, the evidence that shows it, the environment, and a trace to the test case or risk; never runs a suite and never copies a credential or token value.
---

# Write bug report

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `environment` and the base URL of the surface a defect was found on, and the `## Scope`, `## Known risks`, and `## Acceptance criteria` prose sections.
- `evidence/` in the same folder, holding what the owner supplies after running a suite: JUnit XML, terminal output, screenshots, or a hand-written results table, plus `evidence/README.md` naming what each file shows. Read `README.md` first when it exists, then at least one evidence file.
- `docs/test-cases.md` and `docs/test-strategy.md` in the same folder, read when they exist. They supply the `TC-<nnn>` cases, their `Covers` ids, and the `R<n>` risk ids a defect traces to. Their shapes are `agentic/skills/testing/design-test-cases/references/test-cases-template.md` and `agentic/skills/testing/write-test-strategy/references/test-strategy-template.md`.
- The document shape: `references/bug-report-template.md` in this skill's folder, read before writing.
- Missing inputs stop the work, and nothing is written: the engagement folder or `brief.md`; `environment` in the brief's frontmatter; `## Scope`, `## Known risks`, and `## Acceptance criteria`, each with content; an `evidence/` folder that is absent, empty, or holds only `README.md`; an evidence file that cannot be read; or a defect the evidence shows without enough to reproduce it, to state its expected and actual results, or to trace it to a test case or risk. Name each missing item and the owner action or workflow that supplies it, as Procedure steps 2 to 4 list.
- The artifact: `docs/bugs/` inside the engagement folder, one `<id>.md` per defect. When it already exists, read every file first and continue its numbering instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full and confirm `environment` in its frontmatter and `## Scope`, `## Known risks`, and `## Acceptance criteria`, each with content. Then read `evidence/README.md` when it exists, and every evidence file it names and every other file in `evidence/`. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - A missing `brief.md` or `environment`: the owner adds it to the brief's frontmatter, from `agentic/skills/testing/run-testing/references/brief-template.md`.
   - `## Scope`, `## Known risks`, or `## Acceptance criteria` missing or empty: the owner adds that section, named in the reply.
   - `evidence/` absent, empty, or holding only `README.md`: the owner runs the suite and adds its output, with `evidence/README.md` naming what each file shows. Never count the README as evidence of a defect.
   - An evidence file that cannot be read: the owner supplies a readable copy or names what it shows in `evidence/README.md`.

   Evidence is fixture evidence when `evidence/README.md` or the owner says it is fixture, sample, or hand-made data, or that no suite ran against the environment, even when a file also names a run command, date, or environment.
3. **Inventory the defects the evidence shows.** List one defect per failing test, error, or mismatch between an expected and an actual result in the evidence. Group failures the evidence gives the same cause, and name every failure in that file's Evidence section. A passing result is not a defect. Never infer a defect the evidence does not show; a suspicion goes in the reply to the owner, not in a file.
   - For each defect, confirm the evidence shows what it takes to reproduce it, what was expected, and what happened. A defect missing one of these is a stop: name the evidence file and the missing part, with the owner action that supplies it.
4. **Trace each defect.** Take the failing test's module and function from the evidence, and read that function's docstring in the engagement's `.projects/testing/<engagement>/tests/api/` or `.projects/testing/<engagement>/tests/ui/` for its `TC-<nnn>` case and the ids in its `Covers`. When the evidence names a case id, take the case from `docs/test-cases.md`. Confirm the case and its `Covers` ids in `docs/test-cases.md`; a case id that file does not contain is not cited.
   - With no case to cite, take the risk from `docs/test-strategy.md` `## Risks` or, with no strategy, from the brief's `## Known risks` in order as `R1` to `Rn`, and say which file the id comes from.
   - A defect whose evidence names no test case and no risk is a stop: name the evidence file, and the owner action of naming the case or risk in `evidence/README.md` or `design-test-cases` writing the missing case. Write nothing for the whole run.
   - Never cite a `TC-<nnn>` or `R<n>` id that is not in those files.
5. **Set severity and priority** from the evidence, the case, and the brief, on these scales:
   - **Severity** is the impact of the defect: `critical` for data loss, a security exposure, or a core flow that cannot complete with no workaround; `high` for a failed acceptance criterion or a core flow blocked behind a costly workaround; `medium` for a non-core flow or a partial failure with a workaround; `low` for a cosmetic or minor inconvenience.
   - **Priority** is the order to fix it in: `P1` before the engagement's exit criteria can be met; `P2` in the client's current release; `P3` in a later release; `P4` when convenient.
   - Give one line of rationale after each value, naming the user, flow, data, or acceptance criterion the impact falls on. Assign them independently: a low-severity defect on the only path to an exit criterion can be `P1`. Never raise either on an opinion the evidence states without a fact.
6. **Write one file per defect** at `docs/bugs/BUG-<nnn>.md`, using `references/bug-report-template.md` and creating `docs/bugs/` when absent. Read every existing bug file first: keep its id and update it with the new evidence when the same defect is already reported, and continue the numbering after the highest id otherwise. Never reuse or delete an id.
   - Take every step, value, status, and message from the evidence and the case; never invent one.
   - With fixture evidence, the Environment and Evidence sections say `fixture evidence, not a run against <environment>`, and no part says the defect was found or reproduced on that environment.
   - Replace a credential or token value the evidence shows with its `credentials_env` variable name or `[redacted]`, and report the redaction. Never read the engagement's `.env`.
7. **Check the result.** Run through **Done when**, fix every miss, and rerun the check.

## Output

- The folder `.projects/testing/<engagement>/docs/bugs/` and one line per file: its id, title, severity, priority, the evidence file that shows it, and the `TC-<nnn>` or `R<n>` trace.
- Each file written, and for an existing bug that was updated, the id and what was added.
- The redactions made, each by variable name or `[redacted]`; never the value.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report a bug file that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never run a test suite, a test file, a browser, or an API or UI request. Evidence is the owner's, supplied in `evidence/`; a defect with no evidence is not written.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and never hold their values; a value the evidence shows is replaced before it reaches a file or a reply.
- Never invent a defect, a reproduction step, an expected or actual result, a severity, a priority, or a trace id. What the evidence, the case, and the brief do not show is a stop.
- Never edit `brief.md`, `evidence/`, `docs/test-strategy.md`, `docs/test-cases.md`, the engagement's tests, or another workflow's artifact; `docs/bugs/` is this skill's only output.
- Route a missing case to `design-test-cases`, a missing strategy to `write-test-strategy`, and a missing brief field or evidence to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/bugs/` exists inside `.projects/testing/<engagement>/` with one `<id>.md` file per defect the evidence shows and no file for a passing result, and the brief and at least one evidence file were read.
- Every file has the ten parts of `references/bug-report-template.md` in order: title, Severity, Priority, Environment, Steps to reproduce, Expected result, Actual result, Evidence, Impact, Traceability.
- Every file names at least one file in `evidence/` other than `README.md`, and at least one `TC-<nnn>` or `R<n>` id from `docs/test-cases.md`, `docs/test-strategy.md`, or the brief's `## Known risks`, with the file it comes from.
- Every Severity is one of `critical`, `high`, `medium`, or `low`, every Priority one of `P1`, `P2`, `P3`, or `P4`, and each has a one-line rationale naming the user, flow, data, or acceptance criterion.
- Every step, expected result, and actual result comes from the evidence and the case or brief, with no invented value, and every Environment names the brief's `environment` value and the surface's base URL.
- Where `evidence/README.md` or the owner says the evidence is fixture data, every file's Environment and Evidence label it `fixture evidence, not a run against <environment>`, and no part presents it as a run against the brief's environment.
- No credential or token value is in any file or in the reply; each credential appears only as a variable name from `credentials_env` or as `[redacted]`, and every value the evidence showed was redacted and reported.
- No suite ran; nothing outside the engagement folder changed; the reply names `docs/bugs/`, each file's id and trace, any update, and any stop.

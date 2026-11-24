---
name: summarise-test-execution
description: Use when a testing engagement's execution evidence needs a summary, as `run-testing`'s last step or when the owner asks for one. Reads the brief, `evidence/`, `docs/test-cases.md`, `docs/test-strategy.md` when present, and `docs/bugs/` when present, and writes `docs/execution-summary.md` with results by suite, a defect table linked to the bug files, coverage against the strategy's risks and the acceptance criteria, residual risks, and an explicit go or no-go recommendation; never runs a suite, and offers reusable lessons to the Knowledge Base through `add-kb` without writing them unasked.
---

# Summarise test execution

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `environment`, `surfaces`, and the `## Scope`, `## Out of scope`, `## Known risks`, and `## Acceptance criteria` prose sections.
- `evidence/` in the same folder, holding what the owner supplies after running a suite: JUnit XML, terminal output, screenshots, or a hand-written results table, plus `evidence/README.md` naming what each file shows. Read `README.md` first when it exists, then every evidence file. At least one file other than `README.md` must hold a result.
- `docs/test-cases.md` in the same folder, read in full. It supplies the `TC-<nnn>` cases, their `Covers` ids, and the `## Coverage` rows this skill maps to results. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- `docs/test-strategy.md` in the same folder, read when it exists. It supplies the `R1` to `Rn` risk ids and their impact; with no strategy, the brief's `## Known risks` supply them in order, and the summary names the file the ids come from. Its shape is `agentic/skills/testing/write-test-strategy/references/test-strategy-template.md`.
- `docs/bugs/` in the same folder, read when it exists: one `<id>.md` per defect, with its severity, priority, and trace. Its shape is `agentic/skills/testing/write-bug-report/references/bug-report-template.md`.
- The engagement's `.projects/testing/<engagement>/tests/` folder when it exists, read only for each test's docstring, which names its `TC-<nnn>` case and its `AC<n>` and `R<n>` ids. The docstrings map a result to the case it proves.
- The document shape: `references/execution-summary-template.md` in this skill's folder, read before writing.
- Missing inputs stop the work, and nothing is written: the engagement folder or `brief.md`; `## Scope`, `## Out of scope`, `## Known risks`, or `## Acceptance criteria` missing or empty; `evidence/` absent, empty, or holding only `README.md`; an evidence file that cannot be read; `docs/test-cases.md` missing or holding no case with a `Covers` id; a strategy whose `## Risks` has no ids; a defect the evidence shows with no bug file; a bug file that cannot be read or has no severity, priority, or trace. Name each missing item and the owner action or workflow that supplies it, as Procedure step 2 lists.
- The artifact: `docs/execution-summary.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full and confirm `## Scope`, `## Out of scope`, `## Known risks`, and `## Acceptance criteria`, each with content. Read `evidence/README.md` when it exists, then every evidence file. Read `docs/test-cases.md`, the strategy when it exists, every file in `docs/bugs/` when it exists, and the test docstrings when the test folders exist. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - A missing `brief.md`, or `## Scope`, `## Out of scope`, `## Known risks`, or `## Acceptance criteria` missing or empty: the owner completes the brief, adding each section named in the reply, from `agentic/skills/testing/run-testing/references/brief-template.md`.
   - `evidence/` absent, empty, or holding only `README.md`: the owner runs the suite and adds its output, with `evidence/README.md` naming what each file shows. Never count the README as a result.
   - An evidence file that cannot be read: the owner supplies a readable copy or names what it shows in `evidence/README.md`.
   - A missing `docs/test-cases.md`, or no case with a `Covers` id: `design-test-cases` writes or completes the cases.
   - A strategy whose `## Risks` has no ids: `write-test-strategy` completes the risks.
   - A defect the evidence shows, meaning a failing test, an error, or a mismatch between an expected and an actual result, with no file for it in `docs/bugs/`: `write-bug-report` writes the defect report. A summary never reports a defect without its bug file.
   - A bug file that cannot be read, or one without a severity, a priority, or a trace: the owner supplies a readable copy or `write-bug-report` completes the file.

   Evidence is fixture evidence when `evidence/README.md` or the owner says it is fixture, sample, or hand-made data, or that no suite ran against the environment, even when a file also names a run command, date, or environment.
3. **Record the results by suite.** Take each suite from the brief's `surfaces`, `api` and `ui`, from any suite name the evidence gives, such as a JUnit XML `testsuite` name or a results table heading, and from the test folder a result's module path names. For each, take the evidence file, the total, passed, failed, error, and skipped counts, and the command and date exactly as the evidence states them.
   - Take no count, status, or message from anywhere else. A count the evidence does not state is `not stated`, never zero and never a guess.
   - A surface with no result file is `not run`, with the evidence gap named. Never infer a pass from the tests' existence.
   - A result that names no test, module, or case, and that the test docstrings cannot map to a `TC-<nnn>` case, stays in the suite counts and is named in `## Coverage` as an unmapped result; it never makes an id covered.
4. **Build the defect table.** Read every file in `docs/bugs/` when it exists and give each one a row: its id, title, severity, priority, the file it links to, and its status in this execution.
   - `open` when the evidence shows the failure the file reports, `fixed` when the evidence shows the failure gone, such as its test now passing, and `not observed` when the evidence does not mention it, naming the evidence file or `no evidence`.
   - With no defect in the evidence and no file in `docs/bugs/`, write `None`; never leave the table out.
   - Replace a credential or token value the evidence shows with its `credentials_env` variable name or `[redacted]`, and report the redaction.
5. **Map the coverage.** Take the `AC<n>` ids from the brief's `## Acceptance criteria` in order and the `R<n>` ids from the strategy's `## Risks`, or the brief's `## Known risks` when no strategy exists. For each id, take the cases from `docs/test-cases.md` `## Coverage` and their `Covers`, join each case to its result in step 3, and give one verdict:
   - `covered`: every case for the id ran and passed.
   - `partial`: some cases for the id ran and passed, and at least one failed, was skipped, or did not run.
   - `failed`: at least one case for the id ran and failed, and none passed.
   - `not run`: the id has cases, and none of them ran.
   - `not covered`: the id has no case.
   Name the evidence file behind each verdict, and never call an id covered on a test that did not run and pass.
6. **List the residual risks.** One line per gap that still threatens the client: every id not `covered`, every defect that is `open` or `not observed`, every suite or count `not run` or `not stated`, each brief `## Out of scope` area the client may expect, and each environment limit the brief or evidence names. Give the impact and what would close it, such as a case, a fix, or an owner action. Write `None` only when no gap exists.
7. **Recommend go or no-go.** Use exactly one of `Go` or `No-go`, by this rule:
   - `Go` only when every acceptance criterion is `covered`, every risk the strategy ranks `high` is `covered`, and no defect of `critical` or `high` severity is `open` or `not observed`. With no strategy, every risk from the brief's `## Known risks` must be `covered`.
   - `No-go` on any other result. Name the table rows that decide it, and one line of what would change it.
   Never soften the verdict to a condition, and never state a reason the tables do not show.
8. **Write the summary** at `docs/execution-summary.md` with the five sections of `references/execution-summary-template.md` in order, and every row, count, id, and verdict from steps 3 to 7. When the file exists, read it first, keep the facts that still hold, and report what changed.
   - With fixture evidence, the opening sentence, the Environment line, and every Command and date cell say `fixture evidence, not a run against <environment>`, and no line says a suite ran on that environment.
9. **Check the result.** Run through **Done when**, fix every miss, and rerun the check.
10. **Offer lessons, never write them.** As the last step, offer reusable lessons from the engagement to the Knowledge Base through `add-kb`, such as a technique worth repeating, a defect pattern, or a client constraint that generalizes. Ask the owner which, if any, to record; record only those they name, through `add-kb`, and report the inbox item it returns. With nothing to offer, say so. This is the run's one offer: in a `run-testing` run, `run-testing` step 6 reports it instead of offering again.

## Output

- The artifact path `.projects/testing/<engagement>/docs/execution-summary.md`, and when it replaced an earlier version, what changed.
- One line per suite: its evidence file and its total, passed, failed, error, and skipped counts, or `not run`.
- The defect table: one line per bug file with its id, severity, priority, and status, or `None`.
- Each acceptance criterion and risk with its verdict, and every id that is not `covered`.
- The residual risks, and the `Go` or `No-go` recommendation with its reasons and what would change it.
- The redactions made, each by variable name or `[redacted]`; never the value.
- The lessons offered and whether the owner asked to record them, with the inbox item `add-kb` returned.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report a summary that was not written, a defect without a bug file, or a suite that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012), with one exception: lessons the owner asks to record go through `add-kb`, which writes `.kb/inbox/`, `.kb/raw/`, and `.kb/log.md` (D-015, D-017, D-018). Never write to `.kb` unasked, and never to its `wiki/` or `index.md`. Never add engagement files to the repository or commit them, and never touch another engagement.
- Never run a test suite, a test file, a browser, or an API or UI request. Evidence is the owner's, supplied in `evidence/`; a result with no evidence is not reported.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env`; a value the evidence shows is replaced before it reaches the summary or a reply.
- Never invent a result, count, status, defect, coverage verdict, residual risk, or reason for the recommendation. What the brief, evidence, cases, bugs, and strategy do not show is a gap or a stop.
- Never edit `brief.md`, `evidence/`, `docs/test-strategy.md`, `docs/test-cases.md`, `docs/bugs/`, the engagement's tests, or another workflow's artifact; `docs/execution-summary.md` is this skill's only engagement output.
- Route a missing case to `design-test-cases`, a strategy with no risk ids to `write-test-strategy`, a missing bug file to `write-bug-report`, and missing brief fields or evidence to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/execution-summary.md` exists inside `.projects/testing/<engagement>/` with the five headings of `references/execution-summary-template.md` in order: Results by suite, Defects, Coverage, Residual risks, Recommendation.
- Every suite row names an evidence file other than `README.md` with counts that match it, or is `not run` with the gap named; the brief, `docs/test-cases.md`, and at least one real evidence file were read.
- The defect table has one row per file in `docs/bugs/`, each linking `bugs/<id>.md` relative to `docs/` so it resolves to `docs/bugs/<id>.md`, with the severity, priority, and status that file and the evidence support, or `None`; every defect the evidence shows has a file.
- Every `AC<n>` from the brief and every `R<n>` from the strategy or the brief has one coverage row with a verdict of `covered`, `partial`, `failed`, `not run`, or `not covered`, naming the evidence, and every id not `covered` is a residual risk.
- Where `evidence/README.md` or the owner says the evidence is fixture data, the opening sentence, the Environment line, and every Command and date cell label it `fixture evidence, not a run against <environment>`, and no line presents it as a run against the brief's environment.
- The recommendation is exactly `Go` or `No-go`, cites the table rows that decide it, follows step 7's rule, and names what would change it.
- No credential or token value is in the file or the reply; each value the evidence showed was redacted and reported; no suite ran.
- Nothing outside the engagement folder changed except the `.kb` files `add-kb` wrote for lessons the owner asked to record; with none asked for, nothing outside the folder changed.
- The lessons were offered, and the reply names the artifact, the verdict, each id not `covered`, and the inbox item `add-kb` returned or that none was recorded.

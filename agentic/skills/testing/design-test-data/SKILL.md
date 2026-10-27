---
name: design-test-data
description: Use when a testing engagement needs test data, as `run-testing`'s sixth step after the cases or when the owner asks for it. Reads the engagement brief and `docs/test-cases.md` and writes `docs/test-data.md` keyed to case ids, plus synthetic JSON or CSV fixtures under `data/`, each data set with its source, edge cases, and cleanup, and no real personal data.
---

# Design test data

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `client`, `engagement`, `environment`, `credentials_env` as variable names only, and the `## Scope` and `## Acceptance criteria` prose sections.
- `docs/test-cases.md` in the same folder, required and read in full. Each case supplies the data its steps and `Preconditions` name and the exact values its expected result states. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- The document shape: `references/test-data-template.md` in this skill's folder, read before writing.
- Missing brief, a brief `## Scope` or `## Acceptance criteria` missing or empty, a missing `docs/test-cases.md`, or no case in it: stop and name every missing item and the workflow or owner action that supplies it. Write nothing.
- A case whose steps or preconditions need a value that neither the case nor the brief gives: stop and name the case and the value, with the owner or `design-test-cases` as the source.
- The artifacts: `docs/test-data.md` and the fixtures it names under `data/`, inside the engagement folder. When they already exist, read them first and update them instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief and `docs/test-cases.md` in full. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - A brief `## Scope` or `## Acceptance criteria` missing or empty: the owner completes the brief.
   - A missing `docs/test-cases.md` or a document with no `TC-<nnn>` case: `design-test-cases` writes the cases.
   - A case with no steps or no expected result: `design-test-cases` completes the case.
   - A value a case's steps or preconditions need that neither the case nor the brief gives: the owner or `design-test-cases` supplies it.
3. **List the data each case names.** For every case in id order, take its `Preconditions`, each step's input or request body, and each value its expected result fixes. Keep the `TC-<nnn>` id with every value; a case that names none is recorded as no data.
4. **Group the values into data sets.** One data set per input or state that several cases share or that a case uses alone, numbered `DS-001` upward. A data set holds values of one kind and cites every case that uses it; a data set that holds values the tests send has one fixture file. A `credentials_env` name the cases use is listed in a data set without its value.
5. **Choose edge cases from the cases.** For each data set, list the boundary, empty, duplicate, missing, invalid, or maximum values the cases name or their steps imply, each with its case id. Where the cases state no boundary, write `none stated` and the reason; never add a value or a case the material does not use. Name any boundary the cases leave untested in the reply as a gap for `design-test-cases`.
6. **Write the fixtures under `data/`.** One JSON file for an object, a list, or a nested value, or one CSV file for rows with one header, named `data/ds-<nnn>-<name>.json` or `.csv`. Use synthetic values only: `example.com` and `example.test` addresses, names beginning `Test`, values prefixed with the case id, and reserved addresses such as `192.0.2.x`. Never a real person's name, email, phone number, address, or other personal data, and never a credential or token value: a credential data set names its `credentials_env` variable and has no file, and state a case creates through the application has none and names the steps that create it.
7. **Name the cleanup.** For each data set, state what removes or resets what a case creates with it: the delete or reset step the cases give, or `none` and why, such as a read-only fixture or a staging environment that resets between runs. A fixture file itself needs no cleanup beyond the repository.
8. **Write `docs/test-data.md`.** Copy the headings of `references/test-data-template.md` into the engagement folder, creating `docs/` when absent, and fill every section, with the header naming the client, the engagement, the environment, the cases, and the date. Name every fixture by its path relative to the engagement folder, `data/<file>`. Replacing an earlier document is allowed only after reading it; report what changed.
9. **Fill coverage.** One row per case id in `docs/test-cases.md` with its data set ids, or `none` and the reason the case sends no data. Every data set cites at least one existing case id.
10. **Check the result.** Read every fixture back and confirm it parses: JSON with `json`, CSV with `csv` and one header row and the same number of cells in every row. Run no test and no request. Then run through **Done when** and fix every miss before reporting.

## Output

- The artifact paths `.projects/testing/<engagement>/docs/test-data.md` and each `data/<file>`, and when they replaced earlier files, what changed.
- A short summary: the number of data sets and files, the case ids each serves, and every case with no data.
- Each boundary the cases leave untested, named as a gap for `design-test-cases`.
- On a stop, each missing item with the workflow or owner action that supplies it, and that nothing was written.
- Never report a data set or fixture that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Synthetic data only. Never copy or derive a real person's details from the client, the brief, the cases, a client document, or the environment, and never use production data.
- Never read, print, copy, or write a credential or token value. A credential data set names the variables in `credentials_env`; values stay in `.env` and are read at run time by whoever runs the tests.
- Never run a test suite, a test file, or an API or UI request. This workflow writes documents and fixtures only.
- Never invent a value, a boundary, a source, or a cleanup step. A missing source stops the work; a boundary the cases do not state is `none stated`.
- Never edit `brief.md`, `docs/test-cases.md`, or another workflow's artifact; `docs/test-data.md` and `data/` are this skill's only outputs.
- Route missing cases and missing case detail to `design-test-cases`, and missing brief content to the owner. This is `run-testing`'s step after `design-test-cases`, whose `TC-<nnn>` ids every data set keys to. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/test-data.md` exists inside `.projects/testing/<engagement>/` with the four headings of `references/test-data-template.md` in order: Sources, Data sets, Fixture files, Coverage.
- Every data set has a unique `DS-<nnn>` id, at least one existing `TC-<nnn>` id, a source, its edge cases or `none stated` with the reason, a cleanup or `none` with the reason, and either a named `data/` file, or no file with the reason when it is a credential, an existing environment value, or state a case creates through the application.
- Every file under `data/` is named in `## Fixture files` and parses, and every file named there exists; each data set's file is JSON or CSV, and a CSV has one header row and the same number of cells in every row.
- Every `TC-<nnn>` id in `docs/test-cases.md` has a row in `## Coverage` with at least one `DS-<nnn>` id or `none` and its reason, and no data set cites a case id that is not in `docs/test-cases.md`.
- No real personal data and no credential or token value is in the document, a fixture, or the reply; no test or request ran.
- Nothing outside the engagement folder changed, and the reply names the artifact, each fixture, the cases with no data, and any boundary gap.

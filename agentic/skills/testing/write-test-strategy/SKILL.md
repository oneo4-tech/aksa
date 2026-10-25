---
name: write-test-strategy
description: Use when a testing engagement needs its test strategy, as `run-testing`'s first step or when the owner asks for one. Reads the engagement brief and writes `docs/test-strategy.md` with scope, risks ranked by impact, an approach for each risk, environments, entry and exit criteria, and open questions.
---

# Write test strategy

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`.
- These prose sections of the brief, each with content: `## Background`, `## Scope`, `## Out of scope`, `## Known risks`, and `## Acceptance criteria`. When `## Scope`, `## Known risks`, or any other one of them is missing or empty, stop and name every section the brief must add; write nothing.
- The document shape: `references/test-strategy-template.md` in this skill's folder, read before writing.
- Missing engagement folder or brief: stop and report the path. Never create, complete, or edit a brief.
- The artifact: `docs/test-strategy.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the brief before writing.** Read `brief.md` in full and confirm the five prose sections exist and are not empty. On a missing or empty one, stop and name every section to add. Do not plan, draft, or write anything.
3. **Draft the strategy from the brief, using only its facts.**
   - **Scope:** what is tested and what is not, naming the endpoints, pages, and flows from `## Scope` and `## Out of scope`.
   - **Risks:** each risk from `## Known risks` as one row, ranked by impact on `## Acceptance criteria`, highest first, with ids `R1` to `Rn`. Never invent a client risk; a suspicion the brief does not state goes under open questions.
   - **Approach:** one entry per risk id, naming the test level (API, UI, or manual), the technique, and the artifact that will show the risk covered. Point at later artifacts such as `docs/test-cases.md` or the engagement's API and UI tests rather than writing them here.
   - **Environments:** each environment the tests run in, with the base URLs from the brief's frontmatter and the variable names in `credentials_env`, never their values.
   - **Entry and exit criteria:** what must be ready before testing starts, then one exit criterion per acceptance criterion in the brief.
   - **Open questions:** each question the brief leaves open, who can answer it, and what it blocks.
4. **Write the document.** Copy the headings of `references/test-strategy-template.md` into `docs/test-strategy.md` inside the engagement folder, creating `docs/` when absent, and fill every section. Keep the brief's wording for a risk or acceptance criterion when it is precise. Replacing an earlier strategy is allowed only after reading it; report what changed.
5. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/docs/test-strategy.md`, and when it replaced an earlier version, what changed.
- A short summary: the scope, the risk ids in impact order with their approaches, the environments, and each open question with who can answer it.
- On a brief that lacks a section, each missing section name followed by a stop, and that nothing was written.
- On a missing folder or brief, the path and the brief template to start from. Never report a strategy that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never copy a value from the engagement's `.env` into the strategy, a reply, or any other file. Name the variables only; values stay in `.env` and are read at run time by whoever runs the tests.
- Never run a test suite, a test file, or an API or UI request against the client's application. This workflow writes a document only.
- Do not invent client details, risks, environments, or acceptance criteria. What the brief leaves open goes under open questions.
- Never edit `brief.md` or another workflow's artifact; `docs/test-strategy.md` is this skill's only output.
- Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/test-strategy.md` exists inside `.projects/testing/<engagement>/` with the six headings of `references/test-strategy-template.md` in order: Scope, Risks, Approach, Environments, Entry and exit criteria, Open questions.
- Every risk is ranked by impact and has an approach naming its test level, technique, and the artifact that will show it covered.
- Every environment is named with the brief's base URLs and only `credentials_env` variable names; no value from `.env` is in the file.
- Every acceptance criterion in the brief maps to an exit criterion, and the entry criteria name what must be ready before testing starts.
- Every question the brief leaves open is under Open questions with who can answer it; nothing was invented.
- No test suite ran, nothing outside the engagement folder changed, and the reply names the artifact and any earlier version it replaced.

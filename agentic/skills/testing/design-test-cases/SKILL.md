---
name: design-test-cases
description: Use when a testing engagement needs test cases, as `run-testing`'s second step or when the owner asks for them. Reads the engagement brief and `docs/test-strategy.md` and writes `docs/test-cases.md`, deriving cases with equivalence partitioning, boundary values, decision tables, and state transitions as the material allows, each with steps, an expected result, and a trace to a requirement or risk.
---

# Design test cases

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`, and its `## Scope` and `## Acceptance criteria` are the requirement material.
- `docs/test-strategy.md` in the same folder, read in full. It supplies `## Scope`, `## Risks` with ids `R1` to `Rn`, and `## Approach` with one entry per risk. Its shape is `agentic/skills/testing/write-test-strategy/references/test-strategy-template.md`.
- Missing brief, missing `docs/test-strategy.md`, or a strategy without scope content, risk ids, or an approach for each risk: stop and name every missing item and the workflow or owner action that supplies it. Write nothing.
- The document shape: `references/test-cases-template.md` in this skill's folder, read before writing.
- The artifact: `docs/test-cases.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full and, when it exists, the strategy. When `docs/test-strategy.md` is missing, stop and name `write-test-strategy` as the workflow that supplies it. Stop and name each item the brief or strategy must add: brief `## Scope` or `## Acceptance criteria` with content; strategy `## Scope` with content, `## Risks` with ids, and `## Approach` with one entry per risk id. Do not plan, draft, or write anything on a stop.
3. **List the trace ids.** Take the acceptance criteria from the brief in order as `AC1` to `ACn`, and the risks from the strategy's `## Risks` as the ids it already gives, `R1` to `Rn`. These ids are the only valid `Covers` values; never invent a requirement or a risk.
4. **Derive cases, one technique at a time**, using only the brief, the strategy, and any input file they name inside the engagement folder:
   - **Equivalence partitioning:** for each input, field, or behaviour in scope, split it into valid and invalid classes that behave the same, and give each class that changes the outcome one case, error classes included.
   - **Boundary values:** for each input with a range, a length, a count, or an order, take each edge, one below it, and one above it, such as minimum minus one, minimum, maximum, and maximum plus one.
   - **Decision table:** where two or more conditions combine into different outcomes, build a table of the condition combinations and their outcomes, and give each rule that changes the outcome one case.
   - **State transition:** where the material names an object with states and allowed events, give each allowed transition one case and each event the object must reject one case.
   - When the material gives a technique no input, do not invent material; record the technique as `Not applicable` with the reason in `## Design techniques`.
5. **Write each case** as its own `###` section in `docs/test-cases.md`, following `references/test-cases-template.md`: a unique id in ascending `TC-001`, `TC-002` order, the one technique that derived it, at least one `AC<n>` or `R<n>` in `Covers`, preconditions, numbered steps with one action each naming the data or input it uses, and an expected result a person can observe and compare, with the exact value or state where the material gives one.
6. **Fill the summary sections.** In `## Sources`, name the scope, the acceptance criteria ids, and the risk ids the cases draw from. In `## Design techniques`, give one row per technique with what it was applied to and its case ids, or `Not applicable` and the reason. In `## Coverage`, give one row per acceptance criterion and risk with the case ids that cover it, or `none` and the gap or out-of-scope reason. Replacing an earlier file is allowed only after reading it; report what changed.
7. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/docs/test-cases.md`, and when it replaced an earlier version, what changed.
- A short summary: the number of cases, the case ids for each technique, the acceptance criteria and risks covered, and any id with no case.
- On a missing brief or strategy, each missing item followed by a stop, and that nothing was written.
- Never report a case document that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never copy a value from the engagement's `.env` into the test cases, a reply, or any other file. Name the variables only; values stay in `.env` and are read at run time by whoever runs the tests.
- Never run a test suite, a test file, or an API or UI request against the client's application. This workflow writes a document only.
- Do not invent client details, requirements, risks, inputs, or expected results. A missing input stops the work; a technique with no material is `Not applicable`.
- Never edit `brief.md`, `docs/test-strategy.md`, or another workflow's artifact; `docs/test-cases.md` is this skill's only output.
- Route an absent or incomplete strategy to `write-test-strategy`. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/test-cases.md` exists inside `.projects/testing/<engagement>/` with the four headings of `references/test-cases-template.md` in order: Sources, Design techniques, Test cases, Coverage.
- Every case has a unique id in `TC-<nnn>` form, one named technique, at least one `AC<n>` or `R<n>` from Sources in `Covers`, numbered steps, and an expected result that can be observed.
- Each of the four techniques is either used with its case ids in `## Design techniques`, or marked `Not applicable` with the material's reason.
- Every `AC<n>` and `R<n>` in `## Sources` has a row in `## Coverage` with at least one case id or a stated gap or out-of-scope reason, and no case cites an id that is not in Sources.
- No value from `.env` is in the file; no test suite ran; nothing outside the engagement folder changed; the reply names the artifact and any earlier version it replaced.

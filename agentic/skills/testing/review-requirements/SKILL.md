---
name: review-requirements
description: Use when a testing engagement starts and its brief needs review before work, as `run-testing`'s first step or when the owner asks for one. Reads the engagement brief and the `api_spec` it names, and writes `docs/requirements-review.md` listing each ambiguity, missing acceptance criterion, and untestable statement with a question for the client and a severity; it invents no requirement.
---

# Review requirements

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reviews `## Background`, `## Scope`, `## Out of scope`, `## Known risks`, and `## Acceptance criteria`.
- The brief's `api_spec` frontmatter field when it names a file: read that file inside the engagement folder, such as `specs/openapi.yaml`, and review the operations, parameters, schemas, and stated responses it defines.
- The document shape: `references/requirements-review-template.md` in this skill's folder, read before writing.
- Missing engagement folder or `brief.md`: stop and report the path. A missing or empty `## Scope` or `## Acceptance criteria`, or an `api_spec` file that is missing or cannot be read: stop and name the section or file. Write nothing on a stop.
- The artifact: `docs/requirements-review.md` inside the engagement folder. When it already exists, read it first and update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full and confirm `## Scope` and `## Acceptance criteria` have content. Read the `api_spec` when the brief names one. Stop on a missing section or file and name it with the owner action that supplies it; do not review, draft, or write anything.
3. **Number the acceptance criteria.** Take each acceptance criterion from the brief's `## Acceptance criteria` in order and give it `AC1` to `ACn`. These ids with the brief's words are the header's sources reviewed; this skill never adds a criterion or a requirement of its own.
4. **Find each ambiguity.** Record one row for each place where two people could build different behaviour from the same words:
   - a quality or quantity with no bound, such as fast, some, many, all, correct, or user friendly;
   - a scope item with no stated behaviour, such as a page named with nothing it must show;
   - a term used with no definition, such as shopper, product, or plan;
   - two statements that can disagree, such as `## Scope` naming a flow that `## Acceptance criteria` does not cover, or the brief and the `api_spec` giving different results for the same operation.
5. **Find each missing acceptance criterion.** Take every in-scope endpoint, page, and flow from `## Scope`, every risk from `## Known risks`, and every in-scope operation the `api_spec` defines. Record one row for each that has no criterion which would fail when it breaks. A gap is a row, never a criterion written here.
6. **Find each untestable statement.** Record one row for each statement no test could pass or fail as written:
   - no observable result, such as no status, value, state, or screen a person can compare;
   - no threshold or tolerance where the result needs one;
   - it needs production data, a client tool, or an environment the brief does not name;
   - it depends on a third party that `## Out of scope` excludes;
   - it can only be judged after the engagement ends.
7. **Give each finding an id, a question, and a severity.** Number each section in its own series, `A1`, `M1`, `U1`, upward. Write one question per row, phrased so the client's answer settles it: the value, the behaviour, the data, or the result that will be accepted. A question asks, and never states a requirement as agreed. Give each row one severity:
   - `blocker`: the review cannot say what will be accepted, so the exit criteria and the cases cannot be written;
   - `high`: the answer changes scope, cost, or the exit criteria;
   - `medium`: one flow or one case cannot be written until it is answered;
   - `low`: wording only, with no effect on scope or cases.
8. **Write the document.** Copy the headings of `references/requirements-review-template.md` into `docs/requirements-review.md` inside the engagement folder, creating `docs/` when absent. Fill the header with the client, the engagement, the brief, the `api_spec` or that none is named, and every acceptance criterion with its id and the brief's words. Fill each section; a section with nothing to report says `None` in one line, and no section is dropped. Replacing an earlier review is allowed only after reading it; report what changed.
9. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/docs/requirements-review.md`, and when it replaced an earlier version, what changed.
- One line per finding: its id, its section, and its severity.
- The count per section, and every `blocker` and `high` finding with the question that clears it.
- On a stop, each missing section or file with the owner action that supplies it, and that nothing was written.
- Never report a review that was not written.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012); never add engagement files to the repository or commit them, never touch another engagement, and write nothing to the Knowledge Base (D-015).
- Never copy a value from the engagement's `.env` into the review, a reply, or any other file. Name the `credentials_env` variables only; values stay in `.env` and are read at run time.
- Never send a question to the client. Record it; the owner asks.
- Never invent a requirement, acceptance criterion, expected result, client fact, or a severity outside step 7's scale. What the brief and the `api_spec` do not settle is a row with a question.
- Never edit `brief.md`, the `api_spec`, or another workflow's artifact; `docs/requirements-review.md` is this skill's only output.
- This is `run-testing`'s first step: it runs before `write-test-strategy`, whose `## Open questions` record what the brief still leaves open. Route a missing or unreadable brief to the owner through `run-testing`. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `docs/requirements-review.md` exists inside `.projects/testing/<engagement>/` with the four headings of `references/requirements-review-template.md` in order: Ambiguities, Missing acceptance criteria, Untestable statements, Review summary.
- The header names the client, the engagement, the brief, the `api_spec` or that none is named, and every acceptance criterion from the brief with its `AC<n>` id and the brief's words.
- Each ambiguity, missing acceptance criterion, and untestable statement the review found appears once, in its own section, with an id in `A<n>`, `M<n>`, or `U<n>` form, its location, what is wrong, one question for the client, and a severity of `blocker`, `high`, `medium`, or `low`; a section with nothing to report says `None`.
- No requirement, acceptance criterion, expected result, or client detail appears in the file that the brief and the `api_spec` do not support.
- No credential or token value is in the file or the reply; nothing ran; nothing outside the engagement folder changed; the reply names the artifact and each finding's id and severity.

---
name: scaffold-test-framework
description: Use when a testing engagement needs its test skeleton, as `run-testing`'s seventh step before the API and UI suites or when the owner asks for it. Reads the engagement brief and `docs/test-cases.md` and writes the engagement's `pyproject.toml`, its root conftest that loads `.env` at run time, and, when the brief names a `ui` surface, the page-object README for the one folder the UI suite imports from, registering the markers and tools both suites need; refuses to overwrite existing scaffold files unless the owner asks to rerun the scaffold.
---

# Scaffold test framework

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `engagement` for the project name, `surfaces` to decide whether it writes the page-object README, and `credentials_env` as variable names only.
- The brief check: `agentic/skills/testing/run-testing/scripts/run_testing.py check .projects/testing/<engagement>`, run from the repository root with `uv run`. Exit 0 means the brief can be used; exit 2 means stop and report its lines.
- `docs/test-cases.md` in the same folder, required and read in full. The cases confirm the engagement has work for the suites this skeleton serves. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- The file contents: `references/conftest-template.md` in this skill's folder, read before writing. It holds the three files, their merge rules, and the `.env` loading rule.
- The scaffold files: the engagement's `pyproject.toml`, its root conftest at `.projects/testing/<engagement>/tests/conftest.py`, and, when the brief's `surfaces` includes `ui`, its page-object README at `.projects/testing/<engagement>/tests/ui/pages/README.md`. Any one of them existing means the scaffold already ran: report each and stop unless the owner explicitly asked to rerun the scaffold.
- The engagement's `.env` may be absent while authoring. This skill never reads it; it writes the loader that reads it at run time.
- Missing brief: stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. A missing or invalid brief, a missing `docs/test-cases.md`, or a document with no case stops the work as Procedure step 2 lists.
- The artifact: `.projects/testing/<engagement>/tests/conftest.py`, with `pyproject.toml` written beside it and, when the brief names a `ui` surface, `.projects/testing/<engagement>/tests/ui/pages/README.md`.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Run the brief check from the repository root. On exit 2, report every line and stop. Read `docs/test-cases.md` in full; when it is missing, has no `TC-<nnn>` case, or a case has no steps or expected result, stop and name `design-test-cases` as the workflow that supplies it. Write nothing on a stop.
3. **Check for existing scaffold files before writing anything.** List `.projects/testing/<engagement>/pyproject.toml`, `.projects/testing/<engagement>/tests/conftest.py`, and, when the brief's `surfaces` includes `ui`, `.projects/testing/<engagement>/tests/ui/pages/README.md`. When any exists and the owner has not explicitly asked to rerun this scaffold, report each existing path and stop, writing nothing. On an explicit rerun, continue and report every file created, updated, or kept unchanged.
4. **Write `pyproject.toml`.** Create it from `references/conftest-template.md`, naming the project `<engagement>-tests` and listing `pytest`, `httpx`, `jsonschema`, `pytest-playwright`, `playwright`, and `ruff` as dependencies, with `testpaths = ["tests"]`, one `live` marker, `line-length = 120`, and `pages` as a first-party import group. On an explicit rerun, add only a missing dependency or setting and keep every other entry, such as one a suite added; never remove one. Never add these dependencies to aksa's `pyproject.toml` or change aksa's `uv.lock`.
5. **Write the root conftest.** Copy the block from `references/conftest-template.md` to `.projects/testing/<engagement>/tests/conftest.py`, creating the folder when absent. It loads `.env` from the engagement folder at run time before collection imports a suite's conftest, sets only names the environment does not already hold, and prints no name or value. A missing `.env` is skipped; an unreadable one fails with its path. Never write a credential or token value. On an explicit rerun, replace the file and report the change.
6. **Write the UI page-object README when the brief names a `ui` surface.** Copy the short block from the same reference to `.projects/testing/<engagement>/tests/ui/pages/README.md`, the one home for UI page objects, so it sits where `write-ui-tests` imports `pages.<module>` from. It says what a page object holds and when to put one there; write no page object and no test. With no `ui` in the brief's `surfaces`, write no page-object folder and no README, and say so in the Output.
7. **Install and check.** From the engagement folder run `uv sync` and report its exit code. Then run `uv run --project . pytest --collect-only` from that folder and report the number collected; from the repository root the same check is `uv run --project .projects/testing/<engagement> pytest --collect-only .projects/testing/<engagement>/tests`. Collection reads no `.env` value and starts no browser. With no test module yet, pytest exits 5 with `no tests ran`: report that as the expected state before the suites exist, not as a pass. Never run `pytest` without `--collect-only`, never run `playwright install`, and never launch a browser.
8. **Check the result.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/tests/conftest.py`, and the `pyproject.toml` written beside it, with what each contains; and, when the brief names a `ui` surface, `.projects/testing/<engagement>/tests/ui/pages/README.md`, or that no page-object folder was written because the brief has no `ui` surface.
- The dependencies and tool settings in `pyproject.toml`, the `uv sync` result, and the `pytest --collect-only` result with the number collected, or the exit 5 and `no tests ran` expected before a suite exists.
- The owner's commands: `uv sync`, then `uv run playwright install` once before a live UI run, then `uv run pytest`, each from the engagement folder; and that no browser ran while authoring.
- On an existing scaffold without an explicit rerun, each existing file followed by a stop and that nothing was written.
- On a stop, each missing item with the owner action or workflow that supplies it.
- Never report a file that was not written or a suite that was not collected.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never change an existing `pyproject.toml`, root conftest, or page-object README unless the owner explicitly asks to rerun this scaffold.
- Write no test, page object, schema, or suite fixture: `write-api-tests` and `write-ui-tests` own those, and they add to this skeleton. The scaffold serves the cases `design-test-cases` wrote.
- Never add a dependency to aksa's `pyproject.toml`, and never change its `uv.lock`; every dependency here belongs to the engagement's own environment and lock file.
- Never read, print, copy, or write a credential or token value. The conftest loads `.env` through `os.environ` at run time, so no value reaches a file, a commit, or a reply.
- Never run the suite, a live request, `pytest` without `--collect-only`, `playwright install`, or a browser.
- This is `run-testing`'s seventh step, after `design-test-data` and before `write-api-tests` and `write-ui-tests`, which add their suites to this skeleton. Route missing cases to `design-test-cases` and missing brief fields to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- The engagement's `pyproject.toml` and root conftest exist inside `.projects/testing/<engagement>/`, and, when the brief names a `ui` surface, its page-object README exists at `.projects/testing/<engagement>/tests/ui/pages/README.md`; the reply names the conftest as the artifact.
- `pyproject.toml` lists `pytest`, `httpx`, `jsonschema`, `pytest-playwright`, `playwright`, and `ruff`, with `testpaths = ["tests"]`, one `live` marker, `line-length = 120`, and `pages` as a first-party import group.
- The root conftest loads `.env` at run time, keeps every value already in the environment, prints no name or value, and imports cleanly when `.env` is absent; no credential or token value is in any written file.
- The page-object README says what a page object holds and when to put one there, and states that the UI suite's own folder is the one home for UI page objects, the layout `write-ui-tests` uses; no test or page object was written. No page-object folder is written when the brief has no `ui` surface.
- `uv sync` exits 0 in the engagement folder, and `uv run --project . pytest --collect-only` exits 0 there with the suites present and reports the number collected; with no test module yet, the exit 5 and `no tests ran` is reported as the expected state.
- No browser ran, no suite ran, and aksa's `pyproject.toml` and `uv.lock` are unchanged; nothing outside the engagement folder changed.
- When a scaffold file existed and the owner did not ask to rerun, the reply lists each existing file and nothing was written or changed.

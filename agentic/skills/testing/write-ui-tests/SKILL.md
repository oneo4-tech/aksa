---
name: write-ui-tests
description: Use when a testing engagement needs UI tests, as `run-testing`'s fourth step or when the owner asks for them. Reads the engagement brief and `docs/test-cases.md` and writes Playwright for Python tests under `.projects/testing/<engagement>/tests/ui/` with page objects and role- or label-based selectors, one module per journey, every test independent and runnable without hand edits; sets up the engagement's `pyproject.toml` and test dependencies and verifies the files pass `ruff check` and `pytest --collect-only`.
---

# Write UI tests

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `surfaces` with `ui` in it, `ui_base_url`, and `credentials_env` as variable names only.
- `docs/test-cases.md` in the same folder, read in full. It supplies the journeys in scope, the page each step visits, the elements it names, and the `AC<n>` and `R<n>` ids every test traces to. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- `references/ui-test-layout.md` in this skill's folder, read before writing: the files the generated tests have, their fixtures, the selector policy, and the sign-in fixture.
- The engagement's `.env`, holding the values for the names in `credentials_env`. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads it at run time; this skill never reads a value.
- The engagement's `pyproject.toml`, created or updated with `pytest`, `playwright`, and `ruff`, then installed with `uv sync` in that folder. aksa's own `pyproject.toml` is never touched.
- Browsers, installed by the owner with `uv run playwright install` before a live run. Collection and every check in this skill work with none installed.
- A missing input stops the work: the engagement folder or `brief.md`, `docs/test-cases.md`, `ui` in `surfaces`, `ui_base_url`, or, while an in-scope case starts signed in, no `credentials_env` names or no sign-in steps and page path in the cases. Name the item and the action that supplies it, as Procedure step 2 lists, and write nothing.
- The artifact: `.projects/testing/<engagement>/tests/ui/`. When it already exists, read it first and extend or update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief and `docs/test-cases.md` in full. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - `surfaces` without `ui`: the owner confirms the UI surface in the brief.
   - A missing `ui_base_url`: the owner adds it to the brief's frontmatter.
   - An in-scope case that starts signed in, by a precondition naming a signed-in user or session, with no `credentials_env` names: the owner adds the variable names to the brief and their values to `.env`. Never invent a variable name or a value, and write no sign-in helper and no signed-in test without a name.
   - The same signed-in case with no sign-in steps and page path anywhere in the cases: `design-test-cases` adds the case that names them.
   - A missing `docs/test-cases.md`, or no case naming a UI journey: `design-test-cases` writes the cases, with every journey in the strategy's scope.
   - An in-scope case with no numbered steps, no named page, or no expected result: `design-test-cases` completes it.
3. **Set up the engagement environment.** Create or update `pyproject.toml` in the engagement folder as `references/ui-test-layout.md` shows, listing `pytest`, `playwright`, and `ruff` as its dependencies, `testpaths = ["tests"]`, the `live` marker, `line-length = 120`, and `pages` as a first-party import group for ruff. Keep every entry this skill did not add, such as another workflow's dependencies or an existing `live` marker with its description, and never remove one. Run `uv sync` from the engagement folder and report its exit code. Never add these dependencies to aksa's `pyproject.toml`.
4. **Plan one module per journey.** List each journey in scope by its cases, the pages it visits in order with their paths, the elements and inputs the cases name, its preconditions, and whether it starts signed in. A journey is one set of steps from an entry page to an observable outcome; give each one `test_<journey>.py` and one test per case in it.
   - Take every page, path, element, input, and expected value from the cases; never invent one. A case that names no page path, element, or expected result is a stop naming the case, the missing part, and `design-test-cases` as the workflow that completes it.
   - One page object per page the journeys visit, named for the page, holding its path, locators, and actions. Shared browser setup lives in `conftest.py` only.
5. **Write the files** in the layout `references/ui-test-layout.md` gives: `conftest.py` for the base URL, browser, context, and page fixtures; `pages/base_page.py` and one page object per page; and one `test_<journey>.py` per journey. Each test's docstring names its `TC-<nnn>` case and the `AC<n>` and `R<n>` ids from that case's `Covers`.
   - Locate an element by its role and accessible name, then by its label, then by the visible text the case quotes. Use a CSS or XPath selector only when the case names none of these, leave a comment giving the reason in the page object, and report the exception. Never invent an accessible name, label, or element.
   - Assert with Playwright's `expect` on a page object's locator, such as `to_be_visible` or `to_have_text`, so the test waits for the outcome; never use a fixed sleep.
   - Assert every value the case's expected result states, such as a price or a total, with `to_have_text` or `to_contain_text`; `to_be_visible` alone never proves a stated value.
   - Give every test that drives a browser the `live` marker.
6. **Sign in at run time when needed.** When a case starts signed in, the function-scoped `signed_in_page` fixture drives the sign-in journey through its page object in the test's own fresh context, reading each credential from `os.environ` by a name in `credentials_env`. No storage state, cookie, or session is shared between tests, so no cart or other session data carries over. When the account keeps state across sessions, such as a saved cart, and the cases give no step that returns it to the case's starting state, stop and name the case and the missing precondition to `design-test-cases`. Never write a storage state, a trace, or a credential value to a file.
7. **Check the result.** From the engagement folder run `uv run ruff format tests/ui`, then `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only -q`. Collection imports each module and loads `conftest.py`, but starts no browser, reads no credential, and needs no browser binaries, so it passes with no `playwright install` and no `.env`. Fix every miss and rerun. Never run `pytest` without `--collect-only`, and never launch a browser: the owner's live run is `uv run playwright install` once, then `uv run --env-file .env pytest` from the same folder, which loads `.env` into the test process at run time.

## Output

- The artifact path `.projects/testing/<engagement>/tests/ui/`, with `conftest.py`, the page objects, the journey modules, and the count of tests for each journey and case.
- The `pyproject.toml` fields added or kept, the `uv sync` result, and the results of `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only`, with the number collected.
- The owner's browser and run commands, `uv run playwright install` and `uv run --env-file .env pytest` from the engagement folder, and that no browser ran while authoring.
- The selector exceptions: each element located without a role, label, or quoted text, with its page and the reason.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report tests that were not written, or a suite that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never add `pytest`, `playwright`, or `ruff` to aksa's `pyproject.toml`: each engagement has its own environment.
- Never run the suite, a browser, or `pytest` without `--collect-only`, and never install a browser. Running the tests is the owner's step through `run-testing`.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and read them with `os.environ`; the owner's `uv run --env-file .env pytest` loads the values at run time, and no storage state is shared or written.
- Never weaken a test to make collection pass: no `skip`, `skipif`, `xfail`, or conditional collection. A test that cannot be written is a stop.
- Never invent a page, path, element, selector, or expected value. The brief and `docs/test-cases.md` are the only sources.
- Route missing cases and sign-in journeys to `design-test-cases` and missing brief fields to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `.projects/testing/<engagement>/tests/ui/` exists with `conftest.py`, `pages/__init__.py`, `pages/base_page.py`, one page object per page in the journeys, and one `test_<journey>.py` per journey.
- Every in-scope journey has one test per case, each docstring naming its `TC-<nnn>` case and its `AC<n>` and `R<n>` ids, or a reported stop for the missing case.
- Every locator uses a role, label, or quoted text from the cases; each CSS or XPath exception is named in the reply with its page and reason.
- Each test runs on its own: a fresh context and page per test, signed in inside that context when its case starts signed in, with no storage state, cookie, cart, or session shared with another test; data created inside the test with a unique value, no module-level browser, credential read, or navigation, and no dependence on another test's state or order.
- Every test asserts each value its case's expected result states, such as a price or a total, with `to_have_text` or `to_contain_text`, not only that an element is visible.
- The suite runs without hand edits: the base URL comes from `ui_base_url`, every credential comes from a name in `credentials_env`, and no placeholder is left in a file.
- Where a case starts signed in, every variable the sign-in fixture reads is named in `credentials_env`, the cases give the sign-in journey, and no credential value or storage state is in any written file.
- `uv run pytest --collect-only` exits 0 from the engagement folder with no browser installed and no `.env`, and collects every planned test; `uv run ruff check` and `uv run ruff format --check` exit 0.
- The engagement's `pyproject.toml` lists `pytest`, `playwright`, and `ruff`, `uv sync` succeeded there, and aksa's `pyproject.toml` is unchanged.
- The reply names the artifact, the count collected, each selector exception, and the owner's `uv run playwright install` and `uv run --env-file .env pytest` commands; no browser ran while authoring, and nothing outside the engagement folder changed.

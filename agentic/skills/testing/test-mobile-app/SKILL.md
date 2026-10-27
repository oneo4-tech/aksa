---
name: test-mobile-app
description: Use when a testing engagement needs mobile web tests, as `run-testing`'s fourteenth step after the UI suite or when the owner asks for them. Reads the brief's `ui_base_url`, `mobile_devices`, and `docs/test-cases.md` and writes Playwright for Python tests under `.projects/testing/<engagement>/tests/mobile/` that emulate each named device through Playwright's device descriptors, cover the UI journeys in the cases, and keep every test independent; mobile web only, native apps out of scope, and the files import cleanly for `pytest --collect-only` without a live server.
---

# Test mobile app

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `surfaces` with `ui` in it, `ui_base_url`, `mobile_devices` as Playwright device names, and `credentials_env` as variable names only.
- `docs/test-cases.md` in the same folder, required and read in full. Its UI cases supply the journeys, each page path, the elements and inputs the steps name, the sign-in flow, and the `AC<n>` and `R<n>` ids every test traces to. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- `references/mobile-tests-template.md` in this skill's folder, read before writing: the files the mobile suite has, its device-emulation fixtures, its sign-in fixture, and its live and collect-only rules.
- The engagement's `pyproject.toml`, created or updated with `pytest`, `playwright`, and `ruff`, then installed with `uv sync` in that folder. aksa's own `pyproject.toml` is never touched.
- Playwright's device registry, read from the installed `playwright` package. Every name in `mobile_devices` must be a key in it.
- The engagement's `.env`, holding the values for the names in `credentials_env`. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads it at run time; this skill never reads a value.
- Browsers, installed by the owner with `uv run playwright install` before a live run. Collection and every check in this skill work with none installed.
- A missing input stops the work: `mobile_devices` absent or empty, a device name that is not a Playwright descriptor, `ui` in `surfaces` missing, `ui_base_url` missing, `docs/test-cases.md` missing or with no UI journey, a UI case with no page, steps, or expected result, or a signed-in case with no `credentials_env` names or no sign-in steps and page path. Name the item and the action that supplies it, as Procedure step 2 lists, and write nothing.
- The artifact: `.projects/testing/<engagement>/tests/mobile/`. When it already exists, read it first and extend or update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief and `docs/test-cases.md` in full, and read the Playwright device registry. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - `surfaces` without `ui`: the owner confirms the UI surface in the brief.
   - `mobile_devices` absent, empty, or not a list of device names: the owner adds the devices to the brief. Name `mobile_devices` and the devices mobile web must cover.
   - A name that is not a Playwright device descriptor: the owner replaces it with the Playwright name, such as `Pixel 7` or `iPhone 14`. Name the device and the closest descriptor when there is one; never substitute a device silently.
   - A missing `ui_base_url`: the owner adds it to the brief's frontmatter.
   - A missing `docs/test-cases.md`, or no UI case naming a page and a journey: `design-test-cases` writes the cases, with every UI journey in scope. A UI case is one without an `Endpoint`.
   - A UI case with no numbered steps, named page, or expected result: `design-test-cases` completes it.
   - A signed-in case with no `credentials_env` names: the owner adds the variable names to the brief and their values to `.env`. Never invent a name or a value.
   - A signed-in case with no sign-in steps and page path anywhere in the cases: `design-test-cases` adds the case that names them.
3. **Set up the engagement environment.** Create or update `pyproject.toml` in the engagement folder as `references/mobile-tests-template.md` shows, listing `pytest`, `playwright`, and `ruff` as its dependencies, `testpaths = ["tests"]`, the `live` marker, and `line-length = 120` for ruff. Keep every entry this skill did not add, such as another workflow's dependencies, and never remove one; keep a single `live` marker reworded as the template shows when its description names one suite only. Run `uv sync` from the engagement folder and report its exit code. Never add these dependencies to aksa's `pyproject.toml`.
4. **Plan one module per UI journey.** List each UI case by its `TC-<nnn>` id, the pages it visits in order with their paths, the elements and inputs its steps name, whether it starts signed in, and the values its expected result states. A journey is one set of steps from an entry page to an observable outcome; give each one `test_mobile_<journey>.py` and one test per case in it. Every test runs once per device in `mobile_devices`.
   - Take every page, path, element, input, and expected value from the cases; never invent one. A case that names no page, element, or expected result is a stop naming the case, the missing part, and `design-test-cases` as the workflow that completes it.
   - These are mobile web tests: they emulate a browser on a device. A native or hybrid app, an app store build, a real device, and a native driver are out of scope and stay out of the plan.
5. **Write the files** in the layout `references/mobile-tests-template.md` gives:
   - `conftest.py` with the base URL from `ui_base_url`, the device parameter, a fresh context and page per test, and the signed-in fixture. The device parameter comes from `mobile_devices`; each context is built from that device's Playwright descriptor, with its `default_browser_type` used to launch the browser and removed from the context options.
   - One `test_mobile_<journey>.py` per UI journey, with one test per case, beside an empty `.projects/testing/<engagement>/tests/mobile/__init__.py` so the module names cannot collide with the desktop UI suite's same-named journeys under pytest's default import mode. Each test's docstring names its `TC-<nnn>` case and the `AC<n>` and `R<n>` ids from that case's `Covers`, and its node id includes the device from the parameter.
   - Locate an element by its role and accessible name, then by its label, then by the visible text the case quotes. Never invent an accessible name, label, or element. Assert every value the case's expected result states with Playwright's `expect`, such as `to_contain_text` or `to_have_text`, so the test waits for the outcome; never use a fixed sleep.
   - Every test gets the `live` marker. A test that starts signed in uses the signed-in fixture, which signs in inside the test's own fresh context, reading each value from `os.environ` by a name in `credentials_env`; no storage state, cookie, or session is shared or written.
6. **Check the result.** From the engagement folder run `uv run ruff format tests/mobile`, then `uv run ruff check`, `uv run ruff format --check`, `uv run pytest --collect-only -q tests/mobile`, and `uv run pytest --collect-only -q` over the whole engagement. Collection imports each module and loads `conftest.py`, but starts no browser, reads no credential, and needs no browser binaries, so it passes with no `playwright install` and no `.env`. Fix every miss and rerun. Never run `pytest` without `--collect-only`, and never launch a browser: the owner's live run is `uv run playwright install` once, then `uv run --env-file .env pytest` from the same folder.
7. **Check the result against this skill.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/tests/mobile/`, with `conftest.py`, `__init__.py`, and one `test_mobile_<journey>.py` per UI journey.
- The devices emulated, each with its Playwright descriptor, and the collected test count for each journey and device.
- The `pyproject.toml` fields added or kept, the `uv sync` result, and the results of `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only`, with the number collected.
- The owner's browser and run commands, `uv run playwright install` and `uv run --env-file .env pytest` from the engagement folder, and that no browser ran while authoring.
- That the suite is mobile web only and native apps are out of scope.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report tests that were not written, or a suite that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never add `pytest`, `playwright`, or `ruff` to aksa's `pyproject.toml`: each engagement has its own environment. Never change aksa's `uv.lock`.
- Never run the suite, a browser, or `pytest` without `--collect-only`, and never install a browser. Running the mobile suite is the owner's step through `run-testing`.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and read them with `os.environ` at run time; no storage state is shared or written.
- Never weaken a test to make collection pass: no `skip`, `skipif`, `xfail`, or conditional collection. A test that cannot be written is a stop.
- Never invent a device, page, path, element, selector, or expected value. The brief and `docs/test-cases.md` are the only sources; a device the brief does not name is never added.
- This skill covers mobile web only. Native apps through Appium, real devices, and scanner-based checks are out of scope, and no such tool is added.
- This is `run-testing`'s fourteenth step, after `write-ui-tests` and its desktop suite, and it reuses that suite's cases, not its page objects. Route missing cases to `design-test-cases` and missing brief fields or device names to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042, and the per-engagement stack is D-043.

## Done when

- `.projects/testing/<engagement>/tests/mobile/` exists with `conftest.py`, `__init__.py`, and one `test_mobile_<journey>.py` per UI journey in `docs/test-cases.md`.
- Every device in `mobile_devices` runs every journey: each test's node id carries the device, and each context is built from that device's Playwright descriptor with its browser type.
- Every UI case has one test per device, each docstring naming its `TC-<nnn>` case and its `AC<n>` and `R<n>` ids, or a reported stop for the missing case.
- Each test runs on its own: a fresh context and page per test and device, signed in inside that context when its case starts signed in, with no storage state, cookie, or session shared with another test; data is created inside the test, no module-level browser, credential read, or navigation exists, and no test depends on another test's state or order.
- Every locator uses a role, label, or quoted text from the cases; every value the expected result states is asserted with `expect`, not only visibility.
- From `.projects/testing/<engagement>/`, `uv run --project . pytest --collect-only tests/mobile` exits 0 with no browser installed and no `.env` and collects every planned test, and `uv run --project . pytest --collect-only` over the whole engagement exits 0 with no `import file mismatch` against the desktop UI suite; `uv run --project . ruff check` and `uv run --project . ruff format --check` exit 0.
- The engagement's `pyproject.toml` lists `pytest`, `playwright`, and `ruff`, `uv sync` succeeded there, and aksa's `pyproject.toml` and `uv.lock` are unchanged.
- No browser ran and no credential value is in any written file; the reply states that the suite is mobile web only, that native apps are out of scope, and names the artifact, the devices, the count collected, and the owner's commands.

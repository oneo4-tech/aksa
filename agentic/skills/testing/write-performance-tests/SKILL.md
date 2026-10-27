---
name: write-performance-tests
description: Use when a testing engagement needs load tests, as `run-testing`'s eleventh step after the cases or when the owner asks for them. Reads the brief's `performance_targets` and `docs/test-cases.md` and writes Locust scenarios under `.projects/testing/<engagement>/tests/performance/`, one per targeted flow or endpoint, with the load profile it used recorded in a short `README.md` beside them and a pytest shape test in the same folder so `pytest --collect-only` passes; adds `locust` to the engagement's `pyproject.toml` only and never runs a load.
---

# Write performance tests

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `performance_targets`, the mapping of flow or endpoint names to target strings, `api_base_url`, and `credentials_env` as variable names only.
- `docs/test-cases.md` in the same folder, required and read in full. Its cases supply each targeted flow or endpoint, the order of its requests, its request bodies and values, and the credentials its preconditions name. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- `references/performance-tests-template.md` in this skill's folder, read before writing: the files the scenarios have, the target and load-profile shape, the shape test, and the README headings.
- The engagement's `pyproject.toml`, created or updated with `pytest`, `locust`, and `ruff`, then installed with `uv sync` in that folder. aksa's own `pyproject.toml` is never touched.
- The engagement's `.env`, holding the values for the names in `credentials_env`. The owner's run command loads it at run time; this skill never reads a value.
- A missing input stops the work: `performance_targets` absent or empty, `docs/test-cases.md` absent or with no case, `api_base_url` missing, a target that names no case, a flow whose cases name no HTTP request, credentials a case names while the brief lists no `credentials_env` name, or a credential scheme the case does not state. Name the item and the action that supplies it, as Procedure step 2 lists, and write nothing.
- The artifact: `.projects/testing/<engagement>/tests/performance/`. When it already exists, read it first and extend or update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief and `docs/test-cases.md` in full. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - `performance_targets` absent, empty, or not a mapping of names to target strings: the owner adds one entry per flow or endpoint to the brief.
   - A missing `docs/test-cases.md` or a document with no `TC-<nnn>` case: `design-test-cases` writes the cases, with the API flow or endpoint each target needs.
   - A missing `api_base_url`: the owner adds it to the brief's frontmatter.
   - A target whose name matches no case's `Endpoint` or flow: `design-test-cases` adds the case or the owner corrects the target name. Name the target.
   - A target flow whose cases name no HTTP request: Locust drives HTTP only, so the owner replaces the target with an API flow or endpoint that its cases name.
   - Credentials a case names, such as basic credentials, with no `credentials_env` names in the brief: the owner adds the variable names. Never invent a name or a value.
   - Credentials a case names with no scheme, such as basic or bearer: `design-test-cases` states the scheme in the case.
3. **Map each target to its case and requests.** For every key in `performance_targets`, write down the cases that cover it, each request in the case's order with its method, path, body, and path values, and the credentials the case names. An endpoint target gets one request; a flow target gets every request its cases name, in order. Use only what the cases give: never invent an endpoint, a body, a value, or a flow.
4. **Set up the engagement environment.** Create or update `pyproject.toml` in the engagement folder as `references/performance-tests-template.md` shows, listing `pytest`, `locust`, and `ruff`, with `testpaths = ["tests"]`, the `live` marker when another suite already has it, and `line-length = 120` for ruff. Keep every entry this skill did not add and never remove one. Run `uv sync` from the engagement folder and report its exit code. Never add these dependencies to aksa's `pyproject.toml`.
5. **Choose the load profile and record it.** The brief gives a target, not a load. Use this workflow's default profile unless the owner has supplied one: `10` users, a spawn rate of `2` users per second, and `1m` duration for each scenario. Record the profile per target in `targets.py` and in the folder's `README.md`, and state that it is this workflow's default because the brief states none, so the owner can confirm or change it. Never present the profile as a client fact.
6. **Write the files** in the layout `references/performance-tests-template.md` gives:
   - `targets.py` with one `Target` per brief entry: its name, its target text verbatim, the `TC-<nnn>` cases it uses, its users, spawn rate, and duration.
   - `locustfile.py` with one `HttpUser` scenario per target and a `SCENARIOS` mapping from target name to class. Each class carries its target text and load profile as class attributes, takes its host from `api_base_url`, and sends the case's requests in order, naming each in Locust statistics as the case names its endpoint.
   - A request body comes from the case's steps, never from a guess. Where a flow creates an object and then reads it, use the created id, as the case does.
   - When the cases name credentials, read each value at run time with `os.environ` by a name in `credentials_env`: two names for basic, one for a bearer token. A missing name raises with the variable's name when the load starts, never at import and never as a silent default. With no credentials in the cases, send none.
   - `README.md` with the target, case, endpoint, and load-profile table, the owner's run command for each scenario, and that no load was run while authoring.
   - `test_scenarios.py`, the pytest shape test: one test that every target has a scenario, and one parametrized test per target that imports the class and asserts its target text and load profile match `targets.py`.
7. **Check the result.** From the engagement folder run `uv run ruff format tests/performance`, then `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only -q`. Collection imports `locustfile.py` and `targets.py` but starts no load, sends no request, and needs no `.env`; `locust` must be synced for the import to succeed. Fix every miss and rerun. Never run `locust`, `pytest` without `--collect-only`, or any load.
8. **Check the result against this skill.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/tests/performance/`, with `targets.py`, `locustfile.py`, `test_scenarios.py`, and `README.md`.
- One row per target: its name and target text, the cases it uses, its requests, and its users, spawn rate, and duration.
- The `pyproject.toml` fields added or kept, the `uv sync` result, and the results of `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only`, with the number collected.
- The owner's run command for each scenario, such as `uv run --env-file .env locust -f tests/performance/locustfile.py <Scenario> --headless -u <users> -r <spawn-rate> -t <duration>`, and that no load was run while authoring.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report a scenario that was not written, or a load that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never add `pytest`, `locust`, or `ruff` to aksa's `pyproject.toml`: each engagement has its own environment. Never change aksa's `uv.lock`.
- Never run `locust`, a load, a live request, or `pytest` without `--collect-only`. Running the load is the owner's step; this workflow writes the scenarios and their shape test.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and read them with `os.environ` when the load starts; no value ever reaches a file, a commit, or a reply.
- Never weaken the shape test to make collection pass: no `skip`, `skipif`, `xfail`, or conditional collection. A scenario that cannot be written is a stop.
- Never invent a target, a case, an endpoint, a request body, a value, or a load profile the owner gave. The brief and `docs/test-cases.md` are the only sources; an absent load profile is this workflow's stated default.
- Locust drives HTTP requests, not a browser: a target that only a UI journey covers is a stop naming the target. Route missing cases to `design-test-cases` and missing brief fields to the owner. This is `run-testing`'s eleventh step, after `design-test-cases`, and the performance stack is per engagement under D-043. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `.projects/testing/<engagement>/tests/performance/` exists with `targets.py`, `locustfile.py`, `test_scenarios.py`, and `README.md`.
- Every entry in the brief's `performance_targets` has exactly one scenario, and `SCENARIOS` has no key the brief does not name.
- Each scenario carries its target text and its users, spawn rate, and duration, equal to its `Target`; every scenario's users are at least 1 and its spawn rate is above 0.
- The shape test collects one node per target plus the coverage test, imports the scenarios, and asserts each target and load profile; from `.projects/testing/<engagement>/`, `uv run --project . pytest --collect-only tests/performance` exits 0 without a server or a load.
- `README.md` names each target, its cases and requests, and the users, spawn rate, and duration used; it states the profile is this workflow's default when the brief states none, and gives the owner's run command per scenario.
- `uv run --project . ruff check` and `uv run --project . ruff format --check` exit 0 from the engagement folder, and the engagement's `pyproject.toml` lists `pytest`, `locust`, and `ruff`, with `uv sync` succeeded there.
- No load ran, no credential value is in any written file, aksa's `pyproject.toml` and `uv.lock` are unchanged, and nothing outside the engagement folder changed.
- The reply names the artifact, every target and its profile, each command's result, and the owner's run commands.

---
name: write-api-tests
description: Use when a testing engagement needs API tests, as `run-testing`'s third step or when the owner asks for them. Reads the engagement brief and `docs/test-cases.md` and writes Python `pytest` tests under `.projects/testing/<engagement>/tests/api/` with `httpx` and `jsonschema`, covering success, error, and response-schema checks for the endpoints in scope, plus authentication checks when the API needs authentication; sets up the engagement's `pyproject.toml` and test dependencies and verifies the files pass `ruff check` and `pytest --collect-only`.
---

# Write API tests

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `surfaces` with `api` in it, `api_base_url`, `credentials_env` as variable names only, and `api_spec` when the brief names a file in the engagement folder.
- `docs/test-cases.md` in the same folder, read in full. Each API case gives its endpoint in `Endpoint`, its request in its steps, and its status and body values in its expected result, with the `AC<n>` and `R<n>` ids every test traces to in `Covers`. Its shape is `agentic/skills/testing/design-test-cases/references/test-cases-template.md`.
- Whether the API needs authentication: it does when `api_spec` declares a security scheme, or the brief or a case states authentication. Otherwise it is public.
- `references/api-test-layout.md` in this skill's folder, read before writing: the files the generated tests have, their fixtures, schema helper, and markers.
- The engagement's `.env`, holding the values for the names in `credentials_env`. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads it at run time; this skill never reads a value.
- The engagement's `pyproject.toml`, created or updated with `pytest`, `httpx`, `jsonschema`, and `ruff`, then installed with `uv sync` in that folder. aksa's own `pyproject.toml` is never touched.
- A missing input stops the work: the engagement folder or `brief.md`, `docs/test-cases.md`, `api` in `surfaces`, `api_base_url`, no `credentials_env` names while the API needs authentication, or an API endpoint with no case. A public API needs no `credentials_env`. Name the item and the action that supplies it, as Procedure step 2 lists, and write nothing.
- The artifact: `.projects/testing/<engagement>/tests/api/`. When it already exists, read it first and extend or update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief and `docs/test-cases.md` in full. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - `surfaces` without `api`: the owner confirms the API surface in the brief.
   - A missing `api_base_url`: the owner adds it to the brief's frontmatter.
   - No `credentials_env` names while the API needs authentication: the owner adds the variable names to the brief. Never invent a variable name or a value, and write no authentication check without one. A public API is not a stop: ask for no names.
   - A missing `docs/test-cases.md`, or no case with an `Endpoint`: `design-test-cases` writes the cases, with the success case for each in-scope endpoint.
   - An `api_spec` the brief names that is not in the engagement folder: the owner adds the file or comments the field out.
3. **Set up the engagement environment.** Create or update `pyproject.toml` in the engagement folder as `references/api-test-layout.md` shows, listing `pytest`, `httpx`, `jsonschema`, and `ruff` as its dependencies, `testpaths = ["tests"]`, the `live` marker, and `line-length = 120` for ruff. Keep every entry this skill did not add, such as another workflow's dependencies, and never remove one. Run `uv sync` from the engagement folder and report its exit code. Never add these dependencies to aksa's `pyproject.toml`.
4. **Plan one module per resource.** List each endpoint in scope as the method and path in its cases' `Endpoint`, with the `TC-<nnn>` cases that name it, then group the endpoints by resource: the first path segment after any version prefix such as `/v1`, such as `orders` for `GET /v1/orders` and `POST /v1/orders/{id}`. Every endpoint gets success, error, and response-schema checks, plus authentication checks when the API needs authentication.
   - Take each request, status, body, and expected value from the matching case. For an error or authentication check the cases do not state, take the error statuses and the authentication scheme from `api_spec`; when neither the cases nor a spec states one, stop and name the endpoint, the missing check, and `design-test-cases` as the workflow that adds the case. Never invent a status, field, or error shape.
   - When the API needs authentication, write one missing-credential check and one invalid-credential check per endpoint that needs it, parametrized over the module's endpoints, not one per case, even when no case states authentication, taking the scheme and status from `api_spec`. Use only a variable named in `credentials_env`: with no name, step 2 stops before any file is written.
   - A public API gets no authentication check and no credential fixture; the reply says the API is public and why.
5. **Write the files** in the layout `references/api-test-layout.md` gives: one `test_<resource>.py` per resource, `conftest.py` for the base URL and client fixtures, `schemas.py` for validation, and one JSON Schema per response body under `schemas/`. Each test's docstring names its `TC-<nnn>` case, and the `AC<n>` and `R<n>` ids from that case's `Covers`. Read credentials only through `os.environ` with the names in `credentials_env`, and give every test that sends a request the `live` marker.
   - A success check asserts every body value and comparison its case's expected result states, such as an item, a quantity, or a total equal between two responses, beside the status; a schema check alone never proves a stated value.
   - Build each response schema from the response in `api_spec`. When the brief names no spec, validate only the fields and types that the case's expected result states, and name that basis in the reply. Where a case requires a non-empty value, such as a name that is not empty or a list with at least one item, the schema also requires it with `minLength: 1` or `minItems: 1`. Never tighten a schema beyond the spec and the cases.
6. **Check the result.** From the engagement folder run `uv run ruff format tests/api`, then `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only -q`; collection reads no credential, so it needs no `.env`. Fix every miss and rerun. Never run `pytest` without `--collect-only`: the owner's live run is `uv run --env-file .env pytest` from the same folder, which loads `.env` into the test process at run time.

## Output

- The artifact path `.projects/testing/<engagement>/tests/api/`, with the modules, the schema files, and the count of success, error, authentication, and schema checks for each endpoint, or that the API is public with no authentication checks and the basis.
- The `pyproject.toml` fields added or kept, the `uv sync` result, and the results of `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only`, with the number collected.
- The owner's run command, `uv run --env-file .env pytest` from the engagement folder, and that it was not run while authoring.
- The basis of each response schema: `api_spec`, or the test cases when the brief names no spec, and any assumption the layout reference names, such as a bearer `Authorization` header.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report tests that were not written, or a suite that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never add `pytest`, `httpx`, `jsonschema`, or `ruff` to aksa's `pyproject.toml`: each engagement has its own environment.
- Never run the suite, a live request, or `pytest` without `--collect-only`. Running the tests is the owner's step through `run-testing`.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and read them with `os.environ`; the owner's `uv run --env-file .env pytest` loads the values at run time, so no value ever reaches a file, a commit, or a reply.
- Never weaken a check to make collection pass: no `skip`, `skipif`, `xfail`, or conditional collection. A check that cannot be written is a stop.
- Never invent an endpoint, status, field, error shape, or schema constraint. The brief, `api_spec`, and `docs/test-cases.md` are the only sources.
- Route missing cases to `design-test-cases` and missing brief fields to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042.

## Done when

- `.projects/testing/<engagement>/tests/api/` exists with `conftest.py`, `schemas.py`, `schemas/`, and one `test_<resource>.py` per resource in the cases.
- Every endpoint in scope has a success, error, and response-schema test, and an authentication test when the API needs authentication, each docstring naming its `TC-<nnn>` case and its `AC<n>` and `R<n>` ids, or a reported stop for the missing case.
- Every success test asserts each body value and comparison its case states, not only the status and schema, and every schema requires a non-empty value with `minLength: 1` or `minItems: 1` wherever its case does.
- When the API needs authentication, the brief lists at least one `credentials_env` name and every authentication check reads a named variable; a public API has no authentication check and no credential read; no name or value was invented.
- `uv run pytest --collect-only` exits 0 from the engagement folder without a live server and collects every planned test; `uv run ruff check` and `uv run ruff format --check` exit 0.
- The engagement's `pyproject.toml` lists `pytest`, `httpx`, `jsonschema`, and `ruff`, `uv sync` succeeded there, and aksa's `pyproject.toml` is unchanged.
- No credential value is in any written file; each credential is read through `os.environ` by a name in `credentials_env`, and the reply gives `uv run --env-file .env pytest` as the owner's run command.
- Nothing outside the engagement folder changed, and the reply names the artifact, the schema basis, and each command's result.

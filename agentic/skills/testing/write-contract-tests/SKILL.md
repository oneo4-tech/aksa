---
name: write-contract-tests
description: Use when a testing engagement needs contract tests, as `run-testing`'s tenth step or when the owner asks for them. Reads the engagement brief and the OpenAPI file its `api_spec` names and writes `pytest` tests under `.projects/testing/<engagement>/tests/contract/` that build each operation's request from the spec's parameters and examples, assert the status its responses document, and validate the response against its `$ref`-resolved schema with `jsonschema`; unlike `write-api-tests`, every check derives from the spec rather than the cases, and the files pass `ruff check` and `pytest --collect-only` without a live server.
---

# Write contract tests

## Inputs and prerequisites

- The engagement name, resolved to `.projects/testing/<engagement>/`, the `Engagement` folder defined in `agentic/memory/vocabulary.md`, reached through the repo-root `.projects` symlink (D-012).
- `brief.md` in that folder, read in full. Its shape is `agentic/skills/testing/run-testing/references/brief-template.md`. This skill reads `surfaces` with `api` in it, `api_spec` as a path inside the engagement folder, `api_base_url`, and `credentials_env` as variable names only.
- The file `api_spec` names, read in full: an OpenAPI 3.x document in YAML or JSON inside the engagement folder. It supplies every operation, parameter, example, response, status, `$ref`, and security scheme this skill uses.
- `references/contract-tests-template.md` in this skill's folder, read before writing: the files the generated tests have, the spec helper, the credentials rule, and the `$ref` and schema checks.
- The engagement's `pyproject.toml`, created or updated with `pytest`, `httpx`, `jsonschema`, `ruff`, and `pyyaml` when the spec is YAML, then installed with `uv sync` in that folder. aksa's own `pyproject.toml` is never touched.
- The engagement's `.env`, holding the values for the names in `credentials_env`. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads it at run time; this skill never reads a value.
- A missing input stops the work: the engagement folder or `brief.md`, `api` in `surfaces`, `api_spec` absent or pointing at no file, `api_base_url`, a spec that does not parse, a schema `$ref` outside `#/components/schemas/` or an external `$ref`, an operation whose required input has no example, an unsupported security scheme, or no unambiguous `credentials_env` names while the spec marks security. Name the item and the action that supplies it, as Procedure step 2 lists, and write nothing.
- The artifact: `.projects/testing/<engagement>/tests/contract/`. When it already exists, read it first and extend or update it instead of starting over.

## Procedure

1. **Resolve the folder.** `<engagement>` is one folder name under `.projects/testing/`. If the folder or its `brief.md` is missing, stop and report the path, with `agentic/skills/testing/run-testing/references/brief-template.md` as the starting point. Never create or edit an engagement folder or its brief; work only inside the one given.
2. **Check the inputs before writing.** Read the brief in full. Stop on each of these and name the item with the action that supplies it, writing nothing:
   - `surfaces` without `api`: the owner confirms the API surface in the brief.
   - `api_spec` absent, empty, or naming a path outside the engagement folder: the owner sets it to the OpenAPI file's path inside the engagement folder.
   - `api_spec` naming a file that is not there: the owner adds the file or corrects the field. Name the path.
   - A missing `api_base_url`: the owner adds it to the brief's frontmatter.
   - A spec that is not OpenAPI 3.x YAML or JSON, or has no `paths`: the owner supplies a readable OpenAPI file.
   - No `credentials_env` names while the spec marks security at the root or on an operation: the owner adds the variable names to the brief. Never invent a name or a value.
3. **Set up the engagement environment.** Create or update `pyproject.toml` in the engagement folder as `references/contract-tests-template.md` shows, listing `pytest`, `httpx`, `jsonschema`, and `ruff`, plus `pyyaml` only when the spec is YAML, with `testpaths = ["tests"]`, the `live` marker, and `line-length = 120` for ruff. Keep every entry this skill did not add, such as another workflow's dependencies, and never remove one. Run `uv sync` from the engagement folder and report its exit code. Never add these dependencies to aksa's `pyproject.toml`.
4. **List every operation before writing.** From `paths` take each method and path, its `operationId` or the method and path as its label, its parameters and request body, its responses, and its security. Follow every local `$ref` as you read, including those into `#/components/schemas/`. Record for each operation:
   - **Request inputs.** Every path, query, and header parameter with its `in`, its required flag, and its value from `example`, the first `examples` entry, the schema's `example` or `default`, or the first `enum` value. Every request body with its `application/json` media type, its `example`, or its schema's required properties with the same value chain.
   - **Status.** The documented response codes and the success status: the lowest documented `2xx`, or the first documented code when it has none.
   - **Responses.** The schema for the success status, as a `$ref` or an inline schema, and every `required` list that schema carries.
   - **Security.** The scheme that applies at the root or, when an operation overrides it, on that operation. An empty operation `security` list means that operation is public.
   Stop and name the operation and input when a required parameter or required request-body property has no example value: the owner adds an `example` to `api_spec`. A required input is never guessed. Stop and name the operation when its success body is neither absent nor `application/json`, when it documents no numeric status or uses a range such as `2XX`, when a path item is given as a `$ref`, when a schema `$ref` points outside `#/components/schemas/`, when any `$ref` is external, or when the spec marks more than one security scheme or one this skill does not support. Never invent an operation, a value, a status, or a schema.
5. **Write the files** in the layout `references/contract-tests-template.md` gives: `conftest.py` for the base URL and HTTP client, `openapi.py` for loading the spec and building each request and schema check, and `test_contract.py` with one test per operation, parametrized over the operations and identified by its `operationId` or its method and path.
   - Build each request from the values from step 4: path parameters fill the path template, query and header parameters are sent when the spec gives a value, and a request body is sent as JSON from the example the spec gives. The base URL comes from the brief's `api_base_url`; the spec's `servers` are not used.
   - Assert the response status equals the success status from step 4, then validate the response body against that status's schema from the spec with `jsonschema`. The schema's own `required` entries are the required-field check: never add, remove, or tighten one. Resolve `$ref` by rewriting `#/components/schemas/<name>` pointers into a `$defs` document that `jsonschema` resolves, so nested and recursive refs work.
   - When the spec marks security, read each value at run time from `os.environ` by a name in `credentials_env`: two names for HTTP basic, one for a bearer token, and one for an `apiKey` header. Choose the names whose suffixes identify the username and password, or the one whose suffix identifies the token; when the brief gives no unambiguous choice, stop and name the scheme and the names rather than guessing. A missing name fails the test naming the variable, never a skip. A public spec reads no credential.
   - Name each test for its operation and give it the `live` marker; collection runs none of it.
6. **Check the result.** From the engagement folder run `uv run ruff format tests/contract`, then `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only -q`. The spec is read at import and needs no server, no `.env`, and no credential value. Fix every miss and rerun. Never run `pytest` without `--collect-only`: the owner's live run is `uv run --env-file .env pytest` from the same folder.
7. **Check the result against this skill.** Run through **Done when** and fix every miss before reporting.

## Output

- The artifact path `.projects/testing/<engagement>/tests/contract/`, with `conftest.py`, `openapi.py`, and `test_contract.py`.
- Every operation covered as `METHOD /path` with its `operationId`, its request inputs and their example sources, its success status, and its response schema name or `$ref`, or a reported stop for a missing example.
- The `pyproject.toml` fields added or kept, the `uv sync` result, and the results of `uv run ruff check`, `uv run ruff format --check`, and `uv run pytest --collect-only`, with the number collected.
- The authentication scheme used and which `credentials_env` names it reads, or that the API is public and why.
- The owner's run command, `uv run --env-file .env pytest` from the engagement folder, and that it was not run while authoring.
- On a stop, each missing item with the owner action or workflow that supplies it, and that nothing was written.
- Never report tests that were not written, or a suite that was not run.

## Constraints

- Write only inside `.projects/testing/<engagement>/` (D-012). Never add engagement files to the repository or commit them, and never touch another engagement.
- Never add `pytest`, `httpx`, `jsonschema`, `pyyaml`, or `ruff` to aksa's `pyproject.toml`: each engagement has its own environment. Never change aksa's `uv.lock`.
- Never run the suite, a live request, or `pytest` without `--collect-only`. Running the tests is the owner's step through `run-testing`.
- Never read, print, copy, or write a credential value. Files name the variables in `credentials_env` and read them with `os.environ`; the owner's `uv run --env-file .env pytest` loads the values at run time, so no value ever reaches a file, a commit, or a reply.
- Never weaken a check to make collection pass: no `skip`, `skipif`, `xfail`, or conditional collection. A check that cannot be written is a stop.
- Never invent an operation, example, status, schema, or required field. `api_spec` is the only source: contract tests derive from the spec, never from `docs/test-cases.md`. The case-based API suite is `write-api-tests`'s artifact, and the two suites complement each other.
- Route a missing case to `design-test-cases`, a missing example or unsupported operation to the owner, and a missing or broken `api_spec` to the owner. Use `Engagement` as `agentic/memory/vocabulary.md` defines it; the `testing` category and its workflows are agreed in D-042, and the per-engagement stack is D-043.

## Done when

- `.projects/testing/<engagement>/tests/contract/` exists with `conftest.py`, `openapi.py`, and `test_contract.py`.
- Every operation in `api_spec` has one collected test whose id names its `operationId` or its method and path, or a reported stop naming the operation and the missing input that blocks it.
- Each test builds its request from the spec's parameter and body examples, asserts the status the spec documents for that operation, and validates the body against the spec's resolved response schema, so every `required` entry the schema carries is checked.
- `$ref` values into `#/components/schemas/` resolve, including nested and recursive refs; no external `$ref` is present in the generated files.
- When the spec marks security, every credential comes from a name in `credentials_env` and is read with `os.environ` at run time; a public spec reads no credential; no name or value was invented and no credential value is in any written file.
- From `.projects/testing/<engagement>/`, `uv run --project . pytest --collect-only tests/contract` exits 0 without a live server, and `uv run --project . ruff check` and `uv run --project . ruff format --check` exit 0.
- The engagement's `pyproject.toml` lists `pytest`, `httpx`, `jsonschema`, `ruff`, and `pyyaml` when the spec is YAML, `uv sync` succeeded there, and aksa's `pyproject.toml` and `uv.lock` are unchanged.
- Nothing outside the engagement folder changed, and the reply names the artifact, every operation covered, the authentication basis, and each command's result.

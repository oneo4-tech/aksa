# API test layout

The shape of the suite `write-api-tests` writes, read before planning and writing in Procedure steps 4 and 5. The engagement folder is `.projects/testing/<engagement>/`; every path below is relative to it, and every `<...>` placeholder in a code sample is replaced with the engagement's value.

## Files

```text
pyproject.toml            the engagement's project and tool settings
tests/api/
  conftest.py             base URL, credentials, and HTTP client fixtures
  schemas.py              JSON Schema loading and validation
  schemas/
    order.json            one schema per response body
    order-list.json
  test_orders.py          one module per resource
```

- Keep fixtures in `conftest.py` under the API test folder, never in a root conftest, so the UI suite keeps its own.
- One module per resource: the first path segment of its endpoints after any version prefix such as `/v1`, such as `orders` for `GET /v1/orders` and `POST /v1/orders/{id}`.
- Shared HTTP and schema code lives in `conftest.py` and `schemas.py` only; a test module holds tests, not helpers.

## pyproject.toml

Create it when absent and otherwise add only what is missing. Keep entries another workflow added, such as Playwright.

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "jsonschema>=4.22", "pytest>=8.2", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: runs against the client's application under test"]

[tool.ruff]
line-length = 120
```

- One `live` marker serves the API and UI suites, so its description names neither; an existing one worded for one suite only is reworded to this one.
- Run `uv sync` in the engagement folder after writing it.

## conftest.py

```python
import os

import httpx
import pytest

BASE_URL = os.environ.get("API_BASE_URL", "<api_base_url from the brief>")
CREDENTIAL_ENV = "<credentials_env name>"


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def auth_headers() -> dict[str, str]:
    if not os.environ.get(CREDENTIAL_ENV):
        pytest.fail(f"set {CREDENTIAL_ENV} in the environment before running these tests")
    return {"Authorization": f"Bearer {os.environ[CREDENTIAL_ENV]}"}


@pytest.fixture(scope="session")
def client(api_base_url: str, auth_headers: dict[str, str]):
    with httpx.Client(base_url=api_base_url, headers=auth_headers, timeout=15.0) as http:
        yield http


@pytest.fixture(scope="session")
def unauthenticated_client(api_base_url: str):
    with httpx.Client(base_url=api_base_url, timeout=15.0) as http:
        yield http
```

- The default base URL is the brief's `api_base_url`; `API_BASE_URL` lets the owner point the same tests at another environment without editing a file.
- `unauthenticated_client` sends no credential; the authentication checks use it.
- A public API, one that needs no authentication by the skill's Inputs, gets no `CREDENTIAL_ENV`, `auth_headers`, or `unauthenticated_client`, and `client` is built without `headers`, so the suite reads no credential.
- Map each `credentials_env` name to the header the authentication scheme in `api_spec` names. With no spec, use the bearer `Authorization` header and name that assumption in the reply.
- `conftest.py` reads `os.environ` only. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads the engagement `.env` into the test process at run time, so no value is copied into a file. A missing `.env` fails the command with uv's `error: No environment file found at:` followed by the `.env` path.
- A missing variable fails the fixture with its name. It never becomes a skip.

## Test modules

One test per check, named for the behaviour and its expected result, with the case and trace ids in the docstring:

```python
@pytest.mark.live
def test_create_order_returns_201(client):
    """TC-004; AC2, R1"""
    response = client.post("/orders", json={"sku": "SKU-1", "quantity": 1})
    assert response.status_code == 201
    assert response.json()["quantity"] == 1
    assert_valid_json(response.json(), "order")


@pytest.mark.live
def test_read_order_matches_the_created_order(client):
    """TC-005; AC3, R2"""
    created = client.post("/orders", json={"sku": "SKU-1", "quantity": 2})
    assert created.status_code == 201
    response = client.get(f"/orders/{created.json()['id']}")
    assert response.status_code == 200
    assert response.json()["items"] == created.json()["items"]
    assert response.json()["total"] == created.json()["total"]
```

- Success checks use the fixture client, assert the status, then every body value and comparison the case states, such as a quantity or a total equal between two responses. A schema check is added beside them, never in their place.
- Error checks use the same client with input the cases name, and assert the status and only the error fields the spec fixes. Never assert a message text the spec does not fix. Where the spec fixes the error body, validate it with `assert_valid_json(response.json(), "<resource>-error")`.
- Authentication checks, only when the API needs authentication, run once per endpoint through `pytest.mark.parametrize` over the module's paths, both with `unauthenticated_client`: one sending no token, one sending an invalid token such as `headers={"Authorization": "Bearer invalid"}`, both asserting the status that `api_spec` or the cases give.
- Response-schema checks call `assert_valid_json(response.json(), "<schema>")` after the status assertion.

## schemas.py

```python
import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMAS = Path(__file__).parent / "schemas"


def assert_valid_json(body: object, name: str) -> None:
    schema = json.loads((SCHEMAS / f"{name}.json").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(body), key=lambda error: list(error.path))
    assert not errors, "; ".join(f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors)
```

- Each schema file is a Draft 2020-12 JSON Schema: `$schema`, `type`, `required`, and `properties` taken from the response in `api_spec`.
- Name a schema per response body, such as `order.json` and `order-list.json`, not per endpoint.
- Without an `api_spec`, copy only the fields, types, and nesting that the case's expected result states, and name that basis in the reply.
- Where a case requires a non-empty value, add `minLength: 1` to the string or `minItems: 1` to the array, with or without a spec, such as a product list whose case requires at least one product with a non-empty `name`.
- Leave objects open with `additionalProperties` unset unless the spec closes them; a new field is not a defect unless the client says so.

## Live versus collect-only

- Every test that sends a request carries `@pytest.mark.live`. The marker is registered in `pyproject.toml` and a plain `pytest` run includes those tests.
- The live run is `uv run --env-file .env pytest`, run from the engagement folder. `uv` loads the engagement `.env` into the test process environment at run time and `conftest.py` reads it through `os.environ`; no value is copied into a file. `uv run` without `--env-file` leaves the variables unset and the fixture fails with the missing name.
- The authoring gate is `uv run pytest --collect-only -q`. Collection imports each module and loads `conftest.py`, but runs no fixture, reads no credential, and sends no request, so it passes with no server and no `.env`.
- Never add `skip`, `skipif`, `pytest.importorskip`, or `xfail` to make collection pass. A check that cannot be written is a stop, reported through the skill.
- One node id appears per planned test. Count them and compare with the plan from Procedure step 4.

## Independence

- A test creates the data it needs in the same test and never relies on another test's state or order.
- Use a unique value per test, such as the case id plus `uuid4()`, for anything the API stores.
- No module-level request, credential read, or network call; only constants and fixtures.

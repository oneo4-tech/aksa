# Contract test template

The shape of the suite `write-contract-tests` writes, read before planning and writing in Procedure steps 4 and 5. The engagement folder is `.projects/testing/<engagement>/`; every path below is relative to it, and every `<...>` placeholder is replaced with the engagement's value.

## Files

```text
pyproject.toml            the engagement's project and tool settings
tests/contract/
  conftest.py             the base URL and HTTP client
  openapi.py              spec loading, operation list, request builder, and schema check
  test_contract.py        one live test per operation, parametrized over the spec
```

- `conftest.py` holds fixtures only. Every spec rule lives in `openapi.py`, so the test module stays one short check per operation.
- `openapi.py` reads the spec at import. That import needs no server, no `.env`, and no credential value, which is what lets `pytest --collect-only` pass before a live run.
- The test module holds no endpoint list: it is parametrized over `openapi.OPERATIONS`, so every operation in the spec is collected or the spec is refused in Procedure step 4.
- Existing files are read first and updated; never overwrite an operation check another run added without reporting the change.

## pyproject.toml

Create it when absent and otherwise add only what is missing. Keep entries another workflow added, such as Playwright or Locust.

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "jsonschema>=4.22", "pytest>=8.2", "pyyaml>=6.0", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: runs against the client's application under test"]

[tool.ruff]
line-length = 120

[tool.ruff.lint.isort]
known-first-party = ["openapi"]
```

- `pyyaml` is added only when `api_spec` is YAML. A JSON spec needs no `pyyaml` and no `yaml` import.
- `known-first-party` keeps `from openapi import ...` in its own block; when the engagement already has the setting, add `openapi` and keep every existing entry.
- One `live` marker serves every suite, so its description names none.
- Run `uv sync` in the engagement folder after writing it.

## conftest.py

```python
import os

import httpx
import pytest

BASE_URL = os.environ.get("API_BASE_URL", "<api_base_url from the brief>")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as http:
        yield http
```

- The default base URL is the brief's `api_base_url`; `API_BASE_URL` lets the owner point the same tests at another environment without editing a file. The spec's `servers` are not read, because the brief decides the environment.
- No credential is read here. `openapi.py` reads a name only when the operation it is checking is secured.

## openapi.py

```python
"""Build a contract request and schema check from the OpenAPI file the brief names."""

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ENGAGEMENT = Path(__file__).resolve().parents[2]
SPEC_PATH = ENGAGEMENT / "<api_spec from the brief>"
SCHEMA_REF = "#/components/schemas/"
HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

# From the spec's single security scheme; None when the spec is public.
SECURITY: dict[str, Any] | None = {"type": "http", "scheme": "basic"}
USERNAME_ENV = "<basic username variable from credentials_env>"
PASSWORD_ENV = "<basic password variable from credentials_env>"
TOKEN_ENV = ""


def load_spec(path: Path) -> dict[str, Any]:
    """The spec as a mapping: JSON by suffix, YAML otherwise."""
    text = path.read_text(encoding="utf-8")
    document = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    if not isinstance(document, dict) or not document.get("paths"):
        raise ValueError(f"{path}: no OpenAPI paths")
    return document


DOCUMENT = load_spec(SPEC_PATH)


@dataclass(frozen=True)
class Operation:
    """One method and path in the spec, with everything its check needs."""

    method: str
    path: str
    operation_id: str
    parameters: tuple[dict[str, Any], ...]
    request_body: dict[str, Any] | None
    responses: dict[str, Any]
    security: tuple[dict[str, Any], ...]

    @property
    def id(self) -> str:
        return self.operation_id or f"{self.method} {self.path}"


def operations() -> list[Operation]:
    """Every operation in the spec, in path order."""
    found: list[Operation] = []
    for path, item in DOCUMENT["paths"].items():
        if "$ref" in item:
            raise ValueError(f"{path}: path item $ref is not supported")
        shared = item.get("parameters", [])
        for method, detail in item.items():
            if method not in HTTP_METHODS:
                continue
            found.append(
                Operation(
                    method=method.upper(),
                    path=path,
                    operation_id=detail.get("operationId", ""),
                    parameters=tuple(shared + detail.get("parameters", [])),
                    request_body=detail.get("requestBody"),
                    responses=detail["responses"],
                    security=tuple(detail.get("security", DOCUMENT.get("security", []))),
                )
            )
    return found


OPERATIONS = operations()


def dereference(node: dict[str, Any]) -> dict[str, Any]:
    """The target of a local `$ref`, or the node itself."""
    ref = node.get("$ref")
    if ref is None:
        return node
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported external $ref: {ref}")
    target: Any = DOCUMENT
    for part in ref[2:].split("/"):
        target = target[part]
    return target


def example_value(node: dict[str, Any]) -> Any:
    """The node's `example`, or the first `examples` entry, when it gives one."""
    if "example" in node:
        return node["example"]
    examples = node.get("examples")
    if isinstance(examples, dict):
        for example in examples.values():
            return example.get("value") if isinstance(example, dict) else example
    return None


def schema_value(schema: dict[str, Any]) -> Any:
    """The schema's `example`, `default`, or first `enum` value, when it gives one."""
    resolved = dereference(schema or {})
    for key in ("example", "default"):
        if key in resolved:
            return resolved[key]
    values = resolved.get("enum")
    return values[0] if values else None


def parameter_value(operation: Operation, parameter: dict[str, Any]) -> Any:
    """A parameter's value from the spec, or None for an optional parameter without one."""
    value = example_value(parameter)
    if value is None:
        value = schema_value(parameter.get("schema", {}))
    if value is None and (parameter.get("required") or parameter["in"] == "path"):
        raise ValueError(f"{operation.id}: required {parameter['in']} parameter '{parameter['name']}' has no example")
    return value


def schema_example(schema: dict[str, Any], operation: Operation, path: str) -> Any:
    """A body example built only from the schema's examples, defaults, and required properties."""
    resolved = dereference(schema or {})
    value = schema_value(resolved)
    if value is not None:
        return value
    if resolved.get("type") == "object" or "properties" in resolved:
        example = {}
        for name in resolved.get("required", []):
            example[name] = schema_example(resolved["properties"][name], operation, f"{path}.{name}")
        return example
    if resolved.get("type") == "array":
        item = resolved.get("items", {})
        return [schema_example(item, operation, f"{path}[]") for _ in range(resolved.get("minItems", 0))]
    raise ValueError(f"{operation.id}: required value '{path}' has no example in the spec")


def request_body(operation: Operation) -> Any:
    """The JSON body example from the spec, or None when the operation sends none."""
    body = operation.request_body
    if not body:
        return None
    media = dereference(body).get("content", {}).get("application/json")
    if media is None:
        raise ValueError(f"{operation.id}: request body is not application/json")
    value = example_value(media)
    return value if value is not None else schema_example(media.get("schema", {}), operation, "body")


@dataclass(frozen=True)
class Request:
    """A request built from one operation's spec entries."""

    path: str
    params: dict[str, Any]
    headers: dict[str, str]
    body: Any


def build_request(operation: Operation) -> Request:
    """Fill the path template and collect the query and header values the spec gives."""
    path = operation.path
    params: dict[str, Any] = {}
    headers: dict[str, str] = {}
    for parameter in operation.parameters:
        parameter = dereference(parameter)
        value = parameter_value(operation, parameter)
        if value is None:
            continue
        if parameter["in"] == "path":
            path = path.replace("{" + parameter["name"] + "}", str(value))
        elif parameter["in"] == "query":
            params[parameter["name"]] = value
        elif parameter["in"] == "header":
            headers[parameter["name"]] = str(value)
        else:
            raise ValueError(f"{operation.id}: unsupported parameter location '{parameter['in']}'")
    return Request(path=path, params=params, headers=headers, body=request_body(operation))


def expected_status(operation: Operation) -> int:
    """The lowest documented 2xx, or the first documented code when there is no 2xx."""
    codes = sorted((str(code) for code in operation.responses if str(code).isdigit()), key=int)
    if not codes:
        raise ValueError(f"{operation.id}: no numeric response status in the spec")
    successes = [code for code in codes if code.startswith("2")]
    return int(successes[0] if successes else codes[0])


def response_schema(operation: Operation, status: int) -> dict[str, Any] | None:
    """The JSON schema the spec gives for a status; None only for a response with no content."""
    response = operation.responses.get(str(status))
    if response is None:
        response = operation.responses.get(status) or operation.responses.get("default")
    if response is None:
        raise ValueError(f"{operation.id}: no documented response for status {status}")
    content = dereference(response).get("content")
    if not content:
        return None
    media = content.get("application/json")
    if media is None:
        raise ValueError(f"{operation.id}: status {status} has no application/json body")
    schema = media.get("schema")
    if schema is None:
        raise ValueError(f"{operation.id}: status {status} documents no schema")
    return schema


def rewrite(node: Any) -> Any:
    """Rewrite every component schema `$ref` into the `$defs` document below."""
    if isinstance(node, dict):
        return {key: rewrite_ref(value) if key == "$ref" else rewrite(value) for key, value in node.items()}
    if isinstance(node, list):
        return [rewrite(item) for item in node]
    return node


def rewrite_ref(ref: str) -> str:
    if not ref.startswith(SCHEMA_REF):
        raise ValueError(f"unsupported schema $ref: {ref}")
    return "#/$defs/" + ref[len(SCHEMA_REF) :]


def schema_with_defs(schema: dict[str, Any]) -> dict[str, Any]:
    """The schema beside every component schema, so jsonschema resolves nested and recursive refs."""
    local = rewrite(schema)
    definitions = {**rewrite(DOCUMENT.get("components", {}).get("schemas", {})), **local.pop("$defs", {})}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": definitions,
        **local,
    }


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"set {name} in the environment before running these tests")
    return value


def auth_headers(operation: Operation) -> dict[str, str]:
    """Headers for one operation from the names in credentials_env; empty for a public operation."""
    if not operation.security:
        return {}
    if SECURITY is None:
        raise ValueError(f"{operation.id}: the spec marks security but defines no scheme")
    kind = SECURITY.get("type")
    scheme = SECURITY.get("scheme")
    if kind == "http" and scheme == "basic":
        pair = f"{required_env(USERNAME_ENV)}:{required_env(PASSWORD_ENV)}"
        return {"Authorization": "Basic " + base64.b64encode(pair.encode()).decode()}
    if (kind == "http" and scheme == "bearer") or kind in ("oauth2", "openIdConnect"):
        return {"Authorization": "Bearer " + required_env(TOKEN_ENV)}
    if kind == "apiKey" and SECURITY.get("in") == "header":
        return {SECURITY["name"]: required_env(TOKEN_ENV)}
    raise ValueError(f"{operation.id}: unsupported security scheme {SECURITY}")


def assert_matches_schema(body: Any, schema: dict[str, Any], label: str) -> None:
    """Fail with each JSON path that breaks the spec's schema, required fields included."""
    validator = Draft202012Validator(schema_with_defs(schema))
    errors = sorted(validator.iter_errors(body), key=lambda error: list(error.path))
    assert not errors, f"{label}: " + "; ".join(
        f"{'/'.join(map(str, error.path))}: {error.message}" for error in errors
    )
```

- For a JSON spec, replace `load_spec` with `json.loads(path.read_text())` and remove the `yaml` import and the `pyyaml` dependency.
- Set `SPEC_PATH` from the brief's `api_spec`, and `API_BASE_URL` stays in `conftest.py`.
- `SECURITY`, `USERNAME_ENV`, `PASSWORD_ENV`, and `TOKEN_ENV` are copied from the spec's one scheme and the brief's names. For basic, use the two names whose suffixes identify a username and a password; for bearer or `apiKey`, the one whose suffix identifies a token. When the brief gives no unambiguous choice, stop and name the scheme and the names rather than guessing. For a public spec set `SECURITY = None` and remove `base64`, the three credential constants, and `auth_headers`; `test_contract.py` then sends `request.headers` alone.
- `dereference` follows any local `#/...` pointer for parameters, bodies, and responses. `rewrite` allows only `#/components/schemas/` inside a schema, because that is the pointer `jsonschema` resolves through `$defs`. An external `$ref` and a path item given as `$ref` are stops, refused at import rather than skipped.
- `expected_status` takes a numeric response code; a spec that uses a range such as `2XX` instead of a number is a stop in Procedure step 4, not a guessed status.
- The validator is Draft 2020-12. OpenAPI 3.0's `nullable` is not a JSON Schema keyword, so it is not enforced; a schema keyword `jsonschema` rejects is a stop naming the operation, not a skipped check.
- No function reads a credential until `auth_headers` is called by a secured operation at run time. No value is logged.

## test_contract.py

```python
import pytest

from openapi import OPERATIONS, assert_matches_schema, auth_headers, build_request, expected_status, response_schema


@pytest.mark.live
@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda operation: operation.id)
def test_operation_matches_the_spec(operation, client):
    """One check per operation: spec-built request, documented status, schema-checked body."""
    request = build_request(operation)
    kwargs = {"params": request.params, "headers": {**request.headers, **auth_headers(operation)}}
    if request.body is not None:
        kwargs["json"] = request.body
    response = client.request(operation.method, request.path, **kwargs)
    status = expected_status(operation)
    assert response.status_code == status, response.text
    schema = response_schema(operation, status)
    if schema is not None:
        assert_matches_schema(response.json(), schema, operation.id)
```

- One parametrized test collects one node per operation. The node id is the `operationId`, or the method and path when the spec gives none.
- The status assertion is the spec's documented success status; the body assertion is that status's schema, so every `required` entry in the spec is checked. Never tighten or relax one.
- A response with no JSON content, such as a 204, has no schema call. It is still status-checked.
- `test_contract.py` and `openapi.py` are not cases: no `TC-<nnn>` id appears here. The case-based suite is `write-api-tests`'s, built from the cases.

## Live versus collect-only

- Every test carries `@pytest.mark.live`. The marker is registered in `pyproject.toml`.
- The live run is `uv run --env-file .env pytest`, run from the engagement folder. `uv` loads the engagement `.env` into the test process environment at run time and `openapi.py` reads it through `os.environ`; no value is copied into a file.
- The authoring gate is `uv run pytest --collect-only -q`. Collection imports the spec and builds the operation list, but sends no request and reads no credential.
- Never add `skip`, `skipif`, `pytest.importorskip`, or `xfail` to make collection pass. A spec entry that cannot be checked is a stop in Procedure step 4.

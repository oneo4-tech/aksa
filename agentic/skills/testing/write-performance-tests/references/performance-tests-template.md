# Performance test template

The shape of the suite `write-performance-tests` writes, read before planning and writing in Procedure steps 3 and 6. The engagement folder is `.projects/testing/<engagement>/`; every path below is relative to it, and every `<...>` placeholder is replaced with the engagement's value.

## Files

```text
pyproject.toml                the engagement's project and tool settings
tests/performance/
  targets.py                  one Target per brief entry: text, cases, load profile
  locustfile.py               one Locust HttpUser scenario per target and SCENARIOS
  test_scenarios.py           pytest shape tests, no server and no load
  README.md                   targets, cases, load profile, and run commands
```

- `targets.py` is the one table: every number in `locustfile.py`, the shape test, and the README comes from it, so they cannot disagree.
- `locustfile.py` holds only scenarios and the `SCENARIOS` map. Locust finds the classes when the owner runs `locust -f tests/performance/locustfile.py`.
- `test_scenarios.py` is the pytest shape test. A folder with no collectable test exits 5, so this file is what makes `pytest --collect-only tests/performance` pass.
- Existing files are read first and updated; never overwrite a scenario another run added without reporting the change.

## pyproject.toml

Create it when absent and otherwise add only what is missing. Keep entries another workflow added, such as Playwright or `jsonschema`.

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["locust>=2.31", "pytest>=8.2", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: runs against the client's application under test"]

[tool.ruff]
line-length = 120

[tool.ruff.lint.isort]
known-first-party = ["locustfile", "targets"]
```

- `known-first-party` keeps `locustfile` and `targets` in their own import block; when the engagement already has the setting, add both and keep every existing entry.
- The `live` marker is kept when another suite registered it; the shape test is not live because it starts no load.
- `locust` must be synced before collection: `test_scenarios.py` imports `locustfile.py`, which imports `locust`.
- Run `uv sync` in the engagement folder after writing it.

## targets.py

```python
from dataclasses import dataclass

USERS = 10
SPAWN_RATE = 2.0
DURATION = "1m"


@dataclass(frozen=True)
class Target:
    """One brief target, the cases behind it, and the load profile used to exercise it."""

    name: str
    target: str
    cases: tuple[str, ...]
    users: int = USERS
    spawn_rate: float = SPAWN_RATE
    duration: str = DURATION


TARGETS = (Target("<target key>", "<target text verbatim>", ("<TC-nnn>",)),)

BY_NAME = {target.name: target for target in TARGETS}
```

- The target text is copied verbatim from `performance_targets`; never paraphrase or invent one.
- `cases` holds the `TC-<nnn>` ids the target maps to, as Procedure step 3 records them.
- `USERS`, `SPAWN_RATE`, and `DURATION` are this workflow's default because the brief gives no load profile. When the owner supplies one, change it here once and rerun Procedure step 6, so the scenarios, shape test, and README follow.

## locustfile.py

```python
import os

from locust import HttpUser, task

from targets import BY_NAME

HOST = os.environ.get("API_BASE_URL", "<api_base_url from the brief>")
USER_ENV = "<basic username variable from credentials_env>"
PASSWORD_ENV = "<basic password variable from credentials_env>"


def basic_auth() -> tuple[str, str]:
    missing = [name for name in (USER_ENV, PASSWORD_ENV) if not os.environ.get(name)]
    if missing:
        raise RuntimeError("set " + ", ".join(missing) + " before running this load")
    return os.environ[USER_ENV], os.environ[PASSWORD_ENV]


class <TargetName>(HttpUser):
    host = HOST
    target = BY_NAME["<target key>"].target
    users = BY_NAME["<target key>"].users
    spawn_rate = BY_NAME["<target key>"].spawn_rate
    duration = BY_NAME["<target key>"].duration

    def on_start(self) -> None:
        self.client.auth = basic_auth()

    @task
    def <request_name>(self) -> None:
        self.client.get("<path>", name="GET <path>")


SCENARIOS = {
    "<target key>": <TargetName>,
}
```

- One class per target, named for the target, so `SCENARIOS` has exactly one scenario per brief entry.
- An endpoint target has one task. A flow target has one task that sends the case's requests in order and names each in Locust statistics, such as:
  `created = self.client.post("/carts", json={"productId": "<case value>", "quantity": <case value>}, name="POST /carts")`,
  then `created.raise_for_status()` and `self.client.get(f"/carts/{created.json()['id']}", name="GET /carts/{cartId}")`.
  The body and values come from the case's steps.
- `host` is the brief's `api_base_url`, with `API_BASE_URL` as the environment override.
- Credentials are included only when the cases name them. Basic auth uses two `credentials_env` names, a bearer token one, read in `on_start` so collection and import read nothing. With no credentials in the cases, remove `on_start`, the constants, and the helper.
- No module-level request, load, or credential read: only constants, classes, and `SCENARIOS`.

## test_scenarios.py

```python
import pytest

import locustfile
from targets import TARGETS, Target


def test_every_target_has_a_scenario() -> None:
    assert set(locustfile.SCENARIOS) == {target.name for target in TARGETS}


@pytest.mark.parametrize("target", TARGETS, ids=lambda target: target.name)
def test_scenario_records_its_target_and_load_profile(target: Target) -> None:
    scenario = locustfile.SCENARIOS[target.name]
    assert scenario.target == target.target
    assert scenario.users == target.users
    assert scenario.users >= 1
    assert scenario.spawn_rate == target.spawn_rate
    assert scenario.spawn_rate > 0
    assert scenario.duration == target.duration
```

- The coverage test fails when a target has no scenario and when a scenario has no target.
- The parametrized test collects one node per target and checks the target text and all three load-profile values against `targets.py`.
- These tests start no load and send no request; they need no `.env` and no server. `pytest --collect-only` collects them after importing `locust`.

## README.md

```markdown
# Performance scenarios: <client> <engagement>

- Cases: `docs/test-cases.md`
- Host: the brief's `api_base_url`
- Authoring: no load was run while these files were written.

## Targets

| Target | Brief target | Cases | Requests |
|---|---|---|---|
| <target key> | <target text> | <TC-nnn> | <METHOD /path> |

## Load profile

| Target | Users | Spawn rate | Duration |
|---|---|---|---|
| <target key> | <users> | <spawn rate> users/s | <duration> |

The brief gives a target, not a load. This profile is `write-performance-tests`'s default, because the brief states none; the owner confirms or changes it, then reruns the workflow.

## Run

```bash
uv run --env-file .env locust -f tests/performance/locustfile.py <TargetName> --headless -u <users> -r <spawn-rate> -t <duration>
```
```

- Name every target, case, and request, and repeat the profile from `targets.py`. Keep the README short: a table and the run command, not a report.
- The run command loads `.env` at run time; no value is written here. Drop `--env-file .env` when the scenarios send no credential.
- With more than one scenario, give one command per class, as the table in Procedure step 6 lists.

## No load during authoring

- The authoring gate is `uv run pytest --collect-only -q` from the engagement folder. It imports the scenarios, checks the shape test's collection, and sends nothing.
- Never run `locust`, `pytest` without `--collect-only`, or any load. The owner runs the load from the README command after the workflow reports.
- Never add `skip`, `skipif`, `pytest.importorskip`, or `xfail` to make collection pass. A target that cannot be written is a stop in Procedure step 2.

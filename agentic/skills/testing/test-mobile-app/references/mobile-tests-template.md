# Mobile test template

The shape of the suite `test-mobile-app` writes, read before planning and writing in Procedure steps 4 and 5. The engagement folder is `.projects/testing/<engagement>/`; every path below is relative to it, and every `<...>` placeholder is replaced with the engagement's value. The target is a mobile web browser: native apps are out of scope.

## Files

```text
pyproject.toml            the engagement's project and tool settings
tests/mobile/
  __init__.py             makes the mobile suite a package, so its module names cannot collide with tests/ui
  conftest.py             base URL, device parameter, browser, context, page, and sign-in fixtures
  test_mobile_<journey>.py  one module per UI journey
```

- Keep every fixture in the suite's `conftest.py`, never in a root conftest, so the desktop UI and API suites keep their own.
- One module per UI journey from `docs/test-cases.md`; one test per case in it. The module name carries the `mobile` prefix and the folder carries `__init__.py`, so a journey the desktop UI suite also has collects without an `import file mismatch`. A test's device comes from the `device` fixture, so its node id carries the device.
- Shared browser and sign-in code lives in `conftest.py` only; a test module holds tests, not helpers.
- Existing files are read first and updated; never overwrite a test another run added without reporting the change.

## pyproject.toml

Create it when absent and otherwise add only what is missing. Keep entries another workflow added, such as `httpx`, `jsonschema`, or `locust`.

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["playwright>=1.46", "pytest>=8.2", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: runs against the client's application under test"]

[tool.ruff]
line-length = 120
```

- One `live` marker serves every suite, so its description names none. An existing one worded for one suite only is reworded to this one.
- `playwright` is the sync API from the package; `pytest-playwright` is not needed.
- Run `uv sync` in the engagement folder after writing it.

## conftest.py

```python
import os

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

BASE_URL = os.environ.get("UI_BASE_URL", "<ui_base_url from the brief>")
DEVICES = ("<device from mobile_devices>", "<device from mobile_devices>")
USER_ENV = "<username variable from credentials_env>"
PASSWORD_ENV = "<password variable from credentials_env>"


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(params=DEVICES)
def device(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def context(playwright_instance: Playwright, device: str) -> BrowserContext:
    descriptor = dict(playwright_instance.devices[device])
    browser_type = descriptor.pop("default_browser_type")
    browser: Browser = getattr(playwright_instance, browser_type).launch()
    context = browser.new_context(base_url=BASE_URL, **descriptor)
    yield context
    context.close()
    browser.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    return context.new_page()


@pytest.fixture
def signed_in_page(page: Page) -> Page:
    for name in (USER_ENV, PASSWORD_ENV):
        if not os.environ.get(name):
            pytest.fail(f"set {name} in the environment before running these mobile tests")
    page.goto("<sign-in page path from the cases>")
    page.get_by_label("<email label from the cases>").fill(os.environ[USER_ENV])
    page.get_by_label("<password label from the cases>").fill(os.environ[PASSWORD_ENV])
    page.get_by_role("button", name="<sign-in control from the cases>").click()
    return page
```

- `DEVICES` is copied from the brief's `mobile_devices`, one name per entry. Do not add, remove, or rename a device. Every name is a key in `playwright_instance.devices`.
- The descriptor is copied and its `default_browser_type` removed before it reaches `new_context`, because that key is not a context option. The same value chooses the browser to launch: `chromium` for an Android device, `webkit` for an iPhone, as the registry says.
- `context` and `page` are function-scoped, so every test and every device gets a fresh browser context and page. No storage state, cookie, or session crosses a test.
- `signed_in_page` signs in through the page the case describes, inside that test's context. Use it only for a case that starts signed in. Each credential is read through `os.environ` by a name in `credentials_env`; a missing name fails with its name, never a skip. A case that starts signed out uses `page`.
- The base URL is the brief's `ui_base_url`; `UI_BASE_URL` lets the owner point the same tests at another environment without editing a file.
- `conftest.py` imports cleanly with no browser installed and no `.env`: `sync_playwright` starts only when the fixture runs, and no credential is read at import.

## Test modules

Give each module a one-line docstring, `Mobile web only; native apps are out of scope.`, then one test per case, named for the journey and its expected result, with the case and trace ids in the docstring:

```python
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.live
def test_mobile_<journey>_<outcome>(signed_in_page: Page) -> None:
    """TC-<nnn>; AC<n>, R<n>; mobile web"""
    signed_in_page.goto("<page path>")
    expect(signed_in_page.get_by_role("heading", name="<heading from the case>")).to_be_visible()
    expect(signed_in_page.get_by_text("<value the case states>")).to_be_visible()
```

- Locate by role and accessible name, then by label, then by the visible text the case quotes. Never invent an accessible name, label, or element.
- Assert every value the expected result states, such as a price or a total, with `to_contain_text` or `to_have_text`; visibility alone never proves a stated value.
- Create data inside the test, in the order the case's steps give, and use only values the case or the brief supplies. A test must not rely on another test's state or order.
- No fixed sleep: use Playwright's `expect`, which waits for the outcome. No module-level browser, navigation, or credential read: only imports and constants.
- A case that starts signed out uses the `page` fixture and its own sign-in steps when it needs an account.

## Device coverage

- Every UI case runs once per device in `DEVICES`: the `device` fixture is parametrized, so `pytest --collect-only` shows one node per case per device.
- The node id carries the device, such as `test_cart_page_shows_the_total[Pixel 7]`, so the reply can count coverage per device and journey.
- A device the brief does not name is never added, even when the Playwright registry has it. A name that is not in the registry is a stop in Procedure step 2, not a substitution.

## Live versus collect-only

- Every test carries `@pytest.mark.live`. The marker is registered in `pyproject.toml`.
- The owner's live run is `uv run playwright install` once, then `uv run --env-file .env pytest` from the engagement folder. `uv` loads the engagement `.env` into the test process environment at run time; no value is copied into a file.
- The authoring gate is `uv run pytest --collect-only -q tests/mobile`, followed by `uv run pytest --collect-only -q` over the whole engagement. Collection imports each module and loads `conftest.py`, but starts no browser, reads no credential, and needs no browser binaries, so it passes with no `playwright install` and no `.env`.
- Never run `pytest` without `--collect-only`, never launch a browser, and never add `skip`, `skipif`, `pytest.importorskip`, or `xfail` to make collection pass. A test that cannot be written is a stop in Procedure step 2.

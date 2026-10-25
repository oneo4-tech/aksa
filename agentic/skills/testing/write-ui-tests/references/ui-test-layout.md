# UI test layout

The shape of the suite `write-ui-tests` writes, read before planning and writing in Procedure steps 4 and 5. The engagement folder is `.projects/testing/<engagement>/`; every path below is relative to it, and every `<...>` placeholder in a code sample is replaced with the engagement's value.

## Files

```text
pyproject.toml            the engagement's project and tool settings
.env                      values for credentials_env, supplied by the owner; never written here
tests/ui/
  conftest.py             base URL, browser, context, page, and sign-in fixtures
  pages/
    __init__.py           makes the page objects importable
    base_page.py          the page object base: its path and open()
    sign_in_page.py       the sign-in page, when a case starts signed in
    checkout_page.py      one module per page, named for the page
  test_checkout.py        one module per journey
```

- Keep fixtures in `conftest.py` under the UI test folder, never in a root conftest, so the API suite keeps its own.
- One page object per page the journeys visit, even a page one journey uses.
- Page objects hold locators and actions; test modules hold tests and assertions.

## pyproject.toml

Create it when absent and otherwise add only what is missing. Keep entries another workflow added, such as `httpx` and `jsonschema` from `write-api-tests`.

```toml
[project]
name = "<engagement>-tests"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["playwright>=1.46", "pytest>=8.2", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: drives a browser against the UI under test"]

[tool.ruff]
line-length = 120

[tool.ruff.lint.isort]
known-first-party = ["pages"]
```

- Add only the dependencies that are missing. An existing `live` marker keeps its description; do not add a second one.
- `known-first-party` keeps the page-object imports in their own group; without it `ruff check` sorts them in with `playwright` and fails.
- Run `uv sync` in the engagement folder after writing it. `uv sync` installs the Python packages only, never the browser binaries.

## conftest.py

```python
import os

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from pages.sign_in_page import SignInPage

BASE_URL = os.environ.get("UI_BASE_URL", "<ui_base_url from the brief>")
USER_ENV = "<credentials_env user name>"
PASSWORD_ENV = "<credentials_env password name>"


@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    context = browser.new_context(base_url=BASE_URL)
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    return context.new_page()


@pytest.fixture
def signed_in_page(page: Page) -> Page:
    for name in (USER_ENV, PASSWORD_ENV):
        if not os.environ.get(name):
            pytest.fail(f"set {name} in the environment before running these tests")
    SignInPage(page).sign_in(os.environ[USER_ENV], os.environ[PASSWORD_ENV])
    return page
```

- The default base URL is the brief's `ui_base_url`; `UI_BASE_URL` lets the owner point the same tests at another environment without editing a file.
- Omit `signed_in_page` and its import when no case starts signed in, and then read no credential at all.
- The browser fixture starts one browser per session and gives each test its own context and page, so a test never sees another test's cookies or storage. Launch the browser the cases name, `chromium` when they name none.
- `conftest.py` reads `os.environ` only. The owner's run command, `uv run --env-file .env pytest` from the engagement folder, loads the engagement `.env` into the test process at run time, so no value is copied into a file. A missing `.env` fails that command with `No environment file found at:` and the path.
- A missing variable fails its fixture with its name. It never becomes a skip.

## Page objects

`pages/base_page.py` holds the path and the navigation every page shares:

```python
from playwright.sync_api import Page


class BasePage:
    path = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        self.page.goto(self.path)
```

One subclass per page, with the locators and actions the cases name:

```python
from playwright.sync_api import Page

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    path = "/checkout"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Checkout")
        self.pay_button = page.get_by_role("button", name="Pay")
        self.confirmation = page.get_by_role("heading", name="Order confirmed")
        self.total = page.get_by_text("Total")

    def pay(self) -> None:
        self.pay_button.click()
```

- `path` comes from the case steps, such as "open `/checkout`". Never guess a path.
- Locators are set in `__init__` from the accessible names the cases state, and never queried in a test module.
- Actions are methods named for what the user does. Assertions stay in the test, so the case's expected result is visible there.
- A page whose case names no path gets no page object: stop and name the case to `design-test-cases`.

## Selector policy

1. **Role and accessible name first:** `page.get_by_role("button", name="Pay")`, `page.get_by_role("textbox", name="Email")`, `page.get_by_role("heading", name="Checkout")`.
2. **Label next:** `page.get_by_label("Email")` when the case names the field's label.
3. **Quoted text:** `page.get_by_text("Order confirmed")` only when the case quotes visible text and names no role or label.
4. **CSS or XPath last:** only when the case names none of the above. Leave a comment on the locator giving the reason, and report the exception in the reply.
- Never invent an accessible name, label, text, or element, and never use a selector copied from a similar page.
- Prefer `to_be_visible`, `to_have_text`, and `to_be_enabled` from `expect`; they wait for the condition. Never use a fixed sleep.
- A locator that matches more than one element is fixed with a more precise role or label from the case, not with `.first` or an index.

## Test modules

One module per journey, named `test_<journey>.py`, with one test per case:

```python
import pytest
from playwright.sync_api import Page, expect

from pages.checkout_page import CheckoutPage


@pytest.mark.live
def test_checkout_confirms_the_order(page: Page) -> None:
    """TC-007; AC2, R3"""
    checkout = CheckoutPage(page)
    checkout.open()
    checkout.pay()
    expect(checkout.confirmation).to_be_visible()
    expect(checkout.total).to_have_text("Total 19.98")
```

- A test with a signed-in precondition takes `signed_in_page` instead of `page`.
- The docstring names the `TC-<nnn>` case and the `AC<n>` and `R<n>` ids from that case's `Covers`.
- Name a test for the behaviour and its expected result, not for the case id.
- Assert every value the expected result states, such as a price or a total, with `to_have_text` or `to_contain_text`; `to_be_visible` proves the element is there, not its value.
- A journey whose cases cover several pages builds each page object it needs in the test; no shared page or context between tests.

## Authentication

- The sign-in journey comes from the cases: the page path and steps that enter the credentials and reach the signed-in app, whether in a case of its own or at the start of a signed-in case. Its page path and steps build `SignInPage`, and its variable names come from `credentials_env`.
- The function-scoped `signed_in_page` fixture drives that journey in each signed-in test's own fresh context, before the test's steps. No storage state is captured or reused, so no cookie, session, or cart tied to a session passes from one test to another, and a test can sign out or change session state without affecting another. Where the sign-in needs a single token or cookie instead of a user and password, the fixture reads that one name and sets it on the test's own context.
- State the account keeps across sessions, such as a saved cart, is not cleared by a fresh context. A test reaches its case's starting state through steps the cases give; with none, stop and name the case and the missing precondition to `design-test-cases`.
- The fixture fails with the missing variable's name when the owner runs without `.env` loaded; it never skips and never falls back to an unauthenticated page.
- Never write a storage state file, a trace, or a screenshot that holds a credential to the engagement folder.

## Live versus collect-only

- Every test that drives a browser carries `@pytest.mark.live`. The marker is registered in `pyproject.toml` and a plain `pytest` run includes those tests.
- The live run is `uv run --env-file .env pytest`, run from the engagement folder after the owner runs `uv run playwright install` once. `uv` loads the engagement `.env` into the test process environment at run time and `conftest.py` reads it through `os.environ`; no value is copied into a file.
- The authoring gate is `uv run pytest --collect-only -q`. Collection imports each module and loads `conftest.py`, but starts no browser, runs no fixture, reads no credential, and navigates nowhere, so it passes with no browser binaries and no `.env`.
- Never add `skip`, `skipif`, `pytest.importorskip`, or `xfail` to make collection pass. A test that cannot be written is a stop, reported through the skill.
- One node id appears per planned test. Count them and compare with the plan from Procedure step 4.

## Browsers

- The owner installs the browser binaries with `uv run playwright install` from the engagement folder, which installs the browsers the conftest launches.
- Collection, `ruff check`, and `ruff format --check` need no browser. Never run `uv run playwright install`, launch a browser, or run `pytest` without `--collect-only` while authoring.

## Independence

- Each test gets its own context and page from its fixture, and a signed-in test signs in inside that context; no storage state, cookie, or session is shared, and no module-level browser, page, credential read, or navigation.
- A test creates the data it needs in the same test through the page objects, with a unique value such as one built from the case id and `uuid4()`, and never relies on another test's order or state.
- A test may not depend on a journey a previous test completed. When the material makes a journey impossible to start from a clean state, stop and name the case and the missing precondition.

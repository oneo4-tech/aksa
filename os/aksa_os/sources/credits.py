"""Read the four agent credit sources, each failing softly with its own read time."""

import json
import platform
import sqlite3
import subprocess
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import requests

from aksa_os.models import CreditProvider, CreditValue, CreditView, Source
from aksa_os.runner import run_command

SOURCE = "Credits"
CLAUDE = "Claude Code"
CLAUDE_SOURCE = "macOS Keychain + Anthropic usage API"
CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_USAGE_LINK = "https://claude.ai/settings/usage"
CLAUDE_BETA = "oauth-2025-04-20"
KEYCHAIN_ITEM = "Claude Code-credentials"
OPENROUTER = "OpenRouter"
OPENROUTER_SOURCE = "OpenRouter credits API"
OPENROUTER_URL = "https://openrouter.ai/api/v1/credits"
OPENROUTER_LINK = "https://openrouter.ai/credits"
OPENCODE = "OpenCode"
OPENCODE_SOURCE = "OpenCode local database"
OPENCODE_LINK = "https://opencode.ai/zen"
GOOGLE = "Google AI Studio"
GOOGLE_SOURCE = "Manual file .local/aksa_os.json"
GOOGLE_LINK = "https://aistudio.google.com/app/billing"
WINDOW_DAYS = 30
GOOGLE_UNSET = "Add google_ai_studio.balance to .local/aksa_os.json."


class HttpResponse(Protocol):
    """What an adapter needs from one HTTP response."""

    status_code: int

    def json(self) -> Any: ...


class HttpGet(Protocol):
    """What an adapter needs to make one request; tests pass a fake."""

    def __call__(self, url: str, *, headers: Mapping[str, str], timeout: float) -> HttpResponse: ...


class Keychain(Protocol):
    """What the Claude Code adapter needs to read its credential; tests pass a fake."""

    def __call__(self) -> str | None: ...


class CreditReader(Protocol):
    """One provider read, called by read_credits."""

    def __call__(self) -> CreditProvider: ...


def http_get(url: str, *, headers: Mapping[str, str], timeout: float) -> HttpResponse:
    """GET a URL with requests, so certificate checks and timeouts apply."""
    return requests.get(url, headers=dict(headers), timeout=timeout)


def read_keychain(timeout: float = 5.0) -> str | None:
    """Read the Claude Code credential item from the macOS Keychain, or None when it is absent."""
    try:
        result = run_command(
            ["security", "find-generic-password", "-s", KEYCHAIN_ITEM, "-w"],
            cwd=Path.cwd(),
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip() or None


def read_claude(
    keychain: Keychain,
    http: HttpGet,
    timeout: float = 10.0,
    *,
    system: Callable[[], str] = platform.system,
) -> CreditProvider:
    """The Claude Code plan and usage from the Keychain token; the token never leaves this function."""
    read_at = datetime.now(UTC)
    if system() != "Darwin":
        return CreditProvider.failure(
            CLAUDE,
            "Claude Code credentials are only available in the macOS Keychain.",
            source=CLAUDE_SOURCE,
            read_at=read_at,
        )
    try:
        credentials = keychain()
    except (OSError, subprocess.SubprocessError, ValueError):
        credentials = None
    if not credentials:
        return CreditProvider.failure(
            CLAUDE, "Claude Code Keychain item not found.", source=CLAUDE_SOURCE, read_at=read_at
        )
    try:
        payload = json.loads(credentials)
    except (json.JSONDecodeError, TypeError):
        return CreditProvider.failure(
            CLAUDE, "Claude Code Keychain item is not valid JSON.", source=CLAUDE_SOURCE, read_at=read_at
        )
    oauth = payload.get("claudeAiOauth") if isinstance(payload, dict) else None
    token = oauth.get("accessToken") if isinstance(oauth, dict) else None
    if not isinstance(token, str) or not token:
        return CreditProvider.failure(
            CLAUDE, "Claude Code credential has no access token.", source=CLAUDE_SOURCE, read_at=read_at
        )
    plan = oauth.get("subscriptionType")
    body, reason = _request(
        http,
        CLAUDE_USAGE_URL,
        {"Authorization": f"Bearer {token}", "anthropic-beta": CLAUDE_BETA},
        timeout,
    )
    if reason:
        return CreditProvider.failure(CLAUDE, f"Claude usage {reason}.", source=CLAUDE_SOURCE, read_at=read_at)
    values = _claude_values(body, plan)
    if not values:
        return CreditProvider.failure(
            CLAUDE, "Claude usage response had no usage values.", source=CLAUDE_SOURCE, read_at=read_at
        )
    return CreditProvider.success(
        CLAUDE,
        source=CLAUDE_SOURCE,
        read_at=read_at,
        values=values,
        link=CLAUDE_USAGE_LINK,
        link_label="Claude usage",
    )


def read_openrouter(env: Mapping[str, str], http: HttpGet, timeout: float = 10.0) -> CreditProvider:
    """The OpenRouter credit totals from its credits endpoint; a missing key fails safely."""
    read_at = datetime.now(UTC)
    key = env.get("OPENROUTER_API_KEY")
    if not key:
        return CreditProvider.failure(
            OPENROUTER, "OPENROUTER_API_KEY is not set in .env.", source=OPENROUTER_SOURCE, read_at=read_at
        )
    body, reason = _request(http, OPENROUTER_URL, {"Authorization": f"Bearer {key}"}, timeout)
    if reason:
        return CreditProvider.failure(
            OPENROUTER, f"OpenRouter credits {reason}.", source=OPENROUTER_SOURCE, read_at=read_at
        )
    data = body.get("data") if isinstance(body, dict) else None
    total = _number(data.get("total_credits")) if isinstance(data, dict) else None
    used = _number(data.get("total_usage")) if isinstance(data, dict) else None
    if total is None or used is None:
        return CreditProvider.failure(
            OPENROUTER, "OpenRouter credits response has no totals.", source=OPENROUTER_SOURCE, read_at=read_at
        )
    values = (
        CreditValue("Total", _money(total)),
        CreditValue("Used", _money(used)),
        CreditValue("Remaining", _money(total - used)),
        CreditValue("Usage", _percent(used / total * 100) if total else "n/a"),
    )
    return CreditProvider.success(
        OPENROUTER,
        source=OPENROUTER_SOURCE,
        read_at=read_at,
        values=values,
        link=OPENROUTER_LINK,
        link_label="OpenRouter credits",
    )


def read_opencode(db_path: Path, *, now: datetime | None = None) -> CreditProvider:
    """Local OpenCode cost and tokens for the last 30 days, read from its database without writing."""
    read_at = now or datetime.now(UTC)
    if not db_path.is_file():
        return CreditProvider.failure(
            OPENCODE, f"OpenCode database not found at {db_path}.", source=OPENCODE_SOURCE, read_at=read_at
        )
    cutoff = int((read_at - timedelta(days=WINDOW_DAYS)).timestamp() * 1000)
    query = (
        "SELECT COUNT(*), COALESCE(SUM(cost), 0), COALESCE(SUM(tokens_input), 0), "
        "COALESCE(SUM(tokens_output), 0), COALESCE(SUM(tokens_reasoning), 0) "
        "FROM session_v2 WHERE time_created >= ?"
    )
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return CreditProvider.failure(
            OPENCODE, "OpenCode database could not be read.", source=OPENCODE_SOURCE, read_at=read_at
        )
    try:
        count, cost, input_tokens, output_tokens, reasoning_tokens = connection.execute(query, (cutoff,)).fetchone()
    except sqlite3.Error:
        return CreditProvider.failure(
            OPENCODE, "OpenCode database schema not recognised.", source=OPENCODE_SOURCE, read_at=read_at
        )
    finally:
        connection.close()
    values = (
        CreditValue("Cost", _money(cost)),
        CreditValue("Input tokens", _tokens(input_tokens)),
        CreditValue("Output tokens", _tokens(output_tokens)),
        CreditValue("Reasoning tokens", _tokens(reasoning_tokens)),
        CreditValue("Sessions", f"{count:,}"),
    )
    note = "Local cost and tokens for the last 30 days. Zen balance has no API; open the console."
    return CreditProvider.success(
        OPENCODE,
        source=OPENCODE_SOURCE,
        read_at=read_at,
        values=values,
        link=OPENCODE_LINK,
        link_label="OpenCode Zen",
        note=note,
    )


def read_google(manual_path: Path) -> CreditProvider:
    """The owner's manual balance from .local/aksa_os.json.

    The shape is {"google_ai_studio": {"balance": 12.34, "currency": "USD", "updated": "2026-10-25"}}.
    A missing file or a missing balance is a successful not-set result; a malformed file is unavailable.
    """
    read_at = datetime.now(UTC)
    if not manual_path.is_file():
        return _google_unset(read_at)
    try:
        text = manual_path.read_text()
    except (OSError, UnicodeDecodeError):
        return CreditProvider.failure(
            GOOGLE, "Local settings file could not be read.", source=GOOGLE_SOURCE, read_at=read_at
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return CreditProvider.failure(
            GOOGLE, "Local settings file is not valid JSON.", source=GOOGLE_SOURCE, read_at=read_at
        )
    if not isinstance(payload, dict):
        return CreditProvider.failure(
            GOOGLE, "Local settings file is not a JSON object.", source=GOOGLE_SOURCE, read_at=read_at
        )
    settings = payload.get("google_ai_studio")
    if settings is None:
        return _google_unset(read_at)
    if not isinstance(settings, dict):
        return CreditProvider.failure(
            GOOGLE, "Manual Google AI Studio settings are not an object.", source=GOOGLE_SOURCE, read_at=read_at
        )
    balance = settings.get("balance")
    if balance is None:
        return _google_unset(read_at)
    amount = _number(balance)
    if amount is None:
        return CreditProvider.failure(
            GOOGLE, "Manual Google AI Studio balance is not a number.", source=GOOGLE_SOURCE, read_at=read_at
        )
    currency = settings.get("currency")
    currency = currency if isinstance(currency, str) and currency else "USD"
    values = [CreditValue("Balance", _amount(amount, currency))]
    updated = settings.get("updated")
    if isinstance(updated, str) and updated:
        values.append(CreditValue("Updated", updated))
    return CreditProvider.success(
        GOOGLE,
        source=GOOGLE_SOURCE,
        read_at=read_at,
        values=tuple(values),
        link=GOOGLE_LINK,
        link_label="AI Studio billing",
        manual=True,
        note="Manual value from .local/aksa_os.json.",
    )


def read_credits(
    claude: CreditReader,
    openrouter: CreditReader,
    opencode: CreditReader,
    google: CreditReader,
) -> Source[CreditView]:
    """All four providers, each read on its own so one failure cannot hide the rest."""
    providers = [
        _safe(claude, CLAUDE, CLAUDE_SOURCE),
        _safe(openrouter, OPENROUTER, OPENROUTER_SOURCE),
        _safe(opencode, OPENCODE, OPENCODE_SOURCE),
        _safe(google, GOOGLE, GOOGLE_SOURCE),
    ]
    return Source.success(
        CreditView(providers=providers),
        source=SOURCE,
        read_at=max(provider.read_at for provider in providers),
    )


def _safe(reader: CreditReader, name: str, source: str) -> CreditProvider:
    """One provider read, turned into a safe failure if the reader breaks its own contract."""
    try:
        return reader()
    except Exception:  # noqa: BLE001 - one broken provider must not blank the page
        return CreditProvider.failure(name, f"{name} could not be read.", source=source, read_at=datetime.now(UTC))


def _request(http: HttpGet, url: str, headers: Mapping[str, str], timeout: float) -> tuple[Any | None, str | None]:
    """A JSON body and no reason, or no body and a reason safe to show."""
    try:
        response = http(url, headers=headers, timeout=timeout)
    except (requests.RequestException, OSError, ValueError):
        return None, "request failed"
    if response.status_code != 200:
        return None, f"endpoint answered {response.status_code}"
    try:
        return response.json(), None
    except ValueError:
        return None, "endpoint returned invalid JSON"


def _claude_values(body: Any, plan: Any) -> tuple[CreditValue, ...]:
    """The plan and every usage window and spend value the response carries."""
    if not isinstance(body, dict):
        return ()
    values = []
    if isinstance(plan, str) and plan:
        values.append(CreditValue("Plan", plan))
    for label, key in (("5-hour", "five_hour"), ("7-day", "seven_day")):
        window = body.get(key)
        if not isinstance(window, dict):
            continue
        utilization = _number(window.get("utilization"))
        if utilization is not None:
            values.append(CreditValue(label, _percent(utilization)))
        reset = _reset(window.get("resets_at"))
        if reset:
            values.append(CreditValue(f"{label} resets", reset))
    spend = body.get("spend")
    used = spend.get("used") if isinstance(spend, dict) else None
    minor = used.get("amount_minor") if isinstance(used, dict) else None
    amount = _number(minor)
    if amount is not None:
        values.append(CreditValue("Spend used", _money(amount / 100)))
    return tuple(values)


def _reset(value: Any) -> str | None:
    """A reset time as a short clock, from an ISO string or an epoch number."""
    if isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            return value
        return _clock(moment)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _clock(datetime.fromtimestamp(value, tz=UTC))
    return None


def _clock(moment: datetime) -> str:
    """A short date and time in UTC."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%d %b %H:%M")


def _number(value: Any) -> float | None:
    """A number from a decoded value, or None when it is missing or not a number."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _money(amount: float) -> str:
    """A dollar amount with two decimals."""
    return f"${amount:,.2f}"


def _amount(balance: float, currency: str) -> str:
    """A balance in its currency, with the dollar sign for USD."""
    return _money(balance) if currency == "USD" else f"{balance:,.2f} {currency}"


def _percent(value: float) -> str:
    """One decimal of a percentage."""
    return f"{value:.1f}%"


def _tokens(count: int) -> str:
    """A token count, compact above a thousand."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return f"{count:,}"


def _google_unset(read_at: datetime) -> CreditProvider:
    """The manual balance is not set yet; that is a successful read, clearly marked."""
    return CreditProvider.success(
        GOOGLE,
        source=GOOGLE_SOURCE,
        read_at=read_at,
        link=GOOGLE_LINK,
        link_label="AI Studio billing",
        manual=True,
        unset=True,
        note=GOOGLE_UNSET,
    )

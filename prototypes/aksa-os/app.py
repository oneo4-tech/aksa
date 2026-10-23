"""AKSA OS overview prototype. Throwaway: reads real local data, writes nothing.

Run from the worktree root:
  uv run --with fastapi --with uvicorn --with jinja2 --with requests \
      python prototypes/aksa-os/app.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parent
HOME = Path.home()

app = FastAPI(title="AKSA OS prototype")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def read_env(name: str) -> str | None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{name}="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def human_ago(epoch_ms: float | None) -> str:
    if not epoch_ms:
        return "never"
    seconds = max(0, int(time.time() - epoch_ms / 1000))
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def iso_ago(value: str | None) -> str:
    if not value:
        return "unknown"
    try:
        dt = datetime.fromisoformat(value)
        return human_ago(dt.timestamp() * 1000)
    except ValueError:
        return value


def reset_label(iso: str | None) -> str:
    if not iso:
        return "no reset"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.astimezone().strftime("%H:%M")
    except ValueError:
        return "no reset"


# ---------------------------------------------------------------- factory


def factory_runs() -> dict:
    try:
        out = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--state",
                "open",
                "--limit",
                "50",
                "--json",
                "number,title,labels,url,updatedAt",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=25,
            cwd=ROOT,
        )
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr else "gh failed")
        issues = json.loads(out.stdout)
        runs = []
        for issue in issues:
            labels = [label["name"] for label in issue.get("labels", [])]
            stage = next((name.split(":", 1)[1] for name in labels if name.startswith("stage:")), None)
            if not stage:
                continue
            runs.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "stage": stage,
                    "url": issue["url"],
                    "waiting": "needs:owner" in labels,
                    "claimed": "claimed" in labels,
                    "updated": iso_ago(issue["updatedAt"]),
                    "updated_raw": issue["updatedAt"],
                }
            )
        runs.sort(key=lambda run: run["updated_raw"], reverse=True)
        return {"ok": True, "runs": runs, "waiting": sum(run["waiting"] for run in runs)}
    except Exception as exc:  # noqa: BLE001 - prototype degrades softly
        return {"ok": False, "error": str(exc), "runs": [], "waiting": 0}


# --------------------------------------------------------------- projects


def project_info(path: Path) -> dict:
    files = 0
    newest = 0.0
    for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
        dirnames[:] = [name for name in dirnames if name != ".git" and not name.startswith(".")]
        for filename in filenames:
            files += 1
            try:
                newest = max(newest, (Path(dirpath) / filename).stat().st_mtime)
            except OSError:
                pass
    branch = None
    dirty = 0
    if (path / ".git").exists():
        try:
            branch = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            dirty = len(
                subprocess.run(
                    ["git", "-C", str(path), "status", "--porcelain"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                .stdout.strip()
                .splitlines()
            )
        except Exception:  # noqa: BLE001
            branch = None
    return {
        "name": path.name,
        "kind": path.parent.name if path.parent != ROOT / ".projects" else "workspace",
        "files": files,
        "changed": human_ago(newest * 1000 if newest else None),
        "branch": branch,
        "dirty": dirty,
        "repo": (path / ".git").exists(),
    }


def projects() -> dict:
    base = ROOT / ".projects"
    if not base.exists():
        return {"ok": False, "error": ".projects is missing", "list": []}
    items = []
    try:
        for dirpath, dirnames, filenames in os.walk(base, followlinks=True):
            dirnames[:] = [name for name in dirnames if name != ".git" and not name.startswith(".")]
            path = Path(dirpath)
            if path == base:
                continue
            marker = (path / ".git").exists() or (path / "config.yaml").exists() or (path / "README.md").exists()
            if marker:
                items.append(project_info(path))
                dirnames[:] = []
        items.sort(key=lambda item: item["name"].lower())
        return {"ok": True, "list": items}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "list": items}


# -------------------------------------------------------------- knowledge


def knowledge() -> dict:
    wiki = ROOT / ".kb" / "wiki"
    inbox = ROOT / ".kb" / "inbox"
    if not wiki.exists():
        return {"ok": False, "error": ".kb/wiki is missing", "pages": [], "inbox": 0}
    try:
        pages = sorted(wiki.rglob("*.md"), key=lambda page: page.stat().st_mtime, reverse=True)
        recent = [
            {
                "name": page.stem.replace("-", " "),
                "area": page.parent.name,
                "changed": human_ago(page.stat().st_mtime * 1000),
            }
            for page in pages[:4]
        ]
        inbox_items = [item for item in inbox.rglob("*") if item.is_file()] if inbox.exists() else []
        return {"ok": True, "pages": recent, "count": len(pages), "inbox": len(inbox_items)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "pages": [], "count": 0, "inbox": 0}


# ---------------------------------------------------------------- credits


def claude_credits() -> dict:
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if out.returncode != 0:
            raise RuntimeError("no Keychain credential")
        oauth = json.loads(out.stdout)["claudeAiOauth"]
        response = requests.get(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {oauth['accessToken']}",
                "anthropic-beta": "oauth-2025-04-20",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        five = data.get("five_hour") or {}
        seven = data.get("seven_day") or {}
        spend = data.get("spend") or {}
        return {
            "ok": True,
            "plan": (oauth.get("subscriptionType") or "subscription").title(),
            "five": five.get("utilization"),
            "five_reset": reset_label(five.get("resets_at")),
            "seven": seven.get("utilization"),
            "seven_reset": reset_label(seven.get("resets_at")),
            "spend": spend.get("used", {}).get("amount_minor"),
            "source": "Keychain OAuth",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "source": "Keychain OAuth"}


def openrouter_credits() -> dict:
    key = read_env("OPENROUTER_API_KEY")
    if not key:
        return {"ok": False, "error": "no OPENROUTER_API_KEY", "source": "OpenRouter API"}
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()["data"]
        total = float(data.get("total_credits") or 0)
        used = float(data.get("total_usage") or 0)
        return {
            "ok": True,
            "total": total,
            "used": used,
            "remaining": max(0.0, total - used),
            "percent": (used / total * 100) if total else 0,
            "source": "OpenRouter API",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "source": "OpenRouter API"}


def opencode_credits() -> dict:
    db = HOME / ".local" / "share" / "opencode" / "opencode.db"
    if not db.exists():
        return {"ok": False, "error": "no local OpenCode database", "source": "OpenCode DB"}
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cutoff = int((time.time() - 30 * 86400) * 1000)
        row = conn.execute(
            """
            select coalesce(sum(cost), 0), coalesce(sum(tokens_input), 0),
                   coalesce(sum(tokens_output), 0), coalesce(sum(tokens_reasoning), 0),
                   count(*)
            from session where time_created >= ?
            """,
            (cutoff,),
        ).fetchone()
        conn.close()
        cost, tin, tout, treason, sessions = row
        return {
            "ok": True,
            "cost": float(cost),
            "tokens": int(tin) + int(tout) + int(treason),
            "sessions": sessions,
            "source": "OpenCode DB",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "source": "OpenCode DB"}


def google_credits() -> dict:
    path = ROOT / ".temp" / "aksa-os" / "google-balance.json"
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return {
                "ok": True,
                "balance": float(data.get("balance", 0)),
                "updated": data.get("updated", "unknown"),
                "source": "Manual entry",
            }
        except Exception:  # noqa: BLE001
            return {"ok": False, "error": "invalid manual balance file", "source": "Manual entry"}
    return {"ok": True, "balance": None, "source": "Manual entry", "manual": True}


# ----------------------------------------------------------------- system


def system() -> dict:
    try:
        branch = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        branch = "unknown"
    worktrees = ROOT / ".worktrees"
    count = 0
    if worktrees.exists():
        try:
            count = sum(1 for item in worktrees.iterdir() if item.is_dir())
        except OSError:
            count = 0
    return {"branch": branch, "worktrees": count, "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}"}


@app.get("/", response_class=HTMLResponse)
def overview(request: Request) -> HTMLResponse:
    factory = factory_runs()
    project_data = projects()
    kb = knowledge()
    credits = {
        "claude": claude_credits(),
        "openrouter": openrouter_credits(),
        "opencode": opencode_credits(),
        "google": google_credits(),
    }
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "factory": factory,
            "projects": project_data,
            "kb": kb,
            "credits": credits,
            "system": system(),
            "now": datetime.now(UTC).astimezone(),
            "question": (
                "Which overview layout and HUD language should AKSA OS use, "
                "and does the aksa palette carry the Jarvis feel?"
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")

"""The AKSA OS FastAPI application."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


def create_app(sources=None) -> FastAPI:
    """Build the app, with the read-only sources the pages call."""
    app = FastAPI(title="AKSA OS", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(request, "index.html", {"page": "overview"})

    return app

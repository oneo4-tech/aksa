"""The AKSA OS FastAPI application."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aksa_os.models import FactoryView, ProjectsView, Source
from aksa_os.runner import run_command
from aksa_os.settings import Settings
from aksa_os.sources.factory import read_factory
from aksa_os.sources.projects import read_projects

PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


@dataclass(frozen=True)
class Sources:
    """The read-only source callables each screen calls; tests pass fakes."""

    factory: Callable[[], Source[FactoryView]]
    projects: Callable[[], Source[ProjectsView]]


def default_sources(settings: Settings | None = None) -> Sources:
    """The real sources, each reading only when a screen calls it."""
    settings = settings or Settings()
    return Sources(
        factory=lambda: read_factory(run_command, settings.repo_root, settings.timeout),
        projects=lambda: read_projects(settings.projects, run_command, settings.timeout),
    )


def create_app(sources: Sources | None = None) -> FastAPI:
    """Build the app, with the read-only sources the pages call."""
    sources = default_sources() if sources is None else sources
    app = FastAPI(title="AKSA OS", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(
            request, "index.html", {"page": "overview", "factory": sources.factory(), "projects": sources.projects()}
        )

    @app.get("/factory", response_class=HTMLResponse)
    def factory_screen(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(request, "factory.html", {"page": "factory", "factory": sources.factory()})

    @app.get("/projects", response_class=HTMLResponse)
    def projects_screen(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(
            request, "projects.html", {"page": "projects", "projects": sources.projects()}
        )

    return app

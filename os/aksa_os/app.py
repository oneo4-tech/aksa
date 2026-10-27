"""The AKSA OS FastAPI application."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aksa_os.env import read_env
from aksa_os.models import CreditView, FactoryView, KnowledgeView, ProjectsView, Source, SystemView
from aksa_os.runner import run_command
from aksa_os.settings import Settings
from aksa_os.sources.credits import (
    http_get,
    read_claude,
    read_credits,
    read_google,
    read_keychain,
    read_opencode,
    read_openrouter,
)
from aksa_os.sources.factory import read_factory
from aksa_os.sources.knowledge import read_knowledge
from aksa_os.sources.projects import read_projects
from aksa_os.sources.system import read_system

PACKAGE_ROOT = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


@dataclass(frozen=True)
class Sources:
    """The read-only source callables each screen calls; tests pass fakes."""

    factory: Callable[[], Source[FactoryView]]
    projects: Callable[[], Source[ProjectsView]]
    knowledge: Callable[[], Source[KnowledgeView]]
    credits: Callable[[], Source[CreditView]]
    system: Callable[[], Source[SystemView]]


def default_sources(settings: Settings | None = None) -> Sources:
    """The real sources, each reading only when a screen calls it."""
    settings = settings or Settings()
    return Sources(
        factory=lambda: read_factory(run_command, settings.repo_root, settings.timeout),
        projects=lambda: read_projects(settings.projects, run_command, settings.timeout),
        knowledge=lambda: read_knowledge(settings.kb),
        credits=lambda: read_credits(
            lambda: read_claude(lambda: read_keychain(settings.timeout), http_get, settings.timeout),
            lambda: read_openrouter(read_env(settings.env_file), http_get, settings.timeout),
            lambda: read_opencode(settings.opencode_db),
            lambda: read_google(settings.local_settings),
        ),
        system=lambda: read_system(settings.repo_root, run_command, settings.timeout),
    )


def status_of(*sources: Source) -> str:
    """online when every source answered, degraded when some did, offline when none."""
    answered = sum(source.ok for source in sources)
    if answered == len(sources):
        return "online"
    return "degraded" if answered else "offline"


def latest_read(*sources: Source) -> datetime | None:
    """The newest read time among the sources that carry one."""
    moments = [source.read_at for source in sources if source.read_at]
    return max(moments) if moments else None


def shell(page: str, system: Source[SystemView], read_at: datetime | None, status: str, **values) -> dict:
    """The values the shell needs on every page, plus the page's own sources."""
    return {"page": page, "system": system, "read_at": read_at, "status": status, **values}


def create_app(sources: Sources | None = None) -> FastAPI:
    """Build the app, with the read-only sources the pages call."""
    sources = default_sources() if sources is None else sources
    app = FastAPI(title="AKSA OS", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        """Each HTML page is read fresh, so the browser must not serve a cached copy."""
        response = await call_next(request)
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request) -> HTMLResponse:
        system = sources.system()
        factory = sources.factory()
        projects = sources.projects()
        knowledge = sources.knowledge()
        credits = sources.credits()
        operating = (factory, projects, knowledge, credits)
        context = shell(
            "overview",
            system,
            latest_read(*operating) or system.read_at,
            status_of(*operating),
            factory=factory,
            projects=projects,
            knowledge=knowledge,
            credits=credits,
            sources_ok=sum(source.ok for source in operating),
            sources_total=len(operating),
        )
        return TEMPLATES.TemplateResponse(request, "index.html", context)

    @app.get("/factory", response_class=HTMLResponse)
    def factory_screen(request: Request) -> HTMLResponse:
        system = sources.system()
        factory = sources.factory()
        context = shell("factory", system, factory.read_at, status_of(factory), factory=factory)
        return TEMPLATES.TemplateResponse(request, "factory.html", context)

    @app.get("/projects", response_class=HTMLResponse)
    def projects_screen(request: Request) -> HTMLResponse:
        system = sources.system()
        projects = sources.projects()
        context = shell("projects", system, projects.read_at, status_of(projects), projects=projects)
        return TEMPLATES.TemplateResponse(request, "projects.html", context)

    @app.get("/knowledge", response_class=HTMLResponse)
    def knowledge_screen(request: Request) -> HTMLResponse:
        system = sources.system()
        knowledge = sources.knowledge()
        context = shell("knowledge", system, knowledge.read_at, status_of(knowledge), knowledge=knowledge)
        return TEMPLATES.TemplateResponse(request, "knowledge.html", context)

    @app.get("/agents", response_class=HTMLResponse)
    def agents_screen(request: Request) -> HTMLResponse:
        system = sources.system()
        credits = sources.credits()
        context = shell("agents", system, credits.read_at, status_of(credits), credits=credits)
        return TEMPLATES.TemplateResponse(request, "agents.html", context)

    return app

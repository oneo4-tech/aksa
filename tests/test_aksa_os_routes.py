"""Tests for the AKSA OS HTTP routes."""

from datetime import UTC, datetime

from aksa_os.app import Sources, create_app
from aksa_os.models import FactoryRun, FactoryView, Project, ProjectsView, Source
from fastapi.testclient import TestClient

READ_AT = datetime(2026, 10, 25, 9, 0, tzinfo=UTC)


def factory_runs() -> FactoryView:
    return FactoryView(
        [
            FactoryRun(
                number=37,
                title="feat(os): add AKSA OS read-only cockpit",
                stage="build",
                needs_owner=True,
                claimed=True,
                url="https://github.com/oneo4-tech/aksa/issues/37",
                updated_at=READ_AT,
            ),
            FactoryRun(
                number=12,
                title="chore(docs): older run",
                stage="plan",
                needs_owner=False,
                claimed=False,
                url="https://github.com/oneo4-tech/aksa/issues/12",
                updated_at=READ_AT,
            ),
        ]
    )


def projects() -> ProjectsView:
    return ProjectsView(
        [
            Project(
                name="oneo4-newsletter",
                path="content/oneo4-newsletter",
                file_count=42,
                last_change=READ_AT,
                is_repo=True,
                branch="main",
                dirty=2,
            ),
            Project(
                name="demo-ecommerce",
                path="testing/demo-ecommerce",
                file_count=7,
                last_change=None,
                is_repo=False,
            ),
        ]
    )


def fake_sources(
    factory: Source[FactoryView] | None = None, projects_source: Source[ProjectsView] | None = None
) -> Sources:
    view = factory or Source.success(factory_runs(), source="GitHub", read_at=READ_AT)
    projects_view = projects_source or Source.success(projects(), source="Projects", read_at=READ_AT)
    return Sources(factory=lambda: view, projects=lambda: projects_view)


def test_overview_answers_with_the_shell():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/")
    assert response.status_code == 200
    assert "AKSA OS" in response.text


def test_static_stylesheet_is_served():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/static/aksa_os.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_factory_screen_lists_every_open_run():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/factory")
    assert response.status_code == 200
    assert "feat(os): add AKSA OS read-only cockpit" in response.text
    assert "chore(docs): older run" in response.text
    assert 'href="https://github.com/oneo4-tech/aksa/issues/37"' in response.text
    assert 'class="stage stage-build">build<' in response.text
    assert 'class="stage stage-plan">plan<' in response.text
    assert ">needs you</span>" in response.text
    assert ">claimed</span>" in response.text


def test_factory_screen_shows_a_source_error():
    failed = Source.failure("gh issue list exited 1", source="GitHub", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(failed)))
    response = client.get("/factory")
    assert response.status_code == 200
    assert "Factory unavailable" in response.text
    assert "gh issue list exited 1" in response.text


def test_factory_failure_leaves_the_overview_usable():
    failed = Source.failure("gh issue list exited 1", source="GitHub", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(failed)))
    response = client.get("/")
    assert response.status_code == 200
    assert "AKSA OS" in response.text
    assert "gh issue list exited 1" in response.text


def test_overview_shows_the_factory_runs():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/")
    assert "feat(os): add AKSA OS read-only cockpit" in response.text
    assert 'class="stage stage-build">build<' in response.text


def test_projects_screen_lists_every_project():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/projects")
    assert response.status_code == 200
    assert "oneo4-newsletter" in response.text
    assert "content/oneo4-newsletter" in response.text
    assert "demo-ecommerce" in response.text
    assert "testing/demo-ecommerce" in response.text
    assert ">42<" in response.text
    assert ">7<" in response.text
    assert "25 Oct 09:00" in response.text
    assert "main" in response.text
    assert ">2<" in response.text
    assert "not a repository" in response.text
    assert 'href="/projects"' in response.text


def test_projects_screen_shows_a_source_error():
    failed = Source.failure("projects could not be read", source="Projects", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(projects_source=failed)))
    response = client.get("/projects")
    assert response.status_code == 200
    assert "Projects unavailable" in response.text
    assert "projects could not be read" in response.text


def test_projects_failure_leaves_the_overview_usable():
    failed = Source.failure("projects could not be read", source="Projects", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(projects_source=failed)))
    response = client.get("/")
    assert response.status_code == 200
    assert "AKSA OS" in response.text
    assert "Projects unavailable" in response.text


def test_overview_shows_the_projects_panel():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/")
    assert "oneo4-newsletter" in response.text
    assert "demo-ecommerce" in response.text
    assert 'href="/projects"' in response.text

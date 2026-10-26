"""Tests for the AKSA OS HTTP routes."""

import json
from datetime import UTC, date, datetime

import pytest
from aksa_os.app import Sources, create_app
from aksa_os.env import read_env
from aksa_os.models import (
    CreditProvider,
    CreditValue,
    CreditView,
    FactoryRun,
    FactoryView,
    KnowledgePage,
    KnowledgeView,
    Project,
    ProjectsView,
    Source,
)
from aksa_os.sources.credits import read_claude, read_credits, read_google, read_opencode, read_openrouter
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


def knowledge_pages() -> KnowledgeView:
    return KnowledgeView(
        pages=[
            KnowledgePage(
                title="OneO4 Newsletter",
                area="projects",
                path="wiki/projects/oneo4-newsletter.md",
                summary="Periodic newsletter for OneO4 projects.",
                updated=date(2026, 10, 25),
            ),
            KnowledgePage(
                title="Agentic design",
                area="ai",
                path="wiki/ai/agentic-design.md",
                summary="Rule, skill, and agent compared.",
                updated=date(2026, 10, 19),
            ),
        ],
        inbox_count=3,
    )


def credit_providers() -> CreditView:
    return CreditView(
        providers=[
            CreditProvider.success(
                "Claude Code",
                source="macOS Keychain + Anthropic usage API",
                read_at=READ_AT,
                values=(CreditValue("Plan", "pro"), CreditValue("5-hour", "72.5%")),
                link="https://claude.ai/settings/usage",
                link_label="Claude usage",
            ),
            CreditProvider.success(
                "OpenRouter",
                source="OpenRouter credits API",
                read_at=READ_AT,
                values=(CreditValue("Total", "$10.00"), CreditValue("Remaining", "$6.50")),
                link="https://openrouter.ai/credits",
                link_label="OpenRouter credits",
            ),
            CreditProvider.success(
                "OpenCode",
                source="OpenCode local database",
                read_at=READ_AT,
                values=(CreditValue("Cost", "$0.75"), CreditValue("Sessions", "2")),
                link="https://opencode.ai/zen",
                link_label="OpenCode Zen",
                note="Local cost and tokens for the last 30 days.",
            ),
            CreditProvider.success(
                "Google AI Studio",
                source="Manual file .local/aksa_os.json",
                read_at=READ_AT,
                values=(CreditValue("Balance", "$12.34"),),
                link="https://aistudio.google.com/app/billing",
                link_label="AI Studio billing",
                manual=True,
            ),
        ]
    )


def credits(overrides: dict[str, CreditProvider] | None = None) -> CreditView:
    """The four fake providers, with any named provider replaced by the test's own."""
    replacements = overrides or {}
    view = credit_providers()
    return CreditView(providers=[replacements.get(provider.name, provider) for provider in view.providers])


def failed_credit(name: str, error: str = "source failed") -> CreditProvider:
    return CreditProvider.failure(name, error, source="Fake", read_at=READ_AT)


def fake_sources(
    factory: Source[FactoryView] | None = None,
    projects_source: Source[ProjectsView] | None = None,
    knowledge_source: Source[KnowledgeView] | None = None,
    credits_source: Source[CreditView] | None = None,
) -> Sources:
    view = factory or Source.success(factory_runs(), source="GitHub", read_at=READ_AT)
    projects_view = projects_source or Source.success(projects(), source="Projects", read_at=READ_AT)
    knowledge_view = knowledge_source or Source.success(knowledge_pages(), source="Knowledge", read_at=READ_AT)
    credits_view = credits_source or Source.success(credit_providers(), source="Credits", read_at=READ_AT)
    return Sources(
        factory=lambda: view,
        projects=lambda: projects_view,
        knowledge=lambda: knowledge_view,
        credits=lambda: credits_view,
    )


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


def test_knowledge_screen_lists_every_wiki_page():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/knowledge")
    assert response.status_code == 200
    assert "OneO4 Newsletter" in response.text
    assert "Periodic newsletter for OneO4 projects." in response.text
    assert "wiki/projects/oneo4-newsletter.md" in response.text
    assert ">projects<" in response.text
    assert "25 Oct 2026" in response.text
    assert "Agentic design" in response.text
    assert "Rule, skill, and agent compared." in response.text
    assert "wiki/ai/agentic-design.md" in response.text
    assert "Most recently changed" in response.text
    assert "3 waiting" in response.text
    assert 'href="/knowledge"' in response.text
    assert 'Knowledge<span class="nav-count">2</span>' in response.text


def test_knowledge_screen_says_when_the_wiki_is_empty():
    empty = Source.success(KnowledgeView(pages=[], inbox_count=0), source="Knowledge", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(knowledge_source=empty)))
    response = client.get("/knowledge")
    assert response.status_code == 200
    assert "No wiki pages under .kb/wiki" in response.text
    assert "0 waiting" in response.text


def test_knowledge_screen_shows_a_source_error():
    failed = Source.failure("wiki could not be read", source="Knowledge", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(knowledge_source=failed)))
    response = client.get("/knowledge")
    assert response.status_code == 200
    assert "Knowledge unavailable" in response.text
    assert "wiki could not be read" in response.text


def test_knowledge_failure_leaves_the_overview_usable():
    failed = Source.failure("wiki could not be read", source="Knowledge", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(knowledge_source=failed)))
    response = client.get("/")
    assert response.status_code == 200
    assert "AKSA OS" in response.text
    assert "Knowledge unavailable" in response.text


def test_overview_shows_the_knowledge_panel():
    client = TestClient(create_app(fake_sources()))
    response = client.get("/")
    assert "Recent pages" in response.text
    assert "OneO4 Newsletter" in response.text
    assert "3 in inbox" in response.text
    assert 'href="/knowledge"' in response.text


def test_knowledge_screen_shows_the_five_most_recent_pages_in_the_recent_section():
    pages = [
        KnowledgePage(
            title=f"Page {day}",
            area="ai",
            path=f"wiki/ai/page-{day}.md",
            summary="A page.",
            updated=date(2026, 10, day),
        )
        for day in range(1, 7)
    ]
    view = Source.success(
        KnowledgeView(pages=list(reversed(pages)), inbox_count=0), source="Knowledge", read_at=READ_AT
    )
    client = TestClient(create_app(fake_sources(knowledge_source=view)))

    response = client.get("/knowledge")

    recent = response.text.split("Most recently changed")[1].split("Wiki pages")[0]
    assert "Page 6" in recent
    assert "Page 2" in recent
    assert "Page 1" not in recent
    assert "Page 1" in response.text


@pytest.mark.parametrize("path", ["/factory", "/projects"])
def test_screens_that_do_not_show_knowledge_do_not_read_it(path):
    def unread() -> Source[KnowledgeView]:
        raise AssertionError(f"{path} read the knowledge source")

    sources = Sources(
        factory=lambda: Source.success(factory_runs(), source="GitHub", read_at=READ_AT),
        projects=lambda: Source.success(projects(), source="Projects", read_at=READ_AT),
        knowledge=unread,
        credits=lambda: Source.success(credit_providers(), source="Credits", read_at=READ_AT),
    )

    response = TestClient(create_app(sources)).get(path)

    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/factory", "/projects", "/knowledge"])
def test_screens_that_do_not_show_credits_do_not_read_them(path):
    def unread() -> Source[CreditView]:
        raise AssertionError(f"{path} read the credits source")

    sources = Sources(
        factory=lambda: Source.success(factory_runs(), source="GitHub", read_at=READ_AT),
        projects=lambda: Source.success(projects(), source="Projects", read_at=READ_AT),
        knowledge=lambda: Source.success(knowledge_pages(), source="Knowledge", read_at=READ_AT),
        credits=unread,
    )

    response = TestClient(create_app(sources)).get(path)

    assert response.status_code == 200


def test_agents_screen_shows_all_four_providers():
    response = TestClient(create_app(fake_sources())).get("/agents")

    assert response.status_code == 200
    for name in ("Claude Code", "OpenRouter", "OpenCode", "Google AI Studio"):
        assert name in response.text
    assert "72.5%" in response.text
    assert "$6.50" in response.text
    assert "macOS Keychain + Anthropic usage API" in response.text
    assert "read 09:00:00" in response.text
    assert 'href="https://openrouter.ai/credits"' in response.text
    assert 'href="https://aistudio.google.com/app/billing"' in response.text
    assert "4/4 available" in response.text
    assert 'Agents<span class="nav-count">4</span>' in response.text


def test_agents_screen_shows_a_failed_provider_without_hiding_the_others():
    view = credits({"Claude Code": failed_credit("Claude Code", "Claude usage endpoint answered 500.")})
    client = TestClient(
        create_app(fake_sources(credits_source=Source.success(view, source="Credits", read_at=READ_AT)))
    )

    response = client.get("/agents")

    assert response.status_code == 200
    assert "Claude usage endpoint answered 500." in response.text
    assert ">unavailable<" in response.text
    assert "OpenRouter" in response.text
    assert "$6.50" in response.text
    assert "3/4 available" in response.text


def test_agents_screen_stays_up_when_every_provider_fails():
    view = CreditView(
        providers=[
            failed_credit(name, f"{name} source failed.")
            for name in ("Claude Code", "OpenRouter", "OpenCode", "Google AI Studio")
        ]
    )
    client = TestClient(
        create_app(fake_sources(credits_source=Source.success(view, source="Credits", read_at=READ_AT)))
    )

    response = client.get("/agents")

    assert response.status_code == 200
    for name in ("Claude Code", "OpenRouter", "OpenCode", "Google AI Studio"):
        assert name in response.text
        assert f"{name} source failed." in response.text
    assert "0/4 available" in response.text


def test_agents_screen_marks_the_manual_balance_unset():
    unset = CreditProvider.success(
        "Google AI Studio",
        source="Manual file .local/aksa_os.json",
        read_at=READ_AT,
        link="https://aistudio.google.com/app/billing",
        link_label="AI Studio billing",
        manual=True,
        unset=True,
        note="No balance in .local/aksa_os.json.",
    )
    client = TestClient(
        create_app(
            fake_sources(
                credits_source=Source.success(credits({"Google AI Studio": unset}), source="Credits", read_at=READ_AT)
            )
        )
    )

    response = client.get("/agents")

    assert response.status_code == 200
    assert "Not set" in response.text
    assert "No balance in .local/aksa_os.json." in response.text
    assert ">manual<" in response.text
    assert "3/4 available" in response.text


def test_agents_screen_keeps_env_and_keychain_values_out_of_the_page(tmp_path, monkeypatch):
    claude_token = "sentinel-claude-token-6c1f"
    openrouter_key = "sentinel-openrouter-key-9a2d"
    monkeypatch.setenv("OPENROUTER_API_KEY", openrouter_key)
    env_file = tmp_path / ".env"
    env_file.write_text(f"OPENROUTER_API_KEY={openrouter_key}\n")
    manual = tmp_path / "aksa_os.json"
    manual.write_text(json.dumps({"google_ai_studio": {"balance": 12.34, "currency": "USD"}}))
    http = StubHttp(
        {
            "https://api.anthropic.com/api/oauth/usage": StubResponse(
                {
                    "five_hour": {"utilization": 72.5, "resets_at": "2026-10-25T14:00:00+00:00"},
                    "seven_day": {"utilization": 41.0, "resets_at": "2026-10-31T09:00:00+00:00"},
                }
            ),
            "https://openrouter.ai/api/v1/credits": StubResponse({"data": {"total_credits": 10.0, "total_usage": 3.5}}),
        }
    )
    source = read_credits(
        lambda: read_claude(
            lambda: json.dumps({"claudeAiOauth": {"accessToken": claude_token, "subscriptionType": "pro"}}),
            http,
            5.0,
            system=lambda: "Darwin",
        ),
        lambda: read_openrouter(read_env(env_file), http, 5.0),
        lambda: read_opencode(tmp_path / "absent.db"),
        lambda: read_google(manual),
    )
    client = TestClient(create_app(fake_sources(credits_source=source)))

    for path in ("/", "/agents"):
        response = client.get(path)
        assert response.status_code == 200
        assert claude_token not in response.text
        assert openrouter_key not in response.text
    assert "Claude Code" in response.text
    assert "$6.50" in response.text


def test_overview_shows_the_credits_panel():
    response = TestClient(create_app(fake_sources())).get("/")

    assert response.status_code == 200
    assert 'id="credits"' in response.text
    assert "OpenRouter" in response.text
    assert "$6.50" in response.text
    assert 'href="/agents"' in response.text


def test_credits_source_failure_leaves_the_page_usable():
    failed = Source.failure("credits could not be read", source="Credits", read_at=READ_AT)
    client = TestClient(create_app(fake_sources(credits_source=failed)))

    for path in ("/", "/agents"):
        response = client.get(path)
        assert response.status_code == 200
        assert "Credits unavailable" in response.text
        assert "credits could not be read" in response.text


class StubResponse:
    """One HTTP response for the injected transport."""

    def __init__(self, payload):
        self.status_code = 200
        self.payload = payload

    def json(self):
        return self.payload


class StubHttp:
    """The injected transport, answering by URL."""

    def __init__(self, responses):
        self.responses = responses

    def __call__(self, url, *, headers, timeout):
        return self.responses[url]

from fastapi.testclient import TestClient

from career_platform.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_renders_database_projects() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Investment Screening Dashboard" in response.text


def test_resume_serves_the_pdf_in_the_browser() -> None:
    response = client.get("/resume")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'inline; filename="Chelsea_Huang_Resume.pdf"'
    assert response.content.startswith(b"%PDF")


def test_resume_falls_back_to_html_without_the_pdf(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("career_platform.main.RESUME_PDF", tmp_path / "missing.pdf")
    response = client.get("/resume")
    assert response.status_code == 200
    assert "attachment; filename=\"resume.html\"" == response.headers["content-disposition"]
    assert "Portfolio Strategy Case Study" in response.text


def test_privacy_page_describes_analytics_and_is_linked_from_the_footer() -> None:
    response = client.get("/privacy")
    assert response.status_code == 200
    assert "Google Analytics" in response.text
    assert "_ga_R24K9LD7H4" in response.text
    assert "does not respond to Do Not Track" in response.text
    assert '<a href="/privacy">Privacy</a>' in client.get("/").text


def test_google_tag_loads_once_on_each_page() -> None:
    for path in ("/", "/privacy"):
        text = client.get(path).text
        assert text.count("googletagmanager.com/gtag/js?id=G-R24K9LD7H4") == 1
        assert text.count("gtag('config', 'G-R24K9LD7H4')") == 1
        # Google's instructions put the tag immediately after <head>.
        after_head = text.split("<head>", 1)[1].lstrip()
        assert after_head.startswith("<!-- Google tag (gtag.js)")


def test_analytics_consent_starts_denied_and_can_be_changed() -> None:
    text = client.get("/").text
    # The default must reach the dataLayer before the config command sends anything.
    assert text.index("gtag('consent', 'default'") < text.index("gtag('config', 'G-R24K9LD7H4')")
    assert "analytics_storage: 'denied'" in text
    assert '<div class="consent-bar" role="region" aria-label="Analytics choice" hidden>' in text
    assert 'data-consent="granted"' in text and 'data-consent="denied"' in text
    assert "data-consent-reset" in client.get("/privacy").text


def test_figures_marks_numbers_and_escapes_the_rest() -> None:
    from career_platform.main import figures

    marked = figures("Modeled $140M at a 7.8% WACC for <20 users")
    assert marked == (
        "Modeled <strong>$140M</strong> at a <strong>7.8%</strong> WACC "
        "for &lt;<strong>20</strong> users"
    )


def test_homepage_puts_the_site_project_last(monkeypatch) -> None:
    from career_platform.models import Project

    projects = [
        Project(id=2, title="Career Platform Website (this site)", summary="A. B", technologies="FastAPI", link=None),
        Project(id=1, title="RMBS Dashboard", summary="Capstone, 2026. Tracked 9 indicators.", technologies="SQL", link=None),
    ]
    monkeypatch.setattr("career_platform.main.get_projects", lambda: projects)
    text = client.get("/").text
    assert text.index("RMBS Dashboard") < text.index("Career Platform Website (this site)")
    assert '<p class="project-meta">Capstone, 2026</p>' in text
    assert "Tracked <strong>9</strong> indicators." in text


def test_homepage_uses_the_fallback_when_the_database_is_unreachable(monkeypatch, caplog) -> None:
    # Nothing listens on port 1, so the connection is refused straight away.
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@127.0.0.1:1/missing_test")
    response = client.get("/")
    assert response.status_code == 200
    assert "Investment Screening Dashboard" in response.text
    assert "Database unavailable" in caplog.text


def test_homepage_uses_the_fallback_when_database_url_is_not_set(monkeypatch, caplog) -> None:
    monkeypatch.delenv("DATABASE_URL")
    response = client.get("/")
    assert response.status_code == 200
    assert "Investment Screening Dashboard" in response.text
    assert "Database unavailable" in caplog.text

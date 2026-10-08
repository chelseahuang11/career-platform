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

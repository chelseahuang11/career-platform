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


def test_resume_download_renders_projects() -> None:
    response = client.get("/resume")
    assert response.status_code == 200
    assert "attachment; filename=\"resume.html\"" == response.headers["content-disposition"]
    assert "Portfolio Strategy Case Study" in response.text

import sqlite3

from career_platform.database import init_db

DEMO_TITLES = {
    "Investment Screening Dashboard",
    "Portfolio Strategy Case Study",
    "Data Storytelling Project",
}


def _use_database(monkeypatch, path) -> None:
    monkeypatch.setenv("CAREER_PLATFORM_DATABASE", str(path))


def _project_titles(path) -> set[str]:
    connection = sqlite3.connect(path)
    try:
        return {row[0] for row in connection.execute("SELECT title FROM projects")}
    finally:
        connection.close()


def test_init_db_seeds_demo_projects_into_empty_database(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "fresh.db"
    _use_database(monkeypatch, db_path)

    init_db()

    assert _project_titles(db_path) == DEMO_TITLES


def test_init_db_does_not_add_demo_projects_next_to_real_ones(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "real.db"
    _use_database(monkeypatch, db_path)
    init_db()
    connection = sqlite3.connect(db_path)
    connection.execute("DELETE FROM projects")
    connection.execute(
        "INSERT INTO projects (title, summary, technologies, link) VALUES (?, ?, ?, ?)",
        ("My Real Project", "Something I built.", "Python", None),
    )
    connection.commit()
    connection.close()

    init_db()

    assert _project_titles(db_path) == {"My Real Project"}


def test_init_db_keeps_an_existing_profile(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "profile.db"
    _use_database(monkeypatch, db_path)
    init_db()
    connection = sqlite3.connect(db_path)
    connection.execute("UPDATE profile SET email = ? WHERE id = 1", ("me@example.edu",))
    connection.commit()
    connection.close()

    init_db()

    connection = sqlite3.connect(db_path)
    email = connection.execute("SELECT email FROM profile WHERE id = 1").fetchone()[0]
    connection.close()
    assert email == "me@example.edu"

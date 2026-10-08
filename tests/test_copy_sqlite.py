import sqlite3

import psycopg
import pytest

from career_platform.config import database_url
from career_platform.copy_sqlite import copy
from career_platform.database import get_profile, get_projects, init_db

DASH_TITLE = "Allegiant–Sun Country Airlines Acquisition Analysis"


def _make_sqlite(path):
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE profile (id INTEGER PRIMARY KEY, name TEXT, title TEXT, location TEXT,"
        " email TEXT, linkedin TEXT, github TEXT)"
    )
    connection.execute(
        "CREATE TABLE projects (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, summary TEXT,"
        " technologies TEXT, link TEXT)"
    )
    connection.execute(
        "INSERT INTO profile VALUES (1, 'Chelsea Huang', 'Student', 'Los Angeles, CA',"
        " 'me@example.edu', NULL, 'https://github.com/chelseahuang11')"
    )
    connection.executemany(
        "INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
        [
            (4, "RollEase Startup Project", "Startup, 2025. Sized a $2M market.", "Research", None),
            (7, DASH_TITLE, "Class, 2026. Built a DCF.", "DCF", "https://example.com/deal"),
        ],
    )
    connection.commit()
    connection.close()
    return path


def test_copy_replaces_demo_data_and_keeps_ids(empty_database, tmp_path) -> None:
    source = _make_sqlite(tmp_path / "source.db")

    assert copy(source) == 2

    projects = get_projects()
    assert [(project.id, project.title) for project in projects] == [
        (7, DASH_TITLE),
        (4, "RollEase Startup Project"),
    ]
    assert projects[1].link is None
    profile = get_profile()
    assert profile.email == "me@example.edu"
    assert profile.linkedin is None


def test_a_project_added_after_the_copy_gets_the_next_id(empty_database, tmp_path) -> None:
    copy(_make_sqlite(tmp_path / "source.db"))

    with psycopg.connect(database_url()) as connection:
        new_id = connection.execute(
            "INSERT INTO projects (title, summary, technologies) VALUES ('New', 'S', 'T') RETURNING id"
        ).fetchone()[0]

    assert new_id == 8


def test_copy_refuses_to_overwrite_real_projects_unless_told(empty_database, tmp_path) -> None:
    source = _make_sqlite(tmp_path / "source.db")
    copy(source)
    with psycopg.connect(database_url()) as connection:
        connection.execute("UPDATE projects SET summary = 'Edited on Railway.' WHERE id = 4")

    with pytest.raises(SystemExit):
        copy(source)
    assert get_projects()[1].summary == "Edited on Railway."

    copy(source, replace=True)
    assert get_projects()[1].summary == "Startup, 2025. Sized a $2M market."


def test_copy_with_a_missing_file_changes_nothing(empty_database, tmp_path) -> None:
    init_db()
    missing = tmp_path / "missing.db"

    with pytest.raises(FileNotFoundError):
        copy(missing)

    assert not missing.exists()
    assert len(get_projects()) == 3

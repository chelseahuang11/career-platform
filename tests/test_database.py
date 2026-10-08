from concurrent.futures import ThreadPoolExecutor

import psycopg

from career_platform.config import database_url
from career_platform.database import init_db

DEMO_TITLES = {
    "Investment Screening Dashboard",
    "Portfolio Strategy Case Study",
    "Data Storytelling Project",
}


def _project_titles() -> set[str]:
    with psycopg.connect(database_url()) as connection:
        return {row[0] for row in connection.execute("SELECT title FROM projects")}


def test_init_db_seeds_demo_projects_into_empty_database(empty_database) -> None:
    init_db()

    assert _project_titles() == DEMO_TITLES


def test_init_db_does_not_add_demo_projects_next_to_real_ones(empty_database) -> None:
    init_db()
    with psycopg.connect(database_url()) as connection:
        connection.execute("DELETE FROM projects")
        connection.execute(
            "INSERT INTO projects (title, summary, technologies, link) VALUES (%s, %s, %s, %s)",
            ("My Real Project", "Something I built.", "Python", None),
        )

    init_db()

    assert _project_titles() == {"My Real Project"}


def test_init_db_keeps_an_existing_profile(empty_database) -> None:
    init_db()
    with psycopg.connect(database_url()) as connection:
        connection.execute("UPDATE profile SET email = %s WHERE id = 1", ("me@example.edu",))

    init_db()

    with psycopg.connect(database_url()) as connection:
        email = connection.execute("SELECT email FROM profile WHERE id = 1").fetchone()[0]
    assert email == "me@example.edu"


def test_init_db_is_safe_when_several_processes_start_together(empty_database) -> None:
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in [pool.submit(init_db) for _ in range(4)]:
            result.result()

    assert _project_titles() == DEMO_TITLES

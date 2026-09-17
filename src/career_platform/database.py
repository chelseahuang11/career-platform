from __future__ import annotations

import sqlite3

from .config import database_path
from .models import Profile, Project

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT NOT NULL,
                email TEXT NOT NULL,
                linkedin TEXT,
                github TEXT
            )
            """,
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                summary TEXT NOT NULL,
                technologies TEXT NOT NULL,
                link TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO profile (id, name, title, location, email, linkedin, github)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "Chelsea Huang",
                "Student | Finance, Investing, and Data Analysis",
                "Los Angeles, CA",
                "chelseahuang11@gmail.com",
                "https://www.linkedin.com/in/chelseahuang",
                "https://github.com/chelseahuang11",
            ),
        )

        for project in [
            (
                "Investment Screening Dashboard",
                "Built a dashboard to evaluate public market opportunities using structured financial metrics and scenario comparisons.",
                "Python, SQLite, Jinja, FastAPI",
                "https://example.com/project/investment-screening",
            ),
            (
                "Portfolio Strategy Case Study",
                "Created a compact investment memo that compared risk-adjusted return assumptions across multiple sectors and allocation scenarios.",
                "Excel, Analysis, Research",
                "https://example.com/project/portfolio-strategy",
            ),
            (
                "Data Storytelling Project",
                "Used a structured dataset to present key business insights with visual summaries and concise narrative explanations.",
                "SQL, Python, Data Visualization",
                "https://example.com/project/data-storytelling",
            ),
        ]:
            connection.execute(
                """
                INSERT INTO projects (title, summary, technologies, link)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM projects WHERE title = ?)
                """,
                (*project, project[0]),
            )
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_profile() -> Profile:
    connection = get_connection()
    row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    connection.close()

    if row is None:
        raise ValueError("Profile is missing from the database")

    return Profile(
        id=row["id"],
        name=row["name"],
        title=row["title"],
        location=row["location"],
        email=row["email"],
        linkedin=row["linkedin"],
        github=row["github"],
    )


def get_projects() -> list[Project]:
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM projects ORDER BY id DESC"
    ).fetchall()
    connection.close()

    return [
        Project(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            technologies=row["technologies"],
            link=row["link"],
        )
        for row in rows
    ]

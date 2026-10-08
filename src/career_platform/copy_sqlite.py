"""Copy the profile and projects from a SQLite file into the PostgreSQL database in DATABASE_URL.

Usage: python -m career_platform.copy_sqlite data/career_platform.db [--replace]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import tuple_row

from .database import get_connection, init_db

PROFILE_COLUMNS = "id, name, title, location, email, linkedin, github"
PROJECT_COLUMNS = "id, title, summary, technologies, link"
DEMO_TITLES = {
    "Investment Screening Dashboard",
    "Portfolio Strategy Case Study",
    "Data Storytelling Project",
}


def read_sqlite(path: Path) -> tuple[list[tuple], list[tuple]]:
    # sqlite3.connect would quietly create an empty file for a mistyped path.
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path)
    try:
        profile = connection.execute(f"SELECT {PROFILE_COLUMNS} FROM profile ORDER BY id").fetchall()
        projects = connection.execute(f"SELECT {PROJECT_COLUMNS} FROM projects ORDER BY id").fetchall()
    finally:
        connection.close()
    return profile, projects


def read_postgres(connection: psycopg.Connection) -> tuple[list[tuple], list[tuple]]:
    cursor = connection.cursor(row_factory=tuple_row)
    profile = cursor.execute(f"SELECT {PROFILE_COLUMNS} FROM profile ORDER BY id").fetchall()
    projects = cursor.execute(f"SELECT {PROJECT_COLUMNS} FROM projects ORDER BY id").fetchall()
    return profile, projects


def copy(sqlite_path: Path, replace: bool = False) -> int:
    """Replace what PostgreSQL holds with the SQLite file's rows; return the number of projects."""
    profile, projects = read_sqlite(sqlite_path)
    init_db()
    # One transaction: a failure anywhere below leaves PostgreSQL as it was.
    with get_connection() as connection:
        _, existing = read_postgres(connection)
        if {row[1] for row in existing} - DEMO_TITLES and not replace:
            raise SystemExit(
                "PostgreSQL already holds projects that are not demo data. "
                "Pass --replace to overwrite them."
            )
        connection.execute("DELETE FROM projects")
        connection.execute("DELETE FROM profile")
        cursor = connection.cursor()
        cursor.executemany(
            f"INSERT INTO profile ({PROFILE_COLUMNS}) VALUES (%s, %s, %s, %s, %s, %s, %s)", profile
        )
        cursor.executemany(
            f"INSERT INTO projects ({PROJECT_COLUMNS}) VALUES (%s, %s, %s, %s, %s)", projects
        )
        # Rows inserted with their own ids do not move the id counter, so set it past the highest.
        connection.execute(
            "SELECT setval(pg_get_serial_sequence('projects', 'id'),"
            " (SELECT COALESCE(MAX(id), 1) FROM projects))"
        )
        if read_postgres(connection) != (profile, projects):
            raise RuntimeError("PostgreSQL does not match the SQLite file; nothing was saved")
    return len(projects)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_path", type=Path)
    parser.add_argument("--replace", action="store_true", help="overwrite projects that are not demo data")
    arguments = parser.parse_args()
    count = copy(arguments.sqlite_path, arguments.replace)
    print(f"Copied 1 profile and {count} projects into PostgreSQL")


if __name__ == "__main__":
    main()

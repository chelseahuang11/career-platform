import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
import pytest

# The tests drop and recreate tables, so they only run against a database whose
# name ends in _test. Importing the app runs init_db() against DATABASE_URL, so
# this is set before any test module imports it.
_test_url = os.environ.get("TEST_DATABASE_URL", "")
if not urlsplit(_test_url).path.endswith("_test"):
    raise pytest.UsageError(
        "Set TEST_DATABASE_URL to a PostgreSQL database whose name ends in _test "
        "(run: uv run --env-file .env pytest)"
    )
os.environ["DATABASE_URL"] = _test_url
os.environ["CAREER_PLATFORM_FALLBACK"] = str(
    Path(__file__).resolve().parents[1] / "data" / "profile_fallback.json"
)


def _drop_tables() -> None:
    with psycopg.connect(_test_url, connect_timeout=15) as connection:
        connection.execute("DROP TABLE IF EXISTS projects, profile")


@pytest.fixture
def empty_database():
    """Start the test with no tables; afterwards put the demo data back for test_app.py."""
    from career_platform.database import init_db

    _drop_tables()
    yield
    _drop_tables()
    init_db()

# Railway and PostgreSQL Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the career-platform site on Railway, reading its profile and projects from Railway's PostgreSQL instead of a SQLite file, with the same content and the same address (`chelseahuang.me`).

**Architecture:** The app keeps its shape: `database.py` is the only file that talks to the database, and it switches from Python's built-in `sqlite3` to the `psycopg` driver, reading one setting, `DATABASE_URL`. A small one-off module copies the two tables from the SQLite file into PostgreSQL. Railway builds the repo from GitHub, starts uvicorn, and gives the web service the database address over its private network. The Azure VM is not touched and keeps serving the site until the last task moves the domain.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, psycopg 3 (`psycopg[binary]`), PostgreSQL 18 on Railway, Railpack (Railway's builder), uv, pytest, Cloudflare DNS.

**Spec:** the request of 2026-10-08 ("plan its move to Railway and PostgreSQL; the Railway project already exists with Postgres and a web service"). There is no separate spec file; the Goal and Global Constraints restate it. Earlier work: `docs/superpowers/plans/2026-09-24-azure-vm-migration.md`, `docs/superpowers/plans/2026-10-01-operate-the-vm.md`.

## What the inspection found (2026-10-08, read-only)

| | |
|---|---|
| App | FastAPI, 3 routes (`/`, `/resume`, `/health`). All database code is in `src/career_platform/database.py` (133 lines, `sqlite3`). `main.py` catches `sqlite3.Error` and serves `data/profile_fallback.json` if the database fails. |
| Tables | `profile` (1 row, `id` fixed to 1) and `projects` (4 rows, ids 4 to 7, next id would be 8). No other tables, no user input, no writes after startup. |
| Data | The laptop's `data/career_platform.db` and the VM's are identical (same rows, compared by hash). One title contains an en dash (`Allegiant–Sun Country`), so text must arrive as UTF-8. |
| VM | Serves `https://chelseahuang.me` from commit `71cd1ec` with SQLite. It does not pull from GitHub on its own. |
| Railway Postgres | PostgreSQL 18.6, UTF-8, reachable from the laptop over SSL through the public address in `.env` (`RAILWAY_DATABASE_URL`). Database `railway` is **empty: no tables**. |
| `.env` bug | `RAILWAY_DATABASE_URL` ends in `/railway/`. The trailing `/` makes PostgreSQL look for a database named `railway/` and refuse the connection. Step 1.1 removes it. |
| Railway web service | Not inspected: the Railway CLI is not installed and the agent has no dashboard access. Step 4.1 is where Chelsea reads its settings. |
| Railway builder | Railpack. It reads `.python-version` (3.12) and `uv.lock`. Its default FastAPI start command is `uvicorn main:app`, which is wrong for this repo (the app is `career_platform.main:app` under `src/`), so a custom start command is needed. |
| `railway.json` | Railway's docs mark config files in the repo as deprecated (working until 2026-12-01). This plan sets the start command in the dashboard instead and adds no Railway file to the repo. |
| DNS | `chelseahuang.me` uses Cloudflare nameservers. The bare name points at the VM. From the laptop, `www.chelseahuang.me` did **not** resolve to the VM's address; step 5.1 looks at that record. |
| Tests | 9 pass today, all against a throwaway SQLite file. |

## Decisions in this plan (say so if you want a different one)

1. **PostgreSQL only.** The app stops supporting SQLite instead of supporting both. One set of SQL is easier to read and test. The VM is unaffected because it stays on its current commit.
2. **Tests use a second database, `career_platform_test`, on the same Railway Postgres.** There is no PostgreSQL on the laptop. Tests refuse to run against any database whose name does not end in `_test`. They need the Internet and take roughly 15 to 30 seconds instead of 1.
   **Changed 2026-10-08:** the tests now use PostgreSQL 18.6 in a Docker container on the laptop (`career_platform_db`, `127.0.0.1:5434`, volume `career_platform_pgdata`), and `TEST_DATABASE_URL` in `.env` points there. `16 passed` in about 9 seconds, with no Internet needed. Docker Desktop has to be running. The `career_platform_test` database on Railway still exists but is no longer used, and `.env.example` still describes the old setup.
3. **The domain moves last, and the VM stays up.** Until Task 5 the public site is the VM. After Task 5 the VM is the way back. Shutting the VM down is not part of this plan.
4. **Chelsea does everything in the Railway dashboard and in Cloudflare.** The agent changes code, and reads and writes the database through the address in `.env`.

## Global Constraints

- The VM is not changed: no `git pull`, no service or nginx change, no change to its SQLite file.
- No password, database address, or Railway hostname goes into any committed file. They live in `.env` (ignored by git) and in Railway's variables. This repo is public.
- Driver: `psycopg[binary]` version 3. No ORM, no connection pool, no migration tool.
- The two tables keep their column names, and every row keeps its `id`. Pages must look the same as today.
- Tests may only connect to a database whose name ends in `_test`.
- Code work happens on the branch `railway-postgres`. `main` changes only at step 4.3.
- Load `.env` with `uv run --env-file .env …` (or `set -a; . ./.env; set +a` in Git Bash). Never print it.

## Review Focus

1. **Tests pointed at the live database.** They drop tables. `tests/conftest.py` stops the run unless the database name ends in `_test` (step 1.3, checked in step 1.4).
2. **The database is down or slow.** A visitor should still get a page within a few seconds, from the fallback file. `connect_timeout=5` plus two tests in step 1.5 pin this. Because the fallback looks normal, every deploy check looks for `RollEase Startup Project`, which exists only in the database.
3. **The id counter after the copy.** Copying rows with their old ids does not move PostgreSQL's counter, so the next new project would collide with id 1 to 7. Step 2.1 tests that the next id is 8.
4. **Two copies of the app start at once.** Railway runs the old and new deployment side by side for a moment, and both run `init_db()`. A PostgreSQL advisory lock makes them take turns; step 1.5 tests four at once.
5. **The stylesheet link is `http://` on an `https://` page.** Behind Railway's proxy the app thinks requests are plain HTTP unless uvicorn is told to trust the proxy, and browsers block the CSS. The start command in step 4.2 sets this; step 4.4 checks the link.

## Progress

| Task | Status | Date | Notes |
|---|---|---|---|
| 1. The app talks to PostgreSQL | Done | 2026-10-08 | Commit `d27e381` on `railway-postgres`. 12 tests pass against `career_platform_test`. |
| 2. The copy tool | Done | 2026-10-08 | Commit `9300e5f`. 16 tests pass. Rehearsed with the real file against the test database. |
| 3. Copy the real data | Done | 2026-10-08 | The live `railway` database holds 1 profile and 4 projects (ids 4 to 7), next id 8. Nothing serves from it yet. |
| 4. Deploy on Railway | Not started | | |
| 5. Move the domain | Not started | | |

## File structure

| File | Change | Responsibility |
|---|---|---|
| `pyproject.toml`, `uv.lock` | Modify | Add `psycopg[binary]`. |
| `src/career_platform/config.py` | Modify | `database_url()` replaces `database_path()`. |
| `src/career_platform/database.py` | Rewrite | Same four functions, PostgreSQL SQL. |
| `src/career_platform/main.py` | Modify (3 lines) | Catch `psycopg.Error` instead of `sqlite3.Error`. |
| `src/career_platform/copy_sqlite.py` | Create | One-off copy from a SQLite file into PostgreSQL. |
| `tests/conftest.py` | Rewrite | Point tests at the `_test` database; `empty_database` fixture. |
| `tests/test_database.py` | Rewrite | Same three tests on PostgreSQL, plus the concurrency test. |
| `tests/test_app.py` | Modify | Two new fallback tests. |
| `tests/test_copy_sqlite.py` | Create | Tests for the copy tool. |
| `.env.example` | Modify | New variable names. |

---

### Task 1: The app talks to PostgreSQL

**For a beginner:** SQLite is a file the app opens. PostgreSQL is a separate program the app connects to over the network, so the app needs an address (a URL with user, password, host, port, database name) and a driver, `psycopg`, that speaks PostgreSQL's language. Three pieces of SQL differ: placeholders are `%s` instead of `?`, the auto-numbered id is written `GENERATED BY DEFAULT AS IDENTITY`, and "insert unless it exists" is `ON CONFLICT DO NOTHING`.

**Where:** laptop, Git Bash, repo root.

**Files:**
- Modify: `pyproject.toml`, `uv.lock`, `.env.example`, `src/career_platform/config.py`, `src/career_platform/main.py:5,55,62`, `tests/test_app.py`
- Rewrite: `src/career_platform/database.py`, `tests/conftest.py`, `tests/test_database.py`

**Interfaces:**
- Produces: `career_platform.config.database_url() -> str` (raises `ValueError` if `DATABASE_URL` is unset); `career_platform.database.get_connection() -> psycopg.Connection` (rows are dicts); `init_db() -> None`, `get_profile() -> Profile`, `get_projects() -> list[Project]` unchanged in name and return type; pytest fixture `empty_database`.

- [x] **Step 1.1: Branch, driver, and a test database**

  ```bash
  git switch -c railway-postgres
  uv add "psycopg[binary]"
  ```

  Remove the trailing `/` from the address in `.env` (the file has one line and is not printed):

  ```bash
  sed -i 's|/*[[:space:]]*$||' .env
  ```

  Create the test database and add its address to `.env`:

  ```bash
  uv run --env-file .env python -c "import os, psycopg; psycopg.connect(os.environ['RAILWAY_DATABASE_URL'], autocommit=True, connect_timeout=15).execute('CREATE DATABASE career_platform_test')"
  uv run --env-file .env python -c "import os; u = os.environ['RAILWAY_DATABASE_URL']; open('.env', 'a').write('\nTEST_DATABASE_URL=' + u.rsplit('/', 1)[0] + '/career_platform_test\n')"
  ```

  **Check:**

  ```bash
  uv run --env-file .env python -c "import os, psycopg; [print(k, psycopg.connect(os.environ[k], connect_timeout=15).execute('select current_database()').fetchone()[0]) for k in ('RAILWAY_DATABASE_URL', 'TEST_DATABASE_URL')]"
  ```

  prints `RAILWAY_DATABASE_URL railway` then `TEST_DATABASE_URL career_platform_test`.

  **Undo:** `DROP DATABASE career_platform_test` with the same one-liner pattern, delete the `TEST_DATABASE_URL` line from `.env`, `git switch main; git branch -D railway-postgres`.

- [x] **Step 1.2: Replace `.env.example`**

  ```bash
  # Copy to .env. Run commands with: uv run --env-file .env ...
  # Paths are relative to the directory uvicorn starts in (the repo root).
  CAREER_PLATFORM_DATA_DIR=data
  CAREER_PLATFORM_FALLBACK=data/profile_fallback.json
  # The app reads DATABASE_URL. On Railway the web service gets it from the Postgres service.
  # The two below are for the laptop. Take the public address from Railway:
  # Postgres service -> Variables -> DATABASE_PUBLIC_URL. No trailing slash.
  RAILWAY_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/railway
  # Same server, a separate database that the tests are allowed to wipe.
  TEST_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/career_platform_test
  ```

- [x] **Step 1.3: Rewrite the tests first**

  `tests/conftest.py`:

  ```python
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
  ```

  `tests/test_database.py`:

  ```python
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
  ```

- [x] **Step 1.4: Run the tests and watch them fail for the right reason**

  ```bash
  uv run pytest -q
  ```

  **Check:** the run stops at once with `Set TEST_DATABASE_URL to a PostgreSQL database whose name ends in _test`. This is Review Focus 1 working.

  ```bash
  uv run --env-file .env pytest -q
  ```

  **Check:** fails with `ImportError: cannot import name 'database_url'`.

- [x] **Step 1.5: Write the code**

  In `src/career_platform/config.py`, replace the `database_path` function with:

  ```python
  def database_url() -> str:
      url = os.getenv("DATABASE_URL")
      if not url:
          raise ValueError("DATABASE_URL is not set")
      return url
  ```

  Replace all of `src/career_platform/database.py`:

  ```python
  from __future__ import annotations

  import psycopg
  from psycopg.rows import dict_row

  from .config import database_url
  from .models import Profile, Project

  # Any fixed number works; every process that runs init_db() has to use the same one.
  INIT_LOCK_ID = 20261008


  def get_connection() -> psycopg.Connection:
      # Without a timeout, an unreachable database would hang every page request.
      return psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=5)


  def init_db() -> None:
      # The with block commits at the end, or rolls back if anything raises.
      with get_connection() as connection:
          # Two app processes starting together take turns here.
          connection.execute("SELECT pg_advisory_xact_lock(%s)", (INIT_LOCK_ID,))
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
                  id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                  title TEXT NOT NULL UNIQUE,
                  summary TEXT NOT NULL,
                  technologies TEXT NOT NULL,
                  link TEXT
              )
              """
          )

          connection.execute(
              """
              INSERT INTO profile (id, name, title, location, email, linkedin, github)
              VALUES (%s, %s, %s, %s, %s, %s, %s)
              ON CONFLICT (id) DO NOTHING
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

          # Demo projects only fill an empty table, so they never reappear next to real ones.
          has_projects = connection.execute("SELECT 1 FROM projects LIMIT 1").fetchone()
          for project in [] if has_projects else [
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
                  VALUES (%s, %s, %s, %s)
                  ON CONFLICT (title) DO NOTHING
                  """,
                  project,
              )


  def get_profile() -> Profile:
      with get_connection() as connection:
          row = connection.execute("SELECT * FROM profile WHERE id = 1").fetchone()

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
      with get_connection() as connection:
          rows = connection.execute(
              "SELECT * FROM projects ORDER BY id DESC"
          ).fetchall()

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
  ```

  In `src/career_platform/main.py`, three edits:

  - line 5: `import sqlite3` becomes `import psycopg`
  - in `load_public_content`: `except (OSError, sqlite3.Error, ValueError):` becomes `except (OSError, psycopg.Error, ValueError):`
  - around `init_db()`: `except (OSError, sqlite3.Error):` becomes `except (OSError, psycopg.Error, ValueError):` (`ValueError` is the missing-`DATABASE_URL` case, which must not stop the app from starting)

  Add to the end of `tests/test_app.py`:

  ```python
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
  ```

- [x] **Step 1.6: Run the tests**

  ```bash
  uv run --env-file .env pytest -q
  ```

  **Check:** `12 passed` (6 old app tests, 2 new, 4 database tests). Run it a second time: still `12 passed`, which shows the tests clean up after themselves.

  ```bash
  grep -rn sqlite src/career_platform/
  ```

  **Check:** the only matches are the two words `SQLite` inside the demo project text in `database.py`.

- [x] **Step 1.7: See it in a browser against the test database**

  ```bash
  set -a; . ./.env; set +a
  DATABASE_URL="$TEST_DATABASE_URL" uv run uvicorn career_platform.main:app --port 8001
  ```

  **Check:** `http://localhost:8001` shows the page with the three demo projects, styled, and the terminal shows no `Database unavailable` line. Stop it with Ctrl+C.

- [x] **Step 1.8: Commit**

  ```bash
  git add pyproject.toml uv.lock .env.example src/career_platform/config.py src/career_platform/database.py src/career_platform/main.py tests/conftest.py tests/test_database.py tests/test_app.py
  git commit -m "Read the profile and projects from PostgreSQL"
  ```

**Results (2026-10-08).** The agent ran every step from the laptop.

| Step | What the check showed |
|---|---|
| 1.1 | Branch `railway-postgres` created. `psycopg` 3.3.6 added. The trailing `/` is gone from `.env`. `career_platform_test` created; both addresses connect (`railway`, `career_platform_test`). |
| 1.4 | Without `--env-file`: the run stopped with the `Set TEST_DATABASE_URL…` message. With it: collection failed on the missing `database_url`, as expected. |
| 1.6 | `12 passed`, twice in a row. Each run takes about 36 seconds, not 15 to 30: every connection to Railway from the laptop costs about 0.7 seconds, and the unreachable-database test waits the full 5-second timeout on Windows. `grep -rn sqlite src/career_platform/` prints nothing (the demo text says `SQLite`, capitalised, which a case-sensitive search skips). |
| 1.7 | Checked with `curl` instead of a browser: the page has `Chelsea Huang` and the demo projects, the CSS answers `200`, and the server log has no `Database unavailable` line. |

**Undo Task 1:** `git switch main` leaves the SQLite app exactly as it was. Nothing outside the laptop changed except the new, separate `career_platform_test` database.

---

### Task 2: The copy tool

**For a beginner:** the real profile and projects live in the SQLite file. This small module reads them and writes them into PostgreSQL in one transaction, so it either finishes completely or changes nothing. It keeps each row's `id`, then moves PostgreSQL's id counter past the highest one, and it compares what landed with what it read before saving.

**Where:** laptop, Git Bash, repo root.

**Files:**
- Create: `src/career_platform/copy_sqlite.py`, `tests/test_copy_sqlite.py`

**Interfaces:**
- Consumes: `get_connection()`, `init_db()` from Task 1; the `empty_database` fixture.
- Produces: `career_platform.copy_sqlite.copy(sqlite_path: Path, replace: bool = False) -> int` (number of projects copied); command `python -m career_platform.copy_sqlite <file.db> [--replace]`.

- [x] **Step 2.1: Write the failing tests**

  `tests/test_copy_sqlite.py`:

  ```python
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
  ```

- [x] **Step 2.2: Run them to see them fail**

  ```bash
  uv run --env-file .env pytest tests/test_copy_sqlite.py -q
  ```

  **Check:** `ModuleNotFoundError: No module named 'career_platform.copy_sqlite'`.

- [x] **Step 2.3: Write the module**

  `src/career_platform/copy_sqlite.py`:

  ```python
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
  ```

- [x] **Step 2.4: Run all the tests**

  ```bash
  uv run --env-file .env pytest -q
  ```

  **Check:** `16 passed`.

- [x] **Step 2.5: Rehearse with the real file against the test database**

  ```bash
  set -a; . ./.env; set +a
  DATABASE_URL="$TEST_DATABASE_URL" uv run python -m career_platform.copy_sqlite data/career_platform.db
  DATABASE_URL="$TEST_DATABASE_URL" uv run uvicorn career_platform.main:app --port 8001
  ```

  **Check:** prints `Copied 1 profile and 4 projects into PostgreSQL`. `http://localhost:8001` shows the four real projects, with `Allegiant–Sun Country` showing a proper dash and the website project last. Stop with Ctrl+C, then put the demo data back so the tests still pass:

  ```bash
  uv run --env-file .env python -c "import os, psycopg; psycopg.connect(os.environ['TEST_DATABASE_URL'], autocommit=True).execute('DROP TABLE projects, profile')"
  uv run --env-file .env pytest -q
  ```

  **Check:** `16 passed`.

- [x] **Step 2.6: Commit**

  ```bash
  git add src/career_platform/copy_sqlite.py tests/test_copy_sqlite.py
  git commit -m "Add a one-off copy from SQLite into PostgreSQL"
  ```

**Results (2026-10-08).**

| Step | What the check showed |
|---|---|
| 2.2 | `ModuleNotFoundError: No module named 'career_platform.copy_sqlite'`, as expected. |
| 2.4 | `16 passed` in about 66 seconds. |
| 2.5 | `Copied 1 profile and 4 projects into PostgreSQL`. The local page listed RMBS, Allegiant–Sun Country (with a proper dash), RollEase, then the website project last, with the LMU email. Checked with `curl`, not a browser. Test database reset afterwards; `16 passed`. |

**Undo Task 2:** `git reset --hard HEAD~1` on the branch. No live database was touched.

---

### Task 3: Copy the real data into Railway's PostgreSQL

**For a beginner:** this is the first step that writes to the live `railway` database. It is still invisible to visitors, because nothing serves from that database yet. It runs before the deploy so the new site never shows demo projects, even for a minute.

**Where:** laptop, Git Bash, repo root. Set `KEY` and `VM` as in the earlier plans.

- [x] **Step 3.1: Take today's file from the VM**

  The VM's file is the one the public site reads, so copy from that, not from the laptop's older copy.

  ```bash
  scp -i $KEY $VM:career-platform/data/career_platform.db data/career_platform.from-vm.db
  ```

  **Check:** `ls -l data/career_platform.from-vm.db` shows a 20480-byte file. `git status --short` does not list it (`data/*.db` is ignored). The VM only reads this file, so copying it while the site runs is safe.

- [x] **Step 3.2: Copy it into the live database**

  ```bash
  set -a; . ./.env; set +a
  DATABASE_URL="$RAILWAY_DATABASE_URL" uv run python -m career_platform.copy_sqlite data/career_platform.from-vm.db
  ```

  **Check:** `Copied 1 profile and 4 projects into PostgreSQL`.

- [x] **Step 3.3: Read it back**

  ```bash
  uv run --env-file .env python -c "
  import os, psycopg
  c = psycopg.connect(os.environ['RAILWAY_DATABASE_URL'], connect_timeout=15)
  print(c.execute('select email, title from profile').fetchall())
  for row in c.execute('select id, title from projects order by id'): print(row)
  print('next id:', c.execute(\"select last_value from pg_sequences where sequencename = 'projects_id_seq'\").fetchone()[0] + 1)
  "
  ```

  **Check:** the LMU email and title; ids 4, 5, 6, 7 with `RollEase Startup Project`, `Allegiant–Sun Country Airlines Acquisition Analysis`, `RMBS Market Intelligence Dashboard`, `Career Platform Website (this site)`; `next id: 8`.

**Results (2026-10-08).**

| Step | What the check showed |
|---|---|
| 3.1 | `data/career_platform.from-vm.db`, 20480 bytes, not listed by `git status`. |
| 3.2 | `Copied 1 profile and 4 projects into PostgreSQL`. |
| 3.3 | The LMU email and title; ids 4, 5, 6, 7 with the four real titles; `next id: 8`. Git Bash showed the dash in the Allegiant title as `?` because of the terminal's encoding; the copy tool compared the stored text with the SQLite text before saving, and they matched. |

**Undo Task 3:** the database had no tables before, so removing them restores it exactly:

```bash
uv run --env-file .env python -c "import os, psycopg; psycopg.connect(os.environ['RAILWAY_DATABASE_URL'], autocommit=True).execute('DROP TABLE projects, profile')"
```

---

### Task 4: Deploy on Railway

> **Changed 2026-10-08, to follow the course guide (Session 12).** The start command lives in the repo, in `Procfile`, not in the dashboard, so step 4.2's Custom Start Command and the `PYTHONPATH` variable are not needed (`--app-dir src` does that job). `DATABASE_URL` was already set on the web service in the guide's section 2. The branch is merged to `main`; Chelsea pushes `main`, clicks Deploy and generates the domain. The build that failed at about 2:31 PM was Railway building the old `main`, which had no start command. In Task 5 only the root domain moves, not `www`: the trial allows one custom domain, and Chelsea does that step by hand.

**For a beginner:** Railway watches the GitHub repo. When `main` changes it builds the code into a container and starts it with the start command. Railway picks the port and passes it as `$PORT`. The web service reaches Postgres over a private network inside the project, using a variable that Railway fills in from the Postgres service. Visitors reach the web service through Railway's proxy, which handles HTTPS.

**Where:** Railway dashboard (Chelsea), then laptop.

- [ ] **Step 4.1: Read the web service's current settings (Chelsea, dashboard)**

  Open the web service and write down, in the Results below: Settings → Source (which repo and branch, or none); Settings → Networking (any public domain); Variables (names only); Deployments (is anything running, and from which commit). If the service has no source yet, connect it to `chelseahuang11/career-platform`, branch `main`. Connecting may start a deploy of today's SQLite code; that is harmless, since the domain does not point here yet.

- [ ] **Step 4.2: Set variables and the start command (Chelsea, dashboard)**

  Web service → Variables, add:

  | Name | Value | Why |
  |---|---|---|
  | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Railway fills in the private address of the database. Use the Postgres service's real name if it is not `Postgres`; the dashboard autocompletes it. |
  | `PYTHONPATH` | `src` | Runs the code straight from the repo's `src/` folder, as the VM does, so the templates, CSS and PDF are found whether or not the build installs the package. |

  Web service → Settings → Deploy:

  - Custom Start Command:

    ```
    python -m uvicorn career_platform.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
    ```

    `--host 0.0.0.0` lets Railway's proxy reach the app. The last two flags tell uvicorn to believe the proxy when it says the visitor used HTTPS (Review Focus 5). That is safe here because the container can only be reached through Railway's proxy.
  - Healthcheck Path: `/health`. Railway switches traffic to a new deployment only after this answers.

  Settings → Networking: if there is no public domain, click Generate Domain. In Git Bash:

  ```bash
  RW=https://<the generated name>.up.railway.app
  ```

- [ ] **Step 4.3: Put the code on `main` (laptop)**

  ```bash
  uv run --env-file .env pytest -q
  git switch main
  git merge --ff-only railway-postgres
  git push origin main
  ```

  **Check:** `16 passed` before the merge. In the dashboard a new deployment starts within a minute and ends as Active. The build log mentions Python 3.12 and uv.

- [ ] **Step 4.4: Check the Railway site (laptop)**

  ```bash
  curl -s -m 15 $RW/health; echo
  curl -s -m 15 $RW/ | grep -o -e 'Chelsea Huang' -e 'RollEase Startup Project' -e 'Investment Screening Dashboard' -e 'href="[^"]*styles.css"' | sort -u
  curl -s -m 15 -o /dev/null -w "%{http_code} %{content_type}\n" $RW/static/css/styles.css
  curl -s -m 15 -o /dev/null -w "%{http_code} %{content_type}\n" $RW/resume
  ```

  **Check:**
  - `{"status":"ok"}`
  - `Chelsea Huang`, `RollEase Startup Project`, and a stylesheet link starting `href="https://`. **Not** `Investment Screening Dashboard`: that title means the page came from the fallback file, so the app could not read the database.
  - `200 text/css; charset=utf-8`
  - `200 application/pdf`

- [ ] **Step 4.5: Check the log and the look (Chelsea)**

  Dashboard → the deployment → Deploy Logs: no line containing `Database unavailable` or `Database initialization failed`. Then open `$RW` in a browser beside `https://chelseahuang.me`: the two pages should be the same, styled, with the resume button opening the PDF.

**If something is wrong:**

| What you see | Cause | Fix |
|---|---|---|
| Deploy log: `No module named 'career_platform'` | `PYTHONPATH` variable missing | Add it (step 4.2) and redeploy. |
| Page shows `Investment Screening Dashboard` | App cannot reach the database | Check `DATABASE_URL` is the `${{…}}` reference and the Postgres service is running; read the traceback in Deploy Logs. |
| Page unstyled, link is `href="http://…` | Proxy flags missing from the start command | Fix the start command (step 4.2). |
| Healthcheck fails | App did not start, or not on `$PORT` | Read Deploy Logs; compare the start command with step 4.2 character by character. |

**Undo Task 4:** visitors still use the VM, so there is no rush. Dashboard → Deployments → the previous deployment → Redeploy. To take the code back off `main`: `git revert` the two commits and push. The two variables and the start command can stay or be deleted.

---

### Task 5: Move the domain

**For a beginner:** DNS is the phone book that turns `chelseahuang.me` into a server's address. Today it lists the VM. Changing the entry sends visitors to Railway instead. Railway gets its own HTTPS certificate once it sees the entry. Nothing on the VM changes, so pointing the entry back at the VM undoes this.

**Where:** Railway dashboard and Cloudflare (Chelsea), then laptop.

- [ ] **Step 5.1: Write down today's DNS records (Chelsea, Cloudflare)**

  Cloudflare → `chelseahuang.me` → DNS → Records. Copy every record for `chelseahuang.me` and `www` into the Results below: type, name, content, and whether the cloud is grey (DNS only) or orange (proxied). This is the undo information. On 2026-10-08 the laptop saw `www` resolving to an address that is not the VM's, so note what that record really is.

- [ ] **Step 5.2: Add the domain in Railway (Chelsea, dashboard)**

  Web service → Settings → Networking → Custom Domain. Add `chelseahuang.me`, then `www.chelseahuang.me`. For each, Railway shows the DNS records it needs (a CNAME target, and a verification TXT record if it asks for one). Check first that your Railway plan allows two custom domains on one service; if it allows one, add only `chelseahuang.me` and leave `www` for later.

- [ ] **Step 5.3: Change the records (Chelsea, Cloudflare)**

  For each name, replace the existing A/CNAME record with the CNAME Railway showed, and add any TXT record it showed. Set the cloud to **grey (DNS only)**. Cloudflare accepts a CNAME on the bare name. Wait until Railway shows a green tick and an issued certificate for each name, usually a few minutes.

- [ ] **Step 5.4: Check the public site (laptop)**

  ```bash
  nslookup chelseahuang.me
  for H in chelseahuang.me www.chelseahuang.me; do
    curl -s -m 15 -o /dev/null -w "$H %{http_code} %{redirect_url}\n" http://$H/
    curl -s -m 15 https://$H/ | grep -o -e 'RollEase Startup Project' -e 'Investment Screening Dashboard' -e 'href="[^"]*styles.css"' | sort -u
  done
  echo | openssl s_client -connect chelseahuang.me:443 -servername chelseahuang.me 2>/dev/null | openssl x509 -noout -issuer -dates
  ```

  **Check:** the address is no longer the VM's; `http://` answers `301` to `https://`; each page has `RollEase Startup Project` and an `https://` stylesheet link, and not `Investment Screening Dashboard`; the certificate's start date is today. Then look in a browser, and once on phone mobile data.

**Undo Task 5 (Chelsea, Cloudflare):** put back the records written down in step 5.1. The VM still has its site, its SQLite file and a certificate valid until 2027-01-04, so it answers again as soon as DNS points at it.

---

## Undoing everything

Go backwards: Task 5 (restore DNS), Task 4 (redeploy the earlier deployment, revert `main`), Task 3 (drop the two tables), Tasks 2 and 1 (delete the branch, drop `career_platform_test`, remove `TEST_DATABASE_URL` from `.env`). After Task 5's undo, visitors are on the VM again and the rest can wait.

## What this plan leaves for you

- **The VM.** It keeps running, and costing Azure credit, as the way back. After Task 5 its certificate can no longer renew itself, because the renewal check follows the domain to Railway; that only matters if you go back to it after 2027-01-04. Decide later when to stop it.
- **`docs/how-this-site-is-secured.md`** describes the VM, Let's Encrypt, nginx and Azure ports. After Task 5 the certificate and the open ports are Railway's, so that page needs rewriting.
- **The website project's own text** lists `FastAPI, SQLite, … Microsoft Azure`. Update the row in PostgreSQL when you want the page to say PostgreSQL and Railway.
- **Backups.** The SQLite file could be copied; a Railway database needs Railway's backup feature or a `pg_dump`. The four rows also still exist in `data/career_platform.from-vm.db` and on the VM.
- **`sqlite-utils`** is listed in `pyproject.toml` but no code imports it. Left alone here.
- **`TEST_DATABASE_URL` shares a server with the live data.** The name check keeps tests out of `railway`, but both databases use the same password.

## Everyday commands (laptop)

```bash
uv run --env-file .env pytest -q                    # tests, against career_platform_test
set -a; . ./.env; set +a                            # load addresses into this shell
DATABASE_URL="$TEST_DATABASE_URL" uv run uvicorn career_platform.main:app --reload --port 8001   # local site
git push origin main                                # deploys to Railway
```

# Implementation Plan

## Project stack
- FastAPI
- Jinja templates
- Plain CSS
- SQLite
- UV for Python dependency management

## Goal
Build a personal resume and career platform that is:
- recruiter-friendly
- easy to update
- structured in a database
- able to keep the public profile visible even when the database is unavailable
- simple enough to run locally in Codespaces and eventually deploy to an Azure VM

## Recommended project structure

This structure keeps responsibilities separated so the app stays simple, readable, and easy to extend.

```text
career-platform/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App bootstrap, route registration, startup logic
│   ├── config.py                  # Settings, environment variables, app configuration
│   ├── database.py                # SQLite connection setup and migration/init helpers
│   ├── models.py                  # Data access helpers or lightweight model definitions
│   ├── dependencies.py            # Shared dependencies for DB access, auth, and fallback logic
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── public.py              # Public profile page and resume rendering routes
│   │   ├── admin.py               # Admin dashboard and CRUD forms for content editing
│   │   └── api.py                 # Optional JSON endpoints for admin or future client use
│   ├── services/
│   │   ├── __init__.py
│   │   ├── profile_service.py     # Fetch profile/content for the public site
│   │   ├── admin_service.py       # Create/update/delete profile records
│   │   ├── fallback_service.py    # Read/write cached profile snapshot when DB is unavailable
│   │   └── resume_service.py      # Build printable/downloadable resume output
│   ├── templates/
│   │   ├── base.html              # Shared layout, nav, footer, global styles hooks
│   │   ├── profile.html           # Public profile page layout
│   │   ├── resume.html            # Printable or downloadable résumé page
│   │   ├── admin/
│   │   │   ├── dashboard.html     # Admin overview and management landing page
│   │   │   ├── profile_form.html  # Form for editing profile information
│   │   │   ├── experience_form.html
│   │   │   ├── project_form.html
│   │   │   └── ...
│   │   └── components/
│   │       ├── hero.html
│   │       ├── experience_list.html
│   │       ├── project_list.html
│   │       └── contact.html
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css         # Global design system and layout styling
│   │   ├── js/
│   │   │   └── main.js            # Small frontend enhancements if needed
│   │   └── images/
│   │       └── .gitkeep
│   └── utils/
│       ├── fallback.py            # Fallback writing and recovery helpers
│       ├── validation.py          # Input validation helpers for forms
│       └── date_utils.py          # Formatting helper functions
├── data/
│   ├── db.sqlite3                 # SQLite database file for local development
│   ├── profile_fallback.json      # Last known good public profile snapshot
│   └── seed.sql                   # Initial seed data for local testing
├── tests/
│   ├── test_public_profile.py     # Public page renders correctly
│   ├── test_admin.py              # Admin content editing works
│   ├── test_fallback.py           # Fallback behavior works when DB is unavailable
│   └── test_resume.py             # Resume export/download works
├── .env.example                   # Example environment config
├── pyproject.toml                 # UV project metadata and dependencies
├── README.md                      # Local setup and deployment instructions
├── uv.lock                        # UV lock file for reproducible installs
├── run.sh                         # Local app start command
└── .gitignore                     # Ignore local SQLite data and generated artifacts
```

### File responsibility summary
- `app/main.py`: starts the app, registers routes, and wires the app factory
- `app/config.py`: keeps environment variables and configuration values in one place
- `app/database.py`: creates the SQLite connection, schema initialization, and database helpers
- `app/models.py`: defines the data structures and record shapes used by the app
- `app/routes/public.py`: handles the public-facing profile page and resume views
- `app/routes/admin.py`: handles the admin dashboard and editing pages
- `app/services/profile_service.py`: fetches and prepares profile information for display
- `app/services/admin_service.py`: manages insert/update/delete actions for the admin flow
- `app/services/fallback_service.py`: keeps the last known good profile available during outages
- `app/services/resume_service.py`: prepares printable résumé output
- `app/templates/*`: contains all Jinja templates for HTML pages and reusable fragments
- `app/static/css/styles.css`: holds the global professional styling for the site
- `app/static/js/main.js`: optional small interactivity such as menu toggles or lightweight UX behavior
- `data/db.sqlite3`: local SQLite database for development and testing
- `data/profile_fallback.json`: fallback content used when the database is unavailable
- `tests/*`: validates the public site, admin behavior, fallback logic, and resume actions

## Workstreams

This project has 5 main workstreams, each tied to a part of the spec:

1. Foundation and environment
2. Data model and SQLite schema
3. Public profile frontend
4. Admin/content management
5. Resilience and deployment

Each workstream contains smaller tasks so the work is easier to estimate, track, and validate.

## Phase 1: Project setup with UV

### Task 1: Initialize the Python project with UV
Done looks like:
- A clean project structure exists
- UV manages dependencies
- The app can be installed and run consistently in the Codespace environment

How to check:
- Run `uv sync` successfully
- Confirm dependencies install without errors
- Confirm the app starts with the expected Python environment

### Task 2: Add app dependencies
Done looks like:
- FastAPI, Jinja2, and any necessary supporting packages are pinned in the project
- SQLite access is working
- No ad hoc package installs are needed

How to check:
- Run `uv run python -c "import fastapi, jinja2"` and confirm success
- Confirm the project is reproducible on another machine using UV

## Phase 2: App foundation

### Task 3: Create the FastAPI application skeleton
Done looks like:
- The app starts successfully
- Routes exist for:
  - homepage / public profile
  - admin dashboard
  - form-based editing pages
- Templates and static CSS folders are organized

How to check:
- Run the app with UV
- Open the page in the browser
- Confirm the startup logs are clean and the page loads

### Task 4: Set up SQLite database schema
Done looks like:
- The database file exists
- Tables are created for:
  - profile
  - experience
  - education
  - skills
  - projects
  - links
  - custom content blocks
- CRUD operations work

How to check:
- Insert sample records
- Query the database manually or via a route
- Verify the information renders correctly in the profile page

### Task 5: Seed starter content for local development
Done looks like:
- A sample profile, sample experiences, sample education, and sample project records are present
- The site loads with useful content immediately without manual setup

How to check:
- Start the app with the seed data loaded
- Open the homepage
- Confirm the profile renders with visible content immediately

## Phase 3: Public profile experience

### Task 6: Build the public profile page in Jinja templates
Done looks like:
- The site includes:
  - hero section
  - summary/about
  - experience
  - education
  - skills
  - projects
  - contact CTA
- The page is polished, scannable, and recruiter-friendly

How to check:
- Open the page at different browser widths
- Confirm sections look clean and readable
- Verify everything is structured and styled consistently

### Task 7: Render database data into templates
Done looks like:
- Jinja templates pull from SQLite records
- Each section displays the correct information
- Reusable loops render multiple items cleanly

How to check:
- Add one experience record and one project record
- Refresh the page
- Confirm both are displayed correctly

### Task 8: Create the resume download flow
Done looks like:
- There is a working way to download the résumé or public profile as a PDF or printable document
- The document is consistent with the online profile

How to check:
- Click the download button
- Confirm the file downloads and opens correctly

## Phase 4: Admin content editing

### Task 9: Build the admin dashboard
Done looks like:
- You can create, edit, and remove profile content
- All common updates are possible without editing raw code

How to check:
- Add a new education item or skill
- Save it
- Ensure the public page reflects the update

### Task 10: Add custom content block editor
Done looks like:
- Optional sections such as the headline, summary, or callout can be edited in a structured form
- These blocks appear in the correct public layout positions

How to check:
- Change a heading or summary in admin
- Refresh the public page
- Confirm the new text appears

### Task 11: Add admin validation and save flow
Done looks like:
- User input is checked before saving
- Invalid values do not break the profile page
- Save operations complete cleanly

How to check:
- Submit empty or malformed values
- Confirm form feedback explains the issue
- Confirm valid entries persist correctly

## Phase 5: Availability and resilience

### Task 12: Add fallback profile behavior
Done looks like:
- If the SQLite database is unavailable, the site still shows the public profile
- It uses the last successfully stored profile snapshot from a file or cache
- The profile remains readable and professional

How to check:
- Simulate a DB failure
- Load the page
- Confirm the profile still renders instead of a broken blank page

### Task 13: Add recovery behavior
Done looks like:
- Once the database is restored, the app resumes normal live data fetching
- The fallback content refreshes to the latest version

How to check:
- Restore the database connection
- Refresh the page
- Confirm it returns to live data without manual intervention

### Task 14: Add fallback refresh and logging
Done looks like:
- The system records fallback usage or failure events
- Admin users can easily see when the app is serving cached content

How to check:
- Trigger a failure
- Confirm the system logs or clearly reports that fallback mode is active

## Phase 6: Quality assurance and deployment

### Task 15: UX and recruiter review
Done looks like:
- The site clearly communicates the profile and target roles
- It is polished enough for a recruiter to review quickly

How to check:
- Read the page as a recruiter would
- Confirm it is understandable within 10–20 seconds

### Task 16: Local Codespace deployment
Done looks like:
- The app runs in the Codespace environment
- It is viewable and testable locally
- UV handles dependency and runtime setup

How to check:
- Run the app with UV
- Open the preview port
- Confirm the site and admin pages work

### Task 17: Azure VM deployment path
Done looks like:
- There is a clear path for running the same app on an Azure VM
- The VM setup includes environment configuration and app startup

How to check:
- SSH into the VM
- Start the app with UV
- Confirm the public URL loads successfully

### Task 18: Final smoke test and launch checklist
Done looks like:
- All critical routes work
- Database reads/writes work
- Fallback profile works
- Admin edits publish correctly
- The public site is stable and visually consistent

How to check:
- Run through a final checklist covering:
  - homepage loads
  - project renders
  - edit form saves
  - fallback mode works
  - recovery works
  - site remains readable

## Recommended milestone order
1. Project setup with UV
2. FastAPI app skeleton
3. SQLite schema
4. Public profile page
5. Admin content editing
6. Fallback profile behavior
7. UX polish
8. Codespace deployment
9. Azure VM deployment

## Final recommendation
This is the recommended architecture for the first version because it is:
- simple to understand
- easy to run locally in Codespaces
- easy to deploy later to an Azure VM
- structured enough to grow

This plan is ready for approval and does not include implementation yet.

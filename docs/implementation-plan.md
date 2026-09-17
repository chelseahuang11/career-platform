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

## Superpowers planning rules
This project should follow a structured, bounded workflow so each phase stays focused and does not expand beyond the original spec.

For every phase and task, apply these rules:
- Define the exact scope before starting work
- State the expected output in plain language
- State what success looks like before implementation begins
- Stop at the end of the task; do not continue into the next task unless the outputs are validated
- Do not add unrequested features or platform complexity during a task
- If a requirement is unclear, pause and resolve it before changing code
- Keep the public profile functional even when the database is unavailable
- Treat the public site and admin site as separate concerns

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

Every task must include all four of the following:
- Objective: what this task is meant to achieve
- Boundaries: what this task does not include
- Done criteria: the exact conditions that prove it is finished
- Validation: how to test it before moving on

## Phase 1: Project setup with UV

### Task 1: Initialize the Python project with UV
Objective:
- Create the base project structure and set up a clean dependency workflow using UV.

Files involved:
- `pyproject.toml`
- `uv.lock`
- `.gitignore`
- `README.md`
- project root directory structure

Boundaries:
- This task does not include app logic, templates, or database schema design.
- Do not add extra packages beyond the required runtime dependencies.
- Do not build a UI or admin screen yet.

Done looks like:
- A clean project structure exists
- UV manages dependencies
- The app can be installed and run consistently in the Codespace environment

Validation:
- Run `uv sync` successfully
- Confirm dependencies install without errors
- Confirm the app starts with the expected Python environment
- Confirm the project can be re-created using a fresh `uv sync`

Stop condition:
- Stop after the project is initialized and the environment is confirmed working. Do not proceed to app features until this is true.

### Task 2: Add app dependencies
Objective:
- Define the required runtime package set for the FastAPI app and confirm the environment works.

Files involved:
- `pyproject.toml`
- `uv.lock`
- `.venv` (local environment)

Boundaries:
- This task is limited to dependency selection and validation.
- Do not create routes, database tables, or UI code within this task.
- Do not install unrelated packages for future features.

Done looks like:
- FastAPI, Jinja2, and any necessary supporting packages are pinned in the project
- SQLite access is working
- No ad hoc package installs are needed

Validation:
- Run `uv run python -c "import fastapi, jinja2"` and confirm success
- Confirm the project is reproducible on another machine using UV

Stop condition:
- Stop once the runtime dependencies are installed and verified. Do not begin route or page work until this is complete.

## Phase 2: App foundation

### Task 3: Create the FastAPI application skeleton
Objective:
- Build the app entry point and establish the base route structure without adding feature logic yet.

Files involved:
- `app/main.py`
- `app/__init__.py`
- `app/config.py`
- `app/routes/__init__.py`
- `app/routes/public.py`
- `app/routes/admin.py`
- `app/templates/base.html`
- `app/static/css/styles.css`

Boundaries:
- This task is limited to bootstrapping the app, route registration, and shared file structure.
- Do not implement admin CRUD logic yet.
- Do not add advanced security, auth, or deployment layers in this step.

Done looks like:
- The app starts successfully
- Routes exist for:
  - homepage / public profile
  - admin dashboard
  - form-based editing pages
- Templates and static CSS folders are organized

Validation:
- Run the app with UV
- Open the page in the browser
- Confirm the startup logs are clean and the page loads

Stop condition:
- Stop after the app boots and the routes are live. Do not begin feature-specific logic until the base app is confirmed stable.

### Task 4: Set up SQLite database schema
Objective:
- Define the persistent data model for the profile, experience, education, skills, projects, and related content.

Files involved:
- `app/database.py`
- `app/models.py`
- `data/db.sqlite3`
- `data/seed.sql`

Boundaries:
- Only the core resume/profile data needs to exist initially.
- Do not add extra tables for broader platform features yet.
- Do not create unrelated user, job, or analytics tables in v1.

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

Validation:
- Insert sample records
- Query the database manually or via a route
- Verify the information renders correctly in the profile page

Stop condition:
- Stop once the database schema is created and basic create/read operations work. Do not expand the schema into future platform functionality.

### Task 5: Seed starter content for local development
Objective:
- Populate the database with sample content so the site is usable immediately during local testing.

Files involved:
- `data/seed.sql`
- `data/db.sqlite3`
- `app/database.py`

Boundaries:
- This is only sample local content, not production data.
- Do not add placeholder content that conflicts with the actual user profile information.
- Keep it small and realistic.

Done looks like:
- A sample profile, sample experiences, sample education, and sample project records are present
- The site loads with useful content immediately without manual setup

Validation:
- Start the app with the seed data loaded
- Open the homepage
- Confirm the profile renders with visible content immediately

Stop condition:
- Stop after the seed content loads reliably and the homepage is useful for development review.

## Phase 3: Public profile experience

### Task 6: Build the public profile page in Jinja templates
Objective:
- Create the recruiter-facing public profile and ensure it presents the personal brand clearly.

Files involved:
- `app/routes/public.py`
- `app/templates/profile.html`
- `app/templates/base.html`
- `app/templates/components/hero.html`
- `app/templates/components/experience_list.html`
- `app/templates/components/project_list.html`
- `app/templates/components/contact.html`
- `app/static/css/styles.css`

Boundaries:
- Focus only on the public-facing profile experience.
- Do not build job-search, networking, or social feed features yet.
- Keep the layout simple and resume-like rather than blog-like.

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

Validation:
- Open the page at different browser widths
- Confirm sections look clean and readable
- Verify everything is structured and styled consistently

Stop condition:
- Stop once the public page reads clearly and reflects the spec. Do not add nonessential portfolio or social features during this phase.

### Task 7: Render database data into templates
Objective:
- Connect the public page to the database so content is driven by structured records rather than hardcoded text.

Files involved:
- `app/services/profile_service.py`
- `app/routes/public.py`
- `app/templates/profile.html`
- `data/db.sqlite3`

Boundaries:
- This task covers read-only rendering of the public profile only.
- Do not build admin editing in the same task.
- Keep all content tied to the structured data model without adding extra content types.

Done looks like:
- Jinja templates pull from SQLite records
- Each section displays the correct information
- Reusable loops render multiple items cleanly

Validation:
- Add one experience record and one project record
- Refresh the page
- Confirm both are displayed correctly

Stop condition:
- Stop after the public page renders correctly from data. Do not expand into dynamic filters or search functionality yet.

### Task 8: Create the resume download flow
Objective:
- Provide a clean downloadable resume or printable profile version.

Files involved:
- `app/services/resume_service.py`
- `app/routes/public.py`
- `app/templates/resume.html`
- `app/static/css/styles.css`

Boundaries:
- Keep this to a simple export flow only.
- Do not implement heavy PDF generation tooling or a large document system yet.
- Do not expand the export into a separate portfolio platform.

Done looks like:
- There is a working way to download the résumé or public profile as a PDF or printable document
- The document is consistent with the online profile

Validation:
- Click the download button
- Confirm the file downloads and opens correctly

Stop condition:
- Stop once the PDF/download path works and is consistent with the public content. Do not add multiple export versions unless explicitly required.

## Phase 4: Admin content editing

### Task 9: Build the admin dashboard
Objective:
- Create the content management area that lets a user edit the public profile without writing code.

Files involved:
- `app/routes/admin.py`
- `app/services/admin_service.py`
- `app/templates/admin/dashboard.html`
- `app/templates/admin/profile_form.html`

Boundaries:
- This task is about structured editing for the core resume profile only.
- Do not add multiple user roles, authentication, or team-level permissions yet.
- Keep the admin flow focused on the profile data model.

Done looks like:
- You can create, edit, and remove profile content
- All common updates are possible without editing raw code

Validation:
- Add a new education item or skill
- Save it
- Ensure the public page reflects the update

Stop condition:
- Stop after the admin dashboard can manage each core content type. Do not widen into broader CMS features yet.

### Task 10: Add custom content block editor
Objective:
- Allow optional custom text blocks without creating a full CMS.

Files involved:
- `app/services/admin_service.py`
- `app/templates/admin/profile_form.html`
- `app/templates/components/hero.html`
- `app/templates/base.html`

Boundaries:
- Keep custom content blocks limited to small, controlled sections.
- Do not allow arbitrary HTML or freeform page layout editing in v1.
- Do not create a general visual builder.

Done looks like:
- Optional sections such as the headline, summary, or callout can be edited in a structured form
- These blocks appear in the correct public layout positions

Validation:
- Change a heading or summary in admin
- Refresh the public page
- Confirm the new text appears

Stop condition:
- Stop once the custom blocks are editable and safely scoped. Do not add arbitrary layout editing.

### Task 11: Add admin validation and save flow
Objective:
- Protect the profile content and admin forms from invalid or harmful input.

Files involved:
- `app/utils/validation.py`
- `app/routes/admin.py`
- `app/services/admin_service.py`

Boundaries:
- Validate only the fields necessary for the resume profile.
- Keep validation simple and explicit; no broad security framework yet.
- Do not add user auth in this task.

Done looks like:
- User input is checked before saving
- Invalid values do not break the profile page
- Save operations complete cleanly

Validation:
- Submit empty or malformed values
- Confirm form feedback explains the issue
- Confirm valid entries persist correctly

Stop condition:
- Stop after validation is in place for the common admin operations and does not compromise the page flow.

## Phase 5: Availability and resilience

### Task 12: Add fallback profile behavior
Objective:
- Preserve the public profile during database outages so the site remains readable and professional.

Files involved:
- `app/services/fallback_service.py`
- `app/utils/fallback.py`
- `data/profile_fallback.json`
- `app/routes/public.py`

Boundaries:
- This applies only to the public profile experience.
- Do not build a general disaster recovery system for every app feature.
- Keep the fallback simple and explicit: last known good profile snapshot.

Done looks like:
- If the SQLite database is unavailable, the site still shows the public profile
- It uses the last successfully stored profile snapshot from a file or cache
- The profile remains readable and professional

Validation:
- Simulate a DB failure
- Load the page
- Confirm the profile still renders instead of a broken blank page

Stop condition:
- Stop once the public profile is stable during outage conditions and remains professional in fallback mode.

### Task 13: Add recovery behavior
Objective:
- Restore normal live profile rendering when the database becomes available again.

Files involved:
- `app/services/fallback_service.py`
- `app/routes/public.py`
- `app/utils/fallback.py`

Boundaries:
- Recovery should be limited to normal data source restoration.
- Do not add a long background sync system in v1.
- Keep recovery automatic and simple.

Done looks like:
- Once the database is restored, the app resumes normal live data fetching
- The fallback content refreshes to the latest version

Validation:
- Restore the database connection
- Refresh the page
- Confirm it returns to live data without manual intervention

Stop condition:
- Stop once recovery is automatic and does not produce a broken or stale page.

### Task 14: Add fallback refresh and logging
Objective:
- Make fallback mode observable and easier to track during troubleshooting.

Files involved:
- `app/utils/fallback.py`
- `app/services/fallback_service.py`
- `app/config.py`

Boundaries:
- Logging here should be minimal and practical.
- Do not build a broad observability stack or analytics dashboard in this step.

Done looks like:
- The system records fallback usage or failure events
- Admin users can easily see when the app is serving cached content

Validation:
- Trigger a failure
- Confirm the system logs or clearly reports that fallback mode is active

Stop condition:
- Stop after fallback status is observable enough to support troubleshooting without creating a larger monitoring system.

## Phase 6: Quality assurance and deployment

### Task 15: UX and recruiter review
Objective:
- Verify that the public profile is clear, credible, and easy for a recruiter to understand.

Files involved:
- `app/templates/profile.html`
- `app/static/css/styles.css`
- `README.md`

Boundaries:
- This is a review task, not a redesign task.
- Only fix clarity issues that directly affect recruiter readability.
- Do not add more sections unless the spec requires them.

Done looks like:
- The site clearly communicates the profile and target roles
- It is polished enough for a recruiter to review quickly

Validation:
- Read the page as a recruiter would
- Confirm it is understandable within 10–20 seconds

Stop condition:
- Stop once the content reads clearly and professionally. Do not continue into extra polish beyond the spec.

### Task 16: Local Codespace deployment
Objective:
- Confirm the application works reliably in a local remote environment before a VM deploy.

Files involved:
- `README.md`
- `run.sh`
- `pyproject.toml`
- `app/main.py`

Boundaries:
- This is a deployment readiness test only.
- Do not add production-level infrastructure in this step.
- Keep the environment simple and appropriate for local preview.

Done looks like:
- The app runs in the Codespace environment
- It is viewable and testable locally
- UV handles dependency and runtime setup

Validation:
- Run the app with UV
- Open the preview port
- Confirm the site and admin pages work

Stop condition:
- Stop after the app is successfully previewable in Codespaces and stable enough for QA.

### Task 17: Azure VM deployment path
Objective:
- Prepare the app for deployment to a remote VM without changing the app architecture.

Files involved:
- `README.md`
- `run.sh`
- `pyproject.toml`
- deployment notes or setup scripts

Boundaries:
- This task is about environment preparation, not a redesign of the app.
- Do not add a container platform or extra infrastructure unless required later.
- Keep the deployment straightforward: app + environment + service start.

Done looks like:
- There is a clear path for running the same app on an Azure VM
- The VM setup includes environment configuration and app startup

Validation:
- SSH into the VM
- Start the app with UV
- Confirm the public URL loads successfully

Stop condition:
- Stop after the app can be started on a VM and remains accessible. Do not add additional deployment complexity unless it is required for the v1 release.

### Task 18: Final smoke test and launch checklist
Objective:
- Verify that all core flows work before launch and ensure the app is ready for the first release.

Files involved:
- all app files
- all tests
- project config files
- `README.md`

Boundaries:
- This is a release gate, not a major new feature phase.
- Focus only on critical flows for the first version.
- Do not add future platform features or broader roadmap work at this stage.

Done looks like:
- All critical routes work
- Database reads/writes work
- Fallback profile works
- Admin edits publish correctly
- The public site is stable and visually consistent

Validation:
- Run through a final checklist covering:
  - homepage loads
  - project renders
  - edit form saves
  - fallback mode works
  - recovery works
  - site remains readable

Stop condition:
- Stop after the app passes the final release checklist. Do not introduce unrelated improvements or expansions before launch.

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

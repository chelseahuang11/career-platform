# career-platform

My personal career site: profile, education, experience and projects, with the projects read from a database on every request. It started in GitHub Codespaces, ran on an Azure Ubuntu VM with SQLite, and now runs on Railway with PostgreSQL.

- **Live:** https://chelseahuang.me/ (`www` redirects there)
- **Repository:** https://github.com/chelseahuang11/career-platform
- **Project 1 submission index:** [docs/project-1-submission.md](docs/project-1-submission.md)

This README was assembled on 2026-10-25 with my coding agent from the repository, its Git history, the plans and the saved evidence. Anything written afterward is labeled as such; anything not checked is marked **unverified**.

## Contents

1. [What the site does](#what-the-site-does)
2. [Run it on my laptop](#run-it-on-my-laptop)
3. [Update the live site](#update-the-live-site)
4. [Roll back a bad change](#roll-back-a-bad-change)
5. [Architecture](#architecture)
6. [Azure deployment (earlier)](#azure-deployment-earlier)
7. [Domain and HTTPS](#domain-and-https)
8. [Migration to Railway and PostgreSQL](#migration-to-railway-and-postgresql)
9. [Email and analytics](#email-and-analytics)
10. [Decisions](#decisions)
11. [Investigated failures](#investigated-failures)
12. [Remaining limitations](#remaining-limitations)
13. [Reflection](#reflection)
14. [Services, costs and cleanup](#services-costs-and-cleanup)

## What the site does

A FastAPI app renders one page with Jinja templates:

- **Profile** (name, headline, location, email, LinkedIn, GitHub) and **projects** come from PostgreSQL, read on every request (`src/career_platform/database.py`).
- **Education** and **Experience** come from my resume and are written in the template (`src/career_platform/templates/index.html`).
- `/resume` serves my resume PDF, `/privacy` explains the analytics, `/health` returns `{"status":"ok"}` for Railway's health check.

**When the database fails** (`src/career_platform/main.py`): the page still shows the profile, from `data/profile_fallback.json`, says **"Projects temporarily unavailable"**, and returns **HTTP 503**. No sample projects are shown. Each request opens a new connection (5-second timeout), so once the database is back the next refresh shows the projects again, with no restart. **When the projects table is empty**, the page says "No projects are listed yet" and returns 200. The app no longer seeds demo projects.

Checked on 2026-10-25 against a local PostgreSQL with my real data, app running with 2 workers, never restarted:

```
18:59:01 GET / -> 200 | RollEase:1 | unavailable:0
$ docker stop career_platform_db
18:59:08 GET / -> 503 | Chelsea Huang:3 | RollEase:0 | unavailable:1
18:59:14 GET / -> 503 | Chelsea Huang:3 | RollEase:0 | unavailable:1
$ docker start career_platform_db
18:59:16 GET / -> 200 | RollEase:1 | unavailable:0
```

The same cases are automated tests in `tests/test_app.py` (503 when unreachable, 503 when `DATABASE_URL` is missing, recovery without restart, empty table, no demo titles). `uv run --env-file .env pytest -q` → `22 passed` (2026-10-25).

## Run it on my laptop

Needs [uv](https://docs.astral.sh/uv/), Python 3.12 and Docker Desktop.

```bash
git clone https://github.com/chelseahuang11/career-platform.git && cd career-platform
uv sync
# Local PostgreSQL 18 on port 5434 (data kept in a Docker volume)
docker run -d --name career_platform_db -p 127.0.0.1:5434:5432 \
  -e POSTGRES_PASSWORD=<choose one> -e POSTGRES_DB=career_platform_test \
  -v career_platform_pgdata:/var/lib/postgresql postgres:18
docker exec career_platform_db psql -U postgres -c "CREATE DATABASE career_platform_dev"
cp .env.example .env            # then put the password into the URLs
uv run --env-file .env pytest -q                       # tests use the _test database
uv run --env-file .env python -m career_platform.copy_sqlite data/career_platform.db  # optional: load my data
uv run --env-file .env uvicorn career_platform.main:app --app-dir src --reload
```

`init_db()` creates the tables and the profile row on start-up; it never adds projects. `.env` is ignored by Git, and passwords stay there or in Railway's Variables.

## Update the live site

Railway deploys the `main` branch of this repository automatically: every deployment in `railway deployment list --json` shows repo `chelseahuang11/career-platform`, branch `main`, and the pushed commit (checked 2026-10-25). The service is `career-platform` in project `imaginative-recreation`, environment `production`, region `iad`; its only custom variable is `DATABASE_URL` (value not displayed here). The start command is in [`Procfile`](Procfile).

1. Make the change on a branch or locally, and review `git diff`.
2. Run `uv run --env-file .env pytest -q` and look at the page locally.
3. Commit and `git push origin main`.
4. Wait for Railway's deployment to succeed, then check the domain.

**The reviewed change for Project 1** (2026-10-25): commit [`d67a3db`](https://github.com/chelseahuang11/career-platform/commit/d67a3db) "Return 503 without sample projects when the database fails" (also adds Education and Experience). Reviewed with `git diff`, 22 tests passed, and the stop/start check above passed locally before the commit. Pushed 19:00 PDT → Railway deployment **`8d01a5c2-57c1-4383-a9d7-e3b3527f8547`** (`railway deployment list --json`: commit `d67a3db`, repo `chelseahuang11/career-platform`, branch `main`, created 02:00:02 UTC; GitHub's record of it is deployment `7322403277`, `success` at 02:01:15 UTC) → at 19:01:21 PDT `https://chelseahuang.me/` returned 200 with the new `Education` and `Experience` sections, all 4 projects, and no demo titles. That deployment now shows `REMOVED` because the next push (`33a7a1b`, deployment `527116a7…`, `SUCCESS`) replaced it, which is how Railway marks superseded deployments.

## Roll back a bad change

**Application code.**

- Fastest: Railway dashboard → web service → **Deployments** → the last good deployment → **Redeploy**. Traffic switches once `/health` answers.
- Then make Git match, so the next push doesn't bring the bad code back: `git revert <bad sha>` and `git push origin main` (Railway deploys the revert). Don't force-push `main`.
- Check: `curl -s https://chelseahuang.me/health` and look for the expected content on `/`.

**Data.** Visitors can't write anything; the data changes only when I change it (SQL or the copy tool). So:

- Before any data change, take a backup. The Railway database has no public address now, so either turn on its TCP proxy for the backup (Postgres service → Settings → Networking) and use that address as `$RAILWAY_DATABASE_URL`, or run `pg_dump` inside Railway with `railway ssh -s Postgres`. From the laptop, `pg_dump` isn't installed, so it runs inside the local Postgres container: `docker exec career_platform_db pg_dump "$RAILWAY_DATABASE_URL" -Fc > data/railway-YYYYMMDD.dump` (`data/` dumps stay out of Git; they hold my data).
- To undo: `docker exec -i career_platform_db pg_restore --clean --if-exists -d "$RAILWAY_DATABASE_URL" < data/railway-YYYYMMDD.dump`, then refresh the page. No app restart is needed, because every request reads the database. Railway's own database backups, if enabled on the plan, are a second option.
- If only the schema change was bad, revert the code first, then restore the dump, so the code and tables match.

**The migration itself (Railway → Azure).** Until 2026-10-13 the way back was to point the root DNS record back at the VM, which still had the site, its SQLite file and its certificate. Because nothing was written to PostgreSQL after cutover, the SQLite file would have been current. The VM was deleted on 2026-10-13 during class, so today a move back means rebuilding a server from the [Azure plans](#azure-deployment-earlier) and exporting PostgreSQL first. If writes after cutover were ever allowed, they would have to be copied back too: the copy tool only goes SQLite → PostgreSQL.

## Architecture

All diagrams: [docs/diagrams/request-path.md](docs/diagrams/request-path.md).

| Path | Diagram section |
|---|---|
| Web request on Railway (DNS UDP 53 → Railway edge HTTPS 443 → app, plain HTTP inside Railway → PostgreSQL) | §1–2 |
| Web request on Azure (DNS → NSG → nginx 443/80 → uvicorn `127.0.0.1:8000`, 2 workers → SQLite file) | §3 |
| Email (MX lookup → Zoho over SMTP 25; Zoho signs DKIM; receivers check SPF/DKIM/DMARC in Cloudflare DNS) | §4 |
| Analytics (browser → `gtag.js` from Google → GA4 `/g/collect` over HTTPS, never through my server) | §5 |
| `www` (proxied to Cloudflare, redirect rule → 301 to the bare domain) | §6 |

PNG exports: `docs/diagrams/request-path-*.png`, `docs/diagrams/azure-request-path-*.png`.

## Azure deployment (earlier)

Plans with recorded results: [Azure VM migration](docs/superpowers/plans/2026-09-24-azure-vm-migration.md) (2026-09-24 to 10-01) and [Operate the VM](docs/superpowers/plans/2026-10-01-operate-the-vm.md) (2026-10-01). Exercise record: [ex03.md](docs/evidence/ex03.md).

| | |
|---|---|
| VM | `vm-career-platform`, Ubuntu 24.04, `Standard_B2ats_v2`, North Central US, resource group `rg-career-platform`, subscription "Azure for Students" |
| Public IP | `135.232.225.216` (static) |
| Private IP | `172.16.0.4` in VNet `vnet-northcentralus-1` (`172.16.0.0/16`), from `az vm list-ip-addresses` on 2026-10-06 |
| SSH | user `azureuser`, key-only (password login disabled), NSG rule `Allow-SSH-Laptop` (priority 300): TCP 22 from my laptop's address only (`/32`) |
| Web entry | NSG `Allow-HTTP-80` (310) and `Allow-HTTPS-443` (320) from anywhere → **nginx**. nginx on 80 redirects to 443; on 443 it holds the Let's Encrypt certificate (certbot, renewal timer) and proxies to the app |
| App | `career-platform.service` (systemd, `enabled`, `Restart=always`), uvicorn **2 workers** as `azureuser` on **`127.0.0.1:8000`** only; no NSG rule for 8000 |
| Database | SQLite file `data/career_platform.db` on the VM's disk, read by the app locally |

What needed configuration to survive a restart: the systemd unit (`enabled` so it starts at boot, `Restart=always` after a crash), nginx (installed from apt, enabled by default), certbot's timer, and the `EnvironmentFile` that gives the workers their settings. Evidence that the site responded and read the database: `curl http://<IP>/` → 200 with my project titles and `Server: nginx/1.24.0`, port 8000 timing out from outside (operate-the-VM plan, Task 3), and HTTPS checks in [how-this-site-is-secured.md](docs/how-this-site-is-secured.md) (my Exercise 04 write-up, 2026-10-08).

**Unverified: the controlled VM restart.** The operate-the-VM plan left the reboot test to me, and no result was recorded (searched the repo, Git history, session logs and screenshots on 2026-10-25). **The VM was deleted on 2026-10-13** during class, so the test can't be run now. The NSG, VNet and static public IP still exist in `rg-career-platform`.

## Domain and HTTPS

[docs/evidence/dns-https-final.md](docs/evidence/dns-https-final.md) has the full DNS records table with each record's purpose, the final checks, and the certificate explanation. In short:

- `chelseahuang.me` is registered at Namecheap (2026-10-01 to 2027-10-01) and uses Cloudflare as authoritative DNS.
- The bare domain is a DNS-only CNAME to Railway, so TLS goes straight to Railway: Let's Encrypt certificate for `chelseahuang.me`, valid 2026-10-08 to 2027-01-06, renewed automatically by Railway.
- `www` is a proxied record. A Cloudflare redirect rule answers `301` to the bare domain, keeping the path, with Cloudflare's certificate (`*.chelseahuang.me`). Fixed and checked on 2026-10-25: `http://www` and `https://www` both land on `https://chelseahuang.me/`.
- Earlier, on Azure, nginx held a certbot certificate for both names: [how-this-site-is-secured.md](docs/how-this-site-is-secured.md) (Exercise 04).

## Migration to Railway and PostgreSQL

- **Plan, written before the change:** [docs/superpowers/plans/2026-10-08-railway-postgres-migration.md](docs/superpowers/plans/2026-10-08-railway-postgres-migration.md), committed in `3e87766` at 15:17 PDT on 2026-10-08. The root CNAME was created at 15:21. The plan's **Goal** and **Decisions** sections are its spec; there is no separate spec file. Its inventory lists what Git moves (code, `pyproject.toml`/`uv.lock`, templates, `Procfile`) and what needs another method (the SQLite data, copied with `copy_sqlite.py`; secrets, set as Railway Variables; the database server, provisioned by Railway).
- **Compatibility:** SQL rewritten for PostgreSQL (`d27e381`): `GENERATED BY DEFAULT AS IDENTITY`, `%s` placeholders, `ON CONFLICT`, an advisory lock so two app processes don't both create tables. The copy tool (`9300e5f`) keeps ids, moves the id sequence past the highest id, keeps UTF-8 (the en dash in "Allegiant–Sun Country"), and compares every row before it commits.
- **Current data, not seed data:** the real profile and projects (ids 4–7) replaced the demo data on 2026-10-01, so restoring the seed could not pass as a transfer.
- **Comparison and cutover:** the plan's "Results recorded afterward" section (written 2026-10-25) has the timeline, the row comparison from the copy, and a rendered-page comparison: every source field found on the live Railway page, 4 of 4 projects. It also records that the domain was moved about 7 minutes **before** Railway's first successful deployment, against the plan's order.
- **Rollback:** see [Roll back a bad change](#roll-back-a-bad-change).

**Who manages what.**

| Layer | Azure VM (IaaS) | Railway (PaaS) | Still mine on Railway |
|---|---|---|---|
| Operating system, patches | Me (Ubuntu updates) | Railway | — |
| Runtime (Python, packages) | Me (`uv sync` on the VM) | Railway builds it (Railpack) from my repo | Pinning versions in `uv.lock`; fixing build failures |
| Web entry point | Me (nginx, NSG rules) | Railway's edge | — |
| TLS certificate | Me (certbot and its timer) | Railway | Keeping DNS pointed at Railway so renewal works |
| Application code | Me | Me | All of it, and the start command in `Procfile` |
| Configuration and secrets | Me (`.env` on the VM, `EnvironmentFile`) | Railway Variables | Choosing and setting them; keeping them out of Git |
| Database software | Me (SQLite library) | Railway (PostgreSQL service) | Schema and its changes |
| Data and backups | Me (file copies) | Railway stores it | Backups before changes, and restores |
| DNS | Me (Cloudflare) | Me (Cloudflare) | All of it |
| Cost and limits | Azure credit | Trial: 30 days or $5 | Watching the trial and moving before it ends |

PaaS took away the server work, not the responsibility: a bad deploy, a bad schema change, a DNS mistake or a lost secret are still mine to prevent and fix.

## Email and analytics

- **Zoho Mail** at `chelsea@chelseahuang.me`: results sheet [ex06.md](docs/evidence/ex06.md) (before-MX message, received, replied, new message, MX/SPF/DKIM/DMARC values and what each does, authentication results) and header analysis [zoho-header-check.md](docs/evidence/zoho-header-check.md). Records: [dns-https-final.md](docs/evidence/dns-https-final.md), and the zone before Zoho: [dns-before-zoho.md](docs/evidence/dns-before-zoho.md).
- **GA4** (`G-R24K9LD7H4`) with Consent Mode: [ex06.md](docs/evidence/ex06.md) §3: a `page_view` and outbound `click` events in Realtime, why the click event matters, and how the data travels.

## Decisions

*Written afterward, on 2026-10-25, with my agent's help from the plans and session records, then reviewed and reworded by me. My in-class write-ups are not in this repository.*

**1. Starting with SQLite.** *Alternatives:* PostgreSQL or MySQL from the start. A database is where the site stores its data. SQLite is the simplest kind: the whole database is one file sitting next to the app, with no separate database program to install or manage. That suited my site because it's small, people mostly read it, and only I write to it. Backing it up or moving it is just copying a file, which is how it moved to the VM. The catch is that SQLite needs a disk that stays put, and that's what caused trouble later.

**2. Moving to Railway with PostgreSQL.** *Alternatives:* keep running the Azure VM; move to Railway but keep SQLite. On the Azure VM I was running the whole computer myself: updating the operating system, configuring nginx (the program that hands web requests to my app), setting up HTTPS certificates, and restarting things when they crashed. Railway is a platform that does all of that for me: I push code to GitHub and Railway deploys it. But Railway's disk can be wiped when the app restarts, so a SQLite file there could disappear. So I switched to PostgreSQL, a database that runs as its own service, which Railway manages. The costs: I had to rewrite some database code and move my data over, the free trial is short (30 days or $5 of usage) and allows only one custom domain, and when something breaks I can only see what Railway's dashboard and logs show me.

**3. Using Zoho for email instead of running my own.** *Alternatives:* run my own mail server (Postfix/Dovecot) on the VM; a paid host such as Google Workspace. Email is hard to get right. Cloud providers often block port 25, the port mail servers use. I'd have to filter spam myself. Providers like Gmail and Microsoft judge whether a sending server looks trustworthy, and a new server usually doesn't. One mistake and mail bounces or vanishes. Zoho handles all of that for free. My only job was adding a few DNS records in Cloudflare: MX (so mail for my domain goes to Zoho), SPF (which servers may send as my domain), DKIM (the key that proves Zoho's signature on my mail), and DMARC (what receivers should do when those checks fail). The cost is depending on Zoho's free-plan limits, and my test messages still landed in Junk.

## Investigated failures

Each has the symptom, checks, diagnosis, repair and the repeated check.

| Failure | Kind | Record |
|---|---|---|
| Demo data would have come back after copying my real data (seed re-inserted missing demo titles) | Application / database dependency, real | [ex03.md](docs/evidence/ex03.md) §3, item 2; fix `71cd1ec` |
| Agent reported the app running when it wasn't; SSH froze from home; resource group "didn't exist" (wrong subscription) | Build and Azure migration, real | [ex03.md](docs/evidence/ex03.md) §3 |
| Railway build failed: "Railpack failed to prepare the build" (no start command; app lives under `src/`) → added `Procfile` (`3e87766`) → deployment `2c13fcf` succeeded 15:28:40 | Migration, real | Railway plan, Task 4 note and "Results recorded afterward" |
| `www.chelseahuang.me` timed out: DNS-only record still pointed at the deleted VM's IP → made it proxied so the redirect rule runs → both `http://www` and `https://www` return 301 to the root | DNS, real (2026-10-25) | [dns-https-final.md](docs/evidence/dns-https-final.md), "The www fix" |
| Certificate name mismatch caused by a stale A record | DNS / TLS, **deliberate lab simulation** (Exercise 05; outputs supplied by the assignment, not from my system) | [ex05.md](docs/evidence/ex05.md) |

## Remaining limitations

- **Controlled VM restart unverified**, and the VM is deleted (2026-10-13), although Project 1 asked to keep it until the instructor's cleanup directions.
- **Direct Railway database comparison on 2026-10-25: not run.** The Postgres service no longer has a public TCP proxy (`DATABASE_PUBLIC_URL` has an empty host and port), so the laptop can't reach it, which also explains the earlier `server closed the connection`. The database is reachable only on Railway's private network. The row-level comparison is the copy tool's check from 2026-10-08, plus the 2026-10-25 rendered-page comparison.
- **Railway trial ends about 2026-11-07** ("13 days or $4.26 left" on 2026-10-25). The site has to move to AWS before then, or Railway stops it.
- The domain was moved to Railway before the Railway URL was tested (about 7 minutes of no working site).
- Education and Experience live in the template, not the database, so changing them needs a deploy.
- Both outgoing test emails reached the Microsoft 365 mailbox but ended up in Junk. DMARC is `p=none` (report only).
- GA4 doesn't count visitors who decline consent or block the tag, and DebugView was not used.
- Tests and the local database need Docker Desktop running.

## Reflection

*Written 2026-10-25, after the work.*

**"It works" isn't one yes-or-no answer.** Loading my site takes a chain of steps, and any link can break while the others look fine:

- **DNS vs. TLS.** DNS is the internet's phone book: it turns `chelseahuang.me` into the address of my server. TLS is the certificate behind the padlock and "https". DNS can send visitors to the right server while the certificate is broken, so the browser shows a warning instead of my site.
- **App vs. database.** The app serving pages can be running fine while the database it pulls content from is down or unreachable.
- **A 200 with the wrong data.** A 200 status means "everything's OK". My old code had a fallback: if it couldn't reach the database, it quietly showed sample demo projects and still sent 200. To me, and to any automated check, the site looked healthy while showing fake content. That's worse than an obvious error, because it hides the real problem. Now it shows "Projects temporarily unavailable" with a 503.

**What a platform does for me vs. what's still my job.** On the VM I handled everything. Railway took over the operating system, the web server, the certificates, and restarting the app after crashes. I still own my code, my data, my secrets (the passwords and keys the app uses), my DNS settings, and keeping an eye on cost.

**What I'd do differently next time.**

- Write down results as I go. This time I had to piece together what happened afterward.
- Test the new home before pointing my domain at it, so visitors never land on a broken site during the switch.
- Do a reboot test before deleting the old server: restart it, confirm everything comes back on its own, and only then destroy the fallback.

## Services, costs and cleanup

Checked 2026-10-25.

| Service | What it runs | Plan / cost | Expires or renews | Cleanup |
|---|---|---|---|---|
| Railway | Web service `career-platform` + `Postgres` (image `postgres-ssl:18`, volume 121 MB of 500 MB), project `imaginative-recreation`, region `iad` | Trial plan: one-time $5.00 credit, 1 GB RAM, 2 vCPU, 1 GB disk. Usage 2026-10-08 to 10-26: **$0.74** (all `imaginative-recreation`); estimated month's cost $0.04 | Railway Usage page, 2026-10-25 19:16 PDT: **"13 days or $4.26 left"**, so the trial ends about **2026-11-07**, or sooner if the $4.26 runs out | Migrate to AWS after the midterm and before the trial ends; then delete the project (`pg_dump` first) |
| Azure for Students | Left in `rg-career-platform`: static public IP `135.232.225.216` (Standard, **unattached**, still billed against the credit), NSG, VNet. VM, OS disk and NIC deleted 2026-10-13 | Student credit. Usage API shows $0.00 pretax (charged to credit); balance only visible in the portal | Credit balance and end date: check in the portal | When the instructor says: `az group delete -n rg-career-platform --subscription "Azure for Students"`. Nothing points at the IP since 2026-10-25 |
| Namecheap | Domain `chelseahuang.me` | Registration cost not recorded here | Expires **2027-10-01** | Decide on renewal before then |
| Cloudflare | Authoritative DNS, `www` redirect, Universal SSL for `www` | Free | — | Keep while the domain is used |
| Zoho Mail | `chelsea@chelseahuang.me` | Forever Free plan | — | Keep; remove MX/SPF/DKIM/DMARC if closed |
| Google Analytics 4 | Property `G-R24K9LD7H4` | Free | — | Keep |
| GitHub | Public repository | Free | — | Keep |

Compute is the Railway web service (and formerly the VM). Retained storage is Railway's PostgreSQL volume, plus the backups on my laptop (`data/*.db`, ignored by Git). The other billable resource is the Azure public IP.

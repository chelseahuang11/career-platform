# Project 1 submission: Own Your Corner of the Internet

- **Repository:** https://github.com/chelseahuang11/career-platform
- **Live HTTPS site:** https://chelseahuang.me/
- **Final commit SHA:** `3c93e739e92709a5b78de5d3e31ec2a3a195f4c7` (submitted in Brightspace). The only commit after it writes this SHA into this file and changes nothing else.

Every link below is a file, section or commit in this repository. Items marked **Unverified** were not checked, and the reason is given. Observations are dated; times are Pacific unless marked UTC.

## 1. README, original spec and plans

- [README.md](../README.md): what the site does, the live address, setup and update steps, rollback, architecture, decisions, failures, limitations, reflection, costs.
- Original application spec: [docs/resume-platform-spec.md](resume-platform-spec.md) (commit `de01067`, 2026-09-15, before the app code in `dc6fc58`)
- Original implementation plan: [docs/implementation-plan.md](implementation-plan.md) (`de01067`)
- Azure VM migration plan with results: [docs/superpowers/plans/2026-09-24-azure-vm-migration.md](superpowers/plans/2026-09-24-azure-vm-migration.md)
- Operate-the-VM plan with results: [docs/superpowers/plans/2026-10-01-operate-the-vm.md](superpowers/plans/2026-10-01-operate-the-vm.md)
- Railway/PostgreSQL migration plan (its Goal and Decisions sections are the spec): [docs/superpowers/plans/2026-10-08-railway-postgres-migration.md](superpowers/plans/2026-10-08-railway-postgres-migration.md)

## 2. Diagrams: Azure and Railway, with email and analytics

- [docs/diagrams/request-path.md](diagrams/request-path.md): Railway §1–2, Azure §3, email §4, analytics §5, `www` §6. PNG exports are in [docs/diagrams/](diagrams/).
- README: [Architecture](../README.md#architecture) (protocols and ports per path).

## 3. Migration, data comparison, cutover, rollback

- Plan committed before the change: [`3e87766`](https://github.com/chelseahuang11/career-platform/commit/3e87766) at 15:17 on 2026-10-08. The root CNAME was created at 15:21.
- Dependency inventory (what Git moves, and what needs another method): Railway plan, top sections, and README [Migration](../README.md#migration-to-railway-and-postgresql).
- PostgreSQL compatibility: [`d27e381`](https://github.com/chelseahuang11/career-platform/commit/d27e381) (SQL for PostgreSQL), [`9300e5f`](https://github.com/chelseahuang11/career-platform/commit/9300e5f) (copy tool that compares rows before committing).
- Real change to the original data (demo rows replaced by my profile and projects 4–7): the Azure migration plan's 2026-10-01 section on replacing the demo data with my profile.
- Source/target comparison and cutover results: Railway plan, Task 3 results (row comparison, 2026-10-08) and "Results recorded afterward" (cutover timeline, rendered-page comparison 2026-10-25: 4 of 4 projects and every profile field match).
- Rollback for code and data: README [Roll back a bad change](../README.md#roll-back-a-bad-change).
- Azure vs Railway responsibilities: README [Who manages what](../README.md#migration-to-railway-and-postgresql).
- **Not run:** a direct row comparison with Railway's database on 2026-10-25. The database has no public proxy any more, so it is reachable only inside Railway; see README [Remaining limitations](../README.md#remaining-limitations).

## 4. Azure HTTP/restart evidence and final DNS/HTTPS

- Azure VM build and site on its public IP: [docs/evidence/ex03.md](evidence/ex03.md) §1–2
- nginx → uvicorn (2 workers, systemd, `127.0.0.1:8000`) and NSG rules, with HTTP checks: [operate-the-VM plan](superpowers/plans/2026-10-01-operate-the-vm.md), Tasks 1–3
- SSH, public/private addresses, network rules: README [Azure deployment](../README.md#azure-deployment-earlier)
- Azure HTTPS, certificate and renewal (my Exercise 04 write-up): [docs/how-this-site-is-secured.md](how-this-site-is-secured.md)
- **Unverified: the controlled VM restart.** No result was recorded, and the VM was deleted on 2026-10-13 during class.
- Final DNS records with purposes, `www` redirect, HTTPS and certificate checks (2026-10-25): [docs/evidence/dns-https-final.md](evidence/dns-https-final.md)

## 5. Reviewed commit, its Railway deployment, and the live change

- Commit [`d67a3db`](https://github.com/chelseahuang11/career-platform/commit/d67a3db): 503 without sample projects on database failure, recovery without restart, empty-table message, plus Education and Experience sections.
- Review, tests and the local stop/start check; Railway deployment `8d01a5c2-57c1-4383-a9d7-e3b3527f8547` built from `d67a3db` on `main` (GitHub record `7322403277`, `success` 02:01:15 UTC); live check at 19:01 on 2026-10-25: README [Update the live site](../README.md#update-the-live-site) and [What the site does](../README.md#what-the-site-does).
- Railway deploys from GitHub `main`: `railway deployment list --json` shows repo `chelseahuang11/career-platform`, branch `main` and the commit for each deployment (2026-10-25).
- Recovery explanation: README [Roll back a bad change](../README.md#roll-back-a-bad-change).

## 6. Zoho email: send, receive, reply, DNS authentication

- Results sheet: [docs/evidence/ex06.md](evidence/ex06.md) §1 (before-MX message, received, replied, new messages) and §2 (MX/SPF/DKIM/DMARC values, explanations and `pass` results)
- Header analysis: [docs/evidence/zoho-header-check.md](evidence/zoho-header-check.md)
- Zone before Zoho: [docs/evidence/dns-before-zoho.md](evidence/dns-before-zoho.md); records today: [dns-https-final.md](evidence/dns-https-final.md)

## 7. GA4: page view and interaction

- [docs/evidence/ex06.md](evidence/ex06.md) §3: `page_view` and outbound `click` (`link_url`, `link_domain`, `outbound=true`) in Realtime, why the click event is useful, and how data goes from the browser to GA4
- Screenshot: [docs/evidence/ex06-ga4-events.png](evidence/ex06-ga4-events.png)
- Code: [`ec7fee1`](https://github.com/chelseahuang11/career-platform/commit/ec7fee1) (tag once per page), [`b6ce0d6`](https://github.com/chelseahuang11/career-platform/commit/b6ce0d6) (consent before cookies)

## 8. Failures, decisions, reflection, costs, limitations

- Investigated failures, including one marked as a deliberate lab simulation: README [Investigated failures](../README.md#investigated-failures). Records: [ex03.md](evidence/ex03.md), [ex05.md](evidence/ex05.md) (lab simulation), [dns-https-final.md](evidence/dns-https-final.md) (`www` fix), and the Railway plan (build failure).
- Decisions: README [Decisions](../README.md#decisions)
- Reflection: README [Reflection](../README.md#reflection)
- Services, costs, expiry dates, cleanup: README [Services, costs and cleanup](../README.md#services-costs-and-cleanup)
- Remaining limitations: README [Remaining limitations](../README.md#remaining-limitations)

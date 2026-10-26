# Project 1 gaps

**Status 2026-10-25:** closed items are ticked. Notes on the open ones are under "Still open".

From the requirements audit on 2026-10-20. Each line: the gap, then the file or check that closes it.

## 1. Profile and project data

- [x] DB failure serves demo projects with 200 → `main.py` keeps the profile, shows "Projects temporarily unavailable", returns 503; `tests/test_app.py` fallback tests assert 503 and no demo titles
- [x] Recovery without restart not recorded → stop/start the database, refresh, record 503 then 200 in an evidence file
- [x] Empty projects table not handled deliberately → `index.html` empty-state message plus a test with an empty table, and no demo re-seed on startup in `database.py`
- [x] Fallback JSON holds demo projects and old Gmail/LinkedIn → update or remove `data/profile_fallback.json` to match the new failure behavior
- [x] No Education section → add Education to `index.html` (or a database table)
- [x] No labeled Experience placeholder → add a clearly labeled placeholder section to `index.html`
- [x] No reason given for choosing SQLite → README "Decisions" section
- [x] Unverified "this site" project entry is labeled in progress → query the live `projects` table and record the row

## 2. Azure deployment

- [ ] VM deleted 2026-10-13 (per saved notes), spec says keep it running → `az vm show` result, then ask the instructor and record the answer in the README
- [ ] No controlled VM restart evidence → reboot result in `docs/superpowers/plans/2026-10-01-operate-the-vm.md`, or marked unverified
- [x] Private IP is a placeholder only → README Azure section with public/private addresses
- [x] Nginx 443/certbot setup and NSG 443 rule not documented → README Azure section or a linked evidence file

## 3. Domain and HTTPS

- [x] `www` is a DNS-only A record pointing at the old VM IP → proxied `www` record plus a Cloudflare redirect rule, recorded in a DNS evidence file
- [x] `http://www` and `https://www` landing on the root not verified → `curl -sIL` output for both, dated
- [x] No DNS records table with each record's purpose → `cf dns records list` capture plus a purpose table in an evidence file
- [x] Railway certificate hostname, dates and renewal not explained → `openssl s_client` output for `chelseahuang.me` plus a short explanation

## 4. Railway / PostgreSQL migration

- [x] Plan Tasks 4–5 still "Not started" → deploy, variables, cutover and post-cutover results in `2026-10-08-railway-postgres-migration.md`
- [x] No rendered-page comparison between source and target → page comparison recorded in the Railway plan
- [x] No spec under `docs/superpowers/` → add the spec, or state in the README that the plan's Goal is the spec
- [x] Plan-before-change timing not explained → README note: plan commit `3e87766` 15:17, root CNAME created 15:21 PDT
- [x] No Azure-vs-Railway responsibility comparison → README migration section
- [x] No Railway trial end date or costs → README costs section

## 5. Reviewed change through Railway

- [x] No commit linked to a Railway deployment and live result → record SHA, Railway deployment ID and observed behavior at the domain
- [x] Railway deploying from GitHub `main` not verified → Railway Settings → Source, recorded
- [x] No rollback procedure for code and data → README rollback section

## 6. Zoho email

- [x] `zoho-header-check.md` untracked → commit `docs/evidence/zoho-header-check.md`
- [x] `dns-before-zoho.md` untracked → commit `docs/evidence/dns-before-zoho.md`
- [x] No before-MX message line → add the line to `docs/evidence/ex06.md`
- [x] Published MX/SPF/DKIM/DMARC values and explanation missing → mail DNS capture plus explanation in an evidence file
- [x] LMU address unredacted → redact `docs/evidence/zoho-header-check.md` lines 3 and 65

## 7. GA4

- [x] No explanation of why the click event is useful → add it to `docs/evidence/ex06.md` §3
- [x] Collection path not explained (browser → gtag → GA) → add it to `docs/evidence/ex06.md` §3 or the README
- [x] Enhanced Measurement outbound-click setting not verified → GA Admin setting, recorded

## 8. Engineering record

- [x] README is one line → write `README.md` sections: what/live URL/setup/update, rollback, diagrams, migration, decisions, failures, reflection, costs, limitations
- [x] Submission index missing → create `docs/project-1-submission.md` with repo URL, live URL, final SHA and the 8 evidence links
- [x] No Azure/Railway diagrams with email and analytics paths → diagrams in the README or a linked file
- [x] Managed-vs-self-hosted email decision not in repo → README decisions section
- [x] No reflection → README reflection section
- [x] No cost/service inventory with expiry and cleanup → README costs section
- [x] No remaining-limitations list → README limitations section
- [x] Failures not linked → README links `docs/evidence/ex03.md` and `docs/evidence/ex05.md` (marked as the lab simulation)

## Other

- [x] `.cloudflare/` could get committed by accident → add it to `.gitignore`
- [ ] VM public IP shown, though the plans use placeholders → replace `135.232.225.216` in `ex03.md` and `dns-before-zoho.md` (or note it's no longer in use)
- [x] Privacy page says visits don't pass through Cloudflare → fix `templates/privacy.html` once `www` is proxied

## Still open (2026-10-25)

- Controlled VM restart: no record exists and the VM was deleted 2026-10-13 in class. Marked unverified in the README.
- Direct row comparison with Railway's database: not run (no public proxy; reading production data from inside Railway needs Chelsea's go-ahead). Deployment ID and source branch: done 2026-10-25.
- Decisions and Reflection in the README are drafts. Chelsea to review and edit them in her own words.
- Cost inventory: done, with the Railway trial (ends ~2026-11-07, $4.26 left). Azure credit balance only visible in the portal.
- `135.232.225.216` stays in `ex03.md`/`dns-before-zoho.md` as a historical record; nothing points at it since 2026-10-25.

# Project 1 gaps

From the requirements audit on 2026-10-20. Each line: the gap, then the file or check that closes it.

## 1. Profile and project data

- [ ] DB failure serves demo projects with 200 → `main.py` keeps the profile, shows "Projects temporarily unavailable", returns 503; `tests/test_app.py` fallback tests assert 503 and no demo titles
- [ ] Recovery without restart not recorded → stop/start the database, refresh, record 503 then 200 in an evidence file
- [ ] Empty projects table not handled deliberately → `index.html` empty-state message plus a test with an empty table, and no demo re-seed on startup in `database.py`
- [ ] Fallback JSON holds demo projects and old Gmail/LinkedIn → update or remove `data/profile_fallback.json` to match the new failure behavior
- [ ] No Education section → add Education to `index.html` (or a database table)
- [ ] No labeled Experience placeholder → add a clearly labeled placeholder section to `index.html`
- [ ] No reason given for choosing SQLite → README "Decisions" section
- [ ] Unverified "this site" project entry is labeled in progress → query the live `projects` table and record the row

## 2. Azure deployment

- [ ] VM deleted 2026-10-13 (per saved notes), spec says keep it running → `az vm show` result, then ask the instructor and record the answer in the README
- [ ] No controlled VM restart evidence → reboot result in `docs/superpowers/plans/2026-10-01-operate-the-vm.md`, or marked unverified
- [ ] Private IP is a placeholder only → README Azure section with public/private addresses
- [ ] Nginx 443/certbot setup and NSG 443 rule not documented → README Azure section or a linked evidence file

## 3. Domain and HTTPS

- [ ] `www` is a DNS-only A record pointing at the old VM IP → proxied `www` record plus a Cloudflare redirect rule, recorded in a DNS evidence file
- [ ] `http://www` and `https://www` landing on the root not verified → `curl -sIL` output for both, dated
- [ ] No DNS records table with each record's purpose → `cf dns records list` capture plus a purpose table in an evidence file
- [ ] Railway certificate hostname, dates and renewal not explained → `openssl s_client` output for `chelseahuang.me` plus a short explanation

## 4. Railway / PostgreSQL migration

- [ ] Plan Tasks 4–5 still "Not started" → deploy, variables, cutover and post-cutover results in `2026-10-08-railway-postgres-migration.md`
- [ ] No rendered-page comparison between source and target → page comparison recorded in the Railway plan
- [ ] No spec under `docs/superpowers/` → add the spec, or state in the README that the plan's Goal is the spec
- [ ] Plan-before-change timing not explained → README note: plan commit `3e87766` 15:17, root CNAME created 15:21 PDT
- [ ] No Azure-vs-Railway responsibility comparison → README migration section
- [ ] No Railway trial end date or costs → README costs section

## 5. Reviewed change through Railway

- [ ] No commit linked to a Railway deployment and live result → record SHA, Railway deployment ID and observed behavior at the domain
- [ ] Railway deploying from GitHub `main` not verified → Railway Settings → Source, recorded
- [ ] No rollback procedure for code and data → README rollback section

## 6. Zoho email

- [ ] `zoho-header-check.md` untracked → commit `docs/evidence/zoho-header-check.md`
- [ ] `dns-before-zoho.md` untracked → commit `docs/evidence/dns-before-zoho.md`
- [ ] No before-MX message line → add the line to `docs/evidence/ex06.md`
- [ ] Published MX/SPF/DKIM/DMARC values and explanation missing → mail DNS capture plus explanation in an evidence file
- [ ] LMU address unredacted → redact `docs/evidence/zoho-header-check.md` lines 3 and 65

## 7. GA4

- [ ] No explanation of why the click event is useful → add it to `docs/evidence/ex06.md` §3
- [ ] Collection path not explained (browser → gtag → GA) → add it to `docs/evidence/ex06.md` §3 or the README
- [ ] Enhanced Measurement outbound-click setting not verified → GA Admin setting, recorded

## 8. Engineering record

- [ ] README is one line → write `README.md` sections: what/live URL/setup/update, rollback, diagrams, migration, decisions, failures, reflection, costs, limitations
- [ ] Submission index missing → create `docs/project-1-submission.md` with repo URL, live URL, final SHA and the 8 evidence links
- [ ] No Azure/Railway diagrams with email and analytics paths → diagrams in the README or a linked file
- [ ] Managed-vs-self-hosted email decision not in repo → README decisions section
- [ ] No reflection → README reflection section
- [ ] No cost/service inventory with expiry and cleanup → README costs section
- [ ] No remaining-limitations list → README limitations section
- [ ] Failures not linked → README links `docs/evidence/ex03.md` and `docs/evidence/ex05.md` (marked as the lab simulation)

## Other

- [ ] `.cloudflare/` could get committed by accident → add it to `.gitignore`
- [ ] VM public IP shown, though the plans use placeholders → replace `135.232.225.216` in `ex03.md` and `dns-before-zoho.md` (or note it's no longer in use)
- [ ] Privacy page says visits don't pass through Cloudflare → fix `templates/privacy.html` once `www` is proxied

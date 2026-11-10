# AWS migration notes

Deviations from the [class AWS migration guide](https://github.com/LMU-ISBA/isba-4775-fa26/blob/main/guides/aws-migration.md) and from my plan, with the reason for each. Full command log: the migration plan in `docs/superpowers/plans/` (kept out of Git because it holds account details). Results: [ex07.md](evidence/ex07.md).

| Guide / plan step | What it says | What I did | Why |
|---|---|---|---|
| §1 Budget | Zero-spend budget from the account owner's console | Created 2026-11-10 as the root user (Use a template → Zero spend budget) | Late: should have been set before creating anything. The IAM user can't create budgets or see bills, so it's done as root, as the guide says |
| §7 RDS backups | 7 days of automated backups | 1 day | The Free plan refused 7 (`FreeTierRestrictionError`). Daily backups still meet my 24-hour RPO; my own `pg_dump` exports give the longer history |
| §8 Image | Ubuntu Server 26.04 LTS | Ubuntu 24.04 LTS | My plan was written before the guide changed. 24.04 is supported to 2029; I installed the PostgreSQL 18 client from the PostgreSQL apt repository (`pg_restore` 18.6, same as Railway) |
| §8 Storage | 20 GB gp3 | 8 GB gp3, encrypted | Enough for the OS, the app and a 5 KB database; costs less |
| §8 Ports | Public 80 and 443 | 443 only, and only from Cloudflare's IP ranges; no port 80 | HTTPS goes through Cloudflare's proxy, which redirects HTTP to HTTPS at its edge. Checked: a direct connection to the server times out |
| §8 Key pair | Made on the laptop, public half imported | Same | The class account denies `ec2:CreateKeyPair` |
| §10 Test record | `aws` A record, DNS only (grey cloud) | `aws` A record, **proxied** (orange cloud) | The server only accepts Cloudflare, and browsers don't trust a Cloudflare origin certificate, so the test has to go through Cloudflare. `nslookup aws.chelseahuang.me` therefore shows Cloudflare's addresses, not the server's |
| §10 Certificate | Let's Encrypt with certbot, nginx redirects HTTP → HTTPS | Cloudflare origin certificate (valid to 2041), SSL mode Full (strict) | No renewals, the server's address stays hidden, and HTTPS could be tested before DNS moved. Changed SSL mode from Full to Full (strict) on 2026-11-10 |
| §11 Before the trial ends | Cut over while Railway still serves | Cut over 2026-11-10, after the trial ended (~Nov 7) | I ran out of time. The site was down for about 3 days. No final dump from Railway was possible, so the 2026-10-29 backup is the final data; I made no edits after it, and the RDS data is line-for-line identical to it |
| §11 Merge | Merge the branch into main and redeploy | Not done yet | My plan disconnects Railway's GitHub link first, so a merge can't redeploy there |
| Plan 6.4 | `CREATE DATABASE … OWNER career_app` | `GRANT career_app TO career_admin` first | The RDS admin isn't a true superuser ("must be able to SET ROLE") |
| Plan 6.6 | `. /etc/career-platform/env` in `sh` | Read `DATABASE_URL` with `sed` | The `&` in the URL makes `sh` run the line in the background, leaving the variable empty. systemd reads the file correctly |

# Operate the VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the career-platform site run like a real website: reachable at `http://<VM_PUBLIC_IP>` with no port number, started automatically at boot, restarted after a crash, and never run as root.

**Architecture:** Two programs on the VM, each managed by systemd (Ubuntu's service manager). A new service, `career-platform`, runs uvicorn as `azureuser` with 2 worker processes on `127.0.0.1:8000`. nginx listens on port 80 and passes every request to that address. The Azure firewall (NSG) lets the Internet reach port 80 only.

**Tech Stack:** Ubuntu 24.04, systemd, nginx (from apt), uvicorn 0.53 from the existing `.venv`, Azure CLI on the laptop for read-only checks.

**Spec:** the request of 2026-10-01 (this plan's Goal and Global Constraints restate it). Earlier work: `docs/superpowers/plans/2026-09-24-azure-vm-migration.md`.

## VM details (found 2026-10-01 with `az`, read-only)

| | |
|---|---|
| VM | `vm-career-platform`, Linux (Ubuntu 24.04), size `Standard_B2ats_v2`, running |
| Resource group / region | `rg-career-platform` / `northcentralus` |
| Subscription | `Azure for Students` (not the CLI default, so every `az` command passes `--subscription "$SUB"`) |
| Public IP | `<VM_PUBLIC_IP>`, Static, no DNS name. It is the only VM in either subscription. |
| SSH | user `azureuser`, key `~/.ssh/<ssh-key>`, password login disabled. The local key matches the one Azure has for the VM. |
| NSG `vm-career-platform-nsg`, inbound | `Allow-SSH-Laptop` (300): port 22 from the laptop's current address only. `Allow-HTTP-80` (310): port 80 from anywhere. **No rule for port 8000.** |

**Placeholders:** this file is committed to a public repo, so, as in the migration plan, the real IP and key name are left out. Set them in your shell, never in this file.

```bash
KEY=~/.ssh/<ssh-key>
VM=azureuser@<VM_PUBLIC_IP>
IP=<VM_PUBLIC_IP>
SUB="Azure for Students"
```

Paste these into Git Bash on the laptop (repo root) before any laptop command.

## Global Constraints

- Service name: `career-platform`. It runs as `azureuser`, never root.
- Use what is already in `/home/azureuser/career-platform`: the code, `.venv`, `.env`, and `data/career_platform.db`. No `uv sync`, no `git pull`.
- No file inside the repo changes, on the laptop or the VM. The two new files live in `/etc`. No tests are added.
- uvicorn listens on `127.0.0.1:8000` only. Port 8000 gets no NSG rule.
- Chelsea makes any NSG change in the portal. The agent only reads Azure.
- Crash and restart tests are out of scope. Chelsea runs those.

## Review Focus

1. **The hand-started uvicorn still holds port 8000.** The new service then fails to start with "address already in use". Step 1.1 stops it first.
2. **nginx's default site is still enabled.** Visitors see "Welcome to nginx!" instead of the site. Steps 2.3 and 3.2 look for `Chelsea Huang` in the page, not just a `200`.
3. **The fallback hides a database problem.** The app serves `profile_fallback.json` if it can't read the database, and the page still looks normal. Steps 1.4 and 3.2 look for `RollEase Startup Project`, which exists only in the database, and step 1.4 checks the log.
4. **Two workers open the database at the same moment.** Each worker runs `init_db()` on start. SQLite waits up to 5 seconds for a lock, so this should pass; the log check in step 1.4 would show it if not.

## Progress

| Task | Status | Date | Notes |
|---|---|---|---|
| 1. The service | Done | 2026-10-01 | `career-platform` is enabled and active as `azureuser`, 2 workers on `127.0.0.1:8000`. No hand-started server was running. All checks passed. |
| 2. nginx on port 80 | Done | 2026-10-01 | nginx 1.24.0 installed, enabled and active; port 80 passes to the app. All checks passed. The site is already public, because the port 80 rule existed. |
| 3. Open to the Internet | Done, except Chelsea's browser and phone look | 2026-10-01 | `http://<VM_PUBLIC_IP>/` → 200 with the database content; port 8000 times out. Two NSG rules, port 80 rule still at priority 310. |

---

### Task 1: The service (about 8 minutes)

**For a beginner:** today the site runs only because someone typed a command. systemd is the program that starts everything else when Ubuntu boots. We give it a small file, called a unit, that says what to run, as which user, and what to do if it stops. `Restart=always` brings the app back after a crash. `--workers 2` runs two copies of the app behind one port, so if one copy crashes the other keeps answering while uvicorn replaces it. `enable` is what makes it start at boot.

**Where:** on the VM, in one SSH session. Open it from the laptop with `ssh -i $KEY $VM`.

**Files:**
- Create: `/etc/systemd/system/career-platform.service` (outside the repo)

- [x] **Step 1.1: Check the pieces are there, then stop the hand-started server**

  ```bash
  cd ~/career-platform
  test -x .venv/bin/python && test -f .env && test -f data/career_platform.db && echo ready
  P=$(ss -ltnp | grep ':8000 ' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
  [ -n "$P" ] && kill "$P"; sleep 2
  ss -ltn | grep ':8000 ' || echo "port 8000 free"
  ```

  **Check:** prints `ready` and `port 8000 free`. If `ready` is missing, stop here.

- [x] **Step 1.2: Write the unit file**

  ```bash
  sudo tee /etc/systemd/system/career-platform.service > /dev/null <<'EOF'
  [Unit]
  Description=Career Platform (FastAPI under uvicorn)
  After=network.target

  [Service]
  User=azureuser
  Group=azureuser
  WorkingDirectory=/home/azureuser/career-platform
  EnvironmentFile=/home/azureuser/career-platform/.env
  ExecStart=/home/azureuser/career-platform/.venv/bin/python -m uvicorn career_platform.main:app --host 127.0.0.1 --port 8000 --workers 2
  Restart=always
  RestartSec=2

  [Install]
  WantedBy=multi-user.target
  EOF
  ```

  If you paste this with the leading spaces, remove them first: the last `EOF` must start at the beginning of its line.

  What each line does: `User` is who the app runs as. `WorkingDirectory` matters because `.env` uses paths like `data/career_platform.db` that are relative to it. `EnvironmentFile` loads `.env`, replacing the old `set -a; . ./.env`. `WantedBy=multi-user.target` means "start during a normal boot".

  **Check:** `systemd-analyze verify /etc/systemd/system/career-platform.service` prints nothing about this file.

- [x] **Step 1.3: Start it now and at every boot**

  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now career-platform
  ```

  **Check:** `systemctl is-enabled career-platform; systemctl is-active career-platform` prints `enabled` then `active`.

- [x] **Step 1.4: Check who runs it, where it listens, and what it serves**

  ```bash
  M=$(systemctl show -p MainPID --value career-platform)
  ps -o user= -p $M; pgrep -c -P $M
  sudo ss -ltnp | grep ':8000 '
  curl -s localhost:8000/health; echo
  curl -s localhost:8000/ | grep -o -e 'Chelsea Huang' -e 'RollEase Startup Project' | sort -u
  sudo journalctl -u career-platform -b --no-pager | grep -c -e 'Database unavailable' -e 'Database initialization failed' -e 'Traceback'
  ```

  **Check, line by line:**
  - `azureuser`, then `3`: the 2 workers plus one helper process Python starts to manage them.
  - One listener, on `127.0.0.1:8000`. Not `0.0.0.0`.
  - `{"status":"ok"}`
  - Both `Chelsea Huang` and `RollEase Startup Project`.
  - `0`. The service's log now lives in systemd's journal, not `uvicorn.log`.

**Results (2026-10-01).** The agent ran every step from the laptop over SSH (`ssh -i $KEY $VM 'bash -s'` with the commands above), not in an interactive session. The commands are the plan's own, unchanged.

| Step | What ran | What the check showed |
|---|---|---|
| 1.1 | Looked for `.venv/bin/python`, `.env` and the database, then for a listener on port 8000 | `ready`. Nothing was listening on 8000, so there was no hand-started server to stop (`pid=none`), and `port 8000 free`. No `career-platform` unit existed yet. |
| 1.2 | Wrote `/etc/systemd/system/career-platform.service` with `sudo tee` | File is 426 bytes, owned by root. `systemd-analyze verify` printed nothing and exited 0. |
| 1.3 | `daemon-reload`, then `enable --now` | systemd created the link in `multi-user.target.wants`. `enabled`, `active`. |
| 1.4 | The six check commands | See below. All passed. |

Step 1.4 in detail:
- **User:** `azureuser` for the main process (pid 1792, parent pid 1) and every child. `systemctl show` reports `User=azureuser`, `NRestarts=0`.
- **Workers:** `pgrep -c` printed `3`: the 2 workers (pids 1795 and 1796) plus one small helper that Python starts to manage them. The journal shows `Started server process` twice.
- **Listener:** `127.0.0.1:8000` only, shared by the parent and both workers.
- **Site:** `/health` → `{"status":"ok"}`. `/` contains `Chelsea Huang` and `RollEase Startup Project`. `/resume` → `200` (extra check).
- **Log:** `0` lines matching `Database unavailable`, `Database initialization failed` or `Traceback`. Both workers started in the same second with no lock error (Review Focus 4).
- **Extra checks:** a worker's environment holds all 3 `CAREER_PLATFORM_*` variables, so `EnvironmentFile` works. The database fingerprint is `f27e4d51…468e45` before and after, the same as the laptop file. `git status --short` on the VM is empty, so nothing in the repo changed.

Not checked here, by design: that the service returns after a crash or a reboot. `enabled` and `Restart=always` are in place; the tests are Chelsea's.

**Undo Task 1 (VM).** Undo Task 2 first if it is done; otherwise nginx answers every visitor with "502 Bad Gateway".

```bash
sudo systemctl disable --now career-platform
sudo rm /etc/systemd/system/career-platform.service
sudo systemctl daemon-reload
```

- `disable --now` stops the app and removes it from the boot list. Deleting the file and reloading makes systemd forget the service.
- **Check:** `systemctl is-active career-platform` prints `inactive`, and `ss -ltn | grep ':8000 ' || echo "port 8000 free"` prints `port 8000 free`.
- The site is now off. Step 1.1 also stopped the hand-started server; to get that back, run step 7.1 of the migration plan.
- Nothing in `~/career-platform` was changed, so there is nothing to restore there.

---

### Task 2: nginx on port 80 (about 7 minutes)

**For a beginner:** browsers go to port 80 when a URL has no port number. Linux lets only root open ports below 1024, and the app must not be root. So nginx, a small web server built for this job, takes port 80 and hands each request to the app on port 8000. This is called a reverse proxy. nginx opens the port as root, then does its work as the unprivileged user `www-data`. apt sets nginx up as a systemd service, so it also starts at boot.

**Where:** on the VM, same SSH session.

**Files:**
- Create: `/etc/nginx/sites-available/career-platform`
- Create: a link to it in `/etc/nginx/sites-enabled/`
- Remove: the link `/etc/nginx/sites-enabled/default` (the "Welcome to nginx!" page; the original stays in `sites-available`)

- [x] **Step 2.1: Install nginx**

  ```bash
  sudo DEBIAN_FRONTEND=noninteractive apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
  ```

  **Check:** `nginx -v` prints a version, and `systemctl is-enabled nginx; systemctl is-active nginx` prints `enabled` then `active`.

- [x] **Step 2.2: Write the site file and switch it on**

  ```bash
  sudo tee /etc/nginx/sites-available/career-platform > /dev/null <<'EOF'
  server {
      listen 80 default_server;
      listen [::]:80 default_server;
      server_name _;

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  EOF
  sudo ln -s /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform
  sudo rm /etc/nginx/sites-enabled/default
  sudo nginx -t && sudo systemctl reload nginx
  ```

  Same note about leading spaces and the last `EOF` as step 1.2.

  What it says: listen on port 80 for any host name, and pass everything to the app. The `proxy_set_header` lines tell the app the visitor's real address, since from the app's side every request now comes from nginx.

  **Check:** `nginx -t` prints `syntax is ok` and `test is successful`. If it doesn't, the reload is skipped and nothing changes.

- [x] **Step 2.3: Check port 80 on the VM**

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost/
  curl -s http://localhost/ | grep -o 'Chelsea Huang' | head -1
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost/static/css/styles.css
  sudo ss -ltnp | grep -E ':(80|8000) '
  ```

  **Check:** `200`, `Chelsea Huang`, `200`, then nginx on `0.0.0.0:80` and `[::]:80` and uvicorn on `127.0.0.1:8000`.

**Results (2026-10-01).** The agent ran every step from the laptop over SSH, as in Task 1. The commands are the plan's own, unchanged.

| Step | What ran | What the check showed |
|---|---|---|
| 2.1 | `apt-get update`, then `apt-get install -y nginx` | Before: nginx not installed, port 80 free. Both commands exited 0. apt added 2 packages, `nginx` and `nginx-common` (the two the Undo removes). `nginx/1.24.0 (Ubuntu)`, `enabled`, `active`. The apt output is in `~/apt-update-nginx.log` and `~/apt-install-nginx.log` on the VM. |
| 2.2 | Wrote `/etc/nginx/sites-available/career-platform`, linked it into `sites-enabled`, removed the `default` link, `nginx -t`, reload | `syntax is ok`, `test is successful`, reload exited 0. `sites-enabled` holds only `career-platform`. The file kept `$host` literally, so the quoted `'EOF'` did its job. |
| 2.3 | The four check commands | `200`, `Chelsea Huang`, `200` for the CSS, then nginx on `0.0.0.0:80` and `[::]:80`, and uvicorn still on `127.0.0.1:8000` only. |

Extra checks:
- **It is the app, through nginx:** the page also contains `RollEase Startup Project` and not `Welcome to nginx`. The response header says `Server: nginx/1.24.0`, and the app's journal shows the same requests arriving. `/health` → `{"status":"ok"}`, `/resume` → `200`.
- **Who runs nginx:** the master process is root (needed to open port 80); the 2 processes that handle visitors are `www-data`. The app is still `azureuser`.
- **Boot:** `systemctl is-enabled nginx career-platform` prints `enabled` twice.
- **Nothing in the repo changed:** `git status --short` on the VM is empty, and the database fingerprint is still `f27e4d51…468e45`.
- **One 405 in the logs is the agent's:** a header-only request (`curl -I`) got `405 Method Not Allowed`, because the app answers `GET` only. Browsers use `GET`, so visitors are not affected.

**The site went public at this step.** `Allow-HTTP-80` already existed, so as soon as nginx started listening, `http://<VM_PUBLIC_IP>/` answered `200` from the laptop. Task 3 is now only checks.

**Undo Task 2 (VM).** nginx was not on the VM before this plan, so undoing means removing it.

```bash
sudo rm /etc/nginx/sites-enabled/career-platform /etc/nginx/sites-available/career-platform
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y nginx nginx-common
sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y
```

- Our site file goes first because apt deletes only the files it installed. `purge` removes the program and its settings in `/etc/nginx`; plain `remove` would leave the settings behind.
- **Check:** `sudo ss -ltn | grep ':80 ' || echo "port 80 free"` prints `port 80 free`, and `dpkg -l nginx 2>/dev/null | grep -c '^ii'` prints `0`.
- The app keeps running on `127.0.0.1:8000`. Visitors get "connection refused" on port 80, and you can still see the site through the SSH tunnel from the migration plan (step 8.4).
- **Smaller undo, to only fix a bad site file:** edit it, then `sudo nginx -t && sudo systemctl reload nginx`. A failed `nginx -t` leaves the running nginx untouched.

---

### Task 3: Open to the Internet (about 5 minutes)

**For a beginner:** the NSG is Azure's firewall, outside the VM. A request from the Internet has to pass the NSG and then find a program listening. Port 80 gets both. Port 8000 gets neither: no NSG rule, and uvicorn listens only on the VM's own loopback address.

**Where:** portal (Chelsea), then laptop (Git Bash).

- [x] **Step 3.1: The port 80 rule (Chelsea, portal)**

  A rule named `Allow-HTTP-80` already exists at priority **310** (TCP 80, source Any). It already does the job, so nothing needs adding. Azure won't accept a second rule with the same name. If you want priority 320, open the rule and change its priority; either number works, since no other rule covers port 80.

  **Check (laptop, read-only):**

  ```bash
  az network nsg rule list --subscription "$SUB" -g rg-career-platform --nsg-name vm-career-platform-nsg --query "[?direction=='Inbound'].{name:name, prio:priority, port:destinationPortRange, src:sourceAddressPrefix, access:access}" -o table
  ```

  Exactly two rules: `Allow-SSH-Laptop` on 22 and `Allow-HTTP-80` on 80. Nothing on 8000.

- [ ] **Step 3.2: The site answers on the public IP with no port (laptop)**

  ```bash
  curl -s -m 10 -o /dev/null -w "%{http_code}\n" http://$IP/
  curl -s -m 10 http://$IP/ | grep -o -e 'Chelsea Huang' -e 'RollEase Startup Project' | sort -u
  ```

  **Check:** `200`, then both names. Then open `http://<VM_PUBLIC_IP>` in the browser, and once on your phone's mobile data, which proves it works from outside campus.

- [x] **Step 3.3: Port 8000 is closed (laptop)**

  ```bash
  curl -s -m 10 -o /dev/null http://$IP:8000/; echo "exit=$?"
  ```

  **Check:** `exit=28` after 10 seconds. That is a timeout: the NSG dropped the request.

**Results (2026-10-01).** The agent ran the laptop checks. It changed nothing in Azure; the one `az` command only lists rules.

| Step | What ran | What the check showed |
|---|---|---|
| 3.1 | `az network nsg rule list` (laptop, read-only) | Exactly two inbound rules: `Allow-SSH-Laptop` (300, TCP 22, from the laptop's address only) and `Allow-HTTP-80` (310, TCP 80, from anywhere). Nothing on 8000. The rule is still at priority 310; no portal change has been made. |
| 3.2 | `curl http://$IP/` from the laptop, no port | `200`. The page contains `Chelsea Huang` and `RollEase Startup Project`, and not `Welcome to nginx`. Extra: the CSS → `200`, `/resume` → `200`, `/health` → `{"status":"ok"}`. |
| 3.3 | `curl -m 10 http://$IP:8000/` from the laptop | `exit=28` after 10 seconds: a timeout, so port 8000 is closed to the Internet. |

Still open, both Chelsea's:
- Open `http://<VM_PUBLIC_IP>` in a browser, and once on phone mobile data. The laptop checks used `curl` from campus, so they show the page's text arrives, not how it looks, and not that it works from another network.
- The priority. The request said 320 and the rule is at 310. It works as it is; change it in the portal only if 320 matters to you.

**Undo Task 3 (Chelsea, portal).** Steps 3.2 and 3.3 only read, so only step 3.1 can need undoing.

- **If you changed the priority to 320:** open `Allow-HTTP-80` and set it back to 310. Visitors notice nothing either way.
- **If you want the site off the Internet:** delete `Allow-HTTP-80`. This goes further than an undo, because the rule existed before this plan. To put it back: add an inbound rule named `Allow-HTTP-80`, source Any, destination port 80, protocol TCP, action Allow, priority 310.
- **Check (laptop):** re-run the `az network nsg rule list` command from step 3.1 and read the rule's priority, or confirm it is gone. With the rule deleted, `curl -s -m 10 -o /dev/null http://$IP/; echo "exit=$?"` prints `exit=28`.
- The agent does not make these changes; they are yours in the portal.

---

## Undoing everything

Undo in reverse order: Task 3, then Task 2, then Task 1. Each task's own Undo block has the commands and a check. Going backwards means visitors never reach a half-removed setup. Afterwards the VM is as it was before this plan, except that the hand-started server is stopped (migration plan step 7.1 starts it again).

## What this plan leaves for you

- Crash test: kill a worker, then the whole service, and watch it come back.
- Restart test: reboot the VM and confirm the site returns with nobody logged in.
- `systemctl is-enabled` in steps 1.3 and 2.1 is the only boot evidence this plan collects.
- HTTPS. It needs a domain name, so the site stays `http://` and the browser will say "Not secure".

## Everyday commands (VM)

```bash
systemctl status career-platform          # is it running, and its processes
sudo journalctl -u career-platform -f     # live app log
sudo systemctl restart career-platform    # after a git pull or a database copy
sudo tail /var/log/nginx/access.log       # who visited
```

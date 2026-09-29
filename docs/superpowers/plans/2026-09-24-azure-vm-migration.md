# Azure VM Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the career-platform FastAPI app on the Azure VM `vm-career-platform`, serving the SQLite data from the laptop, then deallocate the VM.

**Architecture:** The app runs under uvicorn from a git clone on the VM, with its virtualenv built by `uv sync` from `uv.lock`. The laptop's `data/career_platform.db` is copied over with `scp` before the app starts for the first time. We check the site on the VM with `curl`, and from the laptop through an SSH tunnel, so no Azure firewall (NSG) rule is needed.

**Tech Stack:** Azure VM (Ubuntu), OpenSSH (`ssh`/`scp` from Git Bash on Windows), apt, git, uv, Python 3.12, FastAPI, uvicorn, SQLite, Azure CLI (`az`, installed on the laptop).

**Spec:** The migration plan in the request (Server → Packages → Code → Python → Config → Data → Processes → Verify → Shutdown). App behavior: `docs/resume-platform-spec.md`.

## Global Constraints

- VM: `vm-career-platform`, resource group `rg-career-platform`, subscription `Azure for Students` (not the CLI default "Azure subscription 1", so every `az` command passes `--subscription "$SUB"`)
- Public IP: `<VM_PUBLIC_IP>` (Static, confirmed 2026-09-29)
- SSH user: `azureuser`. SSH key: `~/.ssh/<ssh-key>`. Every `ssh`/`scp` uses exactly this user and key.
- Repo: `https://github.com/chelseahuang11/career-platform.git` (public, so no credentials are needed to clone), branch `main`
- App directory on VM: `/home/azureuser/career-platform`
- Python: 3.12 (from `.python-version`); dependencies come only from `uv.lock` (`uv sync --locked`)
- App entry point: `career_platform.main:app`, port `8000`
- Database path: `data/career_platform.db`, relative to the app directory (the default in `src/career_platform/config.py`)
- Laptop commands run in **Git Bash** from the repo root `~/network cloud computing/career-platform`.

## Facts from the codebase that shape this plan

1. **There is no `.env.example` in the repo, and the app never reads `.env`.** `config.py` only calls `os.getenv(...)` for `CAREER_PLATFORM_DATA_DIR`, `CAREER_PLATFORM_DATABASE` and `CAREER_PLATFORM_FALLBACK`. `python-dotenv` is not in `uv.lock`, so `uvicorn --env-file` would fail. The Config section therefore (a) creates and pushes `.env.example` from the laptop and (b) exports `.env` into the shell before uvicorn starts.
2. **Importing the app creates the database.** `main.py` calls `init_db()` at import time. That creates `data/career_platform.db` and fills it with seed rows (`INSERT OR IGNORE`). If anything imports `career_platform` before the `scp` step (for example `uv run python -c "import career_platform"` or `uv run pytest`), a seeded database appears in the spot where the real one is supposed to go. Nothing before the Data section may import the app.
3. **The seed data looks the same as your data.** Your laptop DB holds 1 profile ("Chelsea Huang") and 3 projects ("Investment Screening Dashboard", "Portfolio Strategy Case Study", "Data Storytelling Project"), which are also the seed values. So seeing those names on the page does not prove your file is being served. We prove it with a SHA-256 checksum plus a check that the log never mentions the fallback.
4. **The app falls back quietly.** If the DB can't be read, the app serves `data/profile_fallback.json` and logs `Database unavailable; serving the public profile fallback`. The page still looks fine, so we grep the log for that message.
5. **`data/*.db` is in `.gitignore`**, so `git clone` never brings the DB over. The Data step is the only way it gets to the VM.

## Review Focus

1. **Seeded DB masking a failed copy.** If the app is imported before `scp`, or if `scp` goes to the wrong path, the site still shows "Chelsea Huang" and the 3 projects. Guarded by the checksum steps in Data 6.3 and Verify 8.2.
2. **Fallback JSON masking a broken DB.** A corrupt or unreadable DB still produces a normal-looking page. Guarded by the log grep in Verify 8.3.
3. **uvicorn dying when SSH disconnects.** A plain foreground `uv run uvicorn` stops when the session ends. Processes 7.1 uses `nohup … &`, and Verify 8.1 runs from a *new* SSH session.
4. **Public IP changing after deallocate.** If the IP is Dynamic, `<VM_PUBLIC_IP>` can change on the next start. *Resolved 2026-09-29:* the IP is Static, so it survives deallocation. Shutdown 9.1 still re-checks it.
5. **Local port 8000 already in use on the laptop.** If the local dev server is running, the tunnel in Verify 8.4 can't bind to it. The step uses laptop port `8080` instead.

## Progress

| Section | Status | Date | Notes |
|---|---|---|---|
| 1. Server | Done | 2026-09-29 | VM was deallocated, started, SSH verified. Found the VM under the `Azure for Students` subscription; added `--subscription` to all `az` commands. |
| 2. Packages | Done | 2026-09-29 | `git` and `curl` were already on the image. Installed only `sqlite3`, which is therefore the only package the undo removes. |
| 3. Code | Done | 2026-09-29 | Cloned to `~/career-platform` on the VM at `8b1d27a`, which matches the laptop. No `.db` came with it. |
| 4. Python | Done | 2026-09-29 | uv 0.12.21. `uv lock --check` passed and `uv sync --locked` installed 31 packages on Ubuntu's own Python 3.12.3. Package review is clean; see step 4.2's Result. |
| 5. Config | Done | 2026-09-29 | `.env.example` committed and pushed as `cbae328`. The VM pulled it and copied it to `.env`, which is identical and gitignored. |
| 6. Data | Done | 2026-09-29 | Laptop backup made. DB copied to the VM; fingerprint `ca406667…` matches on both sides; integrity `ok`; 1 profile and 3 projects. |
| 7. Processes | Done | 2026-09-29 | uvicorn listening on `127.0.0.1:8000`, loopback only (restarted twice on request; now listener pid 14033 under `uv run` pid 14027), and it survived the SSH logout. `.env` variables are in its environment. DB fingerprint unchanged by startup. Fixed the plan's `pgrep`/`pkill` commands, which matched their own SSH shell. |
| 8. Verify | Done | 2026-09-29 | Site answers on the VM and through an SSH tunnel on laptop port 8080. All 4 names render; DB fingerprint still equals `LAPTOP_SHA`; 0 fallback/error lines in the log. |
| 9. Shutdown | Not started | | |

**The VM stays billed while it's running.** If you pause between sessions, run 9.2–9.3 to deallocate it, and 1.1 to start it again.

## Variables used below (laptop, Git Bash)

```bash
KEY=~/.ssh/<ssh-key>
VM=azureuser@<VM_PUBLIC_IP>
SUB="Azure for Students"
```

Paste these into each new Git Bash window before running any laptop command.

**Placeholders:** this file is committed to a public repo, so the real values are left out. Replace them in your own shell, never in this file:
- `<ssh-key>`: the SSH private key file name in `~/.ssh/`.
- `<VM_PUBLIC_IP>`: the VM's Static public IP. Look it up with `az vm list-ip-addresses --subscription "$SUB" -g rg-career-platform -n vm-career-platform -o table`.
- `<VM_PRIVATE_IP>`: the VM's address on its Azure virtual network (`ip -br addr` on the VM, `eth0`). It appears only in recorded results.

---

### 1. Server

**Where:** laptop (+ portal as an alternative)

- [x] **Step 1.1: Make sure the VM is running**
  - **Run (laptop):** `az vm get-instance-view --subscription "$SUB" -g rg-career-platform -n vm-career-platform --query "instanceView.statuses[?starts_with(code,'PowerState')].displayStatus" -o tsv`
    If it prints `VM deallocated` or `VM stopped`: `az vm start --subscription "$SUB" -g rg-career-platform -n vm-career-platform`
    *Portal alternative:* Virtual machines → vm-career-platform → Overview → Status; click **Start** if needed.
  - **Why:** SSH needs a running VM.
  - **Check:** the command prints `VM running`.
  - **Undo:** `az vm deallocate --subscription "$SUB" -g rg-career-platform -n vm-career-platform` (the same as Shutdown).
  - **Result (2026-09-29):** without `--subscription`, the first run failed with `ResourceGroupNotFound`. With it, the VM showed `VM deallocated`; `az vm start` brought it to `VM running`.

- [x] **Step 1.2: Confirm SSH with the right user and key**
  - **Run (laptop):** `ssh -i $KEY -o StrictHostKeyChecking=accept-new $VM 'whoami; hostname; lsb_release -ds; df -h ~ | tail -1'`
  - **Why:** proves the key, user and IP work and shows the OS version and free disk space before we change anything.
  - **Check:** prints `azureuser`, a hostname, an Ubuntu version string, and a disk line with at least 2 GB free. `accept-new` trusts the host key the first time and still refuses a key that changed later. The key is now in `~/.ssh/known_hosts`, so later steps use plain `ssh -i $KEY $VM`.
  - **Undo:** nothing to undo (read-only). To forget the host key: `ssh-keygen -R <VM_PUBLIC_IP>`.
  - **Result (2026-09-29):** `azureuser` / `vm-career-platform` / `Ubuntu 24.04.4 LTS` / 27G free of 29G.

### 2. Packages

**Where:** VM (run each command from the laptop with `ssh -i $KEY $VM '…'`, or inside an interactive `ssh -i $KEY $VM` session)

- [x] **Step 2.1: Record what's already installed**
  - **Run (VM):** `dpkg -l git sqlite3 curl 2>/dev/null | grep '^ii' | tee ~/preinstalled-packages.txt`
  - **Why:** Ubuntu images often come with `git` and `curl` already installed. This record means Undo removes only what *we* added.
  - **Check:** `cat ~/preinstalled-packages.txt` lists 0–3 packages.
  - **Undo:** `rm ~/preinstalled-packages.txt`
  - **Result (2026-09-29):** 2 packages were already installed: `curl 8.5.0-2ubuntu10.13` and `git 1:2.43.0-1ubuntu7.3`. `sqlite3` was not installed.

- [x] **Step 2.2: Install git and sqlite3**
  - **Run (VM):** `sudo DEBIAN_FRONTEND=noninteractive apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git sqlite3`
    (`DEBIAN_FRONTEND=noninteractive` stops apt from opening prompts, which would hang a command sent over `ssh`.)
  - **Why:** `git` is for cloning the repo. The `sqlite3` CLI is for checking the copied DB. (The app itself uses Python's built-in `sqlite3` module.)
  - **Check:** `git --version && sqlite3 --version` prints two version lines, and `echo $?` prints `0`.
  - **Undo:** for each package *not* in `~/preinstalled-packages.txt`: `sudo apt-get remove -y <pkg> && sudo apt-get autoremove -y`. As of 2026-09-29 that's just `sudo apt-get remove -y sqlite3 && sudo apt-get autoremove -y`. Don't remove `git`; it came with the image.
  - **Result (2026-09-29):** `apt-get update` and `install` both exited 0. `git version 2.43.0`, `sqlite3 3.45.1 2024-01-30`. The apt output is in `~/apt-update.log` and `~/apt-install.log` on the VM.

### 3. Code

**Where:** VM

- [x] **Step 3.1: Clone the repo**
  - **Run (VM):** `git clone https://github.com/chelseahuang11/career-platform.git ~/career-platform`
  - **Why:** puts the app source, `uv.lock`, `.python-version` and `data/profile_fallback.json` on the VM.
  - **Check:** `git -C ~/career-platform log -1 --oneline` matches `git log -1 --oneline` on the laptop, and `ls ~/career-platform/data` shows `profile_fallback.json` **and no `.db` file**.
  - **Undo:** `rm -rf ~/career-platform`
  - **Result (2026-09-29):** `clone exit=0`. The VM and the laptop are both at `8b1d27a Document bounded implementation workflow`. `data/` holds only `profile_fallback.json`: 1341 bytes on the VM against 1375 on the laptop, because Windows line endings add a byte per line. The content is the same. The plan file and `.env.example` aren't pushed yet, so section 5.2's `git pull` will bring them later.

### 4. Python

**Where:** VM

- [x] **Step 4.1: Install uv**
  - **Run (VM):** `curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env`
  - **Why:** uv installs Python 3.12 and the locked dependencies. We don't depend on the Python version that ships with the image.
  - **Check:** `uv --version` prints a version. In a *new* SSH session, `command -v uv` prints `/home/azureuser/.local/bin/uv`.
  - **Undo:** `uv cache clean; rm -rf ~/.local/share/uv ~/.local/bin/uv ~/.local/bin/uvx` and remove the line the installer added to `~/.bashrc`/`~/.profile` (it sources `~/.local/bin/env`).
  - **Result (2026-09-29):** installer exit 0. `uv 0.12.21 (x86_64-unknown-linux-gnu)`. A fresh login shell finds `/home/azureuser/.local/bin/uv`. Installer output is in `~/uv-install.log`. The version satisfies `pyproject.toml`'s build requirement `uv_build>=0.12.15,<0.13`.

- [x] **Step 4.2: Sync dependencies from the lock file**
  - **Run (VM):** `cd ~/career-platform && uv lock --check && uv sync --locked`
    (`uv lock --check` confirms `uv.lock` still matches `pyproject.toml` before installing anything.)
  - **Why:** builds `.venv` with exactly the versions in `uv.lock`. `--locked` fails if the lock doesn't match `pyproject.toml`, so we never quietly resolve new versions.
  - **Check:** `uv run python --version` prints `Python 3.12.x`, and `uv run python -c "import fastapi, uvicorn, jinja2; print('ok')"` prints `ok`. **Do not** import `career_platform` or run `pytest` here (see Fact 2). `ls data/` must still show no `.db`.
  - **Undo:** `rm -rf ~/career-platform/.venv`. uv didn't download a Python; it used the system's `/usr/bin/python3.12`, so there's nothing else to remove.
  - **Result (2026-09-29):** `uv lock --check`: "Resolved 32 packages", exit 0. `uv sync --locked`: exit 0, output in `~/uv-sync.log`. Python is `3.12.3`, Ubuntu's own (`.venv/pyvenv.cfg`: `home = /usr/bin`, `include-system-site-packages = false`). `data/` still has no `.db`.
    **Package review:**
    - Direct dependencies match `pyproject.toml`'s minimums exactly: fastapi 0.141.1, httpx 0.28.1, jinja2 3.1.6, pytest 9.1.1, sqlite-utils 4.2.1, uvicorn 0.53.0.
    - 31 packages installed against 32 in the lock. The difference is `colorama`, which the lock marks `sys_platform == 'win32'`, so skipping it on Linux is correct. Nothing is installed that isn't in the lock. `pip 26.2.1` is locked as a dependency of `sqlite-utils`.
    - `uv pip check`: "All installed packages are compatible".
    - Import check `fastapi, uvicorn, jinja2, httpx, sqlite_utils, pytest` printed `ok`. `career_platform` was deliberately not imported (Fact 2).
    - Full list: annotated-doc 0.0.5, annotated-types 0.8.0, anyio 4.15.1, career-platform 0.1.0 (editable), certifi 2026.7.22, click 8.5.0, click-default-group 1.2.4, fastapi 0.141.1, h11 0.16.0, httpcore 1.0.9, httpx 0.28.1, idna 3.20, iniconfig 2.3.0, jinja2 3.1.6, markupsafe 3.0.3, packaging 26.3, pip 26.2.1, pluggy 1.6.0, pydantic 2.13.5, pydantic-core 2.46.5, pygments 2.21.0, pytest 9.1.1, python-dateutil 2.9.0.post0, six 1.17.0, sqlite-fts4 1.0.3, sqlite-utils 4.2.1, starlette 1.6.0, tabulate 0.10.0, typing-extensions 4.16.0, typing-inspection 0.4.4, uvicorn 0.53.0.

### 5. Config

**Where:** laptop, then VM

- [x] **Step 5.1: Create `.env.example` in the repo (laptop)**
  - **Run (laptop):** create `.env.example` at the repo root with:

    ```bash
    # Copy to .env. Load it with: set -a; . ./.env; set +a
    # Paths are relative to the directory uvicorn starts in (the repo root).
    CAREER_PLATFORM_DATA_DIR=data
    CAREER_PLATFORM_DATABASE=data/career_platform.db
    CAREER_PLATFORM_FALLBACK=data/profile_fallback.json
    ```

    Then: `git add .env.example && git commit -m "Add .env.example documenting data path settings" && git push origin main`
  - **Why:** the migration plan copies `.env` from `.env.example`, but that file doesn't exist yet (Fact 1). The values match the code's defaults, so nothing changes on the laptop. They just make the settings explicit.
  - **Check:** `git ls-remote origin main` shows the new commit hash, and `git check-ignore .env.example` prints nothing (the file is not ignored; only `.env` is).
  - **Undo:** `git revert cbae328 && git push origin main`
  - **Result (2026-09-29):** committed as `cbae328 Add .env.example documenting data path settings` and pushed (`8b1d27a..cbae328  main -> main`). `git ls-remote origin main` shows `cbae328…`. The file isn't ignored, and `.env` is.

- [x] **Step 5.2: Pull it on the VM and copy to `.env`**
  - **Run (VM):** `cd ~/career-platform && git pull --ff-only && cp --update=none .env.example .env`
    (Ubuntu 24.04's `cp` warns that `-n` is non-portable; `--update=none` does the same thing: it never overwrites.)
  - **Why:** `.env` is the VM's own copy. It's gitignored, so later VM-only edits never get committed. `cp -n` won't overwrite an existing `.env`.
  - **Check:** `diff .env.example .env` prints nothing, and `git status --short` prints nothing (`.env` is ignored).
  - **Undo:** `rm ~/career-platform/.env` (the pull can stay; `git reset --hard 8b1d27a` if you want it gone).
  - **Result (2026-09-29):** VM at `cbae328`. `diff .env.example .env` is empty, `git status --short` is clean, and `file .env` says `ASCII text` (Unix line endings, so `. ./.env` won't pick up a stray `
`). `data/` still has only `profile_fallback.json`.

### 6. Data

**Where:** laptop, then VM

- [x] **Step 6.0: Back up the laptop DB (laptop)**
  - **Run (laptop):** `cp -p data/career_platform.db data/career_platform.2026-09-29.bak.db`
  - **Why:** once the VM serves its own copy, the two will drift apart, and until now the laptop held the only copy. `-p` keeps the timestamps. The name ends in `.db`, so `.gitignore`'s `data/*.db` keeps it out of git.
  - **Check:** `sha256sum data/career_platform.db data/career_platform.2026-09-29.bak.db` prints the same hash twice, and `git status --short data/` prints nothing.
  - **Undo:** `rm data/career_platform.2026-09-29.bak.db`
  - **Result (2026-09-29):** both files hash to `ca4066672f0ed6b502ff504459903531f3b430d81fdf90997ba96e7455fdbc2b`. `git status --short data/` is empty. There were no `-wal`/`-journal` files next to the DB.

- [x] **Step 6.1: Take a fingerprint of the laptop DB (laptop)**
  - **Run (laptop):** make sure no local uvicorn is running, then `sha256sum data/career_platform.db`
    To check for a running app, use PowerShell: `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn|career_platform' }` and `Get-NetTCPConnection -LocalPort 8000 -State Listen`. Avoid `tasklist /V` from Git Bash; it hung for over 2 minutes here.
    Optional read-only integrity check: `python -c "import sqlite3;c=sqlite3.connect('file:data/career_platform.db?mode=ro',uri=True);print(c.execute('pragma integrity_check').fetchone()[0])"`
  - **Why:** this hash is how we prove the VM serves *this* file and not a seeded copy (Fact 3).
  - **Check:** prints a 64-character hash. Write it down as `LAPTOP_SHA`.
  - **Result (2026-09-29):** no app process, port 8000 free. `LAPTOP_SHA = ca4066672f0ed6b502ff504459903531f3b430d81fdf90997ba96e7455fdbc2b`. Laptop integrity `ok`, 1 profile, 3 projects.
  - **Undo:** nothing to undo (read-only).

- [x] **Step 6.2: Copy the DB to the VM (laptop)**
  - **Run (laptop):** `ssh -i $KEY $VM 'test ! -e ~/career-platform/data/career_platform.db || mv ~/career-platform/data/career_platform.db ~/career-platform/data/career_platform.db.bak'` then `scp -i $KEY data/career_platform.db $VM:career-platform/data/career_platform.db`
  - **Why:** `data/*.db` is gitignored (Fact 5). The first command moves aside any stray seeded DB instead of silently overwriting it.
  - **Check:** `scp` prints a 100% progress line (about 20 KB), and `echo $?` prints `0`.
  - **Undo:** `ssh -i $KEY $VM 'rm ~/career-platform/data/career_platform.db; test -e ~/career-platform/data/career_platform.db.bak && mv ~/career-platform/data/career_platform.db.bak ~/career-platform/data/career_platform.db'`
  - **Result (2026-09-29):** the VM had no DB before the copy ("no db on VM yet"), so there's no `.bak` on the VM. `scp exit=0`. The file on the VM is 20480 bytes, the same as the laptop.

- [x] **Step 6.3: Confirm the copy is identical and healthy (VM)**
  - **Run (VM):** `cd ~/career-platform && sha256sum data/career_platform.db && sqlite3 -readonly data/career_platform.db "PRAGMA integrity_check; SELECT count(*) FROM profile; SELECT title FROM projects ORDER BY id;"`
  - **Why:** proves the bytes arrived intact and that SQLite can read them.
  - **Check:** the hash equals `LAPTOP_SHA`. Output is `ok`, `1`, then `Investment Screening Dashboard`, `Portfolio Strategy Case Study`, `Data Storytelling Project`. If there's a `.bak` file from 6.2, note that the app had been imported early. The `.bak` can be deleted after Verify passes.
  - **Undo:** nothing to undo (read-only).
  - **Result (2026-09-29):** VM hash `ca4066672f0ed6b502ff504459903531f3b430d81fdf90997ba96e7455fdbc2b`, equal to `LAPTOP_SHA`, both before and after the SQL check. Output: `ok`, `1`, `Investment Screening Dashboard`, `Portfolio Strategy Case Study`, `Data Storytelling Project`. No `.bak` exists (the app was never imported early).

### 7. Processes

**Where:** VM

- [x] **Step 7.1: Start uvicorn in the background with `.env` loaded**
  - **Run (VM):**

    ```bash
    source ~/.local/bin/env
    cd ~/career-platform
    if ss -ltn | grep -q ':8000 '; then echo "PORT 8000 ALREADY IN USE"; exit 1; fi
    set -a; . ./.env; set +a
    nohup uv run uvicorn career_platform.main:app --host 127.0.0.1 --port 8000 > uvicorn.log 2>&1 < /dev/null &
    echo $! > uvicorn.pid
    curl -s --retry 15 --retry-connrefused --retry-delay 1 localhost:8000/health; echo
    ```

    - `< /dev/null` detaches stdin, so an `ssh … '…'` call returns right away instead of waiting on the background job.
    - The "already running" guard checks **port 8000**, not `pgrep -f`. Over SSH, `pgrep -f "uvicorn career_platform"` (even with `[u]vicorn`) matches the remote `bash -c` whose command text contains that string, so it falsely reported "ALREADY RUNNING" twice.
    - `curl --retry-connrefused` waits for startup without a fixed `sleep`.
    - `uvicorn.pid` holds the `uv run` parent. The process that actually listens is its child; find it with `ss -ltnp | grep ':8000 '`.

  - **Why:** `set -a` exports every variable from `.env` into uvicorn's environment (Fact 1). `nohup … &` keeps the server running after you log out. `--host 127.0.0.1` (current setting, changed 2026-09-29 on request) listens only on the VM's loopback address, so only programs on the VM itself can connect. That includes sshd, which is how the Verify 8.4 tunnel still works. The original setting was `--host 0.0.0.0`, which listens on every network interface; use that only if the port is meant to be reachable from the network.
  - **Check:** after ~3 seconds, `tail uvicorn.log` shows `Uvicorn running on http://127.0.0.1:8000` and no traceback, and `ss -ltnp | grep :8000` shows a listener. `tr '\0' '\n' < /proc/$(ss -ltnp | grep ':8000 ' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)/environ | grep CAREER_PLATFORM` shows the 3 variables.
  - **Undo:** `kill $(ss -ltnp | grep ':8000 ' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2); rm -f ~/career-platform/uvicorn.pid` (the `uv run` parent exits when its child does; keep `uvicorn.log` for debugging, or delete it). Don't use `pkill -f 'uvicorn career_platform…'` over SSH: it matches, and kills, the SSH session's own shell.
  - **Result (2026-09-29):** health returned `{"status":"ok"}` on the first try (after two false "ALREADY RUNNING" results from the old `pgrep` guard; `pgrep -a -f "[u]vicorn"` and `ss` confirmed nothing was running). From a new SSH session:
    - `uvicorn.log` shows `Started server process [2954]`, `Application startup complete.`, `Uvicorn running on http://0.0.0.0:8000`, and `GET /health … 200 OK`, with no tracebacks.
    - `ss`: `0.0.0.0:8000 users:(("uvicorn",pid=2954))`. Its parent is `uv run` pid 2949 with **PPID 1**, so it survived the logout.
    - `/proc/2954/environ` has all 3 `CAREER_PLATFORM_*` variables.
    - DB fingerprint `ca4066672f0ed6b5…` before and after startup. `init_db()` didn't change the file.
  - **Restart (2026-09-29, on request, no Azure changes):** stopped the listener (pid 2954) with the port-based kill from the Undo above. Port 8000 freed within the wait loop, and the `uv run` parent (2949) exited with it. The old log was kept as `uvicorn.<timestamp>.log`. Restarted with the same 7.1 command, still `--host 0.0.0.0`:
    - Why not `--host ::` for IPv6: `ip -br addr` shows only `127.0.0.1`, `::1`, `<VM_PRIVATE_IP>` and link-local `fe80::…`, with no public IPv6. Azure delivers the public IP's traffic to `<VM_PRIVATE_IP>`, so `0.0.0.0` covers every address traffic can arrive on.
    - `sudo ss -ltnp` afterwards: `0.0.0.0:8000 uvicorn pid=13878` (child of `uv run` 13872, PPID 1). The only other listeners are `0.0.0.0:22` / `[::]:22` (sshd) and `127.0.0.53:53` / `127.0.0.54:53` (systemd-resolved, local only).
    - `127.0.0.1:8000/` → 200, `<VM_PRIVATE_IP>:8000/` → 200, and the laptop tunnel `localhost:8080/` → 200. 0 fallback/traceback lines, and the DB fingerprint is still `ca4066672f0ed6b5…`.
  - **Restart to loopback only (2026-09-29, on request, no Azure changes):** stopped the listener (pid 13878) by port. The port freed and the `uv run` parent (13872) exited. The old log was kept. Restarted with `--host 127.0.0.1` (the 7.1 command above now uses this):
    - `sudo ss -ltnp` afterwards: `127.0.0.1:8000 uvicorn pid=14033` (child of `uv run` 14027, PPID 1). The only other listeners are `0.0.0.0:22` / `[::]:22` (sshd) and `127.0.0.53:53` / `127.0.0.54:53` (systemd-resolved, local only). Nothing listens on port 8000 on any non-loopback address.
    - From the VM: `127.0.0.1:8000/` → 200 and `localhost:8000/` → 200. `<VM_PRIVATE_IP>:8000/` → connection refused (curl exit 7), so nothing arriving over the network can reach the app. `[::1]:8000/` → refused, since only IPv4 loopback is bound.
    - The laptop tunnel `localhost:8080/` → 200 still, because sshd on the VM makes the connection to `localhost:8000` itself; only people who can SSH in can use it. 0 fallback/traceback lines; DB fingerprint still `ca4066672f0ed6b5…`.

### 8. Verify

**Where:** VM, then laptop

- [x] **Step 8.1: The site answers on the VM (new SSH session)**
  - **Run (laptop):** `ssh -i $KEY $VM 'curl -s localhost:8000/health; echo; curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/'`
  - **Why:** a fresh session proves the server survived the logout from step 7.1.
  - **Check:** prints `{"status":"ok"}` and then `200`.
  - **Undo:** nothing to undo (read-only).
  - **Result (2026-09-29):** `{"status":"ok"}`, `/` → `200`, and `/resume` → `200` (also checked).

- [x] **Step 8.2: The page shows your data, from your file**
  - **Run (VM):** `cd ~/career-platform && curl -s localhost:8000/ | grep -o -e 'Chelsea Huang' -e 'Investment Screening Dashboard' -e 'Portfolio Strategy Case Study' -e 'Data Storytelling Project' | sort -u && sha256sum data/career_platform.db`
  - **Why:** the names prove the page renders the data. The hash proves the file is still yours and wasn't replaced (Fact 3).
  - **Check:** all 4 strings print, and the hash still equals `LAPTOP_SHA`. (If the hash changed but the rows still match, `init_db`'s no-op transaction touched the file. Re-run the 6.3 SQL; matching rows are acceptable.)
  - **Undo:** nothing to undo (read-only).
  - **Result (2026-09-29):** all 4 strings are present (`Chelsea Huang` 3 times; each project title once). DB hash `ca4066672f0ed6b502ff504459903531f3b430d81fdf90997ba96e7455fdbc2b`, still equal to `LAPTOP_SHA` after serving pages. `/resume` sends `content-type: text/html; charset=utf-8` and `content-disposition: attachment; filename="resume.html"`.

- [x] **Step 8.3: The DB was used, not the fallback**
  - **Run (VM):** `grep -c -e 'Database unavailable' -e 'Database initialization failed' -e 'Traceback' ~/career-platform/uvicorn.log`
  - **Why:** the fallback JSON renders the same names, so only the log tells the two apart (Fact 4).
  - **Check:** prints `0`.
  - **Undo:** nothing to undo (read-only).
  - **Result (2026-09-29):** `0`. The log holds only `200 OK` access lines for `/health`, `/` and `/resume`.

- [x] **Step 8.4: Look at it in your laptop browser through an SSH tunnel**
  - **Run (laptop):** `ssh -i $KEY -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N -L 8080:localhost:8000 $VM` (leave it running), then open `http://localhost:8080` and `http://localhost:8080/resume`
    (`ExitOnForwardFailure` makes ssh exit instead of silently running without a tunnel if port 8080 is taken. `ServerAliveInterval` keeps an idle tunnel from being dropped. Check first that 8080 is free: `Get-NetTCPConnection -LocalPort 8080 -State Listen` in PowerShell should return nothing.)
  - **Why:** you see the real page without opening port 8000 to the internet in the NSG.
  - **Check:** the home page shows your profile and 3 projects, and `/resume` downloads `resume.html`.
  - **Undo:** press Ctrl+C in the tunnel window.
  - **Result (2026-09-29):** laptop port 8080 was free. Through the tunnel: `/health` → `{"status":"ok"}`, all 4 names on `/`, `/resume` → `attachment; filename="resume.html"`, and `/static/css/styles.css` → `200`. Checked with `curl` from the laptop; the browser look is up to Chelsea. The tunnel was left open for that.

### 9. Shutdown

**Where:** laptop (+ portal as an alternative)

- [ ] **Step 9.1: Check whether the public IP will survive**
  - **Run (laptop):** `az network public-ip list --subscription "$SUB" -g rg-career-platform --query "[].{name:name, ip:ipAddress, method:publicIPAllocationMethod}" -o table`
  - **Why:** a `Dynamic` IP is released on deallocate, so `<VM_PUBLIC_IP>` may change. A `Static` IP is kept (and still billed while the VM is off).
  - **Check:** note the `method`. If it's `Dynamic`, expect a new IP next time and update this plan's Global Constraints then.
  - **Undo:** nothing to undo (read-only).

- [ ] **Step 9.2: Stop uvicorn cleanly**
  - **Run (laptop):** `ssh -i $KEY $VM 'P=$(ss -ltnp | grep ":8000 " | grep -o "pid=[0-9]*" | head -1 | cut -d= -f2); test -n "$P" && kill $P; for i in 1 2 3 4 5; do ss -ltn | grep -q ":8000 " || break; sleep 1; done; ss -ltn | grep -q ":8000 " && echo "still running" || echo stopped'`
    (This finds the server by the port it owns. `pkill -f` would kill the SSH shell running the command; see step 7.1.)
  - **Why:** lets SQLite close the DB before the VM powers off.
  - **Check:** prints `stopped`.
  - **Undo:** re-run step 7.1.

- [ ] **Step 9.3: Deallocate the VM**
  - **Run (laptop):** `az vm deallocate --subscription "$SUB" -g rg-career-platform -n vm-career-platform`
    *Portal alternative:* Virtual machines → vm-career-platform → **Stop** (the portal's Stop deallocates).
  - **Why:** stops compute billing. `sudo shutdown` inside the VM stops the OS but keeps the VM allocated and billed.
  - **Check:** `az vm get-instance-view --subscription "$SUB" -g rg-career-platform -n vm-career-platform --query "instanceView.statuses[?starts_with(code,'PowerState')].displayStatus" -o tsv` prints `VM deallocated`.
  - **Undo:** `az vm start --subscription "$SUB" -g rg-career-platform -n vm-career-platform`, then re-run 7.1 (uvicorn is not a system service, so it won't start by itself on boot) and 8.1. The clone, `.venv`, `.env` and DB stay on the disk.

---

## Verify results (2026-09-29)

What section 8 tested and what each check showed. All checks ran against the live server (uvicorn listener pid 2954) serving the database copied in section 6.

| # | Step | What it tested | Where / how | Result | Pass? |
|---|---|---|---|---|---|
| 1 | 8.1 | Server survived the SSH logout from 7.1 | Laptop → new SSH session → `curl localhost:8000/health` | `{"status":"ok"}` | ✅ |
| 2 | 8.1 | Home page renders | VM: `curl -w "%{http_code}" localhost:8000/` | `200` | ✅ |
| 3 | 8.1 | Resume page renders (extra check) | VM: `curl -w "%{http_code}" localhost:8000/resume` | `200` | ✅ |
| 4 | 8.2 | Page shows the profile name | VM: `grep -o 'Chelsea Huang'` on `/` | Found (3 times) | ✅ |
| 5 | 8.2 | Page shows all 3 projects | VM: `grep -o` for each title on `/` | `Investment Screening Dashboard`, `Portfolio Strategy Case Study`, `Data Storytelling Project`: each found once | ✅ |
| 6 | 8.2 | The served DB is *your* file, not a seeded copy (Fact 3) | VM: `sha256sum data/career_platform.db` | `ca4066672f0ed6b5…dbc2b`, equal to `LAPTOP_SHA` from 6.1 | ✅ |
| 7 | 8.2 | `/resume` downloads as a file (extra check) | VM: response headers of `/resume` | `content-type: text/html; charset=utf-8`, `content-disposition: attachment; filename="resume.html"` | ✅ |
| 8 | 8.3 | Data came from the DB, not `profile_fallback.json` (Fact 4) | VM: `grep -c` for `Database unavailable` / `Database initialization failed` / `Traceback` in `uvicorn.log` | `0` | ✅ |
| 9 | 8.3 | Every request was served normally | VM: `tail uvicorn.log` | Only `200 OK` lines for `/health`, `/`, `/resume` | ✅ |
| 10 | 8.4 | Laptop port 8080 free for the tunnel | Laptop (PowerShell): `Get-NetTCPConnection -LocalPort 8080 -State Listen` | Nothing listening | ✅ |
| 11 | 8.4 | Site reachable from the laptop without opening port 8000 in the NSG | Laptop: SSH tunnel `8080→8000`, then `curl localhost:8080/health` | `{"status":"ok"}` | ✅ |
| 12 | 8.4 | Your data renders through the tunnel | Laptop: `grep -o` for the 4 names on `localhost:8080/` | All 4 found | ✅ |
| 13 | 8.4 | Resume download through the tunnel | Laptop: headers of `localhost:8080/resume` | `attachment; filename="resume.html"` | ✅ |
| 14 | 8.4 | Static files (CSS) are served (extra check) | Laptop: `curl localhost:8080/static/css/styles.css` | `200` | ✅ |
| 15 | 8.4 | Page looks right in a real browser | Chelsea opens `http://localhost:8080` and `/resume` | Not yet confirmed; the tunnel was left open for this | ⏳ |

**What these checks don't cover:**
- The site isn't reachable on the public IP. That's deliberate, because port 8000 was never opened in the NSG.
- Nothing wrote to the DB. The app is read-only for visitors, so the VM copy and the laptop copy stay identical until one of them is edited.
- The server won't come back after a VM reboot, since uvicorn isn't a system service. After `az vm start`, re-run 7.1.

# Request path: chelseahuang.me from home Wi-Fi

Drawn 2026-10-20 from the repository's records, after the work was done. Assumptions: home Wi-Fi, nothing cached, a new TCP connection, no `www`.

Home network details (private IP, router model, resolver, ISP hops) are typical examples, not observations. See [Unknowns](#unknowns).

## 1. Where things are (Railway, live)

```mermaid
flowchart LR
  subgraph HOME["Your home · private network"]
    L["Laptop · browser<br/>private IP 192.168.x.x (example)"]
    R["Home router<br/>Wi-Fi AP + switch + router<br/>NAT + DHCP + firewall<br/>default gateway"]
    M["Modem / ONT"]
  end
  subgraph NET["Internet · public addresses"]
    ISP["ISP network"]
    IR["Internet routers"]
  end
  subgraph RW["Railway"]
    E["Railway edge<br/>:80 → 301 https<br/>:443 TLS ends here"]
    A["App container<br/>uvicorn on $PORT<br/>--proxy-headers"]
    P[("PostgreSQL<br/>DATABASE_URL")]
  end
  subgraph DNS["DNS · separate exchange"]
    RES["DNS resolver<br/>router, ISP or public? (unknown)"]
    CF["Cloudflare · authoritative<br/>CNAME → pfg32veb.up.railway.app<br/>DNS only"]
  end

  L -- "Wi-Fi" --- R --- M --- ISP --- IR
  IR == "HTTPS · TCP 443 · encrypted" ==> E
  E -- "plain HTTP · private network" --> A
  A -- "SQL · private network" --> P

  L -. "UDP 53 query / answer" .-> RES
  RES -. "root → .me → Cloudflare" .-> CF
```

## 2. The order things happen

```mermaid
sequenceDiagram
  autonumber
  participant B as Browser (laptop)
  participant R as Home router (NAT)
  participant D as DNS resolver
  participant C as Cloudflare DNS
  participant E as Railway edge
  participant A as App (uvicorn)
  participant P as PostgreSQL
  participant G as Google (gtag / GA4)

  Note over B: Typed chelseahuang.me → http://, host, port 80, path /
  B->>D: UDP 53: A record for chelseahuang.me?
  D->>C: Recursive lookup (root → .me → Cloudflare)
  C-->>D: CNAME pfg32veb.up.railway.app, flattened to A records
  D-->>B: Railway edge IP
  B->>R: TCP 80 SYN (private source IP)
  R->>E: NAT rewrites source to home public IP
  E-->>B: 301 → https://chelseahuang.me/ (expected, unverified on Railway)
  B->>E: TCP 443 + TLS handshake
  E-->>B: Certificate for chelseahuang.me (check name, dates, chain)
  Note over B,E: Encrypted from here to the edge
  B->>E: GET / (encrypted)
  E->>A: GET / plain HTTP on $PORT + X-Forwarded-Proto: https
  A->>P: SELECT profile, projects
  P-->>A: Rows
  A-->>E: 200 HTML
  E-->>R: Encrypted response to home public IP
  R-->>B: NAT maps reply back to laptop's private IP
  B->>E: GET /static/css/styles.css (same connection)
  B->>G: New DNS + TLS: load gtag.js, then send GA4 events
```

## 3. What changes on Azure

- Cloudflare answers with an **A record pointing to the VM's static public IP**, not a CNAME to Railway.
- The Railway box becomes **NSG** (80 and 443 open, 22 from the laptop only, nothing on 8000) → **nginx** (handles the :80 → 301 redirect, TLS ends here, Let's Encrypt certificate renewed by the certbot timer) → **uvicorn on 127.0.0.1:8000** (2 workers under systemd) → **SQLite file** on the VM's disk.
- The database step is a file read inside the app process, not a network connection.

## Sources in this repo

| Claim | Source |
|---|---|
| Root CNAME to Railway, DNS only | `docs/evidence/dns-before-zoho.md` (2026-10-13) |
| Start command and proxy headers | `Procfile` |
| `DATABASE_URL`, connection per request | `src/career_platform/config.py`, `src/career_platform/database.py` |
| GA4 tag | `src/career_platform/templates/base.html` |
| Azure NSG, nginx, systemd, loopback | `docs/superpowers/plans/2026-10-01-operate-the-vm.md` |
| Azure TLS, redirect, renewal | `docs/how-this-site-is-secured.md` (2026-10-08) |
| Azure SQLite file | `docs/superpowers/plans/2026-09-24-azure-vm-migration.md` |

## Unknowns

| Unknown | Check |
|---|---|
| Laptop's private IP, subnet, gateway, DNS server | `ipconfig /all` |
| Which roles the home router combines | Device label or admin page |
| Who the resolver is | `ipconfig /all`; `nslookup chelseahuang.me` |
| ISP and internet hops | `tracert chelseahuang.me` |
| Railway's HTTP → HTTPS redirect | `curl -sI http://chelseahuang.me/` |
| Railway certificate issuer and dates | `openssl s_client -connect chelseahuang.me:443 -servername chelseahuang.me \| openssl x509 -noout -subject -issuer -dates` |
| Railway internals (region, Postgres host and port) | Railway dashboard |

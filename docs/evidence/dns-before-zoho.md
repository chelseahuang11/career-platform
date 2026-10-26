# DNS records for chelseahuang.me before Zoho Mail

Captured on **2026-10-13 at 21:11 UTC** (14:11 Pacific), before any Zoho Mail record was added.

This is my real zone, not a simulation. I ran the command below against Cloudflare, which is authoritative for `chelseahuang.me`, and the output is copied unchanged.

## Command

Cloudflare CLI `cf` version 1.0.0-beta.13, signed in with `cf auth login`.

```
cf dns records list --zone chelseahuang.me
```

## Summary

The zone holds three records. A `ttl` of 1 means Cloudflare's automatic TTL.

| Type | Name | Content | Proxied | TTL | Created |
|---|---|---|---|---|---|
| A | `www.chelseahuang.me` | `135.232.225.216` | no | auto | 2026-10-01 |
| CNAME | `chelseahuang.me` | `pfg32veb.up.railway.app` | no | auto | 2026-10-08 |
| TXT | `_railway-verify.chelseahuang.me` | `railway-verify=2790c13d673f2e88df47fd6d518382040c07ccbd2072feb1f5744d4e610c38bd` | no | auto | 2026-10-08 |

## What is not there

No record in the zone has anything to do with mail:

- no MX record
- no SPF record (a TXT at `chelseahuang.me` starting `v=spf1`)
- no DKIM record (a TXT under `_domainkey.chelseahuang.me`)
- no DMARC record (a TXT at `_dmarc.chelseahuang.me`)

## Full output

```json
[
  {
    "id": "9ccd078c75f4c5367d6d485f9732cf39",
    "name": "www.chelseahuang.me",
    "type": "A",
    "content": "135.232.225.216",
    "proxiable": true,
    "proxied": false,
    "ttl": 1,
    "settings": {},
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-01T21:41:35.607815Z",
    "modified_on": "2026-10-01T21:41:35.607815Z"
  },
  {
    "id": "ec34befd2d024e9a21ff5e5bba226788",
    "name": "chelseahuang.me",
    "type": "CNAME",
    "content": "pfg32veb.up.railway.app",
    "proxiable": true,
    "proxied": false,
    "ttl": 1,
    "settings": {
      "flatten_cname": false
    },
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-08T22:21:36.525497Z",
    "modified_on": "2026-10-08T22:21:36.525497Z"
  },
  {
    "id": "d17d363b177bb69f079461fbeec59f8e",
    "name": "_railway-verify.chelseahuang.me",
    "type": "TXT",
    "content": "\"railway-verify=2790c13d673f2e88df47fd6d518382040c07ccbd2072feb1f5744d4e610c38bd\"",
    "proxiable": false,
    "proxied": false,
    "ttl": 1,
    "settings": {},
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-08T22:22:31.598951Z",
    "modified_on": "2026-10-08T22:22:31.598951Z"
  }
]
```

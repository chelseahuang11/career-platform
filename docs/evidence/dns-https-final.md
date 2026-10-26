# Final DNS and HTTPS for chelseahuang.me

Checked on **2026-10-25 at about 19:00 PDT**, from my laptop (Git Bash on Windows) unless a line says otherwise. Written afterward as a record of the final state, not as a plan.

Cloudflare is the authoritative DNS for `chelseahuang.me`. The site runs on Railway. Mail is hosted by Zoho.

## DNS records and their purpose

From `cf dns records list --zone chelseahuang.me` (Cloudflare CLI), times converted to Pacific.

| Type | Name | Content | Proxy | Created | Purpose |
|---|---|---|---|---|---|
| CNAME | `chelseahuang.me` | `pfg32veb.up.railway.app` | DNS only | 2026-10-08 15:21 | Sends the bare domain to the Railway web service. DNS only, so the browser's TLS session goes straight to Railway, which holds the certificate. Cloudflare flattens a CNAME at the apex into A records, so lookups return an IP. |
| TXT | `_railway-verify` | `railway-verify=2790c1…` | DNS only | 2026-10-08 15:22 | Proves to Railway that I control the domain, so it would attach the custom domain and issue a certificate. |
| A | `www` | `192.0.2.1` | **Proxied** | 2026-10-01 (changed 2026-10-25) | Exists only so Cloudflare answers for `www`. The address is a reserved documentation address and is never contacted: Cloudflare's redirect rule answers first. |
| MX | `chelseahuang.me` | `mx.zoho.com` 10, `mx2.zoho.com` 20, `mx3.zoho.com` 50 | n/a | 2026-10-13 14:37 | Tells other mail servers to deliver mail for `@chelseahuang.me` to Zoho. Lower number is tried first. |
| TXT | `chelseahuang.me` | `v=spf1 include:zohomail.com ~all` | n/a | 2026-10-13 14:42 | SPF: lists the servers allowed to send as `chelseahuang.me` (Zoho's). `~all` soft-fails anything else. |
| TXT | `zmail._domainkey` | `v=DKIM1; k=rsa; p=MIGf…` | n/a | 2026-10-13 14:46 | DKIM: the public key receivers use to check Zoho's signature (selector `zmail`) on my outgoing mail. |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:chelsea@chelseahuang.me` | n/a | 2026-10-13 15:01 | DMARC: asks receivers to require SPF or DKIM to pass *and* match the From domain. `p=none` means report only, don't reject yet; reports go to my Zoho mailbox. |
| TXT | `chelseahuang.me` | `zoho-verification=zb38810407…` | n/a | 2026-10-13 14:12 | Proves to Zoho that I control the domain. |

The same mail values are visible from Google's public resolver (`https://dns.google/resolve`, 2026-10-25 19:00):

```
MX  chelseahuang.me                  10 mx.zoho.com. / 20 mx2.zoho.com. / 50 mx3.zoho.com.
TXT chelseahuang.me                  v=spf1 include:zohomail.com ~all
TXT _dmarc.chelseahuang.me           v=DMARC1; p=none; rua=mailto:chelsea@chelseahuang.me
TXT zmail._domainkey.chelseahuang.me v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDh8V4C…
```

The records before Zoho are in [dns-before-zoho.md](dns-before-zoho.md). The authentication results these records produce are in [ex06.md](ex06.md) §2 and [zoho-header-check.md](zoho-header-check.md).

## The www fix (2026-10-25)

**Symptom.** `http://www.chelseahuang.me/` and `https://www.chelseahuang.me/` timed out (checked 18:37 PDT).

**Check.** `nslookup www.chelseahuang.me 1.1.1.1` returned `135.232.225.216`, the static IP of the Azure VM that was deleted on 2026-10-13. The Cloudflare record was an A record to that IP set to **DNS only**. The redirect rule already existed (`cf rulesets get … --zone chelseahuang.me`, phase `http_request_dynamic_redirect`, created 2026-10-13 22:22 UTC from Cloudflare's "Redirect from WWW to root" template):

```
expression: (http.request.full_uri wildcard r"http*://www.*")
target:     wildcard_replace(http.request.full_uri, r"http*://www.*", r"https://${2}")   status 301
```

**Diagnosis.** A redirect rule only runs on traffic that passes through Cloudflare. With the record grey (DNS only), browsers went straight to the dead VM address and the rule never ran.

**Repair.** At 2026-10-26 01:53:40 UTC (18:53 PDT on 10-25):

```
cf dns records edit 9ccd078c75f4c5367d6d485f9732cf39 --zone chelseahuang.me \
  --body '{"type":"A","name":"www.chelseahuang.me","content":"192.0.2.1","proxied":true,"ttl":1}'
```

**Repeated check.**

```
$ curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" <url>
http://chelseahuang.me/                       301 -> https://chelseahuang.me/
https://chelseahuang.me/                      200
http://www.chelseahuang.me/                   301 -> https://chelseahuang.me/
https://www.chelseahuang.me/                  301 -> https://chelseahuang.me/
https://www.chelseahuang.me/privacy?ref=test  301 -> https://chelseahuang.me/privacy?ref=test

$ curl -L … https://www.chelseahuang.me/      final https://chelseahuang.me/ 200 after 1 redirect(s)
$ curl -L … http://www.chelseahuang.me/       final https://chelseahuang.me/ 200 after 1 redirect(s)
```

`www.chelseahuang.me` now resolves to Cloudflare (`172.67.135.5`, `104.21.6.162`). Paths and query strings are kept.

Two things I saw on my laptop and how I checked them:

- Windows `curl` (Schannel) at first refused `https://www` with `CRYPT_E_REVOCATION_OFFLINE`: it could not reach the certificate's revocation server. `openssl s_client` verified the same certificate (`Verify return code: 0 (ok)`), and `curl --ssl-no-revoke` followed the redirect, so the certificate is fine. The results above use `--ssl-no-revoke`.
- `http://www` over IPv6 sometimes got `Connection was reset` from my home network. Over IPv4 it returned 301 three times out of three. From outside my network (Firecrawl scrape, 2026-10-25 ~19:02 PDT), `http://www.chelseahuang.me/` ended at `https://chelseahuang.me/` with status 200.

## Certificates

```
$ echo | openssl s_client -connect <host>:443 -servername <host> | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

| Host | Who serves TLS | Subject / SAN | Issuer | Valid | Verify |
|---|---|---|---|---|---|
| `chelseahuang.me` | Railway (DNS only, so TLS ends at Railway's edge) | `CN=chelseahuang.me`, SAN `chelseahuang.me` | Let's Encrypt `YR2` | 2026-10-08 21:25 UTC to 2027-01-06 21:25 UTC | `0 (ok)` |
| `www.chelseahuang.me` | Cloudflare (proxied, so TLS ends at Cloudflare's edge) | `CN=chelseahuang.me`, SAN `*.chelseahuang.me`, `chelseahuang.me` | Let's Encrypt `YE2` | 2026-10-01 21:03 UTC to 2026-12-30 21:03 UTC | `0 (ok)` |

**Hostname.** Each certificate lists the name the browser asked for in its SAN: the Railway one covers only the bare domain, and Cloudflare's covers the bare domain and every first-level subdomain, including `www`.

**Validity and renewal.** Both are 90-day Let's Encrypt certificates, and I don't renew either by hand:

- Railway's certificate says `notBefore` 2026-10-08 21:25 UTC (14:25 PDT). Let's Encrypt backdates `notBefore` by an hour, so it was issued about 15:25 PDT, four minutes after I created the apex CNAME (15:21 PDT). Railway renews it automatically before expiry as long as the domain still points at Railway. I did not see which validation method Railway used.
- Cloudflare's Universal SSL certificate for the zone renews automatically while the zone is active on Cloudflare.

The earlier certificate on the Azure VM (certbot, `chelseahuang.me` and `www`) and its renewal timer are explained in my Exercise 04 write-up, [how-this-site-is-secured.md](../how-this-site-is-secured.md). That VM is deleted, so the certificate is no longer served.

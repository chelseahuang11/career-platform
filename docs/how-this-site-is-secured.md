# How this site is secured

Site: <https://chelseahuang.me> (also <https://www.chelseahuang.me>)

All checks below were run on October 8, 2026.

## How do I know my data to your site is encrypted?

If the address starts with `https://`, your browser and my server agree on a secret code first, then use it to scramble everything. Someone on the same Wi-Fi can see that you're visiting chelseahuang.me, but not what you're doing there. If you type `http://`, the site automatically sends you to `https://`, so you can't land on an unprotected version by mistake.

```text
$ curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://chelseahuang.me/
301 https://chelseahuang.me/
$ curl -s -o /dev/null -w "%{http_code}\n" https://chelseahuang.me/
200
```

## What the certificate proves

Scrambling isn't enough if you're talking to a fake site. The certificate is like an ID card that proves my server really controls chelseahuang.me. Let's Encrypt, a trusted certificate authority, checked that and signed it. The certificate covers two names, `chelseahuang.me` and `www.chelseahuang.me`. Your browser checks the signature, the name, and the dates (Oct 6, 2026 to Jan 4, 2027). If anything's wrong, you see a warning.

This is the actual certificate my server sends (guide section 6):

```text
$ echo | openssl s_client -connect chelseahuang.me:443 -servername chelseahuang.me 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN=chelseahuang.me
issuer=C=US, O=Let's Encrypt, CN=YE1
notBefore=Oct  6 21:04:10 2026 GMT
notAfter=Jan  4 21:04:09 2027 GMT
X509v3 Subject Alternative Name:
    DNS:chelseahuang.me, DNS:www.chelseahuang.me
```

## Renewal

The certificate only lasts 90 days, so a stolen one wouldn't be useful for long. That means it has to renew itself.

- A timer (Certbot's) checks twice a day whether the certificate is close to expiring.
- When it is, it gets a new one and reloads the web server.
- I ran a practice renewal and it worked for both names. The practice run doesn't replace my real certificate.
- The timer check shows it's actually running on schedule: it last ran Oct 8 at 12:24 UTC and the next run is Oct 9 at 05:59 UTC.

```text
$ sudo certbot renew --dry-run
Saving debug log to /var/log/letsencrypt/letsencrypt.log

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Processing /etc/letsencrypt/renewal/chelseahuang.me.conf
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Simulating renewal of an existing certificate for chelseahuang.me and www.chelseahuang.me

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/chelseahuang.me/fullchain.pem (success)
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

$ systemctl list-timers | grep certbot
Fri 2026-10-09 05:59:29 UTC      9h Thu 2026-10-08 12:24:07 UTC        8h ago certbot.timer                  certbot.service
```

## Open ports

Think of ports as doors. Azure keeps every door locked unless I open it.

- **443:** open to everyone. It's the secure website.
- **80:** open to everyone, but used only to redirect people to the secure site and to let Let's Encrypt renew the certificate.
- **22:** my admin door (SSH). It only lets in one address, and only with my private key. No passwords.
- **8000:** where the app runs. Completely closed to the outside.

## Where encryption starts and ends

It starts in your browser and ends at Nginx on my server. Nginx unscrambles the request and passes it to the app inside the same machine (`127.0.0.1:8000`). That last step isn't encrypted, but it never leaves the server, so only someone already inside could see it. Cloudflare just acts like a phone book that points browsers to my server (it is set to DNS only); it never sees the traffic. The private key never leaves the server.

## How a visitor checks

In Chrome, click the icon next to the web address, then **Connection is secure**, then **Certificate is valid**. It should say issued to chelseahuang.me, by Let's Encrypt, expiring Jan 4, 2027. That matches what I showed from the command line.

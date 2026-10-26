# Zoho outbound header check for chelseahuang.me

This is a real message, not a simulation. I sent "Test 02: Outbound" from `chelsea@chelseahuang.me` in Zoho Mail to my LMU school mailbox (address redacted, hosted on Microsoft 365) on **2026-10-13 at 21:56 UTC** (14:56 Pacific), then copied the header from the received message. The message body is not included, and my school address is redacted (2026-10-25); every other header line is unchanged.

## Result

The receiver is Microsoft (`mx.microsoft.com`). SPF and DKIM passed for `chelseahuang.me`. DMARC came back as `bestguesspass`, not `pass`.

| Check | Receiver's verdict | Domain | What the receiver checked |
|---|---|---|---|
| SPF | pass | `chelseahuang.me` | The envelope sender (`smtp.mailfrom`, the Return-Path `chelsea@chelseahuang.me`) against the sending IP `165.173.182.52`, which is `sender5-of-o52.zoho.com` |
| DKIM | pass | `chelseahuang.me` | The signature made with selector `zmail` (`s=zmail; d=chelseahuang.me`) against the key at `zmail._domainkey.chelseahuang.me` |
| DMARC | bestguesspass | `chelseahuang.me` | The From header (`header.from=chelseahuang.me`) against the SPF and DKIM domains |

Microsoft's overall result was `compauth=pass reason=109`.

## Why DMARC says bestguesspass

`bestguesspass` is what Microsoft reports when the From domain has no DMARC record but the message would have passed if one existed. That fits the timing:

- the message was sent at 21:56:25 UTC
- the `_dmarc.chelseahuang.me` record was created in Cloudflare at 22:01:22 UTC, about five minutes later

So this header does not yet show a real DMARC pass from the receiver. A message sent after 22:01 UTC is needed for that.

Zoho's own check on the way out (`ARC-Authentication-Results: i=1; mx.zohomail.com`) lists `dmarc=pass`, but that is the sender grading itself, not the receiver's verdict.

## Alignment

DMARC needs the From header domain to match the domain that passed SPF or the domain that signed with DKIM. Here all three are the same:

- From header: `chelsea@chelseahuang.me`
- SPF domain (envelope sender): `chelseahuang.me`
- DKIM signing domain (`d=`): `chelseahuang.me`

Both SPF and DKIM are aligned, so either one alone would satisfy DMARC.

## Header lines used

Copied unchanged from the received message. Long signature values (`b=`) and Microsoft's internal anti-spam data are left out.

```
Authentication-Results: mx.microsoft.com 1; spf=pass (sender IP is
 165.173.182.52) smtp.mailfrom=chelseahuang.me; dkim=pass (signature was
 verified) header.d=chelseahuang.me;dmarc=bestguesspass action=none
 header.from=chelseahuang.me;compauth=pass reason=109
Received-SPF: Pass (protection.outlook.com: domain of chelseahuang.me
 designates 165.173.182.52 as permitted sender)
 receiver=protection.outlook.com; client-ip=165.173.182.52;
 helo=sender5-of-o52.zoho.com; pr=C
Received: from sender5-of-o52.zoho.com (165.173.182.52) by
 SJ1PEPF00002321.mail.protection.outlook.com (10.167.242.91) with Microsoft
 SMTP Server (version=TLS1_3, cipher=TLS_AES_256_GCM_SHA384) id 15.21.522.6
 via Frontend Transport; Tue, 13 Oct 2026 21:56:29 +0000
ARC-Authentication-Results: i=1; mx.zohomail.com;
    dkim=pass  header.i=chelseahuang.me;
    spf=pass  smtp.mailfrom=chelsea@chelseahuang.me;
    dmarc=pass header.from=<chelsea@chelseahuang.me>
DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/relaxed; t=1791928587;
    s=zmail; d=chelseahuang.me; i=chelsea@chelseahuang.me;
    h=Date:Date:From:From:To:To:Message-Id:Message-Id:Subject:Subject:MIME-Version:Content-Type:Reply-To:Cc;
    bh=W0k3UV0SAZY2Rj00ZWVHDSIQXkWRMW5bP07WnA0Wry0=;
Date: Tue, 13 Oct 2026 14:56:25 -0700
From: Chelsea Huang <chelsea@chelseahuang.me>
To: "[redacted]" <[redacted]@lion.lmu.edu>
Message-Id: <1a137444c3b.5173e7ea192898.5842985139682896734@chelseahuang.me>
Subject: Test 02: Outbound
Return-Path: chelsea@chelseahuang.me
X-Forefront-Antispam-Report:
 CIP:165.173.182.52;CTRY:US;LANG:en;SCL:1;SRV:;IPV:NLI;SFV:NSPM;H:sender5-of-o52.zoho.com;PTR:sender5-of-o52.zoho.com;CAT:NONE;
X-Microsoft-Antispam-Mailbox-Delivery:
    ucf:0;jmr:0;auth:0;dest:I;
```

## Where the message ended up

The header records Microsoft's verdict at delivery as not spam (`SCL:1`, `SFV:NSPM`) with the Inbox as the destination (`dest:I`). I later found the message in the Junk folder, so something moved it after delivery. The header does not show what did.

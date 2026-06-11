# CashGuard Demo — Maria's Catering

## The Scenario

Maria Chen owns Maria's Catering. Today's snapshot:

| | |
|---|---|
| Current balance | $12,400 |
| Daily net burn (slow season) | -$1,000/day |
| Payroll due | $8,000 on June 18 |
| Rent due | $4,500 on June 25 |
| Overdue invoices | $22,000 across 4 clients |

**The gap:** At -$1,000/day, Maria's balance on June 18 = $12,400 - (7 × $1,000) = $5,400. After payroll: $5,400 - $8,000 = **-$2,600 shortfall.** She can't make payroll. She doesn't know this yet.

---

## The 4 Clients

| Client | Invoice | Amount | Days Overdue | Score | Final Tone |
|---|---|---|---|---|---|
| Acme Corp | INV-001 | $4,500 | 14 | 72 | firm |
| Sunrise Hotel | INV-002 | $8,000 | 31 | 38 | serious |
| Bay Area Events | INV-003 | $3,200 | 7 | 88 | warm |
| TechCorp | INV-004 | $6,300 | 22 | 45 | serious |

CashGuard identifies that collecting **INV-002 ($8,000)** alone closes the $2,600 gap and marks it `gap_linked: true`.

---

## 3-Minute Demo Script

**0:00 — Open the dashboard**
Show the metric cards: $12,400 balance, gap date June 18, gap amount $2,600. The 60-day chart is blue for 6 days then turns red.

> "Maria has $12,400 in the bank and thinks she's fine. CashGuard knows she'll miss payroll in 7 days."

**0:30 — Click ▶ Run Pipeline**
The 6-agent LangGraph pipeline fires:
1. Fivetran syncs latest data from QuickBooks
2. Invoice monitor opens a CollectionsCase for each overdue invoice
3. Relationship analyzer scores each client, sets tone
4. Cash flow forecaster builds the 60-day projection, flags gap-linked invoices
5. Gemini drafts a custom email for each case
6. Escalation agent checks for repeat failures

**1:15 — Switch to Collections tab**
Show the 4 cases sorted by urgency. Sunrise Hotel (INV-002) is highlighted as gap-linked and critical.

> "These two emails, if collected, close the gap entirely."

**1:45 — Expand an email draft**
Show the warm email for Bay Area Events vs. the serious final-notice for Sunrise Hotel.

> "Gemini writes a completely different email based on 3 years of relationship history vs. a client who's been late 8 times."

**2:15 — Approvals tab**
Click **Approve** on Sunrise Hotel → SendGrid sends the email instantly.

> "One click. Email sent. Maria didn't write a word."

**2:45 — Fivetran callout**
> "In production, the first agent triggers a Fivetran sync from QuickBooks before every pipeline run — always fresh data, never stale."

---

## Seeding the Demo Data

```bash
source venv/bin/activate
python -m seed.maria_catering
```

Then run the pipeline:
```bash
curl -X POST https://YOUR-URL.run.app/api/pipeline/run
```

Or click **▶ Run Pipeline** in the dashboard.

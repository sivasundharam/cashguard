# CashGuard — AI-Powered SMB Cash Flow & Invoice Collections Agent

> Connect your financial data, predict cash shortages 60 days out, and automatically collect overdue invoices — with the right tone, at the right time — before the crisis hits.

Built for the **Google Cloud Rapid Agent Hackathon** · **Fivetran Track**

---

## The Problem

82% of small businesses that fail cite cash flow problems as the primary cause — not lack of revenue, but the inability to *see* the crisis coming and *act* on it. Existing tools show dashboards. **CashGuard acts.**

---

## End-to-End Architecture

```mermaid
flowchart LR
    QBO["QuickBooks"] -->|sync| FT["Fivetran"] -->|write| DB[("MongoDB")]

    DB -->|read| N1["fivetran_sync"]
    N1 --> N2["invoice_monitor"]
    N2 --> N3["relationship_analyzer"]
    N3 --> N4["cashflow_forecaster"]
    N4 --> N5["communication_agent"]
    N5 --> N6["escalation_agent"]
    N6 -->|write| DB

    DB -->|read| API["FastAPI"]
    API <-->|REST| UI["React UI"]
    API -->|send| SG["SendGrid"]
```

---

## Agent Pipeline — What Each Agent Does

```mermaid
sequenceDiagram
    participant C as Client (Browser)
    participant API as FastAPI
    participant LG as LangGraph
    participant FT as Fivetran
    participant MDB as MongoDB
    participant GEM as Gemini
    participant SG as SendGrid

    C->>API: POST /api/pipeline/run
    API->>LG: ainvoke(initial_state)

    LG->>FT: trigger_sync(connector_id)
    FT-->>LG: sync_status

    LG->>MDB: find overdue invoices
    MDB-->>LG: invoices[]
    LG->>MDB: insert CollectionsCase per invoice

    LG->>MDB: find cases (status=new)
    LG->>MDB: find client_profiles
    MDB-->>LG: score + tone_recommendation
    LG->>MDB: update case tone + status=analyzing

    LG->>MDB: compute 60-day projection
    LG->>MDB: mark gap_linked cases critical

    LG->>MDB: find cases (status=analyzing)
    LG->>GEM: generate email (tone + facts)
    GEM-->>LG: email draft
    LG->>MDB: save draft, status=draft_ready

    LG->>MDB: find cases (attempts >= 3)
    LG->>GEM: choose escalation action
    GEM-->>LG: recommendation
    LG->>MDB: update status=escalated

    LG-->>API: final CashGuardState
    API-->>C: pipeline result JSON

    Note over C,API: Human reviews drafts in UI
    C->>API: POST /api/approvals/{id}/approve
    API->>SG: send_email(to, subject, body)
    SG-->>C: email delivered
```

---

## Tone Calculation

Email tone is determined by two factors: **relationship score** (0–100) from the client profile, and **urgency** (derived from days overdue). The relationship analyzer applies these rules in order:

```mermaid
flowchart TD
    START(["New Case"]) --> Q1{"Score >= 80?"}
    Q1 -->|Yes| Q2{"Critical urgency?"}
    Q1 -->|No| Q3{"Score < 50?"}
    Q2 -->|No| WARM["warm"]
    Q2 -->|Yes| FIRM["firm"]
    Q3 -->|Yes| SERIOUS["serious"]
    Q3 -->|No| FIRM2["firm"]
```

**Urgency** is set by the invoice monitor based on days overdue:

| Days Overdue | Urgency |
|---|---|
| 1 – 7 | low |
| 8 – 14 | medium |
| 15 – 30 | high |
| 30+ | **critical** |

**Gap linking** overrides urgency: if the cash flow forecaster identifies an invoice as needed to close a payroll/rent gap, that case is immediately promoted to `urgency: critical` and `gap_linked: true` — regardless of its age.

Gemini then receives the tone as an instruction alongside exact invoice facts (amount, days overdue, client tenure, payment history) and writes a fully-formed email with no placeholders.

---

## Data Model

```mermaid
erDiagram
    invoices {
        string invoice_id PK
        string client_id FK
        string client_name
        float amount
        string status
        int days_overdue
        date due_date
    }
    client_profiles {
        string client_id PK
        string client_name
        int relationship_score
        string tone_recommendation
        int relationship_tenure_months
        int late_payment_count
        int total_invoices
        string contact_email
    }
    collections_cases {
        string case_id PK
        string invoice_id FK
        string client_id FK
        float invoice_amount
        string status
        string urgency
        string tone
        int outreach_attempts
        string email_draft
        bool gap_linked
        string overdue_bucket
    }
    forecast_snapshots {
        string snapshot_date PK
        float current_balance
        array daily_forecast
        array gap_dates
        float gap_amount
        array linked_invoices
    }

    invoices ||--|| collections_cases : "triggers"
    client_profiles ||--o{ collections_cases : "informs tone"
    invoices ||--o{ forecast_snapshots : "linked_invoices"
```

---

## Collections Case Lifecycle

```mermaid
stateDiagram-v2
    [*] --> new : invoice_monitor creates case
    new --> analyzing : relationship_analyzer sets tone
    analyzing --> draft_ready : communication_agent generates email
    draft_ready --> sent : Human approves → SendGrid delivers
    draft_ready --> rejected : Human rejects draft
    sent --> escalated : 3+ failed outreach attempts
    escalated --> sent : Escalation email approved
```

---

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph 1.2.4 (StateGraph) |
| API | FastAPI + Uvicorn |
| Database | MongoDB Atlas (Motor async driver) |
| LLM | Google Gemini (`gemini-flash-latest`) |
| Email | SendGrid |
| Data sync | Fivetran REST API |
| Frontend | React 18 + Vite 5 + Chart.js 4 |
| Containerisation | Docker (multi-stage: Node 20 → Python 3.11) |
| Hosting | Google Cloud Run |

---

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | MongoDB connection check |
| POST | `/api/pipeline/run` | Run full 6-agent LangGraph pipeline |
| GET | `/api/forecast/latest` | Latest 60-day cash forecast snapshot |
| POST | `/api/forecast/run` | Re-run cash flow forecaster only |
| GET | `/api/invoices` | All invoices |
| GET | `/api/invoices/overdue` | Overdue invoices only |
| GET | `/api/invoices/{id}` | Single invoice |
| GET | `/api/cases` | All collections cases |
| PATCH | `/api/cases/{id}/status` | Update case status |
| GET | `/api/approvals/pending` | Cases with drafted emails awaiting approval |
| POST | `/api/approvals/{id}/approve` | Approve and send email via SendGrid |
| POST | `/api/approvals/{id}/reject` | Reject draft |
| GET | `/api/connectors` | List Fivetran connectors |
| POST | `/api/connectors/{id}/sync` | Trigger Fivetran sync |
| GET | `/api/connectors/{id}/status` | Check sync status |

---

## Quick Start

```bash
git clone https://github.com/sivasundharam/cashguard.git
cd cashguard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys
python -m seed.maria_catering # seed demo data
uvicorn app.main:app --port 8000 --reload
# frontend dev server (separate terminal):
cd frontend && npm install && npm run dev
```

See [DEMO.md](DEMO.md) for the full demo walkthrough.

---

## Deploy to Cloud Run

The repo includes a `cloudbuild.yaml`. Connect it to Cloud Run continuous deployment via the GCP Console, or deploy manually:

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/cashguard
gcloud run deploy cashguard \
  --image gcr.io/$PROJECT_ID/cashguard \
  --platform managed \
  --region us-east5 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URI=... \
  --set-env-vars GEMINI_API_KEY=... \
  --set-env-vars SENDGRID_API_KEY=... \
  --set-env-vars SENDGRID_FROM_EMAIL=...
```

---

## License

MIT © 2026

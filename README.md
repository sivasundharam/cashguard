# CashGuard — AI-Powered SMB Cash Flow & Invoice Collections Agent

> Connect your financial data, predict cash shortages 60 days out, and automatically collect overdue invoices — with the right tone, at the right time — before the crisis hits.

Built for the **Google Cloud Rapid Agent Hackathon** · **Fivetran Track**

---

## The Problem

82% of small businesses that fail cite cash flow problems as the primary cause — not lack of revenue, but the inability to *see* the crisis coming and *act* on it. Existing tools show dashboards. **CashGuard acts.**

---

## End-to-End Architecture

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 1000}}}%%
flowchart TD
    subgraph Data["Data Layer"]
        QBO["QuickBooks / Google Sheets"]
        FT["Fivetran Connector"]
        MONGO[("MongoDB Atlas")]
        QBO -->|sync| FT -->|write| MONGO
    end

    subgraph Pipeline["LangGraph Orchestrator — 6 Agents"]
        A1["fivetran_sync<br/>Trigger fresh data pull"]
        A2["invoice_monitor<br/>Scan overdue invoices<br/>Open CollectionsCases"]
        A3["relationship_analyzer<br/>Score client relationship<br/>Set email tone"]
        A4["cashflow_forecaster<br/>60-day balance projection<br/>Detect gap dates"]
        A5["communication_agent<br/>Gemini drafts emails<br/>per tone + invoice facts"]
        A6["escalation_agent<br/>Payment plans or<br/>Demand letters after 3 failures"]
        A1 --> A2 --> A3 --> A4 --> A5 --> A6
    end

    subgraph Serving["Serving Layer"]
        API["FastAPI"]
        UI["React Dashboard<br/>Chart.js · Vite"]
        SG["SendGrid<br/>Email delivery"]
        API <-->|REST| UI
        API -->|approve| SG
    end

    MONGO -->|read| Pipeline
    Pipeline -->|write| MONGO
    MONGO -->|read| API
```

---

## Agent Pipeline

```mermaid
sequenceDiagram
    participant C as Browser
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
    C->>API: POST /api/approvals/id/approve
    API->>SG: send_email(to, subject, body)
    SG-->>C: email delivered
```

---

## Tone Calculation

Email tone is determined by **relationship score** (0–100) from the client profile and **urgency** from days overdue. Rules applied in order:

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 1000}}}%%
flowchart TD
    START(["Case enters relationship_analyzer"])
    Q1{"Score >= 80?"}
    Q2{"Urgency == critical?"}
    Q3{"Score < 50?"}
    WARM["Tone = warm<br/>Long-term client,<br/>assume oversight"]
    FIRM["Tone = firm<br/>Professional, direct,<br/>clear payment request"]
    SERIOUS["Tone = serious<br/>Final notice,<br/>consequences stated"]

    START --> Q1
    Q1 -->|Yes| Q2
    Q2 -->|No| WARM
    Q2 -->|Yes| FIRM
    Q1 -->|No| Q3
    Q3 -->|Yes| SERIOUS
    Q3 -->|No| FIRM
```

**Urgency** from days overdue:

| Days Overdue | Urgency |
|---|---|
| 1 – 7 | low |
| 8 – 14 | medium |
| 15 – 30 | high |
| 30+ | **critical** |

**Gap-linked override:** If the cash flow forecaster flags an invoice as needed to close a payroll/rent shortfall, that case is immediately promoted to `critical` regardless of age.

---

## Collections Case Lifecycle

```mermaid
stateDiagram-v2
    [*] --> new : invoice_monitor opens case
    new --> analyzing : relationship_analyzer sets tone
    analyzing --> draft_ready : communication_agent writes email
    draft_ready --> sent : Human approves in dashboard
    draft_ready --> rejected : Human rejects draft
    sent --> escalated : 3+ outreach attempts failed
    escalated --> sent : Escalation email approved
```

---

## Data Model

```mermaid
erDiagram
    invoices {
        string invoice_id PK
        string client_id FK
        float amount
        string status
        int days_overdue
    }
    client_profiles {
        string client_id PK
        int relationship_score
        string tone_recommendation
        int tenure_months
        string contact_email
    }
    collections_cases {
        string case_id PK
        string invoice_id FK
        string client_id FK
        string status
        string urgency
        string tone
        bool gap_linked
        string email_draft
    }
    forecast_snapshots {
        string snapshot_date PK
        float current_balance
        float gap_amount
        array gap_dates
        array linked_invoices
    }

    invoices ||--|| collections_cases : "triggers"
    client_profiles ||--o{ collections_cases : "sets tone"
    invoices ||--o{ forecast_snapshots : "linked"
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

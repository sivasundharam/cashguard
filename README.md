# CashGuard — AI-Powered SMB Cash Flow & Invoice Collections Agent

> Connect your financial data, predict cash shortages 60 days out, and automatically collect overdue invoices — with the right tone, at the right time — before the crisis hits.

Built for the **Google Cloud Rapid Agent Hackathon** · **Fivetran Track**

---

## The Problem

82% of small businesses that fail cite cash flow problems as the primary cause — not lack of revenue, but the inability to *see* the crisis coming and *act* on it. Existing tools show dashboards. **CashGuard acts.**

---

## End-to-End Architecture

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 400}}}%%
flowchart LR
    QBO["QuickBooks\nGoogle Sheets"]
    FT["Fivetran\nConnector"]
    DB[("MongoDB\nAtlas")]
    PIPE["LangGraph\nOrchestrator\n6 Agents"]
    API["FastAPI"]
    UI["React\nDashboard"]
    SG["SendGrid"]

    QBO -->|sync| FT -->|write| DB
    DB -->|read| PIPE
    PIPE -->|write| DB
    DB -->|read| API
    API -->|REST| UI
    API -->|email| SG
```

---

## Agent Pipeline

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 400}}}%%
flowchart LR
    A["fivetran_sync\nTrigger data pull"]
    B["invoice_monitor\nOpen CollectionsCases"]
    C["relationship_analyzer\nScore client, set tone"]
    D["cashflow_forecaster\n60-day projection\nDetect gap dates"]
    E["communication_agent\nGemini drafts email\nper tone + facts"]
    F["escalation_agent\nPayment plans after\n3 failed attempts"]

    A --> B --> C --> D --> E --> F
```

---

## Tone Calculation

Email tone is determined by **relationship score** (0–100) from the client profile and **urgency** from days overdue. Rules applied in order:

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 400}}}%%
flowchart TD
    START(["New Case"])

    Q1{"Relationship\nScore >= 80?"}
    Q2{"Urgency ==\ncritical?"}
    Q3{"Relationship\nScore < 50?"}

    WARM["WARM\nLong-term client,\nassume oversight"]
    FIRM1["FIRM\nProfessional,\ndirect request"]
    FIRM2["FIRM\nProfessional,\ndirect request"]
    SERIOUS["SERIOUS\nFinal notice,\nstate consequences"]

    START --> Q1
    Q1 -->|Yes| Q2
    Q1 -->|No| Q3
    Q2 -->|No - keep warm| WARM
    Q2 -->|Yes - override| FIRM1
    Q3 -->|Yes| SERIOUS
    Q3 -->|No| FIRM2
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

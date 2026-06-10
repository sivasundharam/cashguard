# CashGuard — AI-Powered SMB Cash Flow & Invoice Collections Agent

> "CashGuard connects your QuickBooks and bank data, predicts cash shortages 60 days out, and automatically collects your overdue invoices — with the right tone, at the right time — before the crisis hits."

Built for the **Google Cloud Rapid Agent Hackathon** · **Fivetran Track**

---

## The Problem

82% of small businesses that fail cite cash flow problems as the primary cause — not lack of revenue, but the inability to *see* the crisis coming and *act* on it. Existing tools show dashboards. **CashGuard acts.**

## Demo Scenario — Maria's Catering

| | |
|---|---|
| Current balance | $12,400 |
| Payroll due Jun 18 | $8,000 |
| Rent due Jun 25 | $4,500 |
| Overdue invoices | $22,000 across 4 clients |

**Gap detected:** On June 18, projected balance = $2,400 — insufficient for $8,000 payroll → shortfall $5,600.

CashGuard automatically identifies that collecting from **Acme Corp** ($4,500) and **Bay Area Events** ($3,200) closes the gap, drafts context-aware emails with the correct tone for each relationship, and queues them for one-click approval.

---

## Architecture

```
Fivetran MCP (Google Sheets → MongoDB)
         ↓
  LangGraph Orchestrator
  ├── fivetran_sync      — triggers fresh data sync
  ├── invoice_monitor    — scans overdue invoices, opens CollectionsCases
  ├── relationship_analyzer — scores client relationship, sets tone
  ├── cashflow_forecaster — 60-day projection, detects gap dates
  ├── communication_agent — Gemini drafts context-aware emails
  └── escalation_agent   — payment plans / demand letters after 3 failures
         ↓
  FastAPI  ←→  React Dashboard
```

**Stack:** FastAPI · LangGraph · MongoDB Atlas · Gemini (google-generativeai) · SendGrid · Stripe · Fivetran MCP · React · Chart.js

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/cashguard.git
cd cashguard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your keys (see .env.example)
```

### 3. Seed demo data

```bash
python -m seed.maria_catering
```

### 4. Start the API

```bash
uvicorn app.main:app --port 8000 --reload
```

### 5. Start the dashboard (dev)

```bash
cd frontend && npm install && npm run dev
# Open http://localhost:5173
```

### 6. Run the full agent pipeline

```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

Or click **▶ Run Pipeline** in the dashboard.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | MongoDB connection check |
| POST | `/api/pipeline/run` | Run full LangGraph pipeline |
| GET | `/api/forecast/latest` | Latest 60-day cash forecast |
| POST | `/api/forecast/run` | Re-run cash flow forecaster |
| GET | `/api/invoices/overdue` | All overdue invoices |
| GET | `/api/cases` | All collections cases |
| GET | `/api/approvals/pending` | Cases awaiting approval |
| POST | `/api/approvals/{id}/approve` | Approve & send email via SendGrid |
| POST | `/api/approvals/{id}/reject` | Skip / reject draft |
| GET | `/api/connectors` | List Fivetran connectors |
| POST | `/api/connectors/{id}/sync` | Trigger Fivetran sync |
| GET | `/api/connectors/{id}/status` | Check sync status |

---

## MongoDB Collections

| Collection | Purpose |
|---|---|
| `invoices` | Raw invoice data synced by Fivetran |
| `client_profiles` | Relationship scores, tone recommendations |
| `collections_cases` | One case per overdue invoice, tracks full lifecycle |
| `forecast_snapshots` | 60-day balance projections with gap flags |

---

## Fivetran Integration

CashGuard uses Fivetran to sync financial data from QuickBooks (demo: Google Sheets) into MongoDB Atlas before each pipeline run. Set `FIVETRAN_CONNECTOR_ID` in `.env` to enable live sync. Without it, the pipeline runs on pre-seeded demo data.

The `fivetran_sync` node is the first node in the LangGraph graph — it triggers a connector sync so agents always work on fresh data.

---

## Deploy to Cloud Run

```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/cashguard
gcloud run deploy cashguard \
  --image gcr.io/$PROJECT_ID/cashguard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URI=... \
  --set-env-vars GEMINI_API_KEY=... \
  --set-env-vars SENDGRID_API_KEY=... \
  --set-env-vars SENDGRID_FROM_EMAIL=... \
  --set-env-vars FIVETRAN_API_KEY=... \
  --set-env-vars FIVETRAN_API_SECRET=...
```

---

## License

MIT © 2026

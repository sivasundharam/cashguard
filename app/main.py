import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.approvals import router as approvals_router
from app.api.cases import router as cases_router
from app.api.forecast import router as forecast_router
from app.api.invoices import router as invoices_router

load_dotenv()

app = FastAPI(
    title="CashGuard",
    version="1.0.0",
    description="AI-powered SMB cash flow management and invoice collections agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(invoices_router)
app.include_router(cases_router)
app.include_router(forecast_router)
app.include_router(approvals_router)


@app.get("/api/health")
async def health():
    from app.services.mongodb import get_db
    await get_db().command("ping")
    return {"status": "healthy", "mongodb": "connected"}


@app.post("/api/pipeline/run")
async def run_pipeline():
    from app.agents.orchestrator import run_full_pipeline
    result = await run_full_pipeline()
    # Strip non-serialisable datetime objects from forecast before returning
    if result.get("forecast"):
        result["forecast"].pop("created_at", None)
    return result


@app.get("/api/connectors")
async def list_connectors():
    from app.services.fivetran import list_connectors
    return await list_connectors()


@app.post("/api/connectors/{connector_id}/sync")
async def trigger_fivetran_sync(connector_id: str):
    from app.services.fivetran import trigger_sync
    return await trigger_sync(connector_id)


@app.get("/api/connectors/{connector_id}/status")
async def fivetran_sync_status(connector_id: str):
    from app.services.fivetran import get_sync_status
    return await get_sync_status(connector_id)


# Serve built React frontend — must come last so API routes take priority
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")

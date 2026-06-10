from fastapi import APIRouter

from app.agents.cashflow_forecaster import run_cashflow_forecaster
from app.services.mongodb import forecast_snapshots_col

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("/latest")
async def get_latest_forecast():
    snapshot = await forecast_snapshots_col().find_one(
        {}, {"_id": 0}, sort=[("snapshot_date", -1)]
    )
    return snapshot or {}


@router.post("/run")
async def trigger_forecast():
    result = await run_cashflow_forecaster()
    result.pop("_id", None)
    return result

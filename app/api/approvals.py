from datetime import datetime

from fastapi import APIRouter

from app.services.mongodb import collections_cases_col

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending")
async def pending_approvals():
    return await collections_cases_col().find(
        {"status": {"$in": ["draft_ready", "escalated"]}}, {"_id": 0}
    ).to_list(None)


@router.post("/{case_id}/approve")
async def approve(case_id: str):
    from app.agents.communication_agent import run_communication_agent

    await run_communication_agent(case_id=case_id, auto_send=True)
    return {"approved": True, "case_id": case_id}


@router.post("/{case_id}/reject")
async def reject(case_id: str):
    await collections_cases_col().update_one(
        {"case_id": case_id},
        {"$set": {"status": "rejected", "updated_at": datetime.utcnow()}},
    )
    return {"rejected": True, "case_id": case_id}

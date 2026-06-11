from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.services.mongodb import collections_cases_col

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("")
async def list_cases():
    return (
        await collections_cases_col()
        .find({}, {"_id": 0})
        .sort("updated_at", -1)
        .to_list(None)
    )


@router.get("/{case_id}")
async def get_case(case_id: str):
    case = await collections_cases_col().find_one({"case_id": case_id}, {"_id": 0})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}/approve")
async def approve_email(case_id: str):
    from app.agents.communication_agent import run_communication_agent

    await run_communication_agent(case_id=case_id, auto_send=True)
    return {"status": "sent", "case_id": case_id}


@router.patch("/{case_id}/status")
async def update_status(case_id: str, status: str):
    await collections_cases_col().update_one(
        {"case_id": case_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}},
    )
    return {"case_id": case_id, "status": status}

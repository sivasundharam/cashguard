import uuid
from datetime import datetime, timedelta
from typing import List

from app.services.mongodb import collections_cases_col, invoices_col


def _classify_bucket(days: int) -> str:
    if days <= 7:
        return "1-7"
    elif days <= 14:
        return "8-14"
    elif days <= 30:
        return "15-30"
    return "30+"


def _bucket_urgency(days: int) -> str:
    if days > 30:
        return "critical"
    elif days > 14:
        return "high"
    elif days > 7:
        return "medium"
    return "low"


async def run_invoice_monitor() -> List[dict]:
    """Scan overdue invoices and open a CollectionsCase for each new one."""
    overdue = await invoices_col().find({"status": "overdue"}).to_list(None)

    created: List[dict] = []
    for inv in overdue:
        if await collections_cases_col().find_one({"invoice_id": inv["invoice_id"]}):
            continue  # case already exists

        days = inv.get("days_overdue", 0)
        case = {
            "case_id": f"CASE-{uuid.uuid4().hex[:6].upper()}",
            "invoice_id": inv["invoice_id"],
            "client_id": inv["client_id"],
            "client_name": inv["client_name"],
            "invoice_amount": inv["amount"],
            "status": "new",
            "urgency": _bucket_urgency(days),
            "tone": "firm",
            "outreach_attempts": 0,
            "last_contact_date": None,
            "next_action_date": datetime.utcnow() + timedelta(days=1),
            "email_draft": None,
            "gap_linked": False,
            "overdue_bucket": _classify_bucket(days),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await collections_cases_col().insert_one(case)
        case.pop("_id", None)
        created.append(case)

    return created

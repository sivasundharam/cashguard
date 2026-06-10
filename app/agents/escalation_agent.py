from datetime import datetime, timedelta
from typing import List

from app.services.gemini import generate_text
from app.services.mongodb import client_profiles_col, collections_cases_col, invoices_col


def _parse_response(text: str) -> tuple[str, str, str]:
    action, reason, draft = "payment_plan", "", ""
    lines = text.strip().split("\n")
    for i, line in enumerate(lines):
        if line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip().lower().replace(" ", "_")
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()
        elif line.startswith("DRAFT:"):
            draft = "\n".join(lines[i:]).replace("DRAFT:", "", 1).strip()
            break
    return action, reason, draft


async def run_escalation_agent(case_id: str | None = None) -> List[dict]:
    """Escalate cases that have had 3+ failed outreach attempts."""
    query: dict = {
        "outreach_attempts": {"$gte": 3},
        "status": {"$in": ["sent", "draft_ready"]},
    }
    if case_id:
        query["case_id"] = case_id

    cases = await collections_cases_col().find(query, {"_id": 0}).to_list(None)
    escalated: List[dict] = []

    for case in cases:
        inv = await invoices_col().find_one({"invoice_id": case["invoice_id"]})
        profile = await client_profiles_col().find_one({"client_id": case["client_id"]})
        if not inv or not profile:
            continue

        prompt = f"""Collections case stalled after {case['outreach_attempts']} unanswered emails.

Client: {profile['client_name']}
Amount: ${inv['amount']:,.2f}
Days overdue: {inv['days_overdue']}
Relationship score: {profile.get('relationship_score', 50)}/100
Tenure: {profile['relationship_tenure_months']} months

Choose ONE escalation path:
1. payment_plan — structured payment plan offer
2. demand_letter — formal legal demand
3. collections_agency — refer to external collections

Respond exactly in this format:
ACTION: <one of the three options>
REASON: <2-sentence justification>
DRAFT: <brief draft of the escalation communication>"""

        action, reason, draft = _parse_response(generate_text(prompt))

        await collections_cases_col().update_one(
            {"case_id": case["case_id"]},
            {
                "$set": {
                    "status": "escalated",
                    "escalation_action": action,
                    "escalation_reason": reason,
                    "escalation_draft": draft,
                    "updated_at": datetime.utcnow(),
                    "next_action_date": datetime.utcnow() + timedelta(days=2),
                }
            },
        )
        case.pop("_id", None)
        escalated.append({**case, "escalation_action": action})

    return escalated

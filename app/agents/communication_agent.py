from datetime import datetime, timedelta
from typing import List

from app.services.gemini import generate_email
from app.services.mongodb import client_profiles_col, collections_cases_col, invoices_col
from app.services.sendgrid_client import send_email

_TONE_DESC = {
    "warm": "warm and friendly — assume this is an oversight, acknowledge the long relationship",
    "firm": "professional and direct — clearly state the overdue amount and request prompt payment",
    "serious": "serious and firm — this is a final notice; state consequences if unpaid in 5 business days",
}


def _email_prompt(inv: dict, profile: dict, case: dict) -> str:
    return f"""You are writing a collections email for Maria's Catering, a small business.
Tone: {_TONE_DESC.get(case['tone'], 'professional')}

Facts (use these exactly — no placeholders):
- From: Maria Chen, Owner, Maria's Catering
- To: {profile['client_name']} accounts payable
- Invoice #: {inv['invoice_id']}
- Amount due: ${inv['amount']:,.2f}
- Days overdue: {inv['days_overdue']}
- Client relationship: {profile['relationship_tenure_months']} months
- Payment history: {profile['late_payment_count']} late payments out of {profile['total_invoices']} invoices

Output format (no extra commentary):
Subject: <subject line>

<email body, max 180 words, signed as Maria Chen>"""


async def run_communication_agent(
    case_id: str | None = None, auto_send: bool = False
) -> List[dict]:
    """Draft (or send) collections emails for cases in 'analyzing' status."""
    query = {"status": "analyzing"} if case_id is None else {"case_id": case_id}
    cases = await collections_cases_col().find(query, {"_id": 0}).to_list(None)

    drafted: List[dict] = []
    for case in cases:
        inv = await invoices_col().find_one({"invoice_id": case["invoice_id"]})
        profile = await client_profiles_col().find_one({"client_id": case["client_id"]})
        if not inv or not profile:
            continue

        # Reuse existing draft on approve — only call Gemini if no draft yet
        draft = case.get("email_draft") or generate_email(_email_prompt(inv, profile, case))
        new_status = "sent" if auto_send else "draft_ready"

        update: dict = {
            "email_draft": draft,
            "status": new_status,
            "updated_at": datetime.utcnow(),
            "next_action_date": datetime.utcnow() + timedelta(days=3),
        }

        if auto_send:
            lines = draft.strip().split("\n")
            subject = lines[0].replace("Subject:", "").strip()
            body = "\n".join(lines[2:]).strip()
            send_email(profile["contact_email"], subject, body)
            update["outreach_attempts"] = case.get("outreach_attempts", 0) + 1
            update["last_contact_date"] = datetime.utcnow()

        await collections_cases_col().update_one({"case_id": case["case_id"]}, {"$set": update})
        drafted.append({**case, **update})

    return drafted

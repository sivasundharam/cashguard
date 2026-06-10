from datetime import datetime
from typing import List

from app.services.mongodb import client_profiles_col, collections_cases_col


async def run_relationship_analyzer(case_id: str | None = None) -> List[dict]:
    """Read client profiles and write tone + relationship_score onto new cases."""
    query = {"status": "new"} if case_id is None else {"case_id": case_id}
    cases = await collections_cases_col().find(query, {"_id": 0}).to_list(None)

    updated: List[dict] = []
    for case in cases:
        profile = await client_profiles_col().find_one({"client_id": case["client_id"]})
        if not profile:
            continue

        score: int = profile.get("relationship_score", 50)
        tone: str = profile.get("tone_recommendation", "firm")

        # Loyalty override: high-score clients get warmth unless critically overdue
        if score >= 80 and case["urgency"] != "critical":
            tone = "warm"
        elif score < 50:
            tone = "serious"

        await collections_cases_col().update_one(
            {"case_id": case["case_id"]},
            {
                "$set": {
                    "tone": tone,
                    "status": "analyzing",
                    "relationship_score": score,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        updated.append({**case, "tone": tone, "status": "analyzing"})

    return updated

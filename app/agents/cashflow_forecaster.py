from datetime import datetime, timedelta
from typing import List

from app.services.mongodb import collections_cases_col, forecast_snapshots_col, invoices_col

# Maria's Catering financials (demo constants)
CURRENT_BALANCE = 12_400.0
DAILY_NET_BURN = -1_000.0   # slow season: income ~$500, expenses ~$1,500
PAYROLL_DATE = "2026-06-18"
PAYROLL_AMOUNT = 8_000.0
RENT_DATE = "2026-06-25"
RENT_AMOUNT = 4_500.0


async def run_cashflow_forecaster() -> dict:
    """
    Project 60-day cash position, detect gap dates, and link overdue invoices
    that would close the first gap. Bumps urgency on those cases to 'critical'.

    Gap story: $12,400 balance - $1,000/day burn = $2,400 on June 18 (before payroll).
    Payroll hits → balance -$5,600. Agent flags Acme ($4,500) + Bay Area ($3,200)
    to close the $5,600 shortfall.
    """
    today = datetime.utcnow()
    payroll_dt = datetime.strptime(PAYROLL_DATE, "%Y-%m-%d")
    rent_dt = datetime.strptime(RENT_DATE, "%Y-%m-%d")

    balance = CURRENT_BALANCE
    daily_forecast: List[dict] = []
    gap_dates: List[str] = []

    for i in range(60):
        day = today + timedelta(days=i + 1)
        date_str = day.strftime("%Y-%m-%d")
        balance += DAILY_NET_BURN

        if day.date() == payroll_dt.date():
            balance -= PAYROLL_AMOUNT
        if day.date() == rent_dt.date():
            balance -= RENT_AMOUNT

        is_gap = balance < 0
        if is_gap:
            gap_dates.append(date_str)

        daily_forecast.append(
            {"date": date_str, "projected_balance": round(balance, 2), "gap": is_gap}
        )

    first_gap = next((e for e in daily_forecast if e["gap"]), None)
    gap_amount = abs(first_gap["projected_balance"]) if first_gap else 0.0

    linked_invoices: List[str] = []
    if gap_dates:
        overdue = await invoices_col().find(
            {"status": "overdue"}, sort=[("amount", -1)]
        ).to_list(None)
        collected = 0.0
        for inv in overdue:
            if collected >= gap_amount:
                break
            linked_invoices.append(inv["invoice_id"])
            collected += inv["amount"]

    if linked_invoices:
        await collections_cases_col().update_many(
            {"invoice_id": {"$in": linked_invoices}},
            {"$set": {"gap_linked": True, "urgency": "critical", "updated_at": today}},
        )

    snapshot = {
        "snapshot_date": today.strftime("%Y-%m-%d"),
        "current_balance": CURRENT_BALANCE,
        "daily_forecast": daily_forecast,
        "gap_dates": gap_dates,
        "gap_amount": round(gap_amount, 2),
        "linked_invoices": linked_invoices,
        "created_at": today,
    }

    await forecast_snapshots_col().replace_one(
        {"snapshot_date": snapshot["snapshot_date"]}, snapshot, upsert=True
    )
    snapshot.pop("_id", None)  # pymongo adds _id in-place on upsert

    return snapshot

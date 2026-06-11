"""Seed Maria's Catering demo data into MongoDB Atlas.

Run: python -m seed.maria_catering
"""
import asyncio
import os
from datetime import datetime, timedelta

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

TODAY = datetime.utcnow()

CLIENTS = [
    {
        "client_id": "client_001",
        "client_name": "Acme Corp",
        "contact_email": "accounts@acmecorp.com",
        "relationship_tenure_months": 24,
        "total_invoices": 18,
        "late_payment_count": 2,
        "avg_days_to_pay": 32.0,
        "tone_recommendation": "firm",
        "relationship_score": 72,
    },
    {
        "client_id": "client_002",
        "client_name": "Sunrise Hotel",
        "contact_email": "sivasundharam123@gmail.com",
        "relationship_tenure_months": 3,
        "total_invoices": 2,
        "late_payment_count": 1,
        "avg_days_to_pay": 45.0,
        "tone_recommendation": "serious",
        "relationship_score": 38,
    },
    {
        "client_id": "client_003",
        "client_name": "Bay Area Events",
        "contact_email": "ap@bayareaevents.com",
        "relationship_tenure_months": 36,
        "total_invoices": 24,
        "late_payment_count": 1,
        "avg_days_to_pay": 22.0,
        "tone_recommendation": "warm",
        "relationship_score": 88,
    },
    {
        "client_id": "client_004",
        "client_name": "TechCorp Catering",
        "contact_email": "billing@techcorpcatering.com",
        "relationship_tenure_months": 12,
        "total_invoices": 10,
        "late_payment_count": 4,
        "avg_days_to_pay": 38.0,
        "tone_recommendation": "serious",
        "relationship_score": 45,
    },
]

INVOICES = [
    {
        "invoice_id": "INV-001",
        "client_id": "client_001",
        "client_name": "Acme Corp",
        "amount": 4500.00,
        "due_date": TODAY - timedelta(days=14),
        "status": "overdue",
        "days_overdue": 14,
        "source": "google_sheets",
        "synced_at": TODAY,
    },
    {
        "invoice_id": "INV-002",
        "client_id": "client_002",
        "client_name": "Sunrise Hotel",
        "amount": 8000.00,
        "due_date": TODAY - timedelta(days=31),
        "status": "overdue",
        "days_overdue": 31,
        "source": "google_sheets",
        "synced_at": TODAY,
    },
    {
        "invoice_id": "INV-003",
        "client_id": "client_003",
        "client_name": "Bay Area Events",
        "amount": 3200.00,
        "due_date": TODAY - timedelta(days=7),
        "status": "overdue",
        "days_overdue": 7,
        "source": "google_sheets",
        "synced_at": TODAY,
    },
    {
        "invoice_id": "INV-004",
        "client_id": "client_004",
        "client_name": "TechCorp Catering",
        "amount": 6300.00,
        "due_date": TODAY - timedelta(days=22),
        "status": "overdue",
        "days_overdue": 22,
        "source": "google_sheets",
        "synced_at": TODAY,
    },
]


def _build_forecast() -> dict:
    """
    Cash flow math:
      $12,400 current - $1,000/day burn
      June 18: pre-burn balance $2,400 → payroll -$8,000 → -$5,600 (GAP)
      June 25: rent -$4,500 (deeper deficit)
    """
    payroll_dt = datetime(2026, 6, 18)
    rent_dt = datetime(2026, 6, 25)

    balance = 12_400.0
    daily_forecast = []
    gap_dates = []

    for i in range(60):
        day = TODAY + timedelta(days=i + 1)
        date_str = day.strftime("%Y-%m-%d")
        balance -= 1_000.0

        if day.date() == payroll_dt.date():
            balance -= 8_000.0
        if day.date() == rent_dt.date():
            balance -= 4_500.0

        is_gap = balance < 0
        if is_gap:
            gap_dates.append(date_str)

        daily_forecast.append(
            {"date": date_str, "projected_balance": round(balance, 2), "gap": is_gap}
        )

    first_gap = next((e for e in daily_forecast if e["gap"]), None)
    gap_amount = abs(first_gap["projected_balance"]) if first_gap else 0.0

    return {
        "snapshot_date": TODAY.strftime("%Y-%m-%d"),
        "current_balance": 12_400.0,
        "daily_forecast": daily_forecast,
        "gap_dates": gap_dates,
        "gap_amount": round(gap_amount, 2),
        "linked_invoices": ["INV-001", "INV-003"],
        "created_at": TODAY,
    }


async def seed():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
    db = client["cashguard"]

    for col in ["invoices", "client_profiles", "collections_cases", "forecast_snapshots"]:
        await db[col].delete_many({})
        print(f"  cleared  {col}")

    await db["client_profiles"].insert_many(CLIENTS)
    print(f"  inserted {len(CLIENTS)} clients")

    await db["invoices"].insert_many(INVOICES)
    print(f"  inserted {len(INVOICES)} invoices")

    forecast = _build_forecast()
    await db["forecast_snapshots"].insert_one(forecast)
    first_gap = forecast["gap_dates"][0] if forecast["gap_dates"] else "none"
    print(f"  inserted forecast  first_gap={first_gap}  gap_amount=${forecast['gap_amount']:,.2f}")

    # Create indexes
    await db["invoices"].create_index("invoice_id", unique=True)
    await db["client_profiles"].create_index("client_id", unique=True)
    await db["collections_cases"].create_index("case_id", unique=True)
    await db["collections_cases"].create_index("invoice_id")
    await db["forecast_snapshots"].create_index("snapshot_date")
    print("  indexes created")

    client.close()
    print("\nSeed complete. Run the pipeline with: POST /api/pipeline/run")


if __name__ == "__main__":
    asyncio.run(seed())

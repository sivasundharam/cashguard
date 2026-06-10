from unittest.mock import AsyncMock, patch

import pytest

from app.agents.invoice_monitor import _bucket_urgency, _classify_bucket


# ── Pure unit tests ────────────────────────────────────────────────────────────

def test_classify_bucket():
    assert _classify_bucket(3) == "1-7"
    assert _classify_bucket(7) == "1-7"
    assert _classify_bucket(8) == "8-14"
    assert _classify_bucket(14) == "8-14"
    assert _classify_bucket(15) == "15-30"
    assert _classify_bucket(30) == "15-30"
    assert _classify_bucket(31) == "30+"
    assert _classify_bucket(60) == "30+"


def test_bucket_urgency():
    assert _bucket_urgency(3) == "low"
    assert _bucket_urgency(10) == "medium"
    assert _bucket_urgency(20) == "high"
    assert _bucket_urgency(35) == "critical"


# ── Invoice Monitor ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invoice_monitor_creates_case():
    mock_invoices = [
        {
            "invoice_id": "INV-001",
            "client_id": "client_001",
            "client_name": "Acme Corp",
            "amount": 4500.0,
            "status": "overdue",
            "days_overdue": 14,
        }
    ]
    with (
        patch("app.agents.invoice_monitor.invoices_col") as mock_inv,
        patch("app.agents.invoice_monitor.collections_cases_col") as mock_cases,
    ):
        mock_inv.return_value.find.return_value.to_list = AsyncMock(return_value=mock_invoices)
        mock_cases.return_value.find_one = AsyncMock(return_value=None)
        mock_cases.return_value.insert_one = AsyncMock()

        from app.agents.invoice_monitor import run_invoice_monitor

        cases = await run_invoice_monitor()

    assert len(cases) == 1
    assert cases[0]["invoice_id"] == "INV-001"
    assert cases[0]["urgency"] == "medium"
    assert cases[0]["status"] == "new"
    assert cases[0]["tone"] == "firm"


@pytest.mark.asyncio
async def test_invoice_monitor_skips_existing_case():
    mock_invoices = [
        {
            "invoice_id": "INV-001",
            "client_id": "client_001",
            "client_name": "Acme Corp",
            "amount": 4500.0,
            "status": "overdue",
            "days_overdue": 14,
        }
    ]
    with (
        patch("app.agents.invoice_monitor.invoices_col") as mock_inv,
        patch("app.agents.invoice_monitor.collections_cases_col") as mock_cases,
    ):
        mock_inv.return_value.find.return_value.to_list = AsyncMock(return_value=mock_invoices)
        mock_cases.return_value.find_one = AsyncMock(return_value={"case_id": "CASE-EXISTS"})

        from app.agents.invoice_monitor import run_invoice_monitor

        cases = await run_invoice_monitor()

    assert len(cases) == 0


# ── Relationship Analyzer ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_relationship_analyzer_warm_tone_for_loyal_client():
    mock_cases = [
        {"case_id": "CASE-001", "client_id": "client_003", "urgency": "low", "status": "new"}
    ]
    mock_profile = {
        "client_id": "client_003",
        "relationship_score": 88,
        "tone_recommendation": "warm",
    }
    with (
        patch("app.agents.relationship_analyzer.collections_cases_col") as mock_cc,
        patch("app.agents.relationship_analyzer.client_profiles_col") as mock_cp,
    ):
        mock_cc.return_value.find.return_value.to_list = AsyncMock(return_value=mock_cases)
        mock_cp.return_value.find_one = AsyncMock(return_value=mock_profile)
        mock_cc.return_value.update_one = AsyncMock()

        from app.agents.relationship_analyzer import run_relationship_analyzer

        updated = await run_relationship_analyzer()

    assert len(updated) == 1
    assert updated[0]["tone"] == "warm"


@pytest.mark.asyncio
async def test_relationship_analyzer_serious_tone_for_low_score():
    mock_cases = [
        {"case_id": "CASE-002", "client_id": "client_002", "urgency": "high", "status": "new"}
    ]
    mock_profile = {
        "client_id": "client_002",
        "relationship_score": 38,
        "tone_recommendation": "serious",
    }
    with (
        patch("app.agents.relationship_analyzer.collections_cases_col") as mock_cc,
        patch("app.agents.relationship_analyzer.client_profiles_col") as mock_cp,
    ):
        mock_cc.return_value.find.return_value.to_list = AsyncMock(return_value=mock_cases)
        mock_cp.return_value.find_one = AsyncMock(return_value=mock_profile)
        mock_cc.return_value.update_one = AsyncMock()

        from app.agents.relationship_analyzer import run_relationship_analyzer

        updated = await run_relationship_analyzer()

    assert updated[0]["tone"] == "serious"


# ── Cash Flow Forecaster ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cashflow_forecaster_detects_gap_on_payroll_date():
    with (
        patch("app.agents.cashflow_forecaster.invoices_col") as mock_inv,
        patch("app.agents.cashflow_forecaster.forecast_snapshots_col") as mock_snap,
        patch("app.agents.cashflow_forecaster.collections_cases_col") as mock_cases,
    ):
        mock_inv.return_value.find.return_value.to_list = AsyncMock(return_value=[])
        mock_snap.return_value.replace_one = AsyncMock()
        mock_cases.return_value.update_many = AsyncMock()

        from app.agents.cashflow_forecaster import run_cashflow_forecaster

        result = await run_cashflow_forecaster()

    assert result["current_balance"] == 12_400.0
    assert "2026-06-18" in result["gap_dates"]
    assert result["gap_amount"] > 0
    assert len(result["daily_forecast"]) == 60

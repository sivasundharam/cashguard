import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional, TypedDict

logger = logging.getLogger(__name__)

from langgraph.graph import END, START, StateGraph

from app.agents.cashflow_forecaster import run_cashflow_forecaster
from app.agents.communication_agent import run_communication_agent
from app.agents.escalation_agent import run_escalation_agent
from app.agents.invoice_monitor import run_invoice_monitor
from app.agents.relationship_analyzer import run_relationship_analyzer


class CashGuardState(TypedDict):
    run_id: str
    timestamp: str
    fivetran_sync_status: str
    cases_created: List[dict]
    cases_analyzed: List[dict]
    drafts_created: List[dict]
    cases_escalated: List[dict]
    forecast: Optional[dict]
    gap_detected: bool
    linked_invoice_ids: List[str]
    errors: List[str]


async def _fivetran_sync_node(state: CashGuardState) -> dict:
    """
    Trigger a Fivetran sync to pull the latest QuickBooks / bank data into MongoDB
    before the agent pipeline runs. If FIVETRAN_CONNECTOR_ID is not set, this node
    is a no-op (demo mode uses pre-seeded Google Sheets data).
    """
    connector_id = os.getenv("FIVETRAN_CONNECTOR_ID", "").strip()
    if not connector_id:
        return {"fivetran_sync_status": "skipped — set FIVETRAN_CONNECTOR_ID to enable live sync"}

    try:
        from app.services.fivetran import trigger_sync, get_sync_status
        await trigger_sync(connector_id)
        status_data = await get_sync_status(connector_id)
        sync_state = status_data.get("sync_state", "unknown")
        return {"fivetran_sync_status": f"triggered — connector {connector_id} ({sync_state})"}
    except Exception as e:
        return {
            "fivetran_sync_status": f"error: {e}",
            "errors": state["errors"] + [f"fivetran_sync: {e}"],
        }


async def _invoice_monitor_node(state: CashGuardState) -> dict:
    try:
        return {"cases_created": await run_invoice_monitor()}
    except Exception as e:
        return {"errors": state["errors"] + [f"invoice_monitor: {e}"]}


async def _relationship_analyzer_node(state: CashGuardState) -> dict:
    try:
        return {"cases_analyzed": await run_relationship_analyzer()}
    except Exception as e:
        return {"errors": state["errors"] + [f"relationship_analyzer: {e}"]}


async def _cashflow_forecaster_node(state: CashGuardState) -> dict:
    try:
        forecast = await run_cashflow_forecaster()
        return {
            "forecast": forecast,
            "gap_detected": len(forecast.get("gap_dates", [])) > 0,
            "linked_invoice_ids": forecast.get("linked_invoices", []),
        }
    except Exception as e:
        return {"errors": state["errors"] + [f"cashflow_forecaster: {e}"]}


async def _communication_agent_node(state: CashGuardState) -> dict:
    try:
        return {"drafts_created": await run_communication_agent()}
    except Exception as e:
        logger.error("communication_agent failed: %s", e, exc_info=True)
        return {"errors": state["errors"] + [f"communication_agent: {e}"]}


async def _escalation_agent_node(state: CashGuardState) -> dict:
    try:
        return {"cases_escalated": await run_escalation_agent()}
    except Exception as e:
        return {"errors": state["errors"] + [f"escalation_agent: {e}"]}


def _build_graph():
    g = StateGraph(CashGuardState)

    g.add_node("fivetran_sync", _fivetran_sync_node)
    g.add_node("invoice_monitor", _invoice_monitor_node)
    g.add_node("relationship_analyzer", _relationship_analyzer_node)
    g.add_node("cashflow_forecaster", _cashflow_forecaster_node)
    g.add_node("communication_agent", _communication_agent_node)
    g.add_node("escalation_agent", _escalation_agent_node)

    g.add_edge(START, "fivetran_sync")
    g.add_edge("fivetran_sync", "invoice_monitor")
    g.add_edge("invoice_monitor", "relationship_analyzer")
    g.add_edge("relationship_analyzer", "cashflow_forecaster")
    g.add_edge("cashflow_forecaster", "communication_agent")
    g.add_edge("communication_agent", "escalation_agent")
    g.add_edge("escalation_agent", END)

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


async def run_full_pipeline() -> CashGuardState:
    initial: CashGuardState = {
        "run_id": f"run_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat(),
        "fivetran_sync_status": "",
        "cases_created": [],
        "cases_analyzed": [],
        "drafts_created": [],
        "cases_escalated": [],
        "forecast": None,
        "gap_detected": False,
        "linked_invoice_ids": [],
        "errors": [],
    }
    return await get_graph().ainvoke(initial)

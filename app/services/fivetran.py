import os
from base64 import b64encode

import httpx
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://api.fivetran.com/v1"


def _auth() -> str:
    key = os.getenv("FIVETRAN_API_KEY", "")
    secret = os.getenv("FIVETRAN_API_SECRET", "")
    return f"Basic {b64encode(f'{key}:{secret}'.encode()).decode()}"


async def list_connectors(group_id: str | None = None) -> dict:
    url = f"{_BASE}/groups/{group_id}/connectors" if group_id else f"{_BASE}/connectors"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, headers={"Authorization": _auth()})
        r.raise_for_status()
        return r.json()


async def get_connector(connector_id: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{_BASE}/connectors/{connector_id}", headers={"Authorization": _auth()})
        r.raise_for_status()
        return r.json()


async def trigger_sync(connector_id: str) -> dict:
    headers = {"Authorization": _auth(), "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{_BASE}/connectors/{connector_id}/force", headers=headers)
        r.raise_for_status()
        return r.json()


async def get_sync_status(connector_id: str) -> dict:
    data = await get_connector(connector_id)
    status = data.get("data", {}).get("status", {})
    return {
        "connector_id": connector_id,
        "sync_state": status.get("sync_state"),
        "update_state": status.get("update_state"),
        "setup_state": status.get("setup_state"),
        "is_historical_sync": status.get("is_historical_sync"),
    }

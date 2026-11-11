"""User-scoped PostgREST requests. The database also enforces row-level security."""
from typing import Any, Literal

import httpx
from fastapi import HTTPException

from app.core.supabase import CurrentUser, get_config

TABLES = frozenset({"profiles", "customers", "orders", "tickets", "ticket_messages", "knowledge_documents", "knowledge_chunks", "agent_runs", "approval_requests", "operation_audit_events"})
RPC_FUNCTIONS = frozenset({"match_policy_chunks", "decide_approval"})


async def query(
    user: CurrentUser,
    table: str,
    *,
    method: Literal["GET", "POST", "PATCH", "DELETE"] = "GET",
    params: dict[str, str | int] | None = None,
    data: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return only end-user-authorized rows. Never accept table names from URLs."""
    if table not in TABLES:
        raise ValueError("Unknown database table")
    settings = get_config()
    headers = {
        "apikey": settings.publishable_key,
        "Authorization": f"Bearer {user.access_token}",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.request(
                method,
                f"{settings.url}/rest/v1/{table}",
                headers=headers,
                params=params,
                json=data,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    if response.status_code in (401, 403):
        raise HTTPException(status_code=403, detail="Database access denied")
    if response.status_code >= 400:
        # Do not leak internal SQL, schema, or row-level-security details.
        raise HTTPException(status_code=422 if response.status_code < 500 else 502,
                            detail="Database rejected the operation")
    if not response.content:
        return []
    rows = response.json()
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail="Unexpected database response")
    return rows


def owner_filter(user: CurrentUser, **filters: str | int) -> dict[str, str | int]:
    return {"owner_id": f"eq.{user.id}", **filters}

async def rpc(user: CurrentUser, function_name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Allowlisted, user-scoped Supabase RPC; always forward the verified end-user JWT."""
    if function_name not in RPC_FUNCTIONS:
        raise ValueError("Unknown RPC function")
    settings = get_config()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.url}/rest/v1/rpc/{function_name}",
                headers={"apikey": settings.publishable_key,
                         "Authorization": f"Bearer {user.access_token}",
                         "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Knowledge search temporarily unavailable") from exc
    if response.status_code in (401, 403):
        raise HTTPException(status_code=403, detail="Database operation access denied")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Requested database record not found")
    if response.status_code == 409:
        raise HTTPException(status_code=409, detail="Database operation conflicts with current state")
    if response.status_code == 422:
        raise HTTPException(status_code=422, detail="Database rejected this operation")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Database operation failed")
    rows = response.json()
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail="Unexpected knowledge search response")
    return rows

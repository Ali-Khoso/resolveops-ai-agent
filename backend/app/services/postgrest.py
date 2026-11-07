"""User-scoped PostgREST requests. The database also enforces row-level security."""
from typing import Any, Literal

import httpx
from fastapi import HTTPException

from app.core.supabase import CurrentUser, get_config

TABLES = frozenset({"profiles", "customers", "orders", "tickets", "ticket_messages"})


async def query(
    user: CurrentUser,
    table: str,
    *,
    method: Literal["GET", "POST", "PATCH", "DELETE"] = "GET",
    params: dict[str, str | int] | None = None,
    data: dict[str, Any] | None = None,
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

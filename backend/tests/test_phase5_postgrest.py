"""PostgREST errors must preserve meaningful conflict statuses without SQL leakage."""
import httpx
import pytest
from fastapi import HTTPException
from app.core.supabase import CurrentUser, SupabaseConfig
import app.services.postgrest as pg

OWNER = CurrentUser("11111111-1111-4111-8111-111111111111", "demo@example.com", "mock-jwt")


@pytest.mark.asyncio
@pytest.mark.parametrize("code,expected", [(409,409),(422,422),(403,403),(500,502)])
async def test_rpc_http_statuses(monkeypatch, code, expected):
    monkeypatch.setattr(pg, "get_config", lambda: SupabaseConfig(url="https://example.supabase.co", publishable_key="public-key"))
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(code, json={"message": "Sensitive database detail"}))
    monkeypatch.setattr(pg.httpx, "AsyncClient", lambda **kwargs: original(transport=transport))
    with pytest.raises(HTTPException) as error:
        await pg.rpc(OWNER, "decide_approval", {
            "p_approval_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "p_decision": "rejected", "p_note": "Insufficient evidence"
        })
    assert error.value.status_code == expected
    assert "Sensitive database detail" not in error.value.detail

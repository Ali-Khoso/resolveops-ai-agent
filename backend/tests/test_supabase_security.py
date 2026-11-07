"""HTTP mock tests for Supabase Auth and forwarding user-scoped JWTs."""
import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.supabase import CurrentUser, get_config, get_current_user
from app.services.postgrest import query

UUID = "11111111-1111-4111-8111-111111111111"

@pytest.fixture
def mock_supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_safe")
    get_config.cache_clear()
    yield
    get_config.cache_clear()

@pytest.mark.asyncio
async def test_valid_token_is_checked_server_side(mock_supabase, monkeypatch):
    def handler(request):
        assert request.url.path == "/auth/v1/user"
        assert request.headers["Authorization"] == "Bearer example.token"
        return httpx.Response(200, json={"id": UUID, "email": "verified@example.com"})
    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: original(transport=transport, **kwargs))
    user = await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials="example.token"))
    assert user.id == UUID

@pytest.mark.asyncio
async def test_invalid_token_is_rejected(mock_supabase, monkeypatch):
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(401)), **kwargs))
    with pytest.raises(HTTPException) as ex:
        await get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired.jwt"))
    assert ex.value.status_code == 401

@pytest.mark.asyncio
async def test_queries_forward_user_token_for_rls(mock_supabase, monkeypatch):
    def handler(request):
        assert request.url.path == "/rest/v1/customers"
        assert request.headers["apikey"] == "sb_publishable_safe"
        assert request.headers["Authorization"] == "Bearer verified.jwt"
        assert "owner_id=eq." in str(request.url)
        return httpx.Response(200, json=[{"id":"test"}])
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    rows = await query(CurrentUser(UUID, None, "verified.jwt"), "customers", params={"owner_id": f"eq.{UUID}"})
    assert rows == [{"id":"test"}]

@pytest.mark.asyncio
async def test_postgrest_errors_do_not_leak_sql(mock_supabase, monkeypatch):
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(400, json={"message":"secret SQL constraint details"})), **kwargs))
    with pytest.raises(HTTPException) as ex:
        await query(CurrentUser(UUID, None, "valid.jwt"), "customers", method="POST", data={})
    assert ex.value.status_code == 422
    assert "secret SQL" not in str(ex.value.detail)

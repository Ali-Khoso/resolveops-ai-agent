"""Graph-level Phase 4 tests use fake account-scoped reads, never live keys."""
import pytest
from fastapi import HTTPException
from app.core.supabase import CurrentUser
import app.agents.resolution_graph as graph

USER = CurrentUser("11111111-1111-4111-8111-111111111111", "demo@example.com", "test-token")
TICKET = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


@pytest.fixture
def fake_db(monkeypatch):
    calls = []
    async def fake_query(user, table, **kwargs):
        assert user.id == USER.id
        assert kwargs["params"]["owner_id"] == "eq." + USER.id
        calls.append(table)
        if table == "tickets":
            return [{"id": TICKET, "order_id": None, "subject": "Test", "priority": "normal", "status": "open"}]
        if table == "orders":
            return []
        raise AssertionError("Unexpected database table")
    monkeypatch.setattr(graph, "query", fake_query)
    return calls


@pytest.mark.asyncio
async def test_order_tracking_skips_policy_api(fake_db, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    async def no_policy(*args, **kwargs):
        raise AssertionError("Pure order tracking must not call a model")
    monkeypatch.setattr(graph, "answer_policy", no_policy)
    from uuid import UUID
    result = await graph.investigate(USER, UUID(TICKET), "Where is my package?")
    assert result["intent"] == "order"
    assert "policy_skipped:not_needed" in result["steps"]
    assert "verify_order_link" in result["risk_flags"]
    assert fake_db == ["tickets"]


@pytest.mark.asyncio
async def test_auth_failure_is_not_swallowed(fake_db, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    async def blocked(*args, **kwargs):
        raise HTTPException(403, "Forbidden")
    monkeypatch.setattr(graph, "answer_policy", blocked)
    from uuid import UUID
    with pytest.raises(HTTPException) as exc:
        await graph.investigate(USER, UUID(TICKET), "Can I get a refund?")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_policy_outage_degrades_to_review(fake_db, monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    async def unavailable(*args, **kwargs):
        raise HTTPException(503, "Provider unavailable")
    monkeypatch.setattr(graph, "answer_policy", unavailable)
    from uuid import UUID
    result = await graph.investigate(USER, UUID(TICKET), "Can I get a refund?")
    assert result["grounded"] is False
    assert "policy_unavailable" in result["steps"]
    assert "policy_not_verified" in result["risk_flags"]
    assert "No refund issued" in result["draft"]

"""Phase 4 API regressions for durable traces, review flags and timeouts."""
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase import CurrentUser, get_current_user
import app.api.operations as operations

OWNER = "11111111-1111-4111-8111-111111111111"
TICKET = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def setup_user():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        OWNER, "test@example.com", "fixture-jwt"
    )


def test_investigation_persists_workflow_evidence(monkeypatch):
    setup_user()
    saved = {}

    async def fake_query(user, table, **kwargs):
        assert user.id == OWNER
        if table == "tickets":
            assert kwargs["params"]["owner_id"] == "eq." + OWNER
            return [{"id": TICKET, "owner_id": OWNER}]
        assert table == "agent_runs"
        saved.update(kwargs["data"])
        return [{"id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd", **kwargs["data"]}]

    async def fake_graph(user, ticket_id, question):
        return {
            "intent": "refund",
            "draft": "INTERNAL DRAFT: Human review required. No refund issued.",
            "sources": [],
            "steps": ["classified:refund", "looked_up_owned_ticket", "policy_not_configured", "drafted_internal_response"],
            "risk_flags": ["policy_not_verified", "human_refund_review"],
            "suggested_action": "refund_review",
            "requires_approval": True,
        }

    monkeypatch.setattr(operations, "query", fake_query)
    monkeypatch.setattr(operations, "investigate", fake_graph)
    monkeypatch.setattr(operations, "workflow_timeout_seconds", lambda: 30)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/workspace/operations/investigations", json={
                "ticket_id": TICKET, "question": "Please refund my order"
            })
        assert response.status_code == 201
        assert saved["workflow_steps"][0] == "classified:refund"
        assert saved["review_flags"] == ["policy_not_verified", "human_refund_review"]
        assert response.json()["run"]["requires_approval"] is True
    finally:
        app.dependency_overrides.clear()


def test_timeout_exposes_safe_504_response(monkeypatch):
    setup_user()

    async def fake_query(user, table, **kwargs):
        return [{"id": TICKET, "owner_id": OWNER}]

    async def timed_out(*args):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(operations, "query", fake_query)
    monkeypatch.setattr(operations, "investigate", timed_out)
    monkeypatch.setattr(operations, "workflow_timeout_seconds", lambda: 30)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/workspace/operations/investigations", json={
                "ticket_id": TICKET, "question": "Where is the shipment?"
            })
        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()

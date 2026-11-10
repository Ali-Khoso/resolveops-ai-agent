"""Offline regression tests for protected operations and approval boundaries."""
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.agents.resolution_graph import classify_intent, suggested_action
from app.core.supabase import CurrentUser, get_current_user
from app.main import app
from app.services.postgrest import RPC_FUNCTIONS, TABLES
import app.api.operations as operations

OWNER = "11111111-1111-4111-8111-111111111111"
TICKET = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
RUN = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
APPROVAL = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def authenticated():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(OWNER, "test@example.com", "mock-jwt")


def test_operations_are_private(client):
    for route in ("investigations", "approvals", "audit", "analytics"):
        assert client.get(f"/api/v1/workspace/operations/{route}").status_code == 401


def test_classification():
    assert classify_intent("I want my money back") == "refund"
    assert classify_intent("Where is my package?") == "order"
    assert classify_intent("Ask a manager") == "escalation"
    assert classify_intent("What is the warranty policy?") == "policy"
    assert suggested_action("refund", "help") == "refund_review"
    assert suggested_action("general", "resolve the ticket") == "resolve_ticket"


def test_id_spoofing_is_rejected(client):
    authenticated()
    payload = {"ticket_id": TICKET, "question": "Where is it?", "owner_id": OWNER}
    assert client.post("/api/v1/workspace/operations/investigations", json=payload).status_code == 422
    assert client.post("/api/v1/workspace/operations/approvals", json={
        "ticket_id": TICKET, "action_type": "issue_refund",
        "draft_reply": "OK", "reason": "Just do it",
    }).status_code == 422


def test_owner_filtered_listing(client, monkeypatch):
    authenticated()
    seen = []
    async def fake_query(user, table, **kwargs):
        seen.append(kwargs["params"])
        return []
    monkeypatch.setattr(operations, "query", fake_query)
    assert client.get("/api/v1/workspace/operations/investigations").status_code == 200
    assert client.get("/api/v1/workspace/operations/approvals").status_code == 200
    assert all(p["owner_id"] == f"eq.{OWNER}" for p in seen)


def test_investigation_saves_run(client, monkeypatch):
    authenticated()
    async def fake_query(user, table, **kwargs):
        if table == "tickets":
            return [{"id": TICKET}]
        assert table == "agent_runs"
        assert kwargs["data"]["owner_id"] == OWNER
        return [{"id": RUN, **kwargs["data"]}]
    async def fake_agent(user, ticket_id, question):
        return {"intent": "refund", "draft": "Internal draft", "sources": [],
                "requires_approval": True, "suggested_action": "refund_review", "steps": ["classify", "draft"]}
    monkeypatch.setattr(operations, "query", fake_query)
    monkeypatch.setattr(operations, "investigate", fake_agent)
    response = client.post("/api/v1/workspace/operations/investigations", json={
        "ticket_id": TICKET, "question": "I want a refund",
    })
    assert response.status_code == 201
    assert response.json()["run"]["status"] == "pending_approval"


def test_approval_decision_uses_scoped_rpc(client, monkeypatch):
    authenticated()
    called = []
    async def fake_rpc(user, function, payload):
        called.append((user.id, function, payload))
        return [{"id": APPROVAL, "status": payload["p_decision"]}]
    monkeypatch.setattr(operations, "rpc", fake_rpc)
    response = client.post(f"/api/v1/workspace/operations/approvals/{APPROVAL}/decision",
                           json={"decision": "approved"})
    assert response.status_code == 200
    assert called[0][0] == OWNER and called[0][1] == "decide_approval"


def test_no_payment_function_is_exposed():
    assert {"agent_runs", "approval_requests", "operation_audit_events"} <= TABLES
    assert "decide_approval" in RPC_FUNCTIONS
    assert "issue_refund" not in RPC_FUNCTIONS

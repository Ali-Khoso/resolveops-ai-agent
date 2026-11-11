"""HTTP contract tests for Phase 5 approval creation business guards."""
import pytest
from fastapi.testclient import TestClient
from app.core.supabase import CurrentUser, get_current_user
from app.main import app
import app.api.operations as api

OWNER = "11111111-1111-4111-8111-111111111111"
TICKET = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
RUN = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
URL = "/api/v1/workspace/operations/approvals"


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(OWNER, "demo@example.com", "test-jwt")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def request_body(**updates):
    return {"ticket_id": TICKET, "action_type": "send_reply",
            "draft_reply": "Please review this internal response.",
            "reason": "Human verification is required.", **updates}


def test_refund_requires_linked_refund_run(client, monkeypatch):
    async def fake_query(user, table, **kwargs):
        assert user.id == OWNER
        assert kwargs["params"]["owner_id"] == f"eq.{OWNER}"
        if table == "tickets":
            return [{"id": TICKET, "status": "open"}]
        raise AssertionError("Refund request should be rejected before creation")
    monkeypatch.setattr(api, "query", fake_query)
    response = client.post(URL, json=request_body(action_type="refund_review"))
    assert response.status_code == 422


def test_prevents_review_of_closed_ticket(client, monkeypatch):
    async def fake_query(user, table, **kwargs):
        return [{"id": TICKET, "status": "closed"}]
    monkeypatch.setattr(api, "query", fake_query)
    response = client.post(URL, json=request_body())
    assert response.status_code == 409


def test_valid_refund_review_is_created(client, monkeypatch):
    written = []
    async def fake_query(user, table, **kwargs):
        assert user.id == OWNER
        if table == "tickets":
            return [{"id": TICKET, "status": "open"}]
        if table == "agent_runs":
            assert kwargs["params"]["ticket_id"] == f"eq.{TICKET}"
            return [{"id": RUN, "intent": "refund", "requires_approval": True, "status": "pending_approval"}]
        assert table == "approval_requests"
        written.append(kwargs["data"])
        return [{"id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee", **kwargs["data"]}]
    monkeypatch.setattr(api, "query", fake_query)
    response = client.post(URL, json=request_body(run_id=RUN, action_type="refund_review"))
    assert response.status_code == 201
    assert written[0]["owner_id"] == OWNER
    assert written[0]["run_id"] == RUN
    assert written[0]["status"] == "pending"

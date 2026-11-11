"""Endpoint regressions for Phase 5 review decisions."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase import CurrentUser, get_current_user
import app.api.operations as operations

OWNER = "11111111-1111-4111-8111-111111111111"
APPROVAL = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
URL = f"/api/v1/workspace/operations/approvals/{APPROVAL}/decision"


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(OWNER,"demo@example.com","mock-token")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_rejection_without_note_is_blocked_before_database_call(client, monkeypatch):
    async def should_not_call(*args, **kwargs):
        raise AssertionError("Malformed decision should not reach RPC")
    monkeypatch.setattr(operations, "rpc", should_not_call)
    assert client.post(URL,json={"decision":"rejected"}).status_code == 422
    assert client.post(URL,json={"decision":"rejected","note":"  "}).status_code == 422


def test_rejection_reason_is_forwarded_with_authenticated_account(client, monkeypatch):
    received=[]
    async def fake_rpc(user, function, payload):
        received.append((user.id,function,payload))
        return [{"id":APPROVAL,"status":"rejected","decision_note":payload["p_note"]}]
    monkeypatch.setattr(operations, "rpc", fake_rpc)
    result=client.post(URL,json={"decision":"rejected","note":"  Missing policy evidence "})
    assert result.status_code == 200
    assert received[0][0] == OWNER
    assert received[0][1] == "decide_approval"
    assert received[0][2]["p_note"] == "Missing policy evidence"


def test_reviewer_identity_cannot_be_spoofed(client):
    result=client.post(URL,json={"decision":"approved","note":"Reviewed", "decided_by":OWNER})
    assert result.status_code == 422


def test_unapproved_extra_action_is_rejected(client):
    result=client.post(URL,json={"decision":"paid","note":"Not permitted"})
    assert result.status_code == 422

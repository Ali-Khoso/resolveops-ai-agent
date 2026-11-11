"""Audit events remain immutable and queryable only within the signed-in account."""
import pytest
from fastapi.testclient import TestClient
from app.core.supabase import CurrentUser, get_current_user
from app.main import app
import app.api.operations as api

OWNER = "11111111-1111-4111-8111-111111111111"
APPROVAL = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(OWNER,"demo@example.com","token")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_audit_can_filter_one_approval(client, monkeypatch):
    called=[]
    async def fake_query(user, table, **kwargs):
        called.append(kwargs["params"])
        assert table=="operation_audit_events"
        return []
    monkeypatch.setattr(api,"query",fake_query)
    result=client.get(f"/api/v1/workspace/operations/audit?approval_id={APPROVAL}&limit=4&offset=8")
    assert result.status_code==200
    assert called[0]["owner_id"]==f"eq.{OWNER}"
    assert called[0]["approval_id"]==f"eq.{APPROVAL}"
    assert called[0]["limit"]==4 and called[0]["offset"]==8


def test_audit_rejects_unbounded_queries(client):
    assert client.get("/api/v1/workspace/operations/audit?limit=5000").status_code==422
    assert client.get("/api/v1/workspace/operations/audit?offset=-1").status_code==422
    assert client.get("/api/v1/workspace/operations/audit?approval_id=not-a-uuid").status_code==422


def test_audit_is_not_public():
    with TestClient(app) as client:
        assert client.get("/api/v1/workspace/operations/audit").status_code==401

"""Private approval detail and paginated queue HTTP contracts."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase import CurrentUser, get_current_user
import app.api.operations as operations

OWNER = "11111111-1111-4111-8111-111111111111"
APPROVAL = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(OWNER,"demo@example.com","mock-jwt")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_approval_list_has_validated_paging(client,monkeypatch):
    seen=[]
    async def fake_query(user,table,**kw):
        seen.append(kw["params"])
        return [{"id":APPROVAL,"status":"pending"}]
    monkeypatch.setattr(operations,"query",fake_query)
    response=client.get("/api/v1/workspace/operations/approvals?status=pending&limit=3&offset=6")
    assert response.status_code==200
    assert response.json()["offset"]==6
    assert seen[0]["status"]=="eq.pending"
    assert seen[0]["owner_id"]==f"eq.{OWNER}"
    assert seen[0]["limit"]==3 and seen[0]["offset"]==6


def test_invalid_filters_rejected(client):
    assert client.get("/api/v1/workspace/operations/approvals?status=unknown").status_code==422
    assert client.get("/api/v1/workspace/operations/approvals?offset=-1").status_code==422


def test_detail_is_owner_scoped(client,monkeypatch):
    async def fake_query(user,table,**kw):
        assert kw["params"]["owner_id"]==f"eq.{OWNER}"
        assert kw["params"]["id"]==f"eq.{APPROVAL}"
        return [{"id":APPROVAL,"status":"pending"}]
    monkeypatch.setattr(operations,"query",fake_query)
    r=client.get("/api/v1/workspace/operations/approvals/"+APPROVAL)
    assert r.status_code==200
    assert r.json()["id"]==APPROVAL


def test_missing_detail_returns_404(client,monkeypatch):
    async def fake_query(*args,**kw):
        return []
    monkeypatch.setattr(operations,"query",fake_query)
    r=client.get("/api/v1/workspace/operations/approvals/"+APPROVAL)
    assert r.status_code==404

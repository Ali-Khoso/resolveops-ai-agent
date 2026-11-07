"""Offline contract tests for authenticated workspace endpoints."""
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.supabase import CurrentUser, get_current_user
from app.main import app
import app.api.workspace as workspace

USER_A = "11111111-1111-4111-8111-111111111111"
USER_B = "22222222-2222-4222-8222-222222222222"
CUSTOMER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ORDER = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
TICKET = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_authentication_required(client):
    assert client.get("/api/v1/workspace/customers").status_code == 401
    assert client.post("/api/v1/workspace/tickets", json={}).status_code == 401


def test_authenticated_lists_are_user_scoped(client, monkeypatch):
    seen = []
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, "a@example.com", "jwt.a")

    async def fake_query(user, table, **kwargs):
        assert user.id == USER_A
        seen.append((table, kwargs["params"]))
        return []

    monkeypatch.setattr(workspace, "query", fake_query)
    assert client.get("/api/v1/workspace/customers").json() == {"items": []}
    assert client.get("/api/v1/workspace/orders").status_code == 200
    assert client.get("/api/v1/workspace/tickets").status_code == 200
    assert all(item["owner_id"] == f"eq.{USER_A}" for _, item in seen)


def test_customer_create_does_not_trust_owner_id(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, "a@example.com", "jwt.a")
    async def fake_query(user, table, **kwargs):
        assert table == "customers"
        assert kwargs["data"]["owner_id"] == USER_A
        return [{"id": CUSTOMER, **kwargs["data"]}]
    monkeypatch.setattr(workspace, "query", fake_query)
    response = client.post("/api/v1/workspace/customers", json={"full_name":"Test Client", "email":"test@example.com", "owner_id": USER_B})
    assert response.status_code == 422  # Extra fields are rejected rather than ignored.
    response = client.post("/api/v1/workspace/customers", json={"full_name":"Test Client", "email":"test@example.com"})
    assert response.status_code == 201
    assert response.json()["owner_id"] == USER_A


def test_ticket_rejects_invalid_relationship_id(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    assert client.post("/api/v1/workspace/tickets", json={"customer_id": "bad", "subject":"Help", "description":"Details"}).status_code == 422


def test_ticket_create_only_allows_model_fields(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    async def fake_query(user, table, **kwargs):
        assert kwargs["data"]["owner_id"] == USER_A
        assert kwargs["data"]["priority"] == "normal"
        assert "status" not in kwargs["data"]
        return [{"id": TICKET, **kwargs["data"]}]
    monkeypatch.setattr(workspace, "query", fake_query)
    result = client.post("/api/v1/workspace/tickets", json={"customer_id": CUSTOMER, "subject":"Missing parcel", "description":"Package not received"})
    assert result.status_code == 201


def test_messages_cannot_impersonate_another_author(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    payload = {"content": "hello", "author_id": USER_B}
    assert client.post(f"/api/v1/workspace/tickets/{TICKET}/messages", json=payload).status_code == 422


def test_message_creation_checks_parent_and_author(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    calls = []
    async def fake_query(user, table, **kwargs):
        calls.append((table, kwargs))
        if table == "tickets":
            return [{"id": TICKET, "owner_id": USER_A}]
        return [{"id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd", **kwargs["data"]}]
    monkeypatch.setattr(workspace, "query", fake_query)
    resp = client.post(f"/api/v1/workspace/tickets/{TICKET}/messages", json={"content": "Checking your case"})
    assert resp.status_code == 201
    assert calls[0][1]["params"]["owner_id"] == f"eq.{USER_A}"
    assert calls[1][1]["data"]["author_id"] == USER_A
    assert calls[1][1]["data"]["sender_type"] == "agent"


def test_missing_ticket_cannot_receive_message(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    async def missing(user, table, **kwargs):
        assert table == "tickets"
        return []
    monkeypatch.setattr(workspace, "query", missing)
    assert client.post(f"/api/v1/workspace/tickets/{TICKET}/messages", json={"content": "note"}).status_code == 404


def test_get_missing_order_is_404(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    async def missing(user, table, **kwargs):
        assert kwargs["params"]["owner_id"] == f"eq.{USER_A}"
        return []
    monkeypatch.setattr(workspace, "query", missing)
    assert client.get(f"/api/v1/workspace/orders/{ORDER}").status_code == 404


def test_list_pagination_is_bounded(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(USER_A, None, "jwt.a")
    assert client.get("/api/v1/workspace/orders?limit=200").status_code == 422
    assert client.get("/api/v1/workspace/orders?offset=-1").status_code == 422

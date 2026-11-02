from fastapi.testclient import TestClient
from app.core.config import agent_mode
from app.main import app

client = TestClient(app)

def test_health():
    agent_mode.cache_clear()
    result = client.get("/health")
    assert result.status_code == 200
    assert result.json()["status"] == "ok"

def test_orders_are_fictional():
    payload = client.get("/api/v1/orders").json()
    assert payload["demo_data"] is True
    assert len(payload["orders"]) == 3

def test_order_lookup():
    result = client.get("/api/v1/orders/1001")
    assert result.status_code == 200
    assert result.json()["order"]["status"] == "Shipped"

def test_missing_order():
    assert client.get("/api/v1/orders/9999").status_code == 404

def test_chat_demo(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "demo")
    agent_mode.cache_clear()
    result = client.post("/api/v1/agent/chat", json={"message": "Where is order 1002?"})
    assert result.status_code == 200
    assert result.json()["mode"] == "demo"
    assert "processing" in result.json()["answer"].lower()

def test_chat_rejects_blank():
    response = client.post("/api/v1/agent/chat", json={"message": "   "})
    assert response.status_code == 422

def test_chat_rejects_long_input():
    response = client.post("/api/v1/agent/chat", json={"message": "a" * 1501})
    assert response.status_code == 422

from app.agents.support_agent import demo_reply
from app.tools.orders import get_order_status, list_orders

def test_unknown_order():
    assert get_order_status("9999") == {"error": "Order not found"}

def test_cannot_mutate_sample_orders():
    first = get_order_status("1001")
    first["status"] = "Altered"
    assert get_order_status("1001")["status"] == "Shipped"
    orders = list_orders()
    orders[0]["status"] = "Altered"
    assert list_orders()[0]["status"] == "Shipped"

def test_no_order_prompt():
    assert "1001" in demo_reply("hello")

def test_no_fake_refund_confirmation():
    message = demo_reply("refund order 1001")
    assert "refund issued" not in message.lower()
    assert "sample data" in message.lower()

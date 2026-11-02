"""Read-only tools using FICTIONAL sample orders (Phase 1)."""
from copy import deepcopy

_SAMPLE_ORDERS = {
    "1001": {"order_id": "1001", "customer": "Demo Customer A", "item": "Wireless Headphones", "status": "Shipped", "carrier": "DHL", "estimated_delivery": "2026-11-05"},
    "1002": {"order_id": "1002", "customer": "Demo Customer B", "item": "Mechanical Keyboard", "status": "Processing", "carrier": None, "estimated_delivery": None},
    "1003": {"order_id": "1003", "customer": "Demo Customer C", "item": "USB-C Dock", "status": "Delivered", "carrier": "FedEx", "estimated_delivery": "2026-10-28"},
}

def list_orders() -> list[dict]:
    return deepcopy(list(_SAMPLE_ORDERS.values()))

def get_order_status(order_id: str) -> dict:
    """Return a fictional order without modifying records."""
    order = _SAMPLE_ORDERS.get(order_id.strip())
    return deepcopy(order) if order else {"error": "Order not found"}

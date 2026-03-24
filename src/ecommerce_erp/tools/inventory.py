from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Mock ERP data — 5 representative SKUs covering low / boundary / healthy stock
# ---------------------------------------------------------------------------
_MOCK_INVENTORY: dict[str, dict[str, Any]] = {
    "SKU-001": {
        "sku": "SKU-001",
        "product_name": "Wireless Bluetooth Headphones",
        "current_stock": 15,
        "max_stock": 200,
        "stock_pct": 7.5,
        "daily_velocity": 8.0,
        "lead_time_days": 14,
        "unit_cost": 45.00,
        "warehouse": "WH-WEST-01",
    },
    "SKU-002": {
        "sku": "SKU-002",
        "product_name": "USB-C Charging Cable (2m)",
        "current_stock": 80,
        "max_stock": 400,
        "stock_pct": 20.0,
        "daily_velocity": 15.0,
        "lead_time_days": 7,
        "unit_cost": 8.50,
        "warehouse": "WH-EAST-02",
    },
    "SKU-003": {
        "sku": "SKU-003",
        "product_name": "Ergonomic Office Chair",
        "current_stock": 120,
        "max_stock": 150,
        "stock_pct": 80.0,
        "daily_velocity": 2.0,
        "lead_time_days": 21,
        "unit_cost": 280.00,
        "warehouse": "WH-CENTRAL-03",
    },
    "SKU-004": {
        "sku": "SKU-004",
        "product_name": "Mechanical Keyboard",
        "current_stock": 10,
        "max_stock": 100,
        "stock_pct": 10.0,
        "daily_velocity": 5.0,
        "lead_time_days": 10,
        "unit_cost": 120.00,
        "warehouse": "WH-WEST-01",
    },
    "SKU-005": {
        "sku": "SKU-005",
        "product_name": "Smart Home Hub",
        "current_stock": 35,
        "max_stock": 100,
        "stock_pct": 35.0,
        "daily_velocity": 3.5,
        "lead_time_days": 12,
        "unit_cost": 89.00,
        "warehouse": "WH-EAST-02",
    },
}


def get_inventory_stats(sku: str) -> dict[str, Any]:
    """
    Query mock ERP inventory data for a given SKU.

    Returns a structured dict containing stock level, daily sales velocity,
    and supplier lead time.  Returns an error dict if the SKU is unknown.
    """
    data = _MOCK_INVENTORY.get(sku.upper())
    if data is None:
        return {
            "found": False,
            "error": f"SKU '{sku}' not found in inventory system.",
            "sku": sku,
        }
    return {"found": True, **data}

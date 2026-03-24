import pytest

from ecommerce_erp.recommendation.engine import compute_restock

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_INVENTORY_LOW = {
    "sku": "SKU-001",
    "product_name": "Wireless Bluetooth Headphones",
    "current_stock": 15,
    "max_stock": 200,
    "stock_pct": 7.5,
    "daily_velocity": 8.0,
    "lead_time_days": 14,
    "unit_cost": 45.00,
    "warehouse": "WH-WEST-01",
}

_INVENTORY_HEALTHY = {
    **_INVENTORY_LOW,
    "current_stock": 200,
    "stock_pct": 100.0,
}

_MARKET_HIGH_RISING = {
    "found": True,
    "price_trend": "rising",
    "demand_signal": "high",
    "market_avg_price": 52.16,
    "notes": "Seasonal demand spike.",
    "source": "mock",
}

_MARKET_LOW_FALLING = {
    "found": True,
    "price_trend": "falling",
    "demand_signal": "low",
    "market_avg_price": 40.00,
    "notes": "Market oversaturation.",
    "source": "mock",
}


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestOutputStructure:
    def test_returns_json_and_markdown_keys(self) -> None:
        result = compute_restock(_INVENTORY_LOW)
        assert "json" in result
        assert "markdown" in result

    def test_json_contains_required_fields(self) -> None:
        result = compute_restock(_INVENTORY_LOW)
        for field in ("sku", "product_name", "recommendation", "restock_quantity",
                      "calculation", "approval_required", "approval_status"):
            assert field in result["json"], f"Missing JSON field: {field}"

    def test_approval_status_is_pending(self) -> None:
        result = compute_restock(_INVENTORY_LOW)
        assert result["json"]["approval_status"] == "PENDING_APPROVAL"
        assert result["json"]["approval_required"] is True


# ---------------------------------------------------------------------------
# Core Safety Stock math  (SKU-001: velocity=8, lead_time=14, stock=15)
# ---------------------------------------------------------------------------
#   lead_time_demand = 8 × 14 = 112
#   safety_stock     = 112 × 0.20 = 22.4
#   reorder_point    = 112 + 22.4 = 134.4
#   base_restock_qty = 134.4 - 15 = 119.4

class TestSafetyStockCalculation:
    def test_lead_time_demand(self) -> None:
        calc = compute_restock(_INVENTORY_LOW)["json"]["calculation"]
        assert calc["lead_time_demand"] == 112.0

    def test_safety_stock(self) -> None:
        calc = compute_restock(_INVENTORY_LOW)["json"]["calculation"]
        assert calc["safety_stock"] == 22.4

    def test_reorder_point(self) -> None:
        calc = compute_restock(_INVENTORY_LOW)["json"]["calculation"]
        assert calc["reorder_point"] == 134.4

    def test_base_restock_qty(self) -> None:
        calc = compute_restock(_INVENTORY_LOW)["json"]["calculation"]
        assert calc["base_restock_qty"] == 119.4

    def test_no_negative_restock_qty(self) -> None:
        result = compute_restock(_INVENTORY_HEALTHY)
        assert result["json"]["restock_quantity"] == 0
        assert result["json"]["recommendation"] == "NO_ACTION"


# ---------------------------------------------------------------------------
# Market-aware adjustments
# ---------------------------------------------------------------------------
# high demand (×1.15) + rising price (×1.10) → 119.4 × 1.265 ≈ 151

class TestMarketAdjustment:
    def test_high_demand_rising_price_increases_qty(self) -> None:
        result = compute_restock(_INVENTORY_LOW, _MARKET_HIGH_RISING)
        calc = result["json"]["calculation"]
        assert calc["demand_adjustment_factor"] == 1.15
        assert calc["price_adjustment_factor"] == 1.10
        expected = round(119.4 * 1.15 * 1.10)
        assert result["json"]["restock_quantity"] == expected

    def test_low_demand_falling_price_decreases_qty(self) -> None:
        result = compute_restock(_INVENTORY_LOW, _MARKET_LOW_FALLING)
        calc = result["json"]["calculation"]
        assert calc["demand_adjustment_factor"] == 0.90
        assert calc["price_adjustment_factor"] == 0.95
        expected = round(119.4 * 0.90 * 0.95)
        assert result["json"]["restock_quantity"] == expected

    def test_no_market_data_uses_neutral_factors(self) -> None:
        result = compute_restock(_INVENTORY_LOW, None)
        calc = result["json"]["calculation"]
        assert calc["demand_adjustment_factor"] == 1.0
        assert calc["price_adjustment_factor"] == 1.0

    def test_unfound_market_treated_as_no_market(self) -> None:
        bad_market = {"found": False, "error": "API failed"}
        result = compute_restock(_INVENTORY_LOW, bad_market)
        calc = result["json"]["calculation"]
        assert calc["demand_adjustment_factor"] == 1.0


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

class TestMarkdownOutput:
    def test_contains_sku_and_product_name(self) -> None:
        md = compute_restock(_INVENTORY_LOW)["markdown"]
        assert "SKU-001" in md
        assert "Wireless Bluetooth Headphones" in md

    def test_contains_approval_notice(self) -> None:
        md = compute_restock(_INVENTORY_LOW)["markdown"]
        assert "ACTION REQUIRED" in md
        assert "Human Approval" in md

    def test_contains_market_section_when_market_provided(self) -> None:
        md = compute_restock(_INVENTORY_LOW, _MARKET_HIGH_RISING)["markdown"]
        assert "Market-Aware Adjustment" in md
        assert "rising" in md

    def test_no_market_section_when_market_absent(self) -> None:
        md = compute_restock(_INVENTORY_LOW, None)["markdown"]
        assert "Market-Aware Adjustment" not in md

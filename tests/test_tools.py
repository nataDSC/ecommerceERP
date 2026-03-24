from ecommerce_erp.tools.inventory import get_inventory_stats
from ecommerce_erp.tools.market import fetch_market_research


# ── Inventory tool ────────────────────────────────────────────────────────

class TestGetInventoryStats:
    def test_known_sku_returns_found(self) -> None:
        result = get_inventory_stats("SKU-001")
        assert result["found"] is True
        assert result["sku"] == "SKU-001"

    def test_known_sku_contains_required_fields(self) -> None:
        result = get_inventory_stats("SKU-001")
        for field in ("stock_pct", "daily_velocity", "lead_time_days", "current_stock"):
            assert field in result, f"Missing field: {field}"

    def test_lookup_is_case_insensitive(self) -> None:
        assert get_inventory_stats("sku-001")["found"] is True
        assert get_inventory_stats("Sku-001")["found"] is True

    def test_unknown_sku_returns_not_found(self) -> None:
        result = get_inventory_stats("SKU-ZZZZ")
        assert result["found"] is False
        assert "error" in result

    def test_all_mock_skus_are_reachable(self) -> None:
        for sku in ("SKU-001", "SKU-002", "SKU-003", "SKU-004", "SKU-005"):
            assert get_inventory_stats(sku)["found"] is True, f"{sku} not reachable"


# ── Market research tool ──────────────────────────────────────────────────

class TestFetchMarketResearch:
    def test_known_product_returns_found(self) -> None:
        result = fetch_market_research("Wireless Bluetooth Headphones")
        assert result["found"] is True

    def test_known_product_contains_required_fields(self) -> None:
        result = fetch_market_research("Wireless Bluetooth Headphones")
        for field in ("price_trend", "demand_signal", "market_avg_price", "competitor_prices"):
            assert field in result, f"Missing field: {field}"

    def test_unknown_product_returns_default_data(self) -> None:
        result = fetch_market_research("Totally Unknown Widget XYZ")
        # Falls back to default — still "found" but with unknown signals
        assert result["found"] is True
        assert result["price_trend"] == "unknown"
        assert result["demand_signal"] == "unknown"

    def test_no_live_call_when_mock_enabled(self, monkeypatch) -> None:
        """Confirm TAVILY_MOCK=true never touches the live client."""
        monkeypatch.setenv("TAVILY_MOCK", "true")
        # If this tries a live call with no key it would raise; it should not.
        result = fetch_market_research("Mechanical Keyboard")
        assert result["source"] == "mock"

    def test_missing_api_key_in_live_mode_returns_error(self, monkeypatch) -> None:
        monkeypatch.setenv("TAVILY_MOCK", "false")
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        result = fetch_market_research("Some Product")
        assert result["found"] is False
        assert "error" in result

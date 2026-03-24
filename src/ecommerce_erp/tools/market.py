from __future__ import annotations

import os
from typing import Any

# ---------------------------------------------------------------------------
# Mock market dataset keyed on lowercase product name
# ---------------------------------------------------------------------------
_MOCK_MARKET_DATA: dict[str, dict[str, Any]] = {
    "wireless bluetooth headphones": {
        "product_query": "Wireless Bluetooth Headphones",
        "competitor_prices": [
            {"competitor": "TechMart", "price": 52.99, "currency": "USD", "in_stock": True},
            {"competitor": "AudioDirect", "price": 48.00, "currency": "USD", "in_stock": True},
            {"competitor": "ElectroHub", "price": 55.50, "currency": "USD", "in_stock": False},
        ],
        "market_avg_price": 52.16,
        "price_trend": "rising",
        "demand_signal": "high",
        "notes": "High demand expected due to seasonal consumer electronics cycle.",
        "source": "mock",
    },
    "usb-c charging cable (2m)": {
        "product_query": "USB-C Charging Cable (2m)",
        "competitor_prices": [
            {"competitor": "CableWorld", "price": 9.99, "currency": "USD", "in_stock": True},
            {"competitor": "TechMart", "price": 10.49, "currency": "USD", "in_stock": True},
            {"competitor": "QuickCharge", "price": 8.75, "currency": "USD", "in_stock": True},
        ],
        "market_avg_price": 9.74,
        "price_trend": "stable",
        "demand_signal": "moderate",
        "notes": "Commoditised market. Competitive pricing is the primary lever.",
        "source": "mock",
    },
    "ergonomic office chair": {
        "product_query": "Ergonomic Office Chair",
        "competitor_prices": [
            {"competitor": "OfficeDirect", "price": 299.00, "currency": "USD", "in_stock": True},
            {"competitor": "FurniturePlus", "price": 275.00, "currency": "USD", "in_stock": True},
            {"competitor": "ErgoCo", "price": 310.00, "currency": "USD", "in_stock": False},
        ],
        "market_avg_price": 294.67,
        "price_trend": "falling",
        "demand_signal": "low",
        "notes": "Market oversaturation; competitors running aggressive discount campaigns.",
        "source": "mock",
    },
    "mechanical keyboard": {
        "product_query": "Mechanical Keyboard",
        "competitor_prices": [
            {"competitor": "KeyboardKing", "price": 129.99, "currency": "USD", "in_stock": True},
            {"competitor": "TechMart", "price": 119.00, "currency": "USD", "in_stock": True},
            {"competitor": "TypeFast", "price": 135.00, "currency": "USD", "in_stock": True},
        ],
        "market_avg_price": 127.99,
        "price_trend": "rising",
        "demand_signal": "high",
        "notes": "Remote-work trend driving sustained peripheral demand.",
        "source": "mock",
    },
    "smart home hub": {
        "product_query": "Smart Home Hub",
        "competitor_prices": [
            {"competitor": "SmartTech", "price": 95.00, "currency": "USD", "in_stock": True},
            {"competitor": "HomeAuto", "price": 88.00, "currency": "USD", "in_stock": True},
            {"competitor": "TechMart", "price": 92.00, "currency": "USD", "in_stock": True},
        ],
        "market_avg_price": 91.67,
        "price_trend": "stable",
        "demand_signal": "moderate",
        "notes": "Steady demand from home automation adopters.",
        "source": "mock",
    },
}

_DEFAULT_MARKET_RESPONSE: dict[str, Any] = {
    "product_query": "Unknown Product",
    "competitor_prices": [],
    "market_avg_price": None,
    "price_trend": "unknown",
    "demand_signal": "unknown",
    "notes": "No market data available for this product.",
    "source": "mock",
}


def _use_mock() -> bool:
    return os.getenv("TAVILY_MOCK", "false").lower() in ("true", "1", "yes")


def _fetch_live(product_name: str) -> dict[str, Any]:
    """Issue a live Tavily search for competitor pricing data."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "TAVILY_API_KEY is not set. "
            "Add it to your .env file or set TAVILY_MOCK=true for offline mode."
        )

    from tavily import TavilyClient  # type: ignore[import-untyped]

    client = TavilyClient(api_key=api_key)
    query = f"{product_name} competitor pricing market trends"
    result = client.search(query=query, max_results=5, search_depth="advanced")

    competitor_prices: list[dict[str, Any]] = [
        {
            "competitor": r.get("title", "Unknown"),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:300],
        }
        for r in result.get("results", [])
    ]

    return {
        "product_query": product_name,
        "competitor_prices": competitor_prices,
        "market_avg_price": None,
        "price_trend": "unknown",
        "demand_signal": "unknown",
        "notes": f"Live Tavily search results for '{product_name}'.",
        "source": "tavily_live",
        "raw_result_count": len(competitor_prices),
    }


def fetch_market_research(product_name: str) -> dict[str, Any]:
    """
    Retrieve competitor pricing and market trend data for a product.

    Behaviour is controlled by the TAVILY_MOCK environment variable:
      - TAVILY_MOCK=true  → returns deterministic mock data (safe for unit tests)
      - TAVILY_MOCK=false → calls the live Tavily API (requires TAVILY_API_KEY)

    Returns structured JSON. On live-call failure, returns an error dict.
    """
    if _use_mock():
        key = product_name.lower()
        data = _MOCK_MARKET_DATA.get(key, _DEFAULT_MARKET_RESPONSE)
        return {"found": True, **data}

    try:
        data = _fetch_live(product_name)
        return {"found": True, **data}
    except Exception as exc:
        return {
            "found": False,
            "error": str(exc),
            "product_query": product_name,
            "source": "tavily_live",
        }

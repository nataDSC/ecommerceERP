from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Policy constants
# ---------------------------------------------------------------------------
_SAFETY_STOCK_BUFFER = 0.20  # 20% of lead-time demand

# Multipliers applied to the base restock quantity based on market signals
_DEMAND_ADJUSTMENT: dict[str, float] = {
    "high": 1.15,
    "moderate": 1.00,
    "low": 0.90,
    "unknown": 1.00,
}

_PRICE_TREND_ADJUSTMENT: dict[str, float] = {
    "rising": 1.10,   # buy more now before prices climb further
    "stable": 1.00,
    "falling": 0.95,  # wait for cheaper replenishment
    "unknown": 1.00,
}


def compute_restock(
    inventory: dict[str, Any],
    market: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compute a restock recommendation using the Safety Stock formula:

        lead_time_demand  = daily_velocity × lead_time_days
        safety_stock      = lead_time_demand × 0.20          (20% buffer)
        reorder_point     = lead_time_demand + safety_stock
        base_restock_qty  = max(0, reorder_point − current_stock)

    Market-aware adjustments (applied when market data is present):
        demand_factor     = lookup by demand_signal
        price_factor      = lookup by price_trend
        final_qty         = round(base_restock_qty × demand_factor × price_factor)

    Returns a dict with two keys:
        "json"     — machine-readable structured proposal
        "markdown" — human-readable Markdown block
    """
    daily_velocity: float = float(inventory["daily_velocity"])
    lead_time_days: int = int(inventory["lead_time_days"])
    current_stock: int = int(inventory["current_stock"])
    sku: str = inventory["sku"]
    product_name: str = inventory.get("product_name", "Unknown Product")

    # Core calculation
    lead_time_demand = daily_velocity * lead_time_days
    safety_stock = lead_time_demand * _SAFETY_STOCK_BUFFER
    reorder_point = lead_time_demand + safety_stock
    base_restock_qty = max(0.0, reorder_point - current_stock)

    # Market-aware adjustments
    demand_signal = "unknown"
    price_trend = "unknown"
    market_avg_price: float | None = None
    demand_adj = 1.0
    price_adj = 1.0
    market_notes = ""

    if market and market.get("found"):
        demand_signal = market.get("demand_signal", "unknown")
        price_trend = market.get("price_trend", "unknown")
        market_avg_price = market.get("market_avg_price")
        market_notes = market.get("notes", "")
        demand_adj = _DEMAND_ADJUSTMENT.get(demand_signal, 1.0)
        price_adj = _PRICE_TREND_ADJUSTMENT.get(price_trend, 1.0)

    final_qty = round(base_restock_qty * demand_adj * price_adj)
    action = "RESTOCK" if final_qty > 0 else "NO_ACTION"

    calculation = {
        "daily_velocity": daily_velocity,
        "lead_time_days": lead_time_days,
        "lead_time_demand": round(lead_time_demand, 4),
        "safety_stock": round(safety_stock, 4),
        "reorder_point": round(reorder_point, 4),
        "current_stock": current_stock,
        "base_restock_qty": round(base_restock_qty, 4),
        "demand_signal": demand_signal,
        "demand_adjustment_factor": demand_adj,
        "price_trend": price_trend,
        "price_adjustment_factor": price_adj,
        "final_restock_qty": final_qty,
        "market_avg_price": market_avg_price,
    }

    json_proposal: dict[str, Any] = {
        "sku": sku,
        "product_name": product_name,
        "recommendation": action,
        "restock_quantity": final_qty,
        "calculation": calculation,
        "approval_required": True,
        "approval_status": "PENDING_APPROVAL",
    }

    # ------------------------------------------------------------------
    # Markdown block
    # ------------------------------------------------------------------
    md: list[str] = [
        f"## Restock Proposal: `{sku}` — {product_name}",
        "",
        "### Inventory Status",
        f"- **Current Stock:** {current_stock} units  "
        f"({inventory.get('stock_pct', 'N/A')}% of max capacity)",
        f"- **Daily Velocity:** {daily_velocity} units/day",
        f"- **Supplier Lead Time:** {lead_time_days} days",
        "",
        "### Safety Stock Calculation",
        f"| Variable | Formula | Result |",
        f"|----------|---------|--------|",
        f"| Lead-Time Demand | {daily_velocity} × {lead_time_days} | **{round(lead_time_demand, 2)} units** |",
        f"| Safety Stock (20%) | {round(lead_time_demand, 2)} × 0.20 | **{round(safety_stock, 2)} units** |",
        f"| Reorder Point | {round(lead_time_demand, 2)} + {round(safety_stock, 2)} | **{round(reorder_point, 2)} units** |",
        f"| Base Restock Qty | {round(reorder_point, 2)} − {current_stock} | **{round(base_restock_qty, 2)} units** |",
        "",
    ]

    if market and market.get("found"):
        avg_price_str = f"${market_avg_price:.2f}" if market_avg_price is not None else "N/A"
        md += [
            "### Market-Aware Adjustment",
            f"| Signal | Value | Adjustment Factor |",
            f"|--------|-------|-------------------|",
            f"| Demand Signal | {demand_signal} | ×{demand_adj} |",
            f"| Price Trend | {price_trend} | ×{price_adj} |",
            f"| Market Avg Price | {avg_price_str} | — |",
        ]
        if market_notes:
            md.append(f"\n> 💡 **Market Context:** {market_notes}")
        md.append("")

    md += [
        "### Final Recommendation",
        f"| | |",
        f"|--|--|",
        f"| **Action** | {action} |",
        f"| **Restock Quantity** | **{final_qty} units** |",
        f"| **Approval Status** | PENDING_APPROVAL |",
        "",
        "> ⚠️ **ACTION REQUIRED: Awaiting Human Approval.**  "
        "This proposal must be reviewed and approved before any purchase order is placed.",
    ]

    return {
        "json": json_proposal,
        "markdown": "\n".join(md),
    }

import json
from pathlib import Path

import pytest

from ecommerce_erp.agent.orchestrator import build_graph, make_initial_state


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run(sku: str, tmp_path: Path) -> dict:
    """Build a fresh graph and run it for *sku*, writing logs to tmp_path."""
    import os
    os.environ["LOG_DIR"] = str(tmp_path)
    return build_graph().invoke(make_initial_state(sku))


# ---------------------------------------------------------------------------
# End-to-end loop scenarios
# ---------------------------------------------------------------------------

class TestFullAgentLoop:
    def test_low_stock_sku_triggers_market_research(self, tmp_path: Path) -> None:
        """SKU-001 (7.5% stock) must call market research before recommending."""
        result = _run("SKU-001", tmp_path)

        assert result["goal_satisfied"] is True
        assert result["error"] is None
        assert result["inventory_data"] is not None
        assert result["market_competitor_data"] is not None  # stock < 20% threshold
        assert result["final_recommendation"] is not None
        assert result["final_recommendation"]["json"]["restock_quantity"] > 0

    def test_healthy_stock_sku_skips_market_research(self, tmp_path: Path) -> None:
        """SKU-003 (80% stock) must NOT call market research."""
        result = _run("SKU-003", tmp_path)

        assert result["goal_satisfied"] is True
        assert result["inventory_data"] is not None
        assert result["market_competitor_data"] is None  # healthy stock — skipped
        assert result["final_recommendation"] is not None

    def test_boundary_stock_sku_skips_market_research(self, tmp_path: Path) -> None:
        """SKU-002 (exactly 20% stock) must NOT trigger market research (<20 required)."""
        result = _run("SKU-002", tmp_path)

        assert result["goal_satisfied"] is True
        assert result["market_competitor_data"] is None

    def test_unknown_sku_terminates_gracefully(self, tmp_path: Path) -> None:
        result = _run("SKU-ZZZZ", tmp_path)

        assert result["goal_satisfied"] is True
        assert result["error"] is not None
        assert result["final_recommendation"] is None

    def test_approval_status_is_pending(self, tmp_path: Path) -> None:
        result = _run("SKU-001", tmp_path)
        assert result["approval_status"] == "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Reasoning trace
# ---------------------------------------------------------------------------

class TestReasoningTrace:
    def test_trace_is_populated(self, tmp_path: Path) -> None:
        result = _run("SKU-001", tmp_path)
        # At minimum: plan+act+reflect per cycle × 3 cycles for low-stock SKU
        assert len(result["reasoning_steps"]) >= 6

    def test_all_phases_represented(self, tmp_path: Path) -> None:
        result = _run("SKU-001", tmp_path)
        phases = {step["phase"] for step in result["reasoning_steps"]}
        assert "PLAN" in phases
        assert "ACT" in phases
        assert "REFLECT" in phases

    def test_log_file_is_written(self, tmp_path: Path) -> None:
        _run("SKU-001", tmp_path)
        log_file = tmp_path / "reasoning_trace.log"
        assert log_file.exists(), "reasoning_trace.log was not created"
        lines = [ln for ln in log_file.read_text(encoding="utf-8").strip().split("\n") if ln]
        assert len(lines) >= 6, f"Expected ≥6 log lines, got {len(lines)}"

    def test_log_lines_are_valid_jsonl(self, tmp_path: Path) -> None:
        _run("SKU-001", tmp_path)
        log_file = tmp_path / "reasoning_trace.log"
        for i, line in enumerate(log_file.read_text(encoding="utf-8").strip().split("\n")):
            if not line.strip():
                continue
            parsed = json.loads(line)  # raises if not valid JSON
            assert "timestamp" in parsed, f"Line {i} missing 'timestamp'"
            assert "phase" in parsed, f"Line {i} missing 'phase'"
            assert "thought" in parsed, f"Line {i} missing 'thought'"


# ---------------------------------------------------------------------------
# Cost-guard integration
# ---------------------------------------------------------------------------

class TestCostGuardIntegration:
    def test_cost_guard_halts_loop(self, tmp_path: Path, monkeypatch) -> None:
        """Set limit to 0 so the very first external tool call is blocked."""
        monkeypatch.setenv("MAX_TOOL_CALLS_PER_CYCLE", "0")
        result = _run("SKU-001", tmp_path)

        assert result["goal_satisfied"] is True  # loop terminated
        assert result["error"] is not None
        assert "Cost-guard" in result["error"]
        assert result["final_recommendation"] is None

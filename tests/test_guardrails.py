import pytest

from ecommerce_erp.agent.guardrails import CostGuardError, check_cost_guard


class TestCheckCostGuard:
    def test_allows_calls_below_limit(self) -> None:
        state = {"tool_calls_this_cycle": 4}
        check_cost_guard(state)  # must not raise

    def test_allows_zero_calls(self) -> None:
        check_cost_guard({"tool_calls_this_cycle": 0})  # must not raise

    def test_blocks_at_default_limit(self) -> None:
        state = {"tool_calls_this_cycle": 5}
        with pytest.raises(CostGuardError, match="Cost-guard triggered"):
            check_cost_guard(state)

    def test_blocks_above_default_limit(self) -> None:
        state = {"tool_calls_this_cycle": 99}
        with pytest.raises(CostGuardError):
            check_cost_guard(state)

    def test_respects_custom_env_limit(self, monkeypatch) -> None:
        """MAX_TOOL_CALLS_PER_CYCLE is read dynamically — monkeypatch takes effect immediately."""
        monkeypatch.setenv("MAX_TOOL_CALLS_PER_CYCLE", "2")
        # 1 call: allowed
        check_cost_guard({"tool_calls_this_cycle": 1})
        # 2 calls: blocked (>= limit)
        with pytest.raises(CostGuardError):
            check_cost_guard({"tool_calls_this_cycle": 2})

    def test_missing_key_defaults_to_zero(self) -> None:
        check_cost_guard({})  # tool_calls_this_cycle defaults to 0 — must not raise

    def test_error_message_includes_counts(self) -> None:
        state = {"tool_calls_this_cycle": 5}
        with pytest.raises(CostGuardError, match=r"5/5"):
            check_cost_guard(state)

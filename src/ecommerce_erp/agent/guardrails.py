from __future__ import annotations

import os
from typing import Any


class CostGuardError(RuntimeError):
    """Raised when the per-cycle tool call limit is exceeded."""


def check_cost_guard(state: dict[str, Any]) -> None:
    """
    Check whether the tool-call budget for the current cycle has been exhausted.
    Reads MAX_TOOL_CALLS_PER_CYCLE from the environment at call-time so tests
    can override it via monkeypatch without reloading the module.

    Raises:
        CostGuardError: when tool_calls_this_cycle >= MAX_TOOL_CALLS_PER_CYCLE.
    """
    max_calls = int(os.getenv("MAX_TOOL_CALLS_PER_CYCLE", "5"))
    calls = state.get("tool_calls_this_cycle", 0)
    if calls >= max_calls:
        raise CostGuardError(
            f"Cost-guard triggered: {calls}/{max_calls} tool calls consumed this cycle. "
            "Halting to prevent token drain and infinite loops."
        )

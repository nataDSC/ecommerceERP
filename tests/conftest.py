import os

import pytest


@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Globally enforce mock mode for every test.
    Prevents any test from accidentally issuing a live Tavily API call.
    """
    monkeypatch.setenv("TAVILY_MOCK", "true")
    monkeypatch.setenv("MAX_TOOL_CALLS_PER_CYCLE", "5")

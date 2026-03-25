from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from langgraph.types import Command

from ecommerce_erp.agent.orchestrator import build_graph, make_initial_state


@dataclass
class ApiRunSession:
    graph: Any
    config: dict[str, Any]
    state: dict[str, Any]
    created_at: str


class RunRegistry:
    def __init__(self) -> None:
        self._runs: dict[str, ApiRunSession] = {}
        self._lock = threading.Lock()

    def start_run(self, *, sku: str, use_mock: bool) -> tuple[str, dict[str, Any]]:
        os.environ["TAVILY_MOCK"] = "true" if use_mock else "false"

        run_id = str(uuid.uuid4())
        graph = build_graph(human_in_the_loop=True)
        config = {"configurable": {"thread_id": f"api-{run_id}"}}
        state = graph.invoke(make_initial_state(sku), config=config)

        session = ApiRunSession(
            graph=graph,
            config=config,
            state=state,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._runs[run_id] = session
        return run_id, state

    def get_state(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._runs.get(run_id)
        if session is None:
            raise KeyError(run_id)
        return session.state

    def resume(self, run_id: str, decision: str) -> dict[str, Any]:
        with self._lock:
            session = self._runs.get(run_id)
        if session is None:
            raise KeyError(run_id)

        resumed = session.graph.invoke(Command(resume=decision), config=session.config)
        session.state = resumed
        return resumed


registry = RunRegistry()

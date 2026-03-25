from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from langgraph.types import Command

from ecommerce_erp.agent.orchestrator import build_graph, make_initial_state
from ecommerce_erp.api.persistence import RunPersistence, create_run_persistence


@dataclass
class ApiRunSession:
    graph: Any
    config: dict[str, Any]
    state: dict[str, Any]
    sku: str
    created_at: str


class RunRegistry:
    def __init__(self) -> None:
        self._runs: dict[str, ApiRunSession] = {}
        self._lock = threading.Lock()
        self._persistence: RunPersistence = create_run_persistence()

    @staticmethod
    def _state_status(state: dict[str, Any]) -> str:
        if state.get("error"):
            return "error"
        if "__interrupt__" in state:
            return "paused_waiting_approval"
        if state.get("goal_satisfied"):
            return "completed"
        return "running"

    @staticmethod
    def _from_persisted(row: dict[str, Any]) -> dict[str, Any]:
        state: dict[str, Any] = {
            "sku": row.get("sku"),
            "approval_status": row.get("approval_status"),
            "error": row.get("error"),
            "tool_calls_this_cycle": int(row.get("tool_calls_this_cycle", 0)),
            "goal_satisfied": row.get("status") == "completed",
            "reasoning_steps": [{}] * int(row.get("reasoning_steps_count", 0)),
        }

        proposal_json = row.get("final_recommendation_json")
        proposal_markdown = row.get("final_recommendation_markdown")
        if proposal_json is not None or proposal_markdown is not None:
            state["final_recommendation"] = {
                "json": proposal_json,
                "markdown": proposal_markdown,
            }

        if row.get("paused"):
            # Presence of the key indicates paused state for API serializers.
            state["__interrupt__"] = {"persisted": True}

        return state

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
            sku=sku,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._runs[run_id] = session

        self._persistence.upsert_run(
            run_id=run_id,
            sku=sku,
            status=self._state_status(state),
            state=state,
            created_at=session.created_at,
        )
        return run_id, state

    def get_state(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            session = self._runs.get(run_id)
        if session is not None:
            return session.state

        persisted = self._persistence.fetch_run(run_id)
        if persisted is None:
            raise KeyError(run_id)
        return self._from_persisted(persisted)

    def resume(self, run_id: str, decision: str) -> dict[str, Any]:
        with self._lock:
            session = self._runs.get(run_id)
        if session is None:
            raise KeyError(run_id)

        resumed = session.graph.invoke(Command(resume=decision), config=session.config)
        session.state = resumed
        self._persistence.record_approval_event(run_id=run_id, decision=decision)
        self._persistence.upsert_run(
            run_id=run_id,
            sku=session.sku,
            status=self._state_status(resumed),
            state=resumed,
            created_at=session.created_at,
        )
        return resumed

    def get_approval_history(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock:
            in_memory = self._runs.get(run_id) is not None

        if not in_memory and self._persistence.fetch_run(run_id) is None:
            raise KeyError(run_id)

        return self._persistence.fetch_approval_events(run_id)


registry = RunRegistry()

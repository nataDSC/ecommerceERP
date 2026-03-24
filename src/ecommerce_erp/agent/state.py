from __future__ import annotations

import operator
from enum import Enum
from typing import Annotated, Any, TypedDict


class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Phase(str, Enum):
    PLAN = "PLAN"
    ACT = "ACT"
    REFLECT = "REFLECT"
    DONE = "DONE"


class ReasoningStep(TypedDict):
    phase: str
    thought: str
    action: str | None
    observation: str | None
    tool_call_count: int


class AgentState(TypedDict):
    sku: str
    inventory_data: dict[str, Any] | None
    market_competitor_data: dict[str, Any] | None
    # operator.add reducer: each node returns only the NEW steps to append
    reasoning_steps: Annotated[list[ReasoningStep], operator.add]
    final_recommendation: dict[str, Any] | None
    approval_status: str
    tool_calls_this_cycle: int
    plan: list[str]
    current_phase: str
    goal_satisfied: bool
    error: str | None

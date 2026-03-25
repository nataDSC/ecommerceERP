from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    sku: str = Field(..., examples=["SKU-001"])
    use_mock: bool = True


class AnalyzeResponse(BaseModel):
    run_id: str
    status: str
    approval_status: str | None = None
    paused: bool = False
    error: str | None = None


class DecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]


class RunStateResponse(BaseModel):
    run_id: str
    status: str
    approval_status: str | None = None
    paused: bool = False
    error: str | None = None
    tool_calls_this_cycle: int = 0
    reasoning_steps_count: int = 0


class ProposalResponse(BaseModel):
    run_id: str
    approval_status: str | None = None
    proposal_json: dict[str, Any] | None = None
    proposal_markdown: str | None = None


class ApprovalEventResponse(BaseModel):
    id: int
    decision: str
    source: str
    created_at: str


class ApprovalHistoryResponse(BaseModel):
    run_id: str
    events: list[ApprovalEventResponse] = []


class ApiConfigResponse(BaseModel):
    db_backend: str
    db_target: str

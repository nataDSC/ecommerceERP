from __future__ import annotations

import os
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status

from ecommerce_erp.api.auth import require_api_user
from ecommerce_erp.api.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    DecisionRequest,
    ProposalResponse,
    RunStateResponse,
)
from ecommerce_erp.api.store import registry


def _state_status(state: dict[str, Any]) -> str:
    if state.get("error"):
        return "error"
    if "__interrupt__" in state:
        return "paused_waiting_approval"
    if state.get("goal_satisfied"):
        return "completed"
    return "running"


def _to_run_state_response(run_id: str, state: dict[str, Any]) -> RunStateResponse:
    return RunStateResponse(
        run_id=run_id,
        status=_state_status(state),
        approval_status=state.get("approval_status"),
        paused="__interrupt__" in state,
        error=state.get("error"),
        tool_calls_this_cycle=int(state.get("tool_calls_this_cycle", 0)),
        reasoning_steps_count=len(state.get("reasoning_steps", [])),
    )


def create_app() -> FastAPI:
    app = FastAPI(title="ecommerceERP API", version="0.2.0")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/analyze", response_model=AnalyzeResponse)
    def start_analysis(
        payload: AnalyzeRequest,
        _: str = Depends(require_api_user),
    ) -> AnalyzeResponse:
        run_id, state = registry.start_run(sku=payload.sku, use_mock=payload.use_mock)
        return AnalyzeResponse(
            run_id=run_id,
            status=_state_status(state),
            approval_status=state.get("approval_status"),
            paused="__interrupt__" in state,
            error=state.get("error"),
        )

    @app.get("/api/v1/analyze/{run_id}", response_model=RunStateResponse)
    def get_run_state(run_id: str, _: str = Depends(require_api_user)) -> RunStateResponse:
        try:
            state = registry.get_state(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return _to_run_state_response(run_id, state)

    @app.get("/api/v1/analyze/{run_id}/proposal", response_model=ProposalResponse)
    def get_proposal(run_id: str, _: str = Depends(require_api_user)) -> ProposalResponse:
        try:
            state = registry.get_state(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        proposal = state.get("final_recommendation")
        if not proposal:
            return ProposalResponse(run_id=run_id, approval_status=state.get("approval_status"))

        return ProposalResponse(
            run_id=run_id,
            approval_status=state.get("approval_status"),
            proposal_json=proposal.get("json"),
            proposal_markdown=proposal.get("markdown"),
        )

    @app.post("/api/v1/analyze/{run_id}/decision", response_model=RunStateResponse)
    def post_decision(
        run_id: str,
        payload: DecisionRequest,
        _: str = Depends(require_api_user),
    ) -> RunStateResponse:
        try:
            current = registry.get_state(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        if "__interrupt__" not in current:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Run is not waiting for approval.",
            )

        try:
            updated = registry.resume(run_id, payload.decision)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Run cannot be resumed from persisted state. Please start a new run.",
            )
        return _to_run_state_response(run_id, updated)

    return app


def run() -> None:
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("ecommerce_erp.api.app:create_app", factory=True, host=host, port=port)


app = create_app()

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from ecommerce_erp.api.app import create_app
from ecommerce_erp.api.store import registry


def _auth_header(user: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _clear_registry() -> None:
    with registry._lock:  # type: ignore[attr-defined]
        registry._runs.clear()  # type: ignore[attr-defined]


def test_healthz() -> None:
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_and_approval_flow(monkeypatch) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    _clear_registry()

    client = TestClient(create_app())

    start = client.post("/api/v1/analyze", json={"sku": "SKU-001", "use_mock": True})
    assert start.status_code == 200
    data = start.json()
    assert data["status"] == "paused_waiting_approval"
    assert data["paused"] is True
    run_id = data["run_id"]

    state_before = client.get(f"/api/v1/analyze/{run_id}")
    assert state_before.status_code == 200
    assert state_before.json()["approval_status"] == "PENDING_APPROVAL"

    decision = client.post(
        f"/api/v1/analyze/{run_id}/decision",
        json={"decision": "APPROVED"},
    )
    assert decision.status_code == 200
    assert decision.json()["approval_status"] == "APPROVED"
    assert decision.json()["paused"] is False

    proposal = client.get(f"/api/v1/analyze/{run_id}/proposal")
    assert proposal.status_code == 200
    assert proposal.json()["approval_status"] == "APPROVED"
    assert proposal.json()["proposal_json"]["approval_status"] == "APPROVED"


def test_auth_required_rejects_missing_credentials(monkeypatch) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_BASIC_AUTH_USER", "demo")
    monkeypatch.setenv("API_BASIC_AUTH_PASS", "secret")
    _clear_registry()

    client = TestClient(create_app())

    unauthorized = client.post("/api/v1/analyze", json={"sku": "SKU-001", "use_mock": True})
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/v1/analyze",
        json={"sku": "SKU-001", "use_mock": True},
        headers=_auth_header("demo", "secret"),
    )
    assert authorized.status_code == 200

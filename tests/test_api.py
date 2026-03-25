from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from ecommerce_erp.api.app import create_app
from ecommerce_erp.api.persistence import PostgresRunPersistence, SQLiteRunPersistence, create_run_persistence
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


def test_config_endpoint_returns_sanitized_target(monkeypatch) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("API_DB_BACKEND", "postgres")
    monkeypatch.setenv(
        "API_POSTGRES_DSN",
        "postgresql://demo_user:super_secret@localhost:5432/ecommerce_erp?sslmode=disable",
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    body = response.json()
    assert body["db_backend"] == "postgres"
    assert body["db_target"] == "postgresql://localhost:5432/ecommerce_erp"
    assert "super_secret" not in body["db_target"]
    assert "demo_user" not in body["db_target"]


def test_config_endpoint_auth_enforced(monkeypatch) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_BASIC_AUTH_USER", "demo")
    monkeypatch.setenv("API_BASIC_AUTH_PASS", "secret")

    client = TestClient(create_app())

    unauthorized = client.get("/api/v1/config")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/v1/config", headers=_auth_header("demo", "secret"))
    assert authorized.status_code == 200


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


def test_persisted_state_and_proposal_are_readable_after_memory_clear(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("API_DB_PATH", str(tmp_path / "api_runs.db"))
    _clear_registry()

    client = TestClient(create_app())

    start = client.post("/api/v1/analyze", json={"sku": "SKU-001", "use_mock": True})
    assert start.status_code == 200
    run_id = start.json()["run_id"]

    decision = client.post(
        f"/api/v1/analyze/{run_id}/decision",
        json={"decision": "APPROVED"},
    )
    assert decision.status_code == 200

    _clear_registry()

    state = client.get(f"/api/v1/analyze/{run_id}")
    assert state.status_code == 200
    assert state.json()["status"] == "completed"
    assert state.json()["approval_status"] == "APPROVED"
    assert state.json()["paused"] is False

    proposal = client.get(f"/api/v1/analyze/{run_id}/proposal")
    assert proposal.status_code == 200
    assert proposal.json()["approval_status"] == "APPROVED"
    assert proposal.json()["proposal_json"]["approval_status"] == "APPROVED"


def test_resume_rejected_when_only_persisted_state_exists(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("API_DB_PATH", str(tmp_path / "api_runs.db"))
    _clear_registry()

    client = TestClient(create_app())

    start = client.post("/api/v1/analyze", json={"sku": "SKU-001", "use_mock": True})
    assert start.status_code == 200
    run_id = start.json()["run_id"]

    _clear_registry()

    response = client.post(
        f"/api/v1/analyze/{run_id}/decision",
        json={"decision": "APPROVED"},
    )
    assert response.status_code == 409
    assert "cannot be resumed" in response.json()["detail"]


def test_approval_history_endpoint_returns_events(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("API_AUTH_ENABLED", "false")
    monkeypatch.setenv("API_DB_BACKEND", "sqlite")
    monkeypatch.setenv("API_DB_PATH", str(tmp_path / "api_runs.db"))
    _clear_registry()

    client = TestClient(create_app())

    start = client.post("/api/v1/analyze", json={"sku": "SKU-001", "use_mock": True})
    assert start.status_code == 200
    run_id = start.json()["run_id"]

    decision = client.post(
        f"/api/v1/analyze/{run_id}/decision",
        json={"decision": "APPROVED"},
    )
    assert decision.status_code == 200

    history = client.get(f"/api/v1/analyze/{run_id}/approval-history")
    assert history.status_code == 200
    body = history.json()
    assert body["run_id"] == run_id
    assert len(body["events"]) == 1
    assert body["events"][0]["decision"] == "APPROVED"
    assert body["events"][0]["source"] == "api"


def test_create_run_persistence_backend_switch(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("API_DB_BACKEND", "sqlite")
    monkeypatch.setenv("API_DB_PATH", str(tmp_path / "api_runs.db"))
    sqlite_backend = create_run_persistence()
    assert isinstance(sqlite_backend, SQLiteRunPersistence)

    monkeypatch.setenv("API_DB_BACKEND", "postgres")
    monkeypatch.setenv("API_POSTGRES_DSN", "postgresql://user:pass@localhost:5432/db")
    postgres_backend = create_run_persistence()
    assert isinstance(postgres_backend, PostgresRunPersistence)

    monkeypatch.setenv("API_DB_BACKEND", "unsupported")
    try:
        create_run_persistence()
    except ValueError as exc:
        assert "Unsupported API_DB_BACKEND" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported backend")

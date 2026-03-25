from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class RunPersistence(Protocol):
    def upsert_run(
        self,
        *,
        run_id: str,
        sku: str,
        status: str,
        state: dict[str, Any],
        created_at: str,
    ) -> None: ...

    def record_approval_event(self, *, run_id: str, decision: str, source: str = "api") -> None: ...

    def fetch_run(self, run_id: str) -> dict[str, Any] | None: ...

    def fetch_approval_events(self, run_id: str) -> list[dict[str, Any]]: ...


class SQLiteRunPersistence:
    """Persists run snapshots and approval audit events in SQLite."""

    def __init__(
        self,
        *,
        db_path_env: str = "API_DB_PATH",
        default_path: str = ".data/api_runs.db",
    ) -> None:
        self._db_path_env = db_path_env
        self._default_path = default_path

    def _db_path(self) -> str:
        return os.getenv(self._db_path_env, self._default_path)

    def _connect(self) -> sqlite3.Connection:
        db_path = Path(self._db_path())
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        self._ensure_schema(conn)
        return conn

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                sku TEXT NOT NULL,
                status TEXT NOT NULL,
                approval_status TEXT,
                paused INTEGER NOT NULL,
                error TEXT,
                tool_calls_this_cycle INTEGER NOT NULL DEFAULT 0,
                reasoning_steps_count INTEGER NOT NULL DEFAULT 0,
                final_recommendation_json TEXT,
                final_recommendation_markdown TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
            """
        )
        conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _serialize_json(value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=True, default=str)

    @staticmethod
    def _deserialize_json(value: str | None) -> Any:
        if not value:
            return None
        return json.loads(value)

    def upsert_run(
        self,
        *,
        run_id: str,
        sku: str,
        status: str,
        state: dict[str, Any],
        created_at: str,
    ) -> None:
        final = state.get("final_recommendation")
        proposal_json = final.get("json") if isinstance(final, dict) else None
        proposal_markdown = final.get("markdown") if isinstance(final, dict) else None
        now = self._now()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id,
                    sku,
                    status,
                    approval_status,
                    paused,
                    error,
                    tool_calls_this_cycle,
                    reasoning_steps_count,
                    final_recommendation_json,
                    final_recommendation_markdown,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    status=excluded.status,
                    approval_status=excluded.approval_status,
                    paused=excluded.paused,
                    error=excluded.error,
                    tool_calls_this_cycle=excluded.tool_calls_this_cycle,
                    reasoning_steps_count=excluded.reasoning_steps_count,
                    final_recommendation_json=excluded.final_recommendation_json,
                    final_recommendation_markdown=excluded.final_recommendation_markdown,
                    updated_at=excluded.updated_at
                """,
                (
                    run_id,
                    sku,
                    status,
                    state.get("approval_status"),
                    1 if "__interrupt__" in state else 0,
                    state.get("error"),
                    int(state.get("tool_calls_this_cycle", 0)),
                    len(state.get("reasoning_steps", [])),
                    self._serialize_json(proposal_json),
                    proposal_markdown,
                    created_at,
                    now,
                ),
            )
            conn.commit()

    def record_approval_event(self, *, run_id: str, decision: str, source: str = "api") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approval_events (run_id, decision, source, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, decision, source, self._now()),
            )
            conn.commit()

    def fetch_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    run_id,
                    sku,
                    status,
                    approval_status,
                    paused,
                    error,
                    tool_calls_this_cycle,
                    reasoning_steps_count,
                    final_recommendation_json,
                    final_recommendation_markdown,
                    created_at,
                    updated_at
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "run_id": row["run_id"],
            "sku": row["sku"],
            "status": row["status"],
            "approval_status": row["approval_status"],
            "paused": bool(row["paused"]),
            "error": row["error"],
            "tool_calls_this_cycle": int(row["tool_calls_this_cycle"] or 0),
            "reasoning_steps_count": int(row["reasoning_steps_count"] or 0),
            "final_recommendation_json": self._deserialize_json(row["final_recommendation_json"]),
            "final_recommendation_markdown": row["final_recommendation_markdown"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def fetch_approval_events(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, decision, source, created_at
                FROM approval_events
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

        return [
            {
                "id": int(row["id"]),
                "decision": row["decision"],
                "source": row["source"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


class PostgresRunPersistence:
    """Persists run snapshots and approval events in Postgres."""

    def __init__(self, *, dsn_env: str = "API_POSTGRES_DSN") -> None:
        self._dsn_env = dsn_env

    def _dsn(self) -> str:
        dsn = os.getenv(self._dsn_env)
        if not dsn:
            raise ValueError(f"Missing required env var: {self._dsn_env}")
        return dsn

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "Postgres backend requires 'psycopg'. Install project dependencies first."
            ) from exc

        conn = psycopg.connect(self._dsn(), row_factory=dict_row)
        self._ensure_schema(conn)
        return conn

    @staticmethod
    def _ensure_schema(conn) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approval_status TEXT,
                    paused BOOLEAN NOT NULL,
                    error TEXT,
                    tool_calls_this_cycle INTEGER NOT NULL DEFAULT 0,
                    reasoning_steps_count INTEGER NOT NULL DEFAULT 0,
                    final_recommendation_json JSONB,
                    final_recommendation_markdown TEXT,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_events (
                    id BIGSERIAL PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    decision TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
        conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _serialize_json(value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=True, default=str)

    def upsert_run(
        self,
        *,
        run_id: str,
        sku: str,
        status: str,
        state: dict[str, Any],
        created_at: str,
    ) -> None:
        final = state.get("final_recommendation")
        proposal_json = final.get("json") if isinstance(final, dict) else None
        proposal_markdown = final.get("markdown") if isinstance(final, dict) else None
        now = self._now()

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO runs (
                        run_id,
                        sku,
                        status,
                        approval_status,
                        paused,
                        error,
                        tool_calls_this_cycle,
                        reasoning_steps_count,
                        final_recommendation_json,
                        final_recommendation_markdown,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::timestamptz, %s::timestamptz
                    )
                    ON CONFLICT(run_id) DO UPDATE SET
                        status=EXCLUDED.status,
                        approval_status=EXCLUDED.approval_status,
                        paused=EXCLUDED.paused,
                        error=EXCLUDED.error,
                        tool_calls_this_cycle=EXCLUDED.tool_calls_this_cycle,
                        reasoning_steps_count=EXCLUDED.reasoning_steps_count,
                        final_recommendation_json=EXCLUDED.final_recommendation_json,
                        final_recommendation_markdown=EXCLUDED.final_recommendation_markdown,
                        updated_at=EXCLUDED.updated_at
                    """,
                    (
                        run_id,
                        sku,
                        status,
                        state.get("approval_status"),
                        "__interrupt__" in state,
                        state.get("error"),
                        int(state.get("tool_calls_this_cycle", 0)),
                        len(state.get("reasoning_steps", [])),
                        self._serialize_json(proposal_json),
                        proposal_markdown,
                        created_at,
                        now,
                    ),
                )
            conn.commit()

    def record_approval_event(self, *, run_id: str, decision: str, source: str = "api") -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO approval_events (run_id, decision, source, created_at)
                    VALUES (%s, %s, %s, %s::timestamptz)
                    """,
                    (run_id, decision, source, self._now()),
                )
            conn.commit()

    def fetch_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        run_id,
                        sku,
                        status,
                        approval_status,
                        paused,
                        error,
                        tool_calls_this_cycle,
                        reasoning_steps_count,
                        final_recommendation_json,
                        final_recommendation_markdown,
                        created_at,
                        updated_at
                    FROM runs
                    WHERE run_id = %s
                    """,
                    (run_id,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return {
            "run_id": row["run_id"],
            "sku": row["sku"],
            "status": row["status"],
            "approval_status": row["approval_status"],
            "paused": bool(row["paused"]),
            "error": row["error"],
            "tool_calls_this_cycle": int(row["tool_calls_this_cycle"] or 0),
            "reasoning_steps_count": int(row["reasoning_steps_count"] or 0),
            "final_recommendation_json": row["final_recommendation_json"],
            "final_recommendation_markdown": row["final_recommendation_markdown"],
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def fetch_approval_events(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, decision, source, created_at
                    FROM approval_events
                    WHERE run_id = %s
                    ORDER BY id ASC
                    """,
                    (run_id,),
                )
                rows = cur.fetchall()

        return [
            {
                "id": int(row["id"]),
                "decision": row["decision"],
                "source": row["source"],
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]


def create_run_persistence() -> RunPersistence:
    backend = os.getenv("API_DB_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite":
        return SQLiteRunPersistence()
    if backend == "postgres":
        return PostgresRunPersistence()
    raise ValueError("Unsupported API_DB_BACKEND. Use 'sqlite' or 'postgres'.")

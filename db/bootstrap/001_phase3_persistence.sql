BEGIN;

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
);

CREATE TABLE IF NOT EXISTS approval_events (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    decision TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs (status);
CREATE INDEX IF NOT EXISTS idx_runs_updated_at ON runs (updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_events_run_id ON approval_events (run_id);
CREATE INDEX IF NOT EXISTS idx_approval_events_created_at ON approval_events (created_at DESC);

COMMIT;
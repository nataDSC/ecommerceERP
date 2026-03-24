from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ecommerce_erp.utils.sanitization import mask_sensitive_data


def _log_path() -> Path:
    log_dir = Path(os.getenv("LOG_DIR", "./logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "reasoning_trace.log"


def log_event(
    phase: str,
    thought: str,
    action: str | None = None,
    observation: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Append a single JSONL event to reasoning_trace.log.

    Every string field is passed through mask_sensitive_data before writing,
    ensuring that no API keys or PII ever reach the log file.
    """
    event: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": mask_sensitive_data(str(phase)),
        "thought": mask_sensitive_data(thought),
        "action": mask_sensitive_data(action) if action else None,
        "observation": mask_sensitive_data(observation) if observation else None,
    }
    if metadata:
        event["metadata"] = metadata

    with _log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")

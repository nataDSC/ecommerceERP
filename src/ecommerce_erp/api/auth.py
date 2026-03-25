from __future__ import annotations

import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic(auto_error=False)


def _auth_enabled() -> bool:
    return os.getenv("API_AUTH_ENABLED", "false").lower() in ("1", "true", "yes")


def require_api_user(credentials: HTTPBasicCredentials | None = Depends(security)) -> str:
    """
    Optional basic-auth gate for API endpoints.

    - Disabled by default (API_AUTH_ENABLED=false)
    - When enabled, credentials are read from env:
      API_BASIC_AUTH_USER / API_BASIC_AUTH_PASS
    """
    if not _auth_enabled():
        return "anonymous"

    expected_user = os.getenv("API_BASIC_AUTH_USER")
    expected_pass = os.getenv("API_BASIC_AUTH_PASS")
    if not expected_user or not expected_pass:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Basic auth is enabled but API_BASIC_AUTH_USER/API_BASIC_AUTH_PASS "
                "are not configured."
            ),
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    user_ok = secrets.compare_digest(credentials.username, expected_user)
    pass_ok = secrets.compare_digest(credentials.password, expected_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username

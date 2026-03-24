from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Ordered from most-specific to most-general to avoid partial rewrites.
# ---------------------------------------------------------------------------
_REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # OpenAI-style secret keys  (sk-..., sk-proj-...)
    (re.compile(r"\bsk-[A-Za-z0-9\-]{20,}\b"), "[API_KEY_REDACTED]"),
    # Stripe live/test keys
    (re.compile(r"\b(?:pk|sk)_(?:live|test)_[A-Za-z0-9]{24,}\b"), "[STRIPE_KEY_REDACTED]"),
    # GitHub personal access tokens (classic + fine-grained)
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "[GITHUB_PAT_REDACTED]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"), "[GITHUB_PAT_REDACTED]"),
    # Tavily API keys
    (re.compile(r"\btvly-[A-Za-z0-9_\-]{20,}\b"), "[TAVILY_KEY_REDACTED]"),
    # AWS access key IDs
    (re.compile(r"\b(?:AKIA|AIPA|ABIA|ACCA)[A-Z0-9]{16}\b"), "[AWS_KEY_REDACTED]"),
    # Bearer tokens in Authorization headers
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/\-]+=*", re.IGNORECASE), "Bearer [TOKEN_REDACTED]"),
    # Generic high-entropy tokens  (≥40 hex chars)
    (re.compile(r"\b[0-9a-fA-F]{40,}\b"), "[HEX_SECRET_REDACTED]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    # Credit card numbers  (13–19 digit groups separated by spaces or dashes)
    (re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{1,4}\b"), "[CARD_NUM_REDACTED]"),
    # US Social Security Numbers
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
]


def mask_sensitive_data(text: str) -> str:
    """
    Redact known sensitive patterns from *text* before it is logged or stored.

    Handles: API keys, OAuth/Bearer tokens, GitHub PATs, AWS key IDs, Tavily
    keys, email addresses, credit card numbers, and US SSNs.

    Safe to call on any string, including normal log messages — non-matching
    content is returned unchanged.
    """
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

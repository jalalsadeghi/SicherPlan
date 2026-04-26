"""Recursive redaction helpers for assistant tool inputs and outputs."""

from __future__ import annotations

import re
from typing import Any


_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "password_hash",
    "token",
    "jwt",
    "secret",
    "api_key",
    "authorization",
    "refresh_token",
    "reset_token",
    "social_insurance_no",
    "tax_id",
    "bank",
    "iban",
    "bic",
    "health_insurance",
    "religion",
    "private_hr",
    "payroll_amount",
    "salary",
    "wage",
)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+\b"),
)


def redact_tool_payload(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                result[key_text] = "[REDACTED]"
            else:
                result[key_text] = redact_tool_payload(item)
        return result
    if isinstance(value, list):
        return [redact_tool_payload(item) for item in value[:50]]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _redact_string(value: str) -> str:
    text = value
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def _is_sensitive_key(key: str) -> bool:
    lowered = key.strip().casefold()
    return any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS)

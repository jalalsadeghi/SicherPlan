"""Configurable in-process rate limiting for high-risk HTTP endpoints."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.errors import ApiException


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    name: str
    max_requests: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self._entries: dict[tuple[str, str], deque[datetime]] = {}

    def assert_allowed(
        self,
        rule: RateLimitRule,
        *,
        principal: str,
        now: datetime | None = None,
    ) -> None:
        if not self.enabled:
            return
        observed_at = now or datetime.now(UTC)
        cutoff = observed_at - timedelta(seconds=rule.window_seconds)
        bucket = self._entries.setdefault((rule.name, principal), deque())
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= rule.max_requests:
            raise ApiException(
                429,
                "platform.rate_limited",
                "errors.platform.rate_limited",
                {
                    "rule": rule.name,
                    "window_seconds": rule.window_seconds,
                    "max_requests": rule.max_requests,
                },
            )
        bucket.append(observed_at)


rate_limiter = InMemoryRateLimiter(enabled=settings.security_rate_limit_enabled)

AUTH_REFRESH_RULE = RateLimitRule(
    name="auth.refresh",
    max_requests=settings.security_rate_limit_auth_refresh_max,
    window_seconds=settings.security_rate_limit_window_seconds,
)
DOCUMENT_DOWNLOAD_RULE = RateLimitRule(
    name="docs.download",
    max_requests=settings.security_rate_limit_document_download_max,
    window_seconds=settings.security_rate_limit_window_seconds,
)
REPORT_EXPORT_RULE = RateLimitRule(
    name="reporting.export",
    max_requests=settings.security_rate_limit_report_export_max,
    window_seconds=settings.security_rate_limit_window_seconds,
)

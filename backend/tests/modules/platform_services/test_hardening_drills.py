from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from app.errors import ApiException
from app.hardening_manifest import CHECKS
from app.rate_limit import InMemoryRateLimiter, RateLimitRule


class TestHardeningDrills(unittest.TestCase):
    def test_rate_limiter_blocks_after_threshold(self) -> None:
        limiter = InMemoryRateLimiter(enabled=True)
        rule = RateLimitRule(name="docs.download", max_requests=2, window_seconds=300)
        now = datetime.now(UTC)

        limiter.assert_allowed(rule, principal="tenant:user", now=now)
        limiter.assert_allowed(rule, principal="tenant:user", now=now + timedelta(seconds=1))
        with self.assertRaises(ApiException) as exc:
            limiter.assert_allowed(rule, principal="tenant:user", now=now + timedelta(seconds=2))

        self.assertEqual(exc.exception.status_code, 429)
        self.assertEqual(exc.exception.code, "platform.rate_limited")

    def test_hardening_manifest_covers_restore_and_security_checks(self) -> None:
        check_names = {row["name"] for row in CHECKS}
        self.assertIn("restore_validation", check_names)
        self.assertIn("security_drills", check_names)
        self.assertIn("reporting_query_probe", check_names)


if __name__ == "__main__":
    unittest.main()

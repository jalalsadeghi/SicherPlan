from __future__ import annotations

import unittest

from app.db.rls import apply_rls_context, clear_rls_context


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute(self, statement, params=None):  # noqa: ANN001
        self.calls.append((str(statement), params))
        return None


class TestOptionalRlsHelpers(unittest.TestCase):
    def test_apply_rls_context_sets_tenant_and_bypass_flags(self) -> None:
        session = _FakeSession()

        apply_rls_context(session, tenant_id="tenant-1", bypass=False, mode="enforce")

        sql, params = session.calls[-1]
        self.assertIn("set_config('app.rls_mode'", sql)
        self.assertEqual(params["mode"], "enforce")
        self.assertEqual(params["tenant_id"], "tenant-1")
        self.assertEqual(params["bypass"], "off")

    def test_clear_rls_context_resets_session_values(self) -> None:
        session = _FakeSession()

        clear_rls_context(session)

        sql, params = session.calls[-1]
        self.assertIn("set_config('app.tenant_id', '', true)", sql)
        self.assertIsNone(params)


if __name__ == "__main__":
    unittest.main()

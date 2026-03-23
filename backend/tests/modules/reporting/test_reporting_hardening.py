from __future__ import annotations

import unittest

from app.modules.reporting.repository import SqlAlchemyReportingRepository
from app.modules.reporting.schemas import ReportingFilterBase


class _FakeResult:
    def mappings(self) -> "_FakeResult":
        return self

    def all(self) -> list[dict[str, object]]:
        return []


class _FakeSession:
    def __init__(self) -> None:
        self.last_sql = ""
        self.last_params: dict[str, object] | None = None

    def execute(self, query, params):  # noqa: ANN001
        self.last_sql = str(query)
        self.last_params = dict(params)
        return _FakeResult()


class TestReportingHardening(unittest.TestCase):
    def test_dynamic_filter_sql_uses_only_active_predicates(self) -> None:
        repository = SqlAlchemyReportingRepository(_FakeSession())  # type: ignore[arg-type]
        filters = ReportingFilterBase(
            branch_id="branch-1",
            severity_code="critical",
            request_id="req-1",
            date_from="2026-01-01",
        )

        query = repository._build_query("security_activity", filters, None, None)  # noqa: SLF001
        sql = str(query)

        self.assertIn("branch_id = :branch_id", sql)
        self.assertIn("severity_code = :severity_code", sql)
        self.assertIn("request_id = :request_id", sql)
        self.assertIn("occurred_at IS NOT NULL AND occurred_at >= :date_from", sql)
        self.assertNotIn("(:branch_id IS NULL", sql)
        self.assertNotIn("(:severity_code IS NULL", sql)
        self.assertNotIn("invoice_status_code", sql)

    def test_delivery_job_query_only_filters_report_key_when_requested(self) -> None:
        session = _FakeSession()
        repository = SqlAlchemyReportingRepository(session)  # type: ignore[arg-type]

        repository.list_reporting_delivery_jobs("tenant-1", limit=10)
        self.assertNotIn("job.request_payload_json ->> 'report_key' = :report_key", session.last_sql)

        repository.list_reporting_delivery_jobs("tenant-1", report_key="security-activity", limit=10)
        self.assertIn("job.request_payload_json ->> 'report_key' = :report_key", session.last_sql)
        self.assertEqual(session.last_params["report_key"], "security-activity")


if __name__ == "__main__":
    unittest.main()

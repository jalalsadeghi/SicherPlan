"""Emit representative reporting SQL for Sprint 11 hardening review."""

from __future__ import annotations

import json

from app.modules.reporting.repository import SqlAlchemyReportingRepository
from app.modules.reporting.schemas import ReportingFilterBase


def main() -> None:
    repository = SqlAlchemyReportingRepository(None)  # type: ignore[arg-type]
    scenarios = {
        "security-activity": ReportingFilterBase(
            date_from="2026-01-01",
            date_to="2026-03-31",
            severity_code="critical",
            request_id="req-1",
        ),
        "compliance-status": ReportingFilterBase(
            branch_id="branch-1",
            actor_type_code="employee",
            status_code="non_compliant",
        ),
        "customer-profitability": ReportingFilterBase(
            customer_id="customer-1",
            date_from="2026-01-01",
            date_to="2026-01-31",
        ),
    }
    for report_key, filters in scenarios.items():
        clause = repository._build_query(report_key.replace("-", "_"), filters, None, None)  # noqa: SLF001
        print(f"[{report_key}]")
        print(str(clause))
        print(json.dumps(repository._active_filters(report_key.replace("-", "_"), filters), default=str, indent=2))  # noqa: SLF001


if __name__ == "__main__":
    main()

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.modules.reporting.reproducibility import REPORT_TRACEABILITY, compare_csv_to_rows
from app.modules.reporting.schemas import CustomerRevenueReportRow, ReportingFilterBase
from app.modules.reporting.service import ReportingService
from tests.modules.reporting.test_reporting_flows import _FakeReportingRepository, _actor


class ReportingReproducibilityTests(unittest.TestCase):
    def test_0054_compliance_view_uses_text_comparison_for_polymorphic_owner_id(self) -> None:
        migration_sql = Path("backend/alembic/versions/0054_reporting_views_compliance_and_qm.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("ep.qualification_id = eq.id::text", migration_sql)
        self.assertIn("wp.qualification_id = wq.id::text", migration_sql)
        self.assertNotIn("ep.qualification_id = eq.id\n", migration_sql)
        self.assertNotIn("wp.qualification_id = wq.id\n", migration_sql)

    def test_0055_security_view_uses_text_comparison_for_polymorphic_audit_entity_id(self) -> None:
        migration_sql = Path("backend/alembic/versions/0055_reporting_view_security_activity.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("COALESCE(le.user_account_id::text, le.id::text) AS entity_id", migration_sql)
        self.assertIn("ae.entity_id::text AS entity_id", migration_sql)
        self.assertIn("ae.entity_type = 'hr.employee'", migration_sql)
        self.assertIn("e.id::text = ae.entity_id", migration_sql)
        self.assertNotIn("COALESCE(le.user_account_id, le.id) AS entity_id", migration_sql)
        self.assertNotIn("e.id = ae.entity_id\n", migration_sql)

    def test_traceability_catalog_covers_all_reporting_families(self) -> None:
        self.assertEqual(
            {
                "compliance-status",
                "notice-read-stats",
                "free-sundays",
                "absence-visibility",
                "inactivity-signals",
                "security-activity",
                "employee-activity",
                "customer-revenue",
                "subcontractor-control",
                "planning-performance",
                "payroll-basis",
                "customer-profitability",
            },
            set(REPORT_TRACEABILITY.keys()),
        )
        self.assertIn("finance.customer_invoice", REPORT_TRACEABILITY["customer-revenue"]["source_chain"])
        self.assertIn("audit.audit_event", REPORT_TRACEABILITY["security-activity"]["source_chain"])

    def test_export_csv_matches_api_rows_exactly(self) -> None:
        revenue_row = CustomerRevenueReportRow(
            tenant_id="tenant-1",
            customer_id="customer-1",
            customer_number="C-1",
            customer_name="Alpha",
            order_id="order-1",
            order_no="O-1",
            planning_record_id="record-1",
            planning_record_name="Nord",
            planning_mode_code="site",
            invoice_id="invoice-1",
            invoice_no="INV-1",
            issue_date=date(2026, 3, 10),
            due_date=date(2026, 3, 24),
            invoice_status_code="released",
            delivery_status_code="queued",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            released_at=datetime(2026, 3, 10, 10, 0, tzinfo=UTC),
            timesheet_id="timesheet-1",
            timesheet_release_state_code="released",
            actual_record_count=2,
            billable_minutes_total=900,
            payable_minutes_total=840,
            subtotal_amount=Decimal("1000.00"),
            tax_amount=Decimal("190.00"),
            total_amount=Decimal("1190.00"),
            source_document_id="doc-1",
        )
        service = ReportingService(_FakeReportingRepository(revenue_rows=[revenue_row]))
        actor = _actor("reporting.read", "reporting.export")
        api_rows = service.list_customer_revenue("tenant-1", ReportingFilterBase(), actor)
        _, csv_payload = service.export_csv("customer-revenue", "tenant-1", ReportingFilterBase(), actor)
        self.assertTrue(compare_csv_to_rows(csv_payload, [row.model_dump() for row in api_rows]))

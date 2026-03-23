from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.finance.models import SubcontractorInvoiceCheck, SubcontractorInvoiceCheckNote
from app.modules.finance.subcontractor_check_schemas import (
    SubcontractorInvoiceCheckGenerateRequest,
    SubcontractorInvoiceCheckListFilter,
    SubcontractorInvoiceCheckNoteCreate,
    SubcontractorInvoiceCheckStatusRequest,
    SubcontractorInvoiceSubmissionUpdateRequest,
)
from app.modules.finance.subcontractor_check_service import SubcontractorInvoiceCheckService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _actor(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-finance-sub",
        user_id="finance-user",
        tenant_id="tenant-1",
        role_keys=frozenset({"accounting"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="accounting", scope_type="tenant"),),
        request_id="req-finance-sub",
    )


@dataclass
class _FakeRepo:
    checks: dict[str, SubcontractorInvoiceCheck] = field(default_factory=dict)
    notes: list[SubcontractorInvoiceCheckNote] = field(default_factory=list)
    audit: list[object] = field(default_factory=list)
    use_rate: bool = True

    def list_invoice_checks(self, tenant_id: str, filters: SubcontractorInvoiceCheckListFilter):
        rows = [row for row in self.checks.values() if row.tenant_id == tenant_id]
        if filters.subcontractor_id:
            rows = [row for row in rows if row.subcontractor_id == filters.subcontractor_id]
        return rows

    def get_invoice_check(self, tenant_id: str, invoice_check_id: str):
        row = self.checks.get(invoice_check_id)
        return row if row and row.tenant_id == tenant_id else None

    def find_by_period(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date):
        for row in self.checks.values():
            if (
                row.tenant_id == tenant_id
                and row.subcontractor_id == subcontractor_id
                and row.period_start == period_start
                and row.period_end == period_end
            ):
                return row
        return None

    def create_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.invoice_check_id = row.id
            line.created_at = line.created_at or row.created_at
            line.updated_at = line.updated_at or row.updated_at
        self.checks[row.id] = row
        return row

    def save_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck:
        row.updated_at = datetime.now(UTC)
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.invoice_check_id = row.id
            line.updated_at = row.updated_at
        self.checks[row.id] = row
        return row

    def create_note(self, row: SubcontractorInvoiceCheckNote) -> SubcontractorInvoiceCheckNote:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        self.notes.append(row)
        parent = self.checks[row.invoice_check_id]
        parent.notes.append(row)
        return row

    def list_signed_off_actuals_for_subcontractor(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date):
        if tenant_id != "tenant-1" or subcontractor_id != "sub-1":
            return []
        demand_group = SimpleNamespace(function_type_id="fn-1", qualification_type_id=None)
        planning_record = SimpleNamespace(name="Objekt Nord")
        shift_plan = SimpleNamespace(planning_record=planning_record)
        shift = SimpleNamespace(
            id="shift-1",
            starts_at=datetime(2026, 5, 3, 8, 0, tzinfo=UTC),
            ends_at=datetime(2026, 5, 3, 16, 0, tzinfo=UTC),
            break_minutes=30,
            shift_plan=shift_plan,
        )
        assignment = SimpleNamespace(id="assignment-1", demand_group=demand_group, shift=shift)
        worker = SimpleNamespace(id="worker-1", subcontractor_id="sub-1", first_name="Max", last_name="Partner")
        actual = SimpleNamespace(
            id="actual-1",
            assignment=assignment,
            shift=shift,
            subcontractor_worker=worker,
            planned_start_at=shift.starts_at,
            actual_start_at=datetime(2026, 5, 3, 8, 10, tzinfo=UTC),
            actual_end_at=datetime(2026, 5, 3, 15, 55, tzinfo=UTC),
            actual_break_minutes=25,
            payable_minutes=440,
            reconciliations=[],
        )
        return [actual]

    def list_active_subcontractor_rate_cards(self, tenant_id: str, subcontractor_id: str, on_date: date):
        if not self.use_rate or tenant_id != "tenant-1" or subcontractor_id != "sub-1":
            return []
        line = SimpleNamespace(
            id="rate-line-1",
            function_type_id="fn-1",
            qualification_type_id=None,
            billing_unit_code="hour",
            unit_price=Decimal("22.50"),
            minimum_quantity=None,
        )
        return [SimpleNamespace(id="rate-card-1", rate_lines=[line])]

    def get_subcontractor_finance_profile(self, tenant_id: str, subcontractor_id: str):
        return None

    def list_audit_events_for_invoice_check(self, tenant_id: str, invoice_check_id: str):
        return []


class SubcontractorInvoiceCheckServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.service = SubcontractorInvoiceCheckService(self.repo)
        self.actor = _actor("finance.subcontractor_control.read", "finance.subcontractor_control.write")

    def test_generate_is_period_unique_and_refreshes_existing_check(self) -> None:
        payload = SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31))
        first = self.service.generate_invoice_check("tenant-1", payload, self.actor)
        second = self.service.generate_invoice_check("tenant-1", payload, self.actor)
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.repo.checks), 1)

    def test_generated_line_keeps_assignment_and_actual_provenance(self) -> None:
        read = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        self.assertEqual(len(read.lines), 1)
        self.assertEqual(read.lines[0].assignment_id, "assignment-1")
        self.assertEqual(read.lines[0].actual_record_id, "actual-1")
        self.assertGreater(read.approved_amount_total, Decimal("0.00"))

    def test_missing_rate_marks_review_required(self) -> None:
        self.repo.use_rate = False
        read = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        self.assertEqual(read.status_code, "review_required")
        self.assertIn("missing_rate", read.lines[0].variance_reason_codes_json)

    def test_submitted_invoice_capture_updates_variance(self) -> None:
        created = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        updated = self.service.update_submitted_invoice(
            "tenant-1",
            created.id,
            SubcontractorInvoiceSubmissionUpdateRequest(
                submitted_invoice_ref="RE-77",
                submitted_invoice_amount=Decimal("200.00"),
                submitted_invoice_currency_code="EUR",
            ),
            self.actor,
        )
        self.assertEqual(updated.submitted_invoice_ref, "RE-77")
        self.assertIsNotNone(updated.submitted_variance_amount)
        self.assertIn("submitted_amount_discrepancy", updated.review_reason_codes_json)

    def test_status_and_note_flow_is_append_only(self) -> None:
        created = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        noted = self.service.add_note("tenant-1", created.id, SubcontractorInvoiceCheckNoteCreate(note_text="Bitte pruefen"), self.actor)
        approved = self.service.change_status(
            "tenant-1",
            created.id,
            SubcontractorInvoiceCheckStatusRequest(status_code="approved", note_text="Freigegeben"),
            self.actor,
        )
        released = self.service.change_status(
            "tenant-1",
            created.id,
            SubcontractorInvoiceCheckStatusRequest(status_code="released"),
            self.actor,
        )
        self.assertEqual(len(noted.notes), 1)
        self.assertEqual(approved.status_code, "approved")
        self.assertEqual(released.status_code, "released")
        self.assertGreaterEqual(len(released.notes), 2)

    def test_portal_reads_only_released_invoice_check(self) -> None:
        created = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        self.assertEqual(self.service.list_portal_invoice_checks("tenant-1", "sub-1"), [])
        self.service.change_status("tenant-1", created.id, SubcontractorInvoiceCheckStatusRequest(status_code="approved"), self.actor)
        self.service.change_status("tenant-1", created.id, SubcontractorInvoiceCheckStatusRequest(status_code="released"), self.actor)
        rows = self.service.list_portal_invoice_checks("tenant-1", "sub-1")
        self.assertEqual(len(rows), 1)
        detail = self.service.get_portal_invoice_check_detail("tenant-1", "sub-1", created.id)
        self.assertEqual(detail.lines[0].label.startswith("Objekt Nord"), True)

    def test_portal_cannot_read_foreign_subcontractor(self) -> None:
        created = self.service.generate_invoice_check(
            "tenant-1",
            SubcontractorInvoiceCheckGenerateRequest(subcontractor_id="sub-1", period_start=date(2026, 5, 1), period_end=date(2026, 5, 31)),
            self.actor,
        )
        self.service.change_status("tenant-1", created.id, SubcontractorInvoiceCheckStatusRequest(status_code="approved"), self.actor)
        self.service.change_status("tenant-1", created.id, SubcontractorInvoiceCheckStatusRequest(status_code="released"), self.actor)
        with self.assertRaises(ApiException):
            self.service.get_portal_invoice_check_detail("tenant-1", "sub-2", created.id)


if __name__ == "__main__":
    unittest.main()

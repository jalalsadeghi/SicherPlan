from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.modules.field_execution.models import AttendanceRecord
from app.modules.finance.models import ActualRecord
from app.modules.finance.schemas import ActualRecordListFilter
from app.modules.finance.service import FinanceActualService
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository


def _actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-finance",
        user_id="user-accounting",
        tenant_id="tenant-1",
        role_keys=frozenset({"accounting"}),
        permission_keys=frozenset({"finance.actual.read", "finance.actual.write"}),
        scopes=(AuthenticatedRoleScope(role_key="accounting", scope_type="tenant"),),
        request_id="req-finance",
    )


@dataclass
class _FakeRepo:
    tenant_id: str = "tenant-1"
    attendances: dict[str, AttendanceRecord] = field(default_factory=dict)
    actuals: dict[str, ActualRecord] = field(default_factory=dict)

    def __post_init__(self) -> None:
        planning_record = SimpleNamespace(id="planning-1")
        shift_plan = SimpleNamespace(planning_record=planning_record)
        self.shift = SimpleNamespace(
            id="shift-1",
            tenant_id=self.tenant_id,
            release_state="released",
            starts_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
            ends_at=datetime(2026, 3, 20, 16, 0, tzinfo=UTC),
            break_minutes=30,
            shift_plan=shift_plan,
        )
        self.assignment = SimpleNamespace(
            id="assignment-1",
            tenant_id=self.tenant_id,
            shift_id=self.shift.id,
            employee_id="employee-1",
            subcontractor_worker_id=None,
            shift=self.shift,
        )

    def get_assignment(self, tenant_id: str, assignment_id: str):
        if tenant_id == self.tenant_id and assignment_id == self.assignment.id:
            return self.assignment
        return None

    def get_attendance_record(self, tenant_id: str, attendance_record_id: str):
        row = self.attendances.get(attendance_record_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_current_attendance_for_assignment(self, tenant_id: str, assignment_id: str):
        for row in self.attendances.values():
            if row.tenant_id == tenant_id and row.assignment_id == assignment_id and row.is_current and row.archived_at is None:
                return row
        return None

    def get_actual_record(self, tenant_id: str, actual_record_id: str):
        row = self.actuals.get(actual_record_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_current_actual_for_assignment(self, tenant_id: str, assignment_id: str):
        for row in self.actuals.values():
            if row.tenant_id == tenant_id and row.assignment_id == assignment_id and row.is_current and row.archived_at is None:
                return row
        return None

    def list_actual_records(self, tenant_id: str, filters: ActualRecordListFilter):
        rows = [row for row in self.actuals.values() if row.tenant_id == tenant_id]
        if filters.current_only:
            rows = [row for row in rows if row.is_current]
        if filters.assignment_id is not None:
            rows = [row for row in rows if row.assignment_id == filters.assignment_id]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.discrepancy_only:
            rows = [row for row in rows if row.discrepancy_state_code != "clean"]
        return sorted(rows, key=lambda row: row.derived_at, reverse=True)

    def create_actual_record(self, row: ActualRecord) -> ActualRecord:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        self.actuals[row.id] = row
        return row

    def save_actual_record(self, row: ActualRecord) -> ActualRecord:
        row.updated_at = datetime.now(UTC)
        self.actuals[row.id] = row
        return row

    def list_audit_events_for_actual_record(self, tenant_id: str, actual_record_id: str) -> list[AuditEventRead]:
        return []


class FinanceActualServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.audit_repo = _FakeAuditRepository()
        self.service = FinanceActualService(self.repo, AuditService(self.audit_repo))
        self.actor = _actor()

    def _attendance(self, *, attendance_id: str, discrepancy_codes: list[str] | None = None, discrepancy_state_code: str = "clean") -> AttendanceRecord:
        return AttendanceRecord(
            id=attendance_id,
            tenant_id="tenant-1",
            actor_type_code="employee",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            shift_id="shift-1",
            assignment_id="assignment-1",
            check_in_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
            check_out_at=datetime(2026, 3, 20, 16, 0, tzinfo=UTC),
            break_minutes=30,
            worked_minutes=450,
            source_event_count=2,
            first_time_event_id="evt-1",
            last_time_event_id="evt-2",
            source_event_ids_json=["evt-1", "evt-2"],
            discrepancy_state_code=discrepancy_state_code,
            discrepancy_codes_json=discrepancy_codes or [],
            discrepancy_details_json={
                "issues": [
                    {
                        "code": code,
                        "severity": "needs_review",
                        "message_key": "errors.field.attendance.invalid_sequence",
                        "source_event_ids": ["evt-1"],
                        "details": {},
                    }
                    for code in (discrepancy_codes or [])
                ]
            },
            derivation_status_code="derived" if discrepancy_state_code == "clean" else "needs_review",
            derived_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
            is_current=True,
            status="active",
            version_no=1,
            created_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
            updated_at=datetime(2026, 3, 20, 16, 5, tzinfo=UTC),
        )

    def test_actual_derives_payable_and_billable_minutes_from_attendance(self) -> None:
        self.repo.attendances["attendance-1"] = self._attendance(attendance_id="attendance-1")
        read = self.service.derive_for_assignment("tenant-1", "assignment-1", self.actor)
        self.assertEqual(read.attendance_record_id, "attendance-1")
        self.assertEqual(read.payable_minutes, 450)
        self.assertEqual(read.billable_minutes, 450)
        self.assertEqual(read.derivation_status_code, "derived")
        self.assertEqual(read.approval_stage_code, "draft")

    def test_missing_attendance_creates_draft_actual_with_discrepancy(self) -> None:
        read = self.service.derive_for_assignment("tenant-1", "assignment-1", self.actor)
        self.assertEqual(read.derivation_status_code, "draft")
        self.assertEqual(read.discrepancy_state_code, "needs_review")
        self.assertIn("missing_attendance_record", read.discrepancy_codes_json)

    def test_attendance_discrepancies_propagate_into_actual_review_context(self) -> None:
        self.repo.attendances["attendance-2"] = self._attendance(
            attendance_id="attendance-2",
            discrepancy_codes=["missed_checkout"],
            discrepancy_state_code="needs_review",
        )
        read = self.service.derive_for_assignment("tenant-1", "assignment-1", self.actor)
        self.assertEqual(read.derivation_status_code, "needs_review")
        self.assertIn("missed_checkout", read.discrepancy_codes_json)
        self.assertEqual(read.discrepancies[0].attendance_record_id, "attendance-2")

    def test_rederive_supersedes_previous_current_actual(self) -> None:
        self.repo.attendances["attendance-3"] = self._attendance(attendance_id="attendance-3")
        first = self.service.derive_for_assignment("tenant-1", "assignment-1", self.actor)
        updated_attendance = self._attendance(attendance_id="attendance-4")
        updated_attendance.check_out_at = datetime(2026, 3, 20, 17, 0, tzinfo=UTC)
        updated_attendance.worked_minutes = 510
        updated_attendance.break_minutes = 30
        self.repo.attendances = {"attendance-4": updated_attendance}
        second = self.service.derive_for_assignment("tenant-1", "assignment-1", self.actor)
        self.assertNotEqual(first.id, second.id)
        previous = self.repo.actuals[first.id]
        self.assertFalse(previous.is_current)
        self.assertEqual(previous.derivation_status_code, "superseded")
        self.assertEqual(previous.superseded_by_actual_id, second.id)
        self.assertEqual(second.payable_minutes, 510)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.modules.field_execution.attendance_service import AttendanceService
from app.modules.field_execution.models import AttendanceRecord, TimeEvent
from app.modules.field_execution.schemas import AttendanceRecordListFilter
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository


def _actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-attendance",
        user_id="user-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"field.attendance.read", "field.attendance.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-attendance",
    )


@dataclass
class _FakeRepo:
    tenant_id: str = "tenant-1"
    attendances: dict[str, AttendanceRecord] = field(default_factory=dict)
    events: list[TimeEvent] = field(default_factory=list)

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
        self.employee_assignment = SimpleNamespace(
            id="assignment-employee-1",
            tenant_id=self.tenant_id,
            shift_id=self.shift.id,
            employee_id="employee-1",
            subcontractor_worker_id=None,
            shift=self.shift,
        )
        self.worker_assignment = SimpleNamespace(
            id="assignment-worker-1",
            tenant_id=self.tenant_id,
            shift_id=self.shift.id,
            employee_id=None,
            subcontractor_worker_id="worker-1",
            shift=self.shift,
        )

    def get_shift(self, tenant_id: str, shift_id: str):
        return self.shift if tenant_id == self.tenant_id and shift_id == self.shift.id else None

    def get_assignment(self, tenant_id: str, assignment_id: str):
        for row in (self.employee_assignment, self.worker_assignment):
            if tenant_id == self.tenant_id and assignment_id == row.id:
                return row
        return None

    def list_assignments_for_shift(self, tenant_id: str, shift_id: str):
        if tenant_id != self.tenant_id or shift_id != self.shift.id:
            return []
        return [self.employee_assignment, self.worker_assignment]

    def list_events_for_actor_shift(self, tenant_id: str, *, shift_id: str, employee_id: str | None, subcontractor_worker_id: str | None):
        return [
            row
            for row in self.events
            if row.tenant_id == tenant_id
            and row.shift_id == shift_id
            and row.archived_at is None
            and row.employee_id == employee_id
            and row.subcontractor_worker_id == subcontractor_worker_id
        ]

    def get_attendance_record(self, tenant_id: str, attendance_record_id: str):
        row = self.attendances.get(attendance_record_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_current_attendance_for_actor_shift(self, tenant_id: str, *, shift_id: str, employee_id: str | None, subcontractor_worker_id: str | None):
        for row in self.attendances.values():
            if (
                row.tenant_id == tenant_id
                and row.shift_id == shift_id
                and row.employee_id == employee_id
                and row.subcontractor_worker_id == subcontractor_worker_id
                and row.is_current
                and row.archived_at is None
            ):
                return row
        return None

    def list_attendance_records(self, tenant_id: str, filters: AttendanceRecordListFilter):
        rows = [row for row in self.attendances.values() if row.tenant_id == tenant_id]
        if filters.current_only:
            rows = [row for row in rows if row.is_current]
        if filters.assignment_id is not None:
            rows = [row for row in rows if row.assignment_id == filters.assignment_id]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.subcontractor_worker_id is not None:
            rows = [row for row in rows if row.subcontractor_worker_id == filters.subcontractor_worker_id]
        if filters.discrepancy_only:
            rows = [row for row in rows if row.discrepancy_state_code != "clean"]
        return sorted(rows, key=lambda row: row.derived_at, reverse=True)

    def create_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord:
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        self.attendances[row.id] = row
        return row

    def save_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord:
        row.updated_at = datetime.now(UTC)
        self.attendances[row.id] = row
        return row


class AttendanceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.audit_repo = _FakeAuditRepository()
        self.service = AttendanceService(self.repo, AuditService(self.audit_repo))
        self.actor = _actor()

    def _event(self, *, event_id: str, assignment_id: str, employee_id: str | None, worker_id: str | None, event_code: str, hour: int, minute: int = 0, validation_status_code: str = "accepted") -> TimeEvent:
        return TimeEvent(
            id=event_id,
            tenant_id="tenant-1",
            actor_type_code="employee" if employee_id else "subcontractor_worker",
            employee_id=employee_id,
            subcontractor_worker_id=worker_id,
            shift_id="shift-1",
            assignment_id=assignment_id,
            source_channel_code="mobile",
            event_code=event_code,
            occurred_at=datetime(2026, 3, 20, hour, minute, tzinfo=UTC),
            validation_status_code=validation_status_code,
            created_at=datetime(2026, 3, 20, hour, minute, tzinfo=UTC),
            updated_at=datetime(2026, 3, 20, hour, minute, tzinfo=UTC),
            status="active",
            version_no=1,
        )

    def test_employee_attendance_derives_break_and_worked_minutes(self) -> None:
        self.repo.events.extend(
            [
                self._event(event_id="evt-1", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_in", hour=8),
                self._event(event_id="evt-2", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="break_start", hour=12),
                self._event(event_id="evt-3", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="break_end", hour=12, minute=30),
                self._event(event_id="evt-4", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_out", hour=16),
            ]
        )
        read = self.service.derive_for_assignment("tenant-1", "assignment-employee-1", self.actor)
        self.assertEqual(read.break_minutes, 30)
        self.assertEqual(read.worked_minutes, 450)
        self.assertEqual(read.discrepancy_state_code, "clean")
        self.assertTrue(read.is_current)

    def test_worker_attendance_derives_for_subcontractor_actor(self) -> None:
        self.repo.events.extend(
            [
                self._event(event_id="evt-w1", assignment_id="assignment-worker-1", employee_id=None, worker_id="worker-1", event_code="clock_in", hour=9),
                self._event(event_id="evt-w2", assignment_id="assignment-worker-1", employee_id=None, worker_id="worker-1", event_code="clock_out", hour=15),
            ]
        )
        read = self.service.derive_for_assignment("tenant-1", "assignment-worker-1", self.actor)
        self.assertEqual(read.actor_type_code, "subcontractor_worker")
        self.assertEqual(read.subcontractor_worker_id, "worker-1")
        self.assertEqual(read.worked_minutes, 360)

    def test_missing_checkout_and_duplicate_clock_in_surface_discrepancies(self) -> None:
        self.repo.events.extend(
            [
                self._event(event_id="evt-a1", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_in", hour=8),
                self._event(event_id="evt-a2", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_in", hour=8, minute=5),
            ]
        )
        read = self.service.derive_for_assignment("tenant-1", "assignment-employee-1", self.actor)
        self.assertEqual(read.discrepancy_state_code, "needs_review")
        self.assertIn("duplicate_clock_in", read.discrepancy_codes_json)
        self.assertIn("missed_checkout", read.discrepancy_codes_json)
        self.assertGreaterEqual(len(read.discrepancies), 2)

    def test_rederive_supersedes_previous_current_record(self) -> None:
        self.repo.events.append(
            self._event(event_id="evt-r1", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_in", hour=8)
        )
        first = self.service.derive_for_assignment("tenant-1", "assignment-employee-1", self.actor)
        self.repo.events.append(
            self._event(event_id="evt-r2", assignment_id="assignment-employee-1", employee_id="employee-1", worker_id=None, event_code="clock_out", hour=16)
        )
        second = self.service.derive_for_assignment("tenant-1", "assignment-employee-1", self.actor)
        self.assertNotEqual(first.id, second.id)
        previous = self.repo.attendances[first.id]
        self.assertFalse(previous.is_current)
        self.assertEqual(previous.derivation_status_code, "superseded")
        self.assertEqual(previous.superseded_by_attendance_id, second.id)


if __name__ == "__main__":
    unittest.main()

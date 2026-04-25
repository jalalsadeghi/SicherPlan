from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Branch, Mandate, Tenant
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.models import (
    Employee,
    EmployeeAbsence,
    EmployeeAvailabilityRule,
    EmployeeEventApplication,
    EmployeeLeaveBalance,
)
from app.modules.employees.schemas import (
    EmployeeAbsenceCreate,
    EmployeeAbsenceFilter,
    EmployeeAbsenceUpdate,
    EmployeeAvailabilityRuleCreate,
    EmployeeAvailabilityRuleFilter,
    EmployeeAvailabilityRuleUpdate,
    EmployeeEventApplicationCreate,
    EmployeeEventApplicationFilter,
    EmployeeEventApplicationUpdate,
    EmployeeLeaveBalanceFilter,
    EmployeeLeaveBalanceUpsert,
)
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _employee_context(*permissions: str, tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


@dataclass
class FakeAvailabilityRepository:
    tenant_id: str = "tenant-1"
    branch_id: str = "branch-1"
    mandate_id: str = "mandate-1"
    employees: dict[str, Employee] = field(default_factory=dict)
    availability_rules: dict[str, EmployeeAvailabilityRule] = field(default_factory=dict)
    absences: dict[str, EmployeeAbsence] = field(default_factory=dict)
    leave_balances: dict[str, EmployeeLeaveBalance] = field(default_factory=dict)
    event_applications: dict[str, EmployeeEventApplication] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.tenant = Tenant(
            id=self.tenant_id,
            code="nord",
            name="SicherPlan Nord",
            legal_name="SicherPlan Nord GmbH",
            default_locale="de",
            default_currency="EUR",
            timezone="Europe/Berlin",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.branch = Branch(
            id=self.branch_id,
            tenant_id=self.tenant_id,
            code="BER",
            name="Berlin",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.mandate = Mandate(
            id=self.mandate_id,
            tenant_id=self.tenant_id,
            branch_id=self.branch_id,
            code="M-001",
            name="Mandate",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        employee = Employee(
            id="employee-1",
            tenant_id=self.tenant_id,
            personnel_no="EMP-1001",
            first_name="Anna",
            last_name="Wagner",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.employees[employee.id] = employee

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        if getattr(row, "status", None) is None:
            row.status = "active"

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        row = self.employees.get(employee_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        if tenant_id != self.tenant.id:
            return None
        return self.tenant

    def list_availability_rules(
        self,
        tenant_id: str,
        filters: EmployeeAvailabilityRuleFilter | None = None,
    ) -> list[EmployeeAvailabilityRule]:
        rows = [row for row in self.availability_rules.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.rule_kind is not None:
                rows = [row for row in rows if row.rule_kind == filters.rule_kind]
            if filters.status is not None:
                rows = [row for row in rows if row.status == filters.status]
            if filters.active_on is not None:
                rows = [row for row in rows if row.starts_at <= filters.active_on <= row.ends_at]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        rows.sort(key=lambda row: row.starts_at)
        return rows

    def get_availability_rule(self, tenant_id: str, rule_id: str) -> EmployeeAvailabilityRule | None:
        row = self.availability_rules.get(rule_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule:
        self._stamp(row)
        self.availability_rules[row.id] = row
        return row

    def update_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule:
        self._stamp(row)
        self.availability_rules[row.id] = row
        return row

    def list_absences(self, tenant_id: str, filters: EmployeeAbsenceFilter | None = None) -> list[EmployeeAbsence]:
        rows = [row for row in self.absences.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.absence_type is not None:
                rows = [row for row in rows if row.absence_type == filters.absence_type]
            if filters.status is not None:
                rows = [row for row in rows if row.status == filters.status]
            if filters.starts_on_or_after is not None:
                rows = [row for row in rows if row.starts_on >= filters.starts_on_or_after]
            if filters.ends_on_or_before is not None:
                rows = [row for row in rows if row.ends_on <= filters.ends_on_or_before]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        rows.sort(key=lambda row: (row.starts_on, row.ends_on))
        return rows

    def get_absence(self, tenant_id: str, absence_id: str) -> EmployeeAbsence | None:
        row = self.absences.get(absence_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_absence(self, row: EmployeeAbsence) -> EmployeeAbsence:
        self._stamp(row)
        row.requested_at = row.requested_at or datetime.now(UTC)
        self.absences[row.id] = row
        return row

    def update_absence(self, row: EmployeeAbsence) -> EmployeeAbsence:
        self._stamp(row)
        self.absences[row.id] = row
        return row

    def list_leave_balances(
        self,
        tenant_id: str,
        filters: EmployeeLeaveBalanceFilter | None = None,
    ) -> list[EmployeeLeaveBalance]:
        rows = [row for row in self.leave_balances.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.balance_year is not None:
                rows = [row for row in rows if row.balance_year == filters.balance_year]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        rows.sort(key=lambda row: row.balance_year)
        return rows

    def get_leave_balance(self, tenant_id: str, balance_id: str) -> EmployeeLeaveBalance | None:
        row = self.leave_balances.get(balance_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_leave_balance_for_year(self, tenant_id: str, employee_id: str, balance_year: int) -> EmployeeLeaveBalance | None:
        for row in self.leave_balances.values():
            if row.tenant_id == tenant_id and row.employee_id == employee_id and row.balance_year == balance_year:
                return row
        return None

    def create_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance:
        self._stamp(row)
        self.leave_balances[row.id] = row
        return row

    def update_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance:
        self._stamp(row)
        self.leave_balances[row.id] = row
        return row

    def list_event_applications(
        self,
        tenant_id: str,
        filters: EmployeeEventApplicationFilter | None = None,
    ) -> list[EmployeeEventApplication]:
        rows = [row for row in self.event_applications.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.planning_record_id is not None:
                rows = [row for row in rows if row.planning_record_id == filters.planning_record_id]
            if filters.status is not None:
                rows = [row for row in rows if row.status == filters.status]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        rows.sort(key=lambda row: row.applied_at, reverse=True)
        return rows

    def get_event_application(self, tenant_id: str, application_id: str) -> EmployeeEventApplication | None:
        row = self.event_applications.get(application_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_event_application(
        self,
        tenant_id: str,
        employee_id: str,
        planning_record_id: str,
        *,
        exclude_id: str | None = None,
    ) -> EmployeeEventApplication | None:
        for row in self.event_applications.values():
            if (
                row.tenant_id == tenant_id
                and row.employee_id == employee_id
                and row.planning_record_id == planning_record_id
                and row.id != exclude_id
            ):
                return row
        return None

    def create_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication:
        self._stamp(row)
        row.applied_at = row.applied_at or datetime.now(UTC)
        self.event_applications[row.id] = row
        return row

    def update_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication:
        self._stamp(row)
        self.event_applications[row.id] = row
        return row


class EmployeeAvailabilityServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeAvailabilityRepository()
        self.audit_repository = RecordingAuditRepository()
        self.service = EmployeeAvailabilityService(self.repository, audit_service=AuditService(self.audit_repository))

    def test_weekly_recurrence_requires_valid_weekday_mask(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_availability_rule(
                "tenant-1",
                EmployeeAvailabilityRuleCreate(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    rule_kind="free_wish",
                    starts_at=datetime.now(UTC),
                    ends_at=datetime.now(UTC) + timedelta(hours=3),
                    recurrence_type="weekly",
                    weekday_mask="0000000",
                ),
                _employee_context("employees.employee.write"),
            )

        self.assertEqual(raised.exception.message_key, "errors.employees.availability_rule.invalid_recurrence_mask")

    def test_absence_overlap_is_blocked_and_approved_absence_updates_leave_balance(self) -> None:
        balance = self.service.upsert_leave_balance(
            "tenant-1",
            EmployeeLeaveBalanceUpsert(
                tenant_id="tenant-1",
                employee_id="employee-1",
                balance_year=2026,
                entitlement_days=30,
                carry_over_days=5,
            ),
            _employee_context("employees.private.write"),
        )
        absence = self.service.create_absence(
            "tenant-1",
            EmployeeAbsenceCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                absence_type="vacation",
                starts_on=date(2026, 5, 10),
                ends_on=date(2026, 5, 12),
            ),
            _employee_context("employees.private.write"),
        )

        pending_balance = self.service.list_leave_balances(
            "tenant-1",
            EmployeeLeaveBalanceFilter(employee_id="employee-1", balance_year=2026),
            _employee_context("employees.private.read"),
        )[0]
        self.assertEqual(pending_balance.id, balance.id)
        self.assertEqual(pending_balance.pending_days, 3.0)
        self.assertEqual(pending_balance.consumed_days, 0.0)

        approved = self.service.update_absence(
            "tenant-1",
            absence.id,
            EmployeeAbsenceUpdate(status="approved", version_no=absence.version_no),
            _employee_context("employees.private.write"),
        )
        approved_balance = self.service.list_leave_balances(
            "tenant-1",
            EmployeeLeaveBalanceFilter(employee_id="employee-1", balance_year=2026),
            _employee_context("employees.private.read"),
        )[0]
        self.assertEqual(approved.status, "approved")
        self.assertEqual(approved.approved_by_user_id, "user-1")
        self.assertEqual(approved_balance.pending_days, 0.0)
        self.assertEqual(approved_balance.consumed_days, 3.0)

        with self.assertRaises(ApiException) as overlap:
            self.service.create_absence(
                "tenant-1",
                EmployeeAbsenceCreate(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    absence_type="vacation",
                    starts_on=date(2026, 5, 11),
                    ends_on=date(2026, 5, 13),
                ),
                _employee_context("employees.private.write"),
            )
        self.assertEqual(overlap.exception.message_key, "errors.employees.absence.overlap")

    def test_event_application_uses_forward_compatible_planning_reference_without_fk(self) -> None:
        created = self.service.create_event_application(
            "tenant-1",
            EmployeeEventApplicationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                planning_record_id="11111111-1111-1111-1111-111111111111",
                note="Bitte einplanen.",
            ),
            _employee_context("employees.employee.write"),
        )
        updated = self.service.update_event_application(
            "tenant-1",
            created.id,
            EmployeeEventApplicationUpdate(
                status="approved",
                decision_note="Freigegeben",
                version_no=created.version_no,
            ),
            _employee_context("employees.employee.write"),
        )

        self.assertEqual(updated.status, "approved")
        self.assertEqual(updated.decided_by_user_id, "user-1")

        event_application_table = Base.metadata.tables["hr.employee_event_application"]
        foreign_key_targets = {
            element.target_fullname
            for constraint in event_application_table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
            for element in constraint.elements
        }
        self.assertNotIn("ops.planning_record.id", foreign_key_targets)

    def test_metadata_exposes_expected_checks(self) -> None:
        availability_table = Base.metadata.tables["hr.employee_availability_rule"]
        absence_table = Base.metadata.tables["hr.employee_absence"]
        balance_table = Base.metadata.tables["hr.employee_leave_balance"]

        availability_checks = {c.name for c in availability_table.constraints if isinstance(c, CheckConstraint)}
        absence_checks = {c.name for c in absence_table.constraints if isinstance(c, CheckConstraint)}
        balance_checks = {c.name for c in balance_table.constraints if isinstance(c, CheckConstraint)}

        self.assertIn("ck_employee_availability_rule_employee_availability_rule_recurrence_fields_valid", availability_checks)
        self.assertIn("ck_employee_absence_employee_absence_status_valid", absence_checks)
        self.assertIn("ck_employee_leave_balance_employee_leave_balance_year_valid", balance_checks)


if __name__ == "__main__":
    unittest.main()

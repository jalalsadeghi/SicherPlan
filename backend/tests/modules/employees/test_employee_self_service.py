from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from app.errors import ApiException
from app.modules.core.models import Address
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.models import Employee, EmployeeAddressHistory, EmployeeEventApplication
from app.modules.employees.self_service_service import EmployeeSelfService
from app.modules.employees.schemas import (
    EmployeeSelfServiceAddressUpdate,
    EmployeeSelfServiceAvailabilityRuleCreate,
    EmployeeSelfServiceEventApplicationCancel,
    EmployeeSelfServiceEventApplicationCreate,
    EmployeeSelfServiceProfileUpdate,
)
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext

from .test_employee_availability_absence import FakeAvailabilityRepository, RecordingAuditRepository


def _employee_self_service_context(
    *permissions: str,
    tenant_id: str = "tenant-1",
    user_id: str = "user-1",
    role_keys: frozenset[str] | None = None,
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        role_keys=role_keys if role_keys is not None else frozenset({"employee_user"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="employee_user", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeSelfServiceRepository(FakeAvailabilityRepository):
    addresses: dict[str, Address] = field(default_factory=dict)
    address_history_rows: dict[str, EmployeeAddressHistory] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.employees["employee-1"].user_id = "user-1"
        self.employees["employee-1"].preferred_name = "Anni"
        self.employees["employee-1"].work_email = "anna@example.com"
        self.employees["employee-1"].mobile_phone = "+491700000001"
        self.employees["employee-1"].notes = "internal-only"
        self.employees["employee-2"] = Employee(
            id="employee-2",
            tenant_id=self.tenant_id,
            personnel_no="EMP-1002",
            first_name="Ben",
            last_name="Keller",
            user_id="user-2",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> Employee | None:
        for row in self.employees.values():
            if row.tenant_id == tenant_id and row.user_id == user_id and row.id != exclude_id:
                return row
        return None

    def update_employee(self, row: Employee) -> Employee:
        self._stamp(row)
        self.employees[row.id] = row
        return row

    def create_address(self, row: Address) -> Address:
        if row.id is None:
            row.id = str(uuid4())
        self.addresses[row.id] = row
        return row

    def list_employee_address_history(self, tenant_id: str, employee_id: str) -> list[EmployeeAddressHistory]:
        rows = [
            row
            for row in self.address_history_rows.values()
            if row.tenant_id == tenant_id and row.employee_id == employee_id
        ]
        rows.sort(key=lambda row: row.valid_from)
        for row in rows:
            row.address = self.addresses.get(row.address_id)
        return rows

    def get_employee_address_history(self, tenant_id: str, employee_id: str, history_id: str) -> EmployeeAddressHistory | None:
        row = self.address_history_rows.get(history_id)
        if row is None or row.tenant_id != tenant_id or row.employee_id != employee_id:
            return None
        row.address = self.addresses.get(row.address_id)
        return row

    def create_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        self._stamp(row)
        self.address_history_rows[row.id] = row
        row.address = self.addresses.get(row.address_id)
        return row

    def update_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        self._stamp(row)
        self.address_history_rows[row.id] = row
        row.address = self.addresses.get(row.address_id)
        return row


class EmployeeSelfServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSelfServiceRepository()
        self.audit_repository = RecordingAuditRepository()
        self.audit_service = AuditService(self.audit_repository)
        self.service = EmployeeSelfService(
            repository=self.repository,
            availability_service=EmployeeAvailabilityService(self.repository, audit_service=self.audit_service),
            audit_service=self.audit_service,
        )

    def test_get_profile_requires_employee_scope_and_linked_record(self) -> None:
        with self.assertRaises(ApiException) as missing_permission:
            self.service.get_profile(_employee_self_service_context())
        self.assertEqual(missing_permission.exception.status_code, 403)
        self.assertEqual(missing_permission.exception.message_key, "errors.iam.authorization.permission_denied")

        with self.assertRaises(ApiException) as missing_employee:
            self.service.get_profile(
                _employee_self_service_context(
                    "portal.employee.access",
                    user_id="missing-user",
                )
            )
        self.assertEqual(missing_employee.exception.status_code, 404)
        self.assertEqual(missing_employee.exception.message_key, "errors.employees.self_service.employee_not_found")

    def test_update_profile_only_changes_whitelisted_operational_fields(self) -> None:
        employee = self.repository.employees["employee-1"]
        before_first_name = employee.first_name
        before_notes = employee.notes

        profile = self.service.update_profile(
            EmployeeSelfServiceProfileUpdate(
                preferred_name="Anna S.",
                work_email="anna.self@example.com",
                mobile_phone="+491700000099",
            ),
            _employee_self_service_context("portal.employee.access"),
        )

        self.assertEqual(profile.preferred_name, "Anna S.")
        self.assertEqual(profile.work_email, "anna.self@example.com")
        self.assertEqual(profile.mobile_phone, "+491700000099")
        self.assertEqual(employee.first_name, before_first_name)
        self.assertEqual(employee.notes, before_notes)
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        self.assertEqual(self.audit_repository.audit_events[0].event_type, "employees.self_service.profile_updated")

    def test_update_current_address_closes_previous_home_window_and_creates_new_one(self) -> None:
        original_address = self.repository.create_address(
            Address(
                street_line_1="Alte Strasse 1",
                street_line_2=None,
                postal_code="10115",
                city="Berlin",
                state=None,
                country_code="DE",
            )
        )
        self.repository.create_address_history(
            EmployeeAddressHistory(
                tenant_id="tenant-1",
                employee_id="employee-1",
                address_id=original_address.id,
                address_type="home",
                valid_from=date(2026, 1, 1),
                valid_to=None,
                is_primary=True,
                created_by_user_id="user-1",
                updated_by_user_id="user-1",
            )
        )

        created = self.service.update_current_address(
            EmployeeSelfServiceAddressUpdate(
                effective_from=date(2026, 4, 1),
                address={
                    "street_line_1": "Neue Strasse 8",
                    "street_line_2": "2. OG",
                    "postal_code": "20095",
                    "city": "Hamburg",
                    "state": None,
                    "country_code": "DE",
                },
                notes="Umzug",
            ),
            _employee_self_service_context("portal.employee.access"),
        )

        history_rows = self.repository.list_employee_address_history("tenant-1", "employee-1")
        self.assertEqual(len(history_rows), 2)
        self.assertEqual(history_rows[0].valid_to, date(2026, 3, 31))
        self.assertEqual(history_rows[1].id, created.id)
        self.assertEqual(history_rows[1].valid_from, date(2026, 4, 1))
        self.assertEqual(history_rows[1].address.city, "Hamburg")
        self.assertEqual(history_rows[1].notes, "Umzug")
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        self.assertEqual(self.audit_repository.audit_events[0].event_type, "employees.self_service.address_updated")

    def test_create_availability_rule_rejects_non_self_service_kind(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_availability_rule(
                EmployeeSelfServiceAvailabilityRuleCreate(
                    rule_kind="unavailable",
                    starts_at=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
                    ends_at=datetime(2026, 5, 1, 16, 0, tzinfo=UTC),
                    recurrence_type="none",
                ),
                _employee_self_service_context("portal.employee.access"),
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.message_key, "errors.employees.self_service.availability_rule.invalid_kind")

    def test_cancel_event_application_only_allows_owned_application(self) -> None:
        owned = self.service.create_event_application(
            EmployeeSelfServiceEventApplicationCreate(
                planning_record_id="11111111-1111-1111-1111-111111111111",
                note="Bitte einplanen",
            ),
            _employee_self_service_context("portal.employee.access"),
        )
        foreign = self.repository.create_event_application(
            EmployeeEventApplication(
                tenant_id="tenant-1",
                employee_id="employee-2",
                planning_record_id="22222222-2222-2222-2222-222222222222",
                note="Andere Person",
                created_by_user_id="user-2",
                updated_by_user_id="user-2",
            )
        )

        cancelled = self.service.cancel_event_application(
            owned.id,
            EmployeeSelfServiceEventApplicationCancel(
                decision_note="Nicht mehr verfuegbar",
                version_no=owned.version_no,
            ),
            _employee_self_service_context("portal.employee.access"),
        )
        self.assertEqual(cancelled.status, "withdrawn")

        with self.assertRaises(ApiException) as raised:
            self.service.cancel_event_application(
                foreign.id,
                EmployeeSelfServiceEventApplicationCancel(version_no=foreign.version_no),
                _employee_self_service_context("portal.employee.access"),
            )
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.message_key, "errors.employees.self_service.event_application.not_found")


if __name__ == "__main__":
    unittest.main()

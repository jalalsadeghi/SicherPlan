from __future__ import annotations

import base64
import csv
import io
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.errors import ApiException
from app.modules.employees.models import Employee
from app.modules.employees.ops_service import EmployeeOpsService, IMPORT_HEADERS
from app.modules.employees.schemas import (
    EmployeeAccessAttachExistingRequest,
    EmployeeAccessCreateUserRequest,
    EmployeeAccessDetachRequest,
    EmployeeAccessResetPasswordRequest,
    EmployeeAccessUpdateUserRequest,
    EmployeeExportRequest,
    EmployeeFilter,
    EmployeeImportDryRunRequest,
    EmployeeImportExecuteRequest,
    EmployeeOperationalCreate,
    EmployeeOperationalRead,
    EmployeeOperationalUpdate,
)
from app.modules.employees.service import EmployeeService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.platform_services.integration_models import ImportExportJob


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


def _csv_base64(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=IMPORT_HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return base64.b64encode(buffer.getvalue().encode("utf-8")).decode("ascii")


class FakeEmployeeService:
    def __init__(self, repository: "FakeEmployeeRepository") -> None:
        self.repository = repository

    def create_employee(
        self,
        tenant_id: str,
        payload: EmployeeOperationalCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        row = Employee(
            id=f"employee-{len(self.repository.employees) + 1}",
            tenant_id=tenant_id,
            personnel_no=payload.personnel_no,
            first_name=payload.first_name,
            last_name=payload.last_name,
            preferred_name=payload.preferred_name,
            work_email=payload.work_email,
            work_phone=payload.work_phone,
            mobile_phone=payload.mobile_phone,
            default_branch_id=payload.default_branch_id,
            default_mandate_id=payload.default_mandate_id,
            hire_date=payload.hire_date,
            termination_date=payload.termination_date,
            employment_type_code=payload.employment_type_code,
            target_weekly_hours=payload.target_weekly_hours,
            target_monthly_hours=payload.target_monthly_hours,
            user_id=payload.user_id,
            notes=payload.notes,
            status=payload.status or "active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=context.user_id,
            updated_by_user_id=context.user_id,
            version_no=1,
        )
        self.repository.employees.append(row)
        return EmployeeOperationalRead.model_validate(row)

    def update_employee(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeOperationalUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        row = self.repository.get_employee(tenant_id, employee_id)
        if row is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        if payload.personnel_no is not None:
            row.personnel_no = payload.personnel_no
        if payload.first_name is not None:
            row.first_name = payload.first_name
        if payload.last_name is not None:
            row.last_name = payload.last_name
        if payload.preferred_name is not None:
            row.preferred_name = payload.preferred_name
        if payload.work_email is not None:
            row.work_email = payload.work_email
        if payload.work_phone is not None:
            row.work_phone = payload.work_phone
        if payload.mobile_phone is not None:
            row.mobile_phone = payload.mobile_phone
        if payload.default_branch_id is not None:
            row.default_branch_id = payload.default_branch_id
        if payload.default_mandate_id is not None:
            row.default_mandate_id = payload.default_mandate_id
        if payload.hire_date is not None:
            row.hire_date = payload.hire_date
        if payload.termination_date is not None:
            row.termination_date = payload.termination_date
        if payload.employment_type_code is not None:
            row.employment_type_code = payload.employment_type_code
        if payload.target_weekly_hours is not None:
            row.target_weekly_hours = payload.target_weekly_hours
        if payload.target_monthly_hours is not None:
            row.target_monthly_hours = payload.target_monthly_hours
        if payload.user_id is not None:
            row.user_id = payload.user_id
        if payload.notes is not None:
            row.notes = payload.notes
        if payload.status is not None:
            row.status = payload.status
        row.updated_by_user_id = context.user_id
        row.updated_at = datetime.now(UTC)
        row.version_no += 1
        return EmployeeOperationalRead.model_validate(row)


class FakeDocumentService:
    def __init__(self) -> None:
        self.documents: list[dict[str, object]] = []

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document = {"id": f"document-{len(self.documents) + 1}", "tenant_id": tenant_id, "payload": payload, "versions": [], "links": []}
        self.documents.append(document)
        return type("DocumentRead", (), {"id": document["id"]})()

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(row for row in self.documents if row["id"] == document_id and row["tenant_id"] == tenant_id)
        document["versions"].append(payload)
        return payload

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(row for row in self.documents if row["id"] == document_id and row["tenant_id"] == tenant_id)
        document["links"].append(payload)
        return payload


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


@dataclass
class FakeEmployeeRepository:
    employees: list[Employee] = field(default_factory=list)
    users: list[UserAccount] = field(default_factory=list)
    roles: list[Role] = field(
        default_factory=lambda: [
            Role(
                id="role-employee-user",
                key="employee_user",
                name="Employee User",
                description="",
                is_portal_role=True,
                is_system_role=True,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
    )
    assignments: list[UserRoleAssignment] = field(default_factory=list)
    jobs: list[ImportExportJob] = field(default_factory=list)
    revoked_session_events: list[tuple[str, str]] = field(default_factory=list)

    def list_employees(self, tenant_id: str, filters: EmployeeFilter | None = None) -> list[Employee]:
        rows = [row for row in self.employees if row.tenant_id == tenant_id]
        if filters and filters.search:
            needle = filters.search.lower()
            rows = [row for row in rows if needle in row.personnel_no.lower() or needle in row.first_name.lower() or needle in row.last_name.lower()]
        if filters and not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        return next((row for row in self.employees if row.tenant_id == tenant_id and row.id == employee_id), None)

    def update_employee(self, row: Employee) -> Employee:
        row.updated_at = datetime.now(UTC)
        return row

    def find_employee_by_personnel_no(self, tenant_id: str, personnel_no: str, *, exclude_id: str | None = None) -> Employee | None:
        for row in self.employees:
            if row.tenant_id == tenant_id and row.personnel_no == personnel_no and row.id != exclude_id:
                return row
        return None

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> Employee | None:
        for row in self.employees:
            if row.tenant_id == tenant_id and row.user_id == user_id and row.id != exclude_id and row.archived_at is None:
                return row
        return None

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        return next((row for row in self.users if row.tenant_id == tenant_id and row.id == user_id), None)

    def find_user_account_by_username(self, tenant_id: str, username: str) -> UserAccount | None:
        return next((row for row in self.users if row.tenant_id == tenant_id and row.username.lower() == username.lower()), None)

    def find_user_account_by_email(self, tenant_id: str, email: str) -> UserAccount | None:
        return next((row for row in self.users if row.tenant_id == tenant_id and row.email.lower() == email.lower()), None)

    def create_user_account(self, row: UserAccount) -> UserAccount:
        row.id = f"user-{len(self.users) + 1}"
        row.created_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.version_no = 1
        row.status = "active"
        self.users.append(row)
        return row

    def update_user_account(self, row: UserAccount) -> UserAccount:
        row.updated_at = datetime.now(UTC)
        row.version_no += 1
        return row

    def revoke_active_sessions_for_user(self, user_id: str, *, reason: str, at_time: datetime) -> None:
        self.revoked_session_events.append((user_id, reason))

    def get_role_by_key(self, role_key: str) -> Role | None:
        return next((row for row in self.roles if row.key == role_key), None)

    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> UserRoleAssignment | None:
        role = self.get_role_by_key(role_key)
        if role is None:
            return None
        return next(
            (
                row
                for row in self.assignments
                if row.tenant_id == tenant_id and row.user_account_id == user_id and row.role_id == role.id and row.scope_type == "tenant"
            ),
            None,
        )

    def create_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment:
        row.id = f"assignment-{len(self.assignments) + 1}"
        row.created_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.version_no = 1
        row.status = "active"
        self.assignments.append(row)
        return row

    def update_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment:
        row.updated_at = datetime.now(UTC)
        row.version_no += 1
        return row

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        row.id = f"job-{len(self.jobs) + 1}"
        row.created_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.version_no = 1
        self.jobs.append(row)
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        row.updated_at = datetime.now(UTC)
        row.version_no += 1
        return row


class EmployeeOpsServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeEmployeeRepository(
            employees=[
                Employee(
                    id="employee-1",
                    tenant_id="tenant-1",
                    personnel_no="EMP-1001",
                    first_name="Anna",
                    last_name="Wagner",
                    work_email="anna@example.com",
                    notes="Operational only",
                    user_id=None,
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    created_by_user_id="seed",
                    updated_by_user_id="seed",
                    version_no=1,
                )
            ],
            users=[
                UserAccount(
                    id="user-existing",
                    tenant_id="tenant-1",
                    username="anna.user",
                    email="anna.user@example.com",
                    full_name="Anna User",
                    password_hash="hash",
                    locale="de",
                    timezone="Europe/Berlin",
                    is_platform_user=False,
                    is_password_login_enabled=True,
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    version_no=1,
                ),
                UserAccount(
                    id="user-other",
                    tenant_id="tenant-1",
                    username="other.user",
                    email="other.user@example.com",
                    full_name="Other User",
                    password_hash="hash",
                    locale="de",
                    timezone="Europe/Berlin",
                    is_platform_user=False,
                    is_password_login_enabled=True,
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    version_no=1,
                ),
            ],
        )
        self.document_service = FakeDocumentService()
        self.audit_repo = RecordingAuditRepository()
        self.service = EmployeeOpsService(
            employee_service=FakeEmployeeService(self.repository),
            repository=self.repository,
            document_service=self.document_service,
            audit_service=AuditService(self.audit_repo),
        )

    def test_dry_run_reports_row_errors_without_mutating(self) -> None:
        before_count = len(self.repository.employees)
        result = self.service.import_dry_run(
            "tenant-1",
            EmployeeImportDryRunRequest(
                tenant_id="tenant-1",
                csv_content_base64=_csv_base64(
                    [
                        {
                            "personnel_no": "",
                            "first_name": "Max",
                            "last_name": "",
                            "preferred_name": "",
                            "work_email": "",
                            "work_phone": "",
                            "mobile_phone": "",
                            "default_branch_id": "",
                            "default_mandate_id": "",
                            "hire_date": "",
                            "termination_date": "",
                            "status": "",
                            "employment_type_code": "",
                            "target_weekly_hours": "",
                            "target_monthly_hours": "",
                            "user_id": "",
                            "notes": "",
                        }
                    ]
                ),
            ),
            _context("employees.employee.write"),
        )
        self.assertEqual(result.invalid_rows, 1)
        self.assertEqual(len(self.repository.employees), before_count)

    def test_execute_import_is_idempotent_by_personnel_no(self) -> None:
        payload = EmployeeImportExecuteRequest(
            tenant_id="tenant-1",
            csv_content_base64=_csv_base64(
                [
                    {
                        "personnel_no": "EMP-1001",
                        "first_name": "Anna",
                        "last_name": "Wagner-Updated",
                        "preferred_name": "",
                        "work_email": "anna.updated@example.com",
                        "work_phone": "",
                        "mobile_phone": "",
                        "default_branch_id": "",
                        "default_mandate_id": "",
                        "hire_date": "",
                        "termination_date": "",
                        "status": "inactive",
                        "employment_type_code": "part_time",
                        "target_weekly_hours": "30",
                        "target_monthly_hours": "130",
                        "user_id": "",
                        "notes": "Updated",
                    }
                ]
            ),
            continue_on_error=True,
        )
        first = self.service.execute_import("tenant-1", payload, _context("employees.employee.write"))
        second = self.service.execute_import("tenant-1", payload, _context("employees.employee.write"))
        self.assertEqual(first.updated_employees, 1)
        self.assertEqual(second.updated_employees, 1)
        self.assertEqual(len(self.repository.employees), 1)
        self.assertEqual(self.repository.employees[0].last_name, "Wagner-Updated")
        self.assertEqual(self.repository.employees[0].status, "inactive")
        self.assertEqual(self.repository.employees[0].employment_type_code, "part_time")
        self.assertEqual(self.repository.employees[0].target_weekly_hours, 30)
        self.assertEqual(self.repository.employees[0].target_monthly_hours, 130)

    def test_export_uses_operational_fields_only(self) -> None:
        result = self.service.export_employees(
            "tenant-1",
            EmployeeExportRequest(tenant_id="tenant-1"),
            _context("employees.employee.read"),
        )
        self.assertEqual(result.row_count, 1)
        version_payload = self.document_service.documents[0]["versions"][0]
        decoded = base64.b64decode(version_payload.content_base64).decode("utf-8")
        self.assertIn("personnel_no,first_name,last_name", decoded)
        self.assertIn("employment_type_code,target_weekly_hours,target_monthly_hours", decoded)
        self.assertNotIn("tax_id", decoded)
        self.assertNotIn("bank_iban", decoded)

    def test_attach_existing_user_enforces_unique_link(self) -> None:
        self.repository.employees.append(
            Employee(
                id="employee-2",
                tenant_id="tenant-1",
                personnel_no="EMP-2000",
                first_name="Else",
                last_name="Binder",
                user_id="user-other",
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                created_by_user_id="seed",
                updated_by_user_id="seed",
                version_no=1,
            )
        )
        with self.assertRaises(ApiException) as raised:
            self.service.attach_existing_user(
                "tenant-1",
                "employee-1",
                EmployeeAccessAttachExistingRequest(tenant_id="tenant-1", user_id="user-other"),
                _context("employees.employee.write"),
            )
        self.assertEqual(raised.exception.code, "employees.employee.duplicate_user_link")

    def test_create_access_user_links_employee_and_assigns_employee_role(self) -> None:
        result = self.service.create_access_user(
            "tenant-1",
            "employee-1",
            EmployeeAccessCreateUserRequest(
                tenant_id="tenant-1",
                username="employee.anna",
                email="employee.anna@example.com",
                password="SicherPasswort!123",
            ),
            _context("employees.employee.write"),
        )
        self.assertTrue(result.app_access_enabled)
        self.assertEqual(self.repository.employees[0].user_id, "user-3")
        self.assertEqual(len(self.repository.assignments), 1)
        self.assertIn("employees.access.user_created_and_linked", [event.event_type for event in self.audit_repo.audit_events])

    def test_create_access_user_rejects_second_link_for_same_employee(self) -> None:
        self.repository.employees[0].user_id = "user-existing"

        with self.assertRaises(ApiException) as raised:
            self.service.create_access_user(
                "tenant-1",
                "employee-1",
                EmployeeAccessCreateUserRequest(
                    tenant_id="tenant-1",
                    username="employee.anna",
                    email="employee.anna@example.com",
                    password="SicherPasswort!123",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(raised.exception.code, "employees.access.already_linked")

    def test_update_access_user_changes_username_email_and_full_name(self) -> None:
        self.repository.employees[0].user_id = "user-existing"

        result = self.service.update_access_user(
            "tenant-1",
            "employee-1",
            EmployeeAccessUpdateUserRequest(
                tenant_id="tenant-1",
                username="anna.updated",
                email="anna.updated@example.com",
                full_name="Anna Updated",
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(result.username, "anna.updated")
        self.assertEqual(result.email, "anna.updated@example.com")
        self.assertEqual(result.full_name, "Anna Updated")
        self.assertIn("employees.access.user_updated", [event.event_type for event in self.audit_repo.audit_events])

    def test_update_access_user_rejects_duplicate_username(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        self.repository.users.append(
            UserAccount(
                id="user-third",
                tenant_id="tenant-1",
                username="taken.name",
                email="taken@example.com",
                full_name="Taken Name",
                password_hash="hash",
                locale="de",
                timezone="Europe/Berlin",
                is_platform_user=False,
                is_password_login_enabled=True,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        )

        with self.assertRaises(ApiException) as raised:
            self.service.update_access_user(
                "tenant-1",
                "employee-1",
                EmployeeAccessUpdateUserRequest(
                    tenant_id="tenant-1",
                    username="taken.name",
                    email="anna.updated@example.com",
                    full_name="Anna Updated",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(raised.exception.code, "employees.access.username_taken")

    def test_reset_access_user_password_updates_hash_and_revokes_sessions(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        previous_hash = self.repository.users[0].password_hash

        result = self.service.reset_access_user_password(
            "tenant-1",
            "employee-1",
            EmployeeAccessResetPasswordRequest(
                tenant_id="tenant-1",
                password="NeuesSicherPasswort!123",
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(result.user_id, "user-existing")
        self.assertNotEqual(self.repository.users[0].password_hash, previous_hash)
        self.assertEqual(
            self.repository.revoked_session_events,
            [("user-existing", "employee_access_password_reset")],
        )
        self.assertIn("employees.access.password_reset", [event.event_type for event in self.audit_repo.audit_events])

    def test_detach_access_user_clears_link_and_disables_assignment(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        role = self.repository.get_role_by_key("employee_user")
        assert role is not None
        self.repository.assignments.append(
            UserRoleAssignment(
                id="assignment-1",
                tenant_id="tenant-1",
                user_account_id="user-existing",
                role_id=role.id,
                scope_type="tenant",
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        )
        result = self.service.detach_access_user(
            "tenant-1",
            "employee-1",
            EmployeeAccessDetachRequest(tenant_id="tenant-1"),
            _context("employees.employee.write"),
        )
        self.assertIsNone(result.user_id)
        self.assertFalse(self.repository.assignments[0].status == "active")
        self.assertIn("employees.access.user_detached", [event.event_type for event in self.audit_repo.audit_events])


if __name__ == "__main__":
    unittest.main()

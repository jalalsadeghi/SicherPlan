from __future__ import annotations

import base64
import csv
import io
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

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
from app.modules.iam.auth_adapters import AuthExtensionHooks, PasswordResetDelivery, PasswordResetNotifier
from app.modules.iam.auth_schemas import AuthenticatedRoleScope, LoginRequest
from app.modules.iam.auth_service import AuthService, AuthThrottle
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.iam.security import hash_password
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


class SilentNotifier(PasswordResetNotifier):
    def send_password_reset(self, delivery: PasswordResetDelivery) -> str | None:
        return delivery.token_id


class NoopHooks(AuthExtensionHooks):
    def mfa_required(self, user_id: str) -> bool:
        return False

    def sso_hints(self) -> list[str]:
        return []


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
    role_permissions: dict[str, set[str]] = field(default_factory=lambda: {"employee_user": {"portal.employee.access"}})
    sessions: dict[str, object] = field(default_factory=dict)

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

    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]:
        permission_keys: set[str] = set()
        for assignment in self.assignments:
            role = next((row for row in self.roles if row.id == assignment.role_id), None)
            if (
                assignment.user_account_id == user_id
                and assignment.status == "active"
                and assignment.archived_at is None
                and role is not None
                and role.status == "active"
                and role.archived_at is None
            ):
                permission_keys.update(self.role_permissions.get(role.key, set()))
        return sorted(permission_keys)

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

    def find_user_by_tenant_and_identifier(self, tenant_code: str, identifier: str):
        if tenant_code != "tenant-1":
            return None
        user = next((row for row in self.users if row.username == identifier or row.email == identifier), None)
        if user is None:
            return None
        tenant = type("Tenant", (), {"id": "tenant-1", "code": "tenant-1"})()
        return user, tenant

    def get_user_by_id(self, user_account_id: str):
        return next((row for row in self.users if row.id == user_account_id), None)

    def list_role_scopes_for_user(self, user_account_id: str, at_time: datetime | None = None):
        scopes = []
        for assignment in self.assignments:
            role = next((row for row in self.roles if row.id == assignment.role_id), None)
            if assignment.user_account_id != user_account_id or role is None:
                continue
            scopes.append(
                type(
                    "RoleRecord",
                    (),
                    {
                        "role_key": role.key,
                        "scope_type": assignment.scope_type,
                        "branch_id": assignment.branch_id,
                        "mandate_id": assignment.mandate_id,
                        "customer_id": assignment.customer_id,
                        "subcontractor_id": assignment.subcontractor_id,
                    },
                )()
            )
        return scopes

    def create_session(self, session_row):
        session_id = str(uuid4())
        session = type(
            "Session",
            (),
            {
                "id": session_id,
                "tenant_id": session_row.tenant_id,
                "user_account_id": session_row.user_account_id,
                "session_token_hash": session_row.session_token_hash,
                "refresh_token_family": session_row.refresh_token_family,
                "expires_at": session_row.expires_at,
                "status": session_row.status,
                "issued_at": getattr(session_row, "issued_at", datetime.now(UTC)),
                "last_seen_at": session_row.last_seen_at,
                "revoked_at": session_row.revoked_at,
                "revoked_reason": session_row.revoked_reason,
                "device_label": session_row.device_label,
                "device_id": session_row.device_id,
                "ip_address": session_row.ip_address,
                "user_agent": session_row.user_agent,
                "metadata_json": session_row.metadata_json or {},
                "user_account": self.get_user_by_id(session_row.user_account_id),
            },
        )()
        self.sessions[session_id] = session
        return session

    def get_session_by_id(self, session_id: str):
        return self.sessions.get(session_id)

    def get_session_by_token_hash(self, token_hash: str):
        return next((row for row in self.sessions.values() if row.session_token_hash == token_hash), None)

    def list_sessions_for_user(self, user_account_id: str):
        return [row for row in self.sessions.values() if row.user_account_id == user_account_id]

    def update_session(self, session_row):
        self.sessions[session_row.id] = session_row
        return session_row

    def revoke_session(self, session_row, *, reason: str, at_time: datetime):
        session_row.status = "revoked"
        session_row.revoked_at = at_time
        session_row.revoked_reason = reason
        self.sessions[session_row.id] = session_row
        return session_row

    def revoke_all_sessions_for_user(self, user_account_id: str, *, except_session_id: str | None, reason: str, at_time: datetime):
        count = 0
        for session_row in self.sessions.values():
            if session_row.user_account_id != user_account_id or session_row.id == except_session_id:
                continue
            session_row.status = "revoked"
            session_row.revoked_at = at_time
            session_row.revoked_reason = reason
            count += 1
        return count

    def touch_user_login(self, user_account, at_time: datetime):
        user_account.last_login_at = at_time
        return user_account

    def update_user_password(self, user_account, password_hash: str, at_time: datetime):
        user_account.password_hash = password_hash
        user_account.updated_at = at_time
        return user_account

    def invalidate_active_reset_tokens(self, user_account_id: str, at_time: datetime):
        return 0

    def create_password_reset_token(self, token_row):
        return token_row

    def update_password_reset_token(self, token_row):
        return token_row

    def get_password_reset_token_by_hash(self, token_hash: str):
        return None

    def mark_password_reset_token_used(self, token_row, at_time: datetime):
        return token_row


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

    def build_auth_service(self) -> AuthService:
        return AuthService(
            self.repository,
            auth_secret="test-secret",
            access_ttl_minutes=15,
            refresh_ttl_minutes=60,
            remember_me_refresh_ttl_minutes=120,
            reset_ttl_minutes=30,
            notifier=SilentNotifier(),
            extension_hooks=NoopHooks(),
            throttle=AuthThrottle(max_attempts=3, lockout_minutes=15),
            audit_service=None,
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

    def test_access_diagnostics_report_missing_password_hash(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        self.repository.users[0].password_hash = None
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

        result = self.service.get_access_link("tenant-1", "employee-1", _context("employees.employee.write"))

        self.assertTrue(result.diagnostics.user_exists)
        self.assertFalse(result.diagnostics.has_password_hash)
        self.assertFalse(result.diagnostics.can_mobile_login)
        self.assertFalse(result.app_access_enabled)

    def test_access_diagnostics_report_inactive_user(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        self.repository.users[0].status = "inactive"
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

        result = self.service.get_access_link("tenant-1", "employee-1", _context("employees.employee.write"))

        self.assertFalse(result.diagnostics.user_status_active)
        self.assertFalse(result.diagnostics.can_mobile_login)

    def test_access_diagnostics_report_missing_mobile_permission(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        role = self.repository.get_role_by_key("employee_user")
        assert role is not None
        self.repository.role_permissions["employee_user"] = set()
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

        result = self.service.get_access_link("tenant-1", "employee-1", _context("employees.employee.write"))

        self.assertTrue(result.role_assignment_active)
        self.assertFalse(result.diagnostics.portal_employee_access_granted)
        self.assertFalse(result.diagnostics.can_mobile_login)

    def test_access_diagnostics_report_fully_ready_mobile_login_state(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        role = self.repository.get_role_by_key("employee_user")
        assert role is not None
        self.repository.users[0].password_hash = hash_password("SicherPasswort!123")
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

        result = self.service.get_access_link("tenant-1", "employee-1", _context("employees.employee.write"))

        self.assertTrue(result.role_assignment_active)
        self.assertTrue(result.diagnostics.portal_employee_access_granted)
        self.assertTrue(result.diagnostics.can_mobile_login)
        self.assertTrue(result.app_access_enabled)

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

    def test_reset_access_user_password_allows_subsequent_login(self) -> None:
        self.repository.employees[0].user_id = "user-existing"
        self.repository.users[0].password_hash = hash_password("OldSicherPasswort!123")
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

        self.service.reset_access_user_password(
            "tenant-1",
            "employee-1",
            EmployeeAccessResetPasswordRequest(
                tenant_id="tenant-1",
                password="NeuesSicherPasswort!123",
            ),
            _context("employees.employee.write"),
        )

        login = self.build_auth_service().login(
            LoginRequest(
                tenant_code="tenant-1",
                identifier="anna.user",
                password="NeuesSicherPasswort!123",
            ),
            ip_address="127.0.0.1",
            user_agent="employee-app",
        )

        self.assertEqual(login.user.username, "anna.user")
        self.assertTrue(login.session.access_token)

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

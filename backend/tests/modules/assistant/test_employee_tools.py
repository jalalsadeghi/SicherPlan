from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.employees.models import (
    Employee,
    EmployeeAbsence,
    EmployeeAvailabilityRule,
    EmployeeIdCredential,
    EmployeeQualification,
)
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import UserAccount, UserRoleAssignment
from app.modules.iam.security import hash_password


@dataclass
class _AuditEmployeeRepository:
    audits: list[object] = field(default_factory=list)
    employees: list[Employee] = field(default_factory=list)
    users: list[UserAccount] = field(default_factory=list)
    assignments: list[UserRoleAssignment] = field(default_factory=list)
    qualifications: list[EmployeeQualification] = field(default_factory=list)
    absences: list[EmployeeAbsence] = field(default_factory=list)
    availability_rules: list[EmployeeAvailabilityRule] = field(default_factory=list)
    credentials: list[EmployeeIdCredential] = field(default_factory=list)
    role_permissions: dict[str, set[str]] = field(default_factory=lambda: {"employee_user": {}})

    def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
    def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
    def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def list_employees(self, tenant_id: str, filters=None):  # noqa: ANN001, ANN201
        rows = [row for row in self.employees if row.tenant_id == tenant_id]
        if filters and getattr(filters, "search", None):
            needle = filters.search.casefold().strip()
            rows = [
                row
                for row in rows
                if needle in row.personnel_no.casefold()
                or needle in row.first_name.casefold()
                or needle in row.last_name.casefold()
                or needle in (row.preferred_name or "").casefold()
            ]
        if filters and not getattr(filters, "include_archived", False):
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_employee(self, tenant_id: str, employee_id: str):  # noqa: ANN201
        return next((row for row in self.employees if row.tenant_id == tenant_id and row.id == employee_id), None)

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None):  # noqa: ANN201
        return next(
            (
                row
                for row in self.employees
                if row.tenant_id == tenant_id and row.user_id == user_id and row.id != exclude_id and row.archived_at is None
            ),
            None,
        )

    def get_user_account(self, tenant_id: str, user_id: str):  # noqa: ANN201
        return next((row for row in self.users if row.tenant_id == tenant_id and row.id == user_id), None)

    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]:
        del at_time
        permission_keys: set[str] = set()
        for assignment in self.assignments:
            if assignment.user_account_id != user_id or assignment.status != "active" or assignment.archived_at is not None:
                continue
            permission_keys.update(self.role_permissions.get(assignment.role_id, set()))
        return sorted(permission_keys)

    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str):  # noqa: ANN201
        return next(
            (
                row
                for row in self.assignments
                if row.tenant_id == tenant_id and row.user_account_id == user_id and row.role_id == role_key
            ),
            None,
        )

    def list_employee_qualifications(self, tenant_id: str, filters=None):  # noqa: ANN001, ANN201
        rows = [row for row in self.qualifications if row.tenant_id == tenant_id]
        if filters and getattr(filters, "employee_id", None):
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters and not getattr(filters, "include_archived", False):
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def list_absences(self, tenant_id: str, filters=None):  # noqa: ANN001, ANN201
        rows = [row for row in self.absences if row.tenant_id == tenant_id]
        if filters and getattr(filters, "employee_id", None):
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters and not getattr(filters, "include_archived", False):
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def list_availability_rules(self, tenant_id: str, filters=None):  # noqa: ANN001, ANN201
        rows = [row for row in self.availability_rules if row.tenant_id == tenant_id]
        if filters and getattr(filters, "employee_id", None):
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters and not getattr(filters, "include_archived", False):
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def list_credentials(self, tenant_id: str, filters=None):  # noqa: ANN001, ANN201
        rows = [row for row in self.credentials if row.tenant_id == tenant_id]
        if filters and getattr(filters, "employee_id", None):
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters and not getattr(filters, "include_archived", False):
            rows = [row for row in rows if row.archived_at is None]
        return rows


def _context(*, role_keys: tuple[str, ...], permission_keys: tuple[str, ...], user_id: str = "assistant-user-1") -> RequestAuthorizationContext:
    role_key = role_keys[0]
    scope_type = "tenant"
    if role_key == "customer_user":
        scope_type = "customer"
    elif role_key == "employee_user":
        scope_type = "tenant"
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="assistant-req-1",
    )


def _service(repository: _AuditEmployeeRepository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
        tool_registry=build_default_tool_registry(audit_repository=repository, employee_repository=repository),
    )


def _employee(
    *,
    employee_id: str,
    tenant_id: str = "tenant-1",
    first_name: str,
    last_name: str,
    personnel_no: str,
    preferred_name: str | None = None,
    user_id: str | None = None,
    status: str = "active",
    archived_at: datetime | None = None,
    notes: str | None = None,
) -> Employee:
    now = datetime.now(UTC)
    return Employee(
        id=employee_id,
        tenant_id=tenant_id,
        personnel_no=personnel_no,
        first_name=first_name,
        last_name=last_name,
        preferred_name=preferred_name,
        default_branch_id="branch-1",
        default_mandate_id="mandate-1",
        user_id=user_id,
        status=status,
        archived_at=archived_at,
        notes=notes,
        created_at=now,
        updated_at=now,
        version_no=1,
    )


def _repository() -> _AuditEmployeeRepository:
    repository = _AuditEmployeeRepository()
    repository.employees = [
        _employee(employee_id="employee-1", first_name="Markus", last_name="Neumann", personnel_no="E-100", user_id="user-1", notes="operational note"),
        _employee(employee_id="employee-2", first_name="Mark", last_name="Nebel", personnel_no="E-101"),
        _employee(employee_id="employee-3", first_name="Markus", last_name="Noll", personnel_no="E-102", archived_at=datetime(2026, 1, 1, tzinfo=UTC), status="archived"),
        _employee(employee_id="employee-4", tenant_id="tenant-2", first_name="Markus", last_name="Other", personnel_no="X-200"),
    ]
    repository.users = [
        UserAccount(
            id="user-1",
            tenant_id="tenant-1",
            username="markus.user",
            email="markus@example.com",
            full_name="Markus Neumann",
            password_hash=hash_password("SicherPasswort!123"),
            status="active",
            archived_at=None,
            is_password_login_enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        ),
        UserAccount(
            id="user-2",
            tenant_id="tenant-1",
            username="inactive.user",
            email="inactive@example.com",
            full_name="Inactive User",
            password_hash=hash_password("SicherPasswort!123"),
            status="inactive",
            archived_at=None,
            is_password_login_enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        ),
    ]
    repository.assignments = [
        UserRoleAssignment(
            id="assignment-1",
            tenant_id="tenant-1",
            user_account_id="user-1",
            role_id="employee_user",
            scope_type="tenant",
            status="active",
            archived_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        ),
        UserRoleAssignment(
            id="assignment-2",
            tenant_id="tenant-1",
            user_account_id="user-2",
            role_id="employee_user",
            scope_type="tenant",
            status="active",
            archived_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        ),
    ]
    repository.role_permissions = {"employee_user": {"portal.employee.access"}}
    repository.qualifications = [
        EmployeeQualification(
            id="qualification-1",
            tenant_id="tenant-1",
            employee_id="employee-1",
            record_kind="qualification",
            valid_until=date(2026, 4, 1),
            archived_at=None,
            status="active",
        )
    ]
    repository.absences = [
        EmployeeAbsence(
            id="absence-1",
            tenant_id="tenant-1",
            employee_id="employee-1",
            absence_type="vacation",
            starts_on=date(2026, 5, 1),
            ends_on=date(2026, 5, 2),
            quantity_days=2,
            status="approved",
            archived_at=None,
        )
    ]
    repository.availability_rules = [
        EmployeeAvailabilityRule(
            id="availability-1",
            tenant_id="tenant-1",
            employee_id="employee-1",
            rule_kind="unavailable",
            starts_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC),
            ends_at=datetime(2026, 5, 1, 23, 59, tzinfo=UTC),
            recurrence_type="none",
            weekday_mask=None,
            status="active",
            archived_at=None,
        )
    ]
    repository.credentials = [
        EmployeeIdCredential(
            id="credential-1",
            tenant_id="tenant-1",
            employee_id="employee-1",
            credential_no="BADGE-1",
            credential_type="company_id",
            encoded_value="secret-encoded",
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 12, 31),
            status="issued",
            archived_at=None,
        )
    ]
    return repository


def test_authorized_internal_user_can_search_visible_employee_by_name() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Markus"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 1
    assert result.data["matches"][0]["display_name"] == "Markus Neumann"


def test_no_visible_employee_returns_safe_not_found_message() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Nobody"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["matches"] == []
    assert result.data["safe_message_key"] == "assistant.employee.not_found_or_not_permitted"


def test_multiple_visible_matches_respect_limit() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Mark", "limit": 1},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 2
    assert len(result.data["matches"]) == 1
    assert result.data["truncated"] is True


def test_cross_tenant_employee_is_not_returned() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Other"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["matches"] == []


def test_archived_employee_is_excluded_by_default() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Noll"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["matches"] == []


def test_archived_employee_is_included_when_requested() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Noll", "include_archived": True},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["matches"][0]["status"] == "archived"


def test_operational_profile_excludes_hr_private_fields() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_operational_profile",
        input_data={"employee_ref": "employee-1"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["found"] is True
    employee = result.data["employee"]
    assert "birth_date" not in employee
    assert "tax_id" not in employee
    assert "bank_iban" not in employee
    assert employee["user_status"] == "active"


def test_mobile_access_status_covers_missing_link_inactive_and_ready_states() -> None:
    repository = _repository()
    service = _service(repository)
    actor = _context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.write"))

    missing_link = service.execute_registered_tool(
        tool_name="employees.get_employee_mobile_access_status",
        input_data={"employee_ref": "employee-2"},
        actor=actor,
    )
    repository.employees[1].user_id = "user-2"
    inactive = service.execute_registered_tool(
        tool_name="employees.get_employee_mobile_access_status",
        input_data={"employee_ref": "employee-2"},
        actor=actor,
    )
    ready = service.execute_registered_tool(
        tool_name="employees.get_employee_mobile_access_status",
        input_data={"employee_ref": "employee-1"},
        actor=actor,
    )

    assert missing_link.ok is True
    assert any(item["code"] == "missing_access_link" for item in missing_link.data["mobile_access"]["blocking_reasons"])
    assert any(item["code"] == "inactive_user" for item in inactive.data["mobile_access"]["blocking_reasons"])
    assert ready.data["mobile_access"]["can_receive_released_schedules"] is True


def test_readiness_summary_detects_date_specific_absence_and_redacted_summaries() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_readiness_summary",
        input_data={"employee_ref": "employee-1", "date": "2026-05-01"},
        actor=_context(
            role_keys=("tenant_admin",),
            permission_keys=("assistant.chat.access", "employees.employee.read", "employees.private.read"),
        ),
    )

    assert result.ok is True
    assert result.data["found"] is True
    readiness = result.data["readiness"]
    assert readiness["has_active_absence_on_date"] is True
    assert readiness["availability_summary"] == "unavailable"
    assert readiness["qualification_summary"]["details_redacted"] is True
    assert readiness["credential_summary"]["details_redacted"] is True


def test_readiness_summary_handles_missing_private_permission_safely() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_readiness_summary",
        input_data={"employee_ref": "employee-1", "date": "2026-05-01"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert result.data["missing_permissions"] == [
        {
            "permission": "employees.private.read",
            "reason": "Absence details require HR-private read permission.",
        }
    ]


def test_employee_tool_calls_are_audited_without_openai() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_operational_profile",
        input_data={"employee_ref": "employee-1"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is True
    assert repository.audits
    assert repository.audits[0].tool_name == "employees.get_employee_operational_profile"

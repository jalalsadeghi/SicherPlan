from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace

from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import UserAccount, UserRoleAssignment
from app.modules.iam.security import hash_password
from app.modules.planning.schemas import ShiftListFilter, StaffingFilter


@dataclass
class _AuditFieldRepository:
    audits: list[object] = field(default_factory=list)
    employees: dict[str, object] = field(default_factory=dict)
    users: dict[str, UserAccount] = field(default_factory=dict)
    role_assignments: list[UserRoleAssignment] = field(default_factory=list)
    role_permissions: dict[str, set[str]] = field(default_factory=lambda: {"employee_user": {"portal.employee.access"}})
    shifts: dict[str, object] = field(default_factory=dict)
    assignments: dict[str, object] = field(default_factory=dict)

    def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
    def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
    def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def get_employee(self, tenant_id: str, employee_id: str):
        row = self.employees.get(employee_id)
        return row if row is not None and row.tenant_id == tenant_id else None

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None):
        for row in self.employees.values():
            if row.tenant_id == tenant_id and row.user_id == user_id and row.id != exclude_id:
                return row
        return None

    def get_user_account(self, tenant_id: str, user_id: str):
        row = self.users.get(user_id)
        return row if row is not None and row.tenant_id == tenant_id else None

    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]:
        del at_time
        keys: set[str] = set()
        for row in self.role_assignments:
            if row.user_account_id == user_id and row.status == "active" and row.archived_at is None:
                keys.update(self.role_permissions.get(row.role_id, set()))
        return sorted(keys)

    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str):
        return next(
            (
                row
                for row in self.role_assignments
                if row.tenant_id == tenant_id and row.user_account_id == user_id and row.role_id == role_key
            ),
            None,
        )

    def get_shift(self, tenant_id: str, row_id: str):
        row = self.shifts.get(row_id)
        return row if row is not None and row.tenant_id == tenant_id else None

    def get_assignment(self, tenant_id: str, row_id: str):
        row = self.assignments.get(row_id)
        return row if row is not None and row.tenant_id == tenant_id else None

    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[object]:
        rows = [row for row in self.assignments.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        return sorted(rows, key=lambda row: row.id)

    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]:
        return [
            row
            for row in self.assignments.values()
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[object]:
        rows = [row for row in self.shifts.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.release_state is not None:
            rows = [row for row in rows if row.release_state == filters.release_state]
        return sorted(rows, key=lambda row: row.id)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]:
        del tenant_id, owner_type, owner_id
        return []


def _context(*, role_keys: tuple[str, ...], permission_keys: tuple[str, ...], user_id: str = "dispatcher-1") -> RequestAuthorizationContext:
    role_key = role_keys[0]
    scope_type = "tenant"
    if role_key == "customer_user":
        scope_type = "customer"
    elif role_key == "subcontractor_user":
        scope_type = "subcontractor"
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="assistant-req-1",
    )


def _service(repository: _AuditFieldRepository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            planning_repository=repository,
            employee_repository=repository,
        ),
    )


def _employee(*, employee_id: str, user_id: str | None, tenant_id: str = "tenant-1", status: str = "active", archived_at=None):
    return SimpleNamespace(
        id=employee_id,
        tenant_id=tenant_id,
        user_id=user_id,
        status=status,
        archived_at=archived_at,
        personnel_no=f"P-{employee_id}",
        first_name=employee_id,
        last_name="User",
        preferred_name=None,
        notes=None,
        default_branch_id="branch-1",
        default_mandate_id="mandate-1",
    )


def _user(*, user_id: str, tenant_id: str = "tenant-1", status: str = "active", enabled: bool = True, password_hash_value: str | None = None, archived_at=None):
    return UserAccount(
        id=user_id,
        tenant_id=tenant_id,
        username=user_id,
        email=f"{user_id}@example.com",
        full_name=user_id,
        password_hash=password_hash_value if password_hash_value is not None else hash_password("SicherPasswort!123"),
        status=status,
        archived_at=archived_at,
        is_password_login_enabled=enabled,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version_no=1,
    )


def _repository() -> _AuditFieldRepository:
    now = datetime(2026, 5, 1, 8, tzinfo=UTC)
    planning_record_released = SimpleNamespace(id="planning-record-1", release_state="released")
    planning_record_draft = SimpleNamespace(id="planning-record-2", release_state="draft")
    planning_record_released.order_id = "order-1"
    planning_record_released.site_detail = None
    planning_record_released.order = SimpleNamespace(id="order-1")
    planning_record_draft.order_id = "order-2"
    planning_record_draft.site_detail = None
    planning_record_draft.order = SimpleNamespace(id="order-2")
    shift_plan_active = SimpleNamespace(id="shift-plan-1", status="active", planning_record=planning_record_released, planning_record_id="planning-record-1")
    shift_plan_draft = SimpleNamespace(id="shift-plan-2", status="draft", planning_record=planning_record_released, planning_record_id="planning-record-1")
    shift_plan_record_draft = SimpleNamespace(id="shift-plan-3", status="active", planning_record=planning_record_draft, planning_record_id="planning-record-2")
    shifts = {
        "shift-visible": SimpleNamespace(
            id="shift-visible",
            tenant_id="tenant-1",
            shift_plan=shift_plan_active,
            shift_plan_id="shift-plan-1",
            starts_at=now,
            ends_at=now.replace(hour=16),
            release_state="released",
            status="active",
            archived_at=None,
            stealth_mode_flag=False,
            location_text="Objekt A",
            meeting_point="Gate 1",
            released_at=now,
        ),
        "shift-unreleased": SimpleNamespace(
            id="shift-unreleased",
            tenant_id="tenant-1",
            shift_plan=shift_plan_active,
            shift_plan_id="shift-plan-1",
            starts_at=now.replace(day=2),
            ends_at=now.replace(day=2, hour=16),
            release_state="draft",
            status="active",
            archived_at=None,
            stealth_mode_flag=False,
            location_text="Objekt B",
            meeting_point="Gate 2",
            released_at=None,
        ),
        "shift-plan-draft": SimpleNamespace(
            id="shift-plan-draft",
            tenant_id="tenant-1",
            shift_plan=shift_plan_draft,
            shift_plan_id="shift-plan-2",
            starts_at=now.replace(day=3),
            ends_at=now.replace(day=3, hour=16),
            release_state="released",
            status="active",
            archived_at=None,
            stealth_mode_flag=False,
            location_text="Objekt C",
            meeting_point="Gate 3",
            released_at=now,
        ),
        "shift-record-draft": SimpleNamespace(
            id="shift-record-draft",
            tenant_id="tenant-1",
            shift_plan=shift_plan_record_draft,
            shift_plan_id="shift-plan-3",
            starts_at=now.replace(day=4),
            ends_at=now.replace(day=4, hour=16),
            release_state="released",
            status="active",
            archived_at=None,
            stealth_mode_flag=False,
            location_text="Objekt D",
            meeting_point="Gate 4",
            released_at=now,
        ),
        "shift-stealth": SimpleNamespace(
            id="shift-stealth",
            tenant_id="tenant-1",
            shift_plan=shift_plan_active,
            shift_plan_id="shift-plan-1",
            starts_at=now.replace(day=5),
            ends_at=now.replace(day=5, hour=16),
            release_state="released",
            status="active",
            archived_at=None,
            stealth_mode_flag=True,
            location_text="Objekt E",
            meeting_point="Gate 5",
            released_at=now,
        ),
        "shift-tenant-2": SimpleNamespace(
            id="shift-tenant-2",
            tenant_id="tenant-2",
            shift_plan=shift_plan_active,
            shift_plan_id="shift-plan-1",
            starts_at=now,
            ends_at=now.replace(hour=16),
            release_state="released",
            status="active",
            archived_at=None,
            stealth_mode_flag=False,
            location_text="Other",
            meeting_point=None,
            released_at=now,
        ),
    }
    assignments = {
        "assignment-visible": SimpleNamespace(
            id="assignment-visible",
            tenant_id="tenant-1",
            shift_id="shift-visible",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-cancelled": SimpleNamespace(
            id="assignment-cancelled",
            tenant_id="tenant-1",
            shift_id="shift-visible",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="removed",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-archived": SimpleNamespace(
            id="assignment-archived",
            tenant_id="tenant-1",
            shift_id="shift-visible",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=now,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-unreleased": SimpleNamespace(
            id="assignment-unreleased",
            tenant_id="tenant-1",
            shift_id="shift-unreleased",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-plan-draft": SimpleNamespace(
            id="assignment-plan-draft",
            tenant_id="tenant-1",
            shift_id="shift-plan-draft",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-record-draft": SimpleNamespace(
            id="assignment-record-draft",
            tenant_id="tenant-1",
            shift_id="shift-record-draft",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-stealth": SimpleNamespace(
            id="assignment-stealth",
            tenant_id="tenant-1",
            shift_id="shift-stealth",
            employee_id="employee-1",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-ambiguous-1": SimpleNamespace(
            id="assignment-ambiguous-1",
            tenant_id="tenant-1",
            shift_id="shift-visible",
            employee_id="employee-2",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-ambiguous-2": SimpleNamespace(
            id="assignment-ambiguous-2",
            tenant_id="tenant-1",
            shift_id="shift-unreleased",
            employee_id="employee-2",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
        "assignment-tenant-2": SimpleNamespace(
            id="assignment-tenant-2",
            tenant_id="tenant-2",
            shift_id="shift-tenant-2",
            employee_id="employee-9",
            subcontractor_worker_id=None,
            assignment_status_code="assigned",
            archived_at=None,
            offered_at=now,
            confirmed_at=None,
        ),
    }
    repository = _AuditFieldRepository(
        employees={
            "employee-1": _employee(employee_id="employee-1", user_id="user-1"),
            "employee-2": _employee(employee_id="employee-2", user_id="user-2"),
            "employee-no-link": _employee(employee_id="employee-no-link", user_id=None),
            "employee-inactive-user": _employee(employee_id="employee-inactive-user", user_id="user-3"),
            "employee-tenant-2": _employee(employee_id="employee-tenant-2", user_id="user-9", tenant_id="tenant-2"),
        },
        users={
            "user-1": _user(user_id="user-1"),
            "user-2": _user(user_id="user-2"),
            "user-3": _user(user_id="user-3", status="inactive"),
            "user-9": _user(user_id="user-9", tenant_id="tenant-2"),
        },
        role_assignments=[
            UserRoleAssignment(id="role-1", tenant_id="tenant-1", user_account_id="user-1", role_id="employee_user", scope_type="tenant", status="active", archived_at=None, created_at=now, updated_at=now, version_no=1),
            UserRoleAssignment(id="role-2", tenant_id="tenant-1", user_account_id="user-2", role_id="employee_user", scope_type="tenant", status="active", archived_at=None, created_at=now, updated_at=now, version_no=1),
            UserRoleAssignment(id="role-3", tenant_id="tenant-1", user_account_id="user-3", role_id="employee_user", scope_type="tenant", status="active", archived_at=None, created_at=now, updated_at=now, version_no=1),
        ],
        shifts=shifts,
        assignments=assignments,
    )
    assignments["assignment-no-link"] = SimpleNamespace(
        id="assignment-no-link",
        tenant_id="tenant-1",
        shift_id="shift-visible",
        employee_id="employee-no-link",
        subcontractor_worker_id=None,
        assignment_status_code="assigned",
        archived_at=None,
        offered_at=now,
        confirmed_at=None,
    )
    assignments["assignment-inactive-user"] = SimpleNamespace(
        id="assignment-inactive-user",
        tenant_id="tenant-1",
        shift_id="shift-visible",
        employee_id="employee-inactive-user",
        subcontractor_worker_id=None,
        assignment_status_code="assigned",
        archived_at=None,
        offered_at=now,
        confirmed_at=None,
    )
    return repository


def _internal_perms(*extra: str) -> tuple[str, ...]:
    return (
        "assistant.chat.access",
        "assistant.diagnostics.read",
        "planning.staffing.read",
        "planning.shift.read",
        "employees.employee.read",
        "employees.employee.write",
        *extra,
    )


def test_visible_schedule_when_all_rules_pass() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )

    assert result.ok is True
    assert result.data["visibility"]["visible"] is True
    assert result.data["visibility"]["visibility_state"] == "visible"


def test_not_visible_without_linked_user() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-no-link", "employee_ref": "employee-no-link"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    codes = {row["code"] for row in result.data["visibility"]["blocking_reasons"]}
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert "missing_access_link" in codes


def test_not_visible_when_linked_user_is_inactive() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-inactive-user", "employee_ref": "employee-inactive-user"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    codes = {row["code"] for row in result.data["visibility"]["blocking_reasons"]}
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert "inactive_linked_user" in codes


def test_not_visible_when_assignment_is_cancelled() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-cancelled", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert any(row["code"] == "assignment_cancelled" for row in result.data["visibility"]["blocking_reasons"])


def test_not_visible_when_assignment_is_archived() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-archived", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert any(row["code"] == "assignment_archived" for row in result.data["visibility"]["blocking_reasons"])


def test_not_visible_when_shift_is_not_released() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-unreleased", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert any(row["code"] == "shift_not_released" for row in result.data["visibility"]["blocking_reasons"])


def test_not_visible_when_shift_plan_or_planning_record_is_below_released() -> None:
    repository = _repository()
    plan_result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-plan-draft", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    record_result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-record-draft", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert any(row["code"] == "shift_plan_not_released" for row in plan_result.data["visibility"]["blocking_reasons"])
    assert any(row["code"] == "planning_record_not_released" for row in record_result.data["visibility"]["blocking_reasons"])


def test_not_visible_when_stealth_mode_suppresses_display() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-stealth", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert any(row["code"] == "stealth_mode" for row in result.data["visibility"]["blocking_reasons"])


def test_unknown_when_missing_employee_mobile_access_permission() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1"},
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "assistant.diagnostics.read", "planning.staffing.read", "employees.employee.read"),
        ),
    )
    assert result.data["visibility"]["visibility_state"] == "unknown"
    assert any(row["permission"] == "employees.employee.write" for row in result.data["visibility"]["missing_permissions"])


def test_unknown_when_missing_planning_permission() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1"},
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "assistant.diagnostics.read", "employees.employee.read", "employees.employee.write"),
        ),
    )
    assert result.data["visibility"]["visibility_state"] == "unknown"
    assert any(row["permission"] == "planning.staffing.read" for row in result.data["visibility"]["missing_permissions"])


def test_ambiguous_when_multiple_assignments_match_employee_and_date() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"employee_ref": "employee-2", "date_from": "2026-05-01", "date_to": "2026-05-02"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.data["visibility"]["visibility_state"] == "ambiguous"
    assert len(result.data["matches"]) >= 2


def test_employee_self_service_user_can_inspect_own_schedule_only() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access"), user_id="user-1"),
    )
    assert result.ok is True
    assert result.data["visibility"]["employee_ref"] == "employee-1"


def test_employee_self_service_user_cannot_inspect_another_employee() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-ambiguous-1", "employee_ref": "employee-2"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access"), user_id="user-1"),
    )
    assert result.ok is True
    assert result.data["found"] is False


def test_cross_tenant_refs_are_not_inspectable() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-tenant-2", "employee_ref": "employee-tenant-2"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.ok is True
    assert result.data["found"] is False


def test_tool_call_audit_rows_are_created() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=_internal_perms()),
    )
    assert result.ok is True
    assert repository.audits[-1].tool_name == "field.inspect_released_schedule_visibility"

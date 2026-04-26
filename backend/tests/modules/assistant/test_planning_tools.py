from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace

from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.schemas import ShiftListFilter, StaffingFilter


@dataclass
class _AuditPlanningRepository:
    audits: list[object] = field(default_factory=list)
    shifts: list[object] = field(default_factory=list)
    assignments: list[object] = field(default_factory=list)
    demand_groups: list[object] = field(default_factory=list)
    subcontractor_releases: list[object] = field(default_factory=list)
    employees: list[object] = field(default_factory=list)
    subcontractor_workers: list[object] = field(default_factory=list)
    validation_overrides: list[object] = field(default_factory=list)

    def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
    def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
    def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[object]:
        rows = [row for row in self.shifts if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_plan_id is not None:
            rows = [row for row in rows if row.shift_plan_id == filters.shift_plan_id]
        if filters.planning_record_id is not None:
            rows = [row for row in rows if row.shift_plan.planning_record.id == filters.planning_record_id]
        if filters.date_from is not None:
            rows = [row for row in rows if row.starts_at.date() >= filters.date_from]
        if filters.date_to is not None:
            rows = [row for row in rows if row.starts_at.date() < filters.date_to]
        if filters.release_state is not None:
            rows = [row for row in rows if row.release_state == filters.release_state]
        if filters.lifecycle_status is not None:
            rows = [row for row in rows if row.status == filters.lifecycle_status]
        if filters.visibility_state == "customer":
            rows = [row for row in rows if row.customer_visible_flag]
        elif filters.visibility_state == "subcontractor":
            rows = [row for row in rows if row.subcontractor_visible_flag]
        elif filters.visibility_state == "stealth":
            rows = [row for row in rows if row.stealth_mode_flag]
        return sorted(rows, key=lambda row: (row.starts_at, row.id))

    def get_shift(self, tenant_id: str, row_id: str):
        return next((row for row in self.shifts if row.tenant_id == tenant_id and row.id == row_id), None)

    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[object]:
        return [
            row
            for row in self.shifts
            if row.tenant_id == tenant_id and row.archived_at is None and row.shift_plan.planning_record.id == planning_record_id
        ]

    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[object]:
        rows = [row for row in self.assignments if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.subcontractor_worker_id is not None:
            rows = [row for row in rows if row.subcontractor_worker_id == filters.subcontractor_worker_id]
        if filters.assignment_status_code is not None:
            rows = [row for row in rows if row.assignment_status_code == filters.assignment_status_code]
        return sorted(rows, key=lambda row: (row.created_at, row.id))

    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]:
        return [
            row
            for row in self.assignments
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def get_assignment(self, tenant_id: str, row_id: str):
        return next((row for row in self.assignments if row.tenant_id == tenant_id and row.id == row_id), None)

    def get_demand_group(self, tenant_id: str, row_id: str):
        return next((row for row in self.demand_groups if row.tenant_id == tenant_id and row.id == row_id), None)

    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[object]:
        return [row for row in self.demand_groups if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None]

    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[object]:
        return [
            row
            for row in self.subcontractor_releases
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def get_employee(self, tenant_id: str, employee_id: str):
        return next((row for row in self.employees if row.tenant_id == tenant_id and row.id == employee_id), None)

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str):
        return next((row for row in self.subcontractor_workers if row.tenant_id == tenant_id and row.id == worker_id), None)

    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None:
        del tenant_id, key
        return None

    def list_employee_qualifications(self, tenant_id: str, employee_id: str) -> list[object]:
        del tenant_id, employee_id
        return []

    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[object]:
        del tenant_id, worker_id
        return []

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]:
        del tenant_id, owner_type, owner_id
        return []

    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date: date) -> list[object]:
        del tenant_id, customer_id, employee_id, on_date
        return []

    def list_overlapping_assignments(
        self,
        tenant_id: str,
        *,
        starts_at: datetime,
        ends_at: datetime,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        exclude_assignment_id: str | None = None,
    ) -> list[object]:
        del starts_at, ends_at
        rows = [row for row in self.assignments if row.tenant_id == tenant_id and row.id != exclude_assignment_id and row.archived_at is None]
        if employee_id is not None:
            rows = [row for row in rows if row.employee_id == employee_id]
        if subcontractor_worker_id is not None:
            rows = [row for row in rows if row.subcontractor_worker_id == subcontractor_worker_id]
        return rows

    def list_assignments_for_actor_in_window(
        self,
        tenant_id: str,
        *,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        window_start: datetime,
        window_end: datetime,
        exclude_assignment_id: str | None = None,
    ) -> list[object]:
        del window_start, window_end
        return self.list_overlapping_assignments(
            tenant_id,
            starts_at=datetime.now(UTC),
            ends_at=datetime.now(UTC),
            employee_id=employee_id,
            subcontractor_worker_id=subcontractor_worker_id,
            exclude_assignment_id=exclude_assignment_id,
        )

    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str) -> list[object]:
        return [
            row
            for row in self.validation_overrides
            if row.tenant_id == tenant_id and row.assignment_id == assignment_id
        ]


def _context(*, role_keys: tuple[str, ...], permission_keys: tuple[str, ...], user_id: str = "dispatcher-1") -> RequestAuthorizationContext:
    role_key = role_keys[0]
    scope_type = "tenant"
    if role_key == "customer_user":
        scope_type = "customer"
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="assistant-req-1",
    )


def _service(repository: _AuditPlanningRepository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
        tool_registry=build_default_tool_registry(audit_repository=repository, planning_repository=repository),
    )


def _repository() -> _AuditPlanningRepository:
    now = datetime(2026, 5, 1, 8, tzinfo=UTC)
    tenant_1_order = SimpleNamespace(
        id="order-1",
        tenant_id="tenant-1",
        customer_id="customer-1",
        order_no="ORD-100",
        release_state="released",
        status="active",
        archived_at=None,
    )
    tenant_2_order = SimpleNamespace(
        id="order-9",
        tenant_id="tenant-2",
        customer_id="customer-9",
        order_no="ORD-900",
        release_state="released",
        status="active",
        archived_at=None,
    )
    planning_record = SimpleNamespace(
        id="planning-record-1",
        tenant_id="tenant-1",
        order_id="order-1",
        order=tenant_1_order,
        release_state="released",
        status="active",
        archived_at=None,
    )
    planning_record_draft = SimpleNamespace(
        id="planning-record-2",
        tenant_id="tenant-1",
        order_id="order-1",
        order=tenant_1_order,
        release_state="draft",
        status="active",
        archived_at=None,
    )
    planning_record_t2 = SimpleNamespace(
        id="planning-record-9",
        tenant_id="tenant-2",
        order_id="order-9",
        order=tenant_2_order,
        release_state="released",
        status="active",
        archived_at=None,
    )
    shift_plan = SimpleNamespace(
        id="shift-plan-1",
        tenant_id="tenant-1",
        planning_record_id="planning-record-1",
        planning_record=planning_record,
        status="active",
        archived_at=None,
    )
    shift_plan_draft = SimpleNamespace(
        id="shift-plan-2",
        tenant_id="tenant-1",
        planning_record_id="planning-record-2",
        planning_record=planning_record_draft,
        status="draft",
        archived_at=None,
    )
    shift_plan_t2 = SimpleNamespace(
        id="shift-plan-9",
        tenant_id="tenant-2",
        planning_record_id="planning-record-9",
        planning_record=planning_record_t2,
        status="active",
        archived_at=None,
    )

    shift_1 = SimpleNamespace(
        id="shift-1",
        tenant_id="tenant-1",
        shift_plan_id="shift-plan-1",
        shift_plan=shift_plan,
        starts_at=now,
        ends_at=now.replace(hour=16),
        status="active",
        release_state="released",
        customer_visible_flag=False,
        subcontractor_visible_flag=False,
        stealth_mode_flag=False,
        location_text="Objekt A",
        meeting_point="Tor 1",
        archived_at=None,
    )
    shift_2 = SimpleNamespace(
        id="shift-2",
        tenant_id="tenant-1",
        shift_plan_id="shift-plan-2",
        shift_plan=shift_plan_draft,
        starts_at=now.replace(day=2),
        ends_at=now.replace(day=2, hour=18),
        status="active",
        release_state="draft",
        customer_visible_flag=False,
        subcontractor_visible_flag=False,
        stealth_mode_flag=False,
        location_text="Objekt B",
        meeting_point="Tor 2",
        archived_at=None,
    )
    shift_3 = SimpleNamespace(
        id="shift-3",
        tenant_id="tenant-1",
        shift_plan_id="shift-plan-1",
        shift_plan=shift_plan,
        starts_at=now.replace(day=3),
        ends_at=now.replace(day=3, hour=14),
        status="active",
        release_state="released",
        customer_visible_flag=True,
        subcontractor_visible_flag=False,
        stealth_mode_flag=True,
        location_text="Objekt C",
        meeting_point="Tor 3",
        archived_at=None,
    )
    shift_archived = SimpleNamespace(
        id="shift-archived",
        tenant_id="tenant-1",
        shift_plan_id="shift-plan-1",
        shift_plan=shift_plan,
        starts_at=now.replace(day=4),
        ends_at=now.replace(day=4, hour=14),
        status="cancelled",
        release_state="draft",
        customer_visible_flag=False,
        subcontractor_visible_flag=False,
        stealth_mode_flag=False,
        location_text="Archiv",
        meeting_point=None,
        archived_at=now,
    )
    shift_t2 = SimpleNamespace(
        id="shift-tenant-2",
        tenant_id="tenant-2",
        shift_plan_id="shift-plan-9",
        shift_plan=shift_plan_t2,
        starts_at=now,
        ends_at=now.replace(hour=17),
        status="active",
        release_state="released",
        customer_visible_flag=False,
        subcontractor_visible_flag=False,
        stealth_mode_flag=False,
        location_text="Other",
        meeting_point=None,
        archived_at=None,
    )

    demand_group_1 = SimpleNamespace(
        id="demand-group-1",
        tenant_id="tenant-1",
        shift_id="shift-1",
        function_type_id="function-1",
        qualification_type_id="qualification-1",
        min_qty=1,
        target_qty=1,
        archived_at=None,
    )
    demand_group_2 = SimpleNamespace(
        id="demand-group-2",
        tenant_id="tenant-1",
        shift_id="shift-2",
        function_type_id="function-2",
        qualification_type_id=None,
        min_qty=2,
        target_qty=2,
        archived_at=None,
    )
    demand_group_3 = SimpleNamespace(
        id="demand-group-3",
        tenant_id="tenant-1",
        shift_id="shift-3",
        function_type_id="function-1",
        qualification_type_id=None,
        min_qty=1,
        target_qty=1,
        archived_at=None,
    )

    assignment_1 = SimpleNamespace(
        id="assignment-1",
        tenant_id="tenant-1",
        shift_id="shift-1",
        demand_group_id="demand-group-1",
        team_id="team-1",
        employee_id="employee-1",
        subcontractor_worker_id=None,
        assignment_status_code="assigned",
        assignment_source_code="dispatcher",
        offered_at=now,
        confirmed_at=None,
        remarks="internal-only note",
        archived_at=None,
        created_at=now,
    )
    assignment_removed = SimpleNamespace(
        id="assignment-removed",
        tenant_id="tenant-1",
        shift_id="shift-1",
        demand_group_id="demand-group-1",
        team_id=None,
        employee_id="employee-2",
        subcontractor_worker_id=None,
        assignment_status_code="removed",
        assignment_source_code="manual",
        offered_at=None,
        confirmed_at=None,
        remarks=None,
        archived_at=now,
        created_at=now.replace(minute=1),
    )
    assignment_worker = SimpleNamespace(
        id="assignment-worker",
        tenant_id="tenant-1",
        shift_id="shift-2",
        demand_group_id="demand-group-2",
        team_id=None,
        employee_id=None,
        subcontractor_worker_id="worker-1",
        assignment_status_code="confirmed",
        assignment_source_code="subcontractor_release",
        offered_at=now.replace(day=2),
        confirmed_at=now.replace(day=2, hour=9),
        remarks=None,
        archived_at=None,
        created_at=now.replace(day=2),
    )
    assignment_t2 = SimpleNamespace(
        id="assignment-tenant-2",
        tenant_id="tenant-2",
        shift_id="shift-tenant-2",
        demand_group_id="demand-group-9",
        team_id=None,
        employee_id="employee-9",
        subcontractor_worker_id=None,
        assignment_status_code="assigned",
        assignment_source_code="dispatcher",
        offered_at=None,
        confirmed_at=None,
        remarks=None,
        archived_at=None,
        created_at=now,
    )

    repository = _AuditPlanningRepository(
        shifts=[shift_1, shift_2, shift_3, shift_archived, shift_t2],
        assignments=[assignment_1, assignment_removed, assignment_worker, assignment_t2],
        demand_groups=[demand_group_1, demand_group_2, demand_group_3],
        employees=[
            SimpleNamespace(id="employee-1", tenant_id="tenant-1"),
            SimpleNamespace(id="employee-2", tenant_id="tenant-1"),
        ],
        subcontractor_workers=[SimpleNamespace(id="worker-1", tenant_id="tenant-1", subcontractor_id="sub-1")],
        validation_overrides=[SimpleNamespace(id="override-1", tenant_id="tenant-1", assignment_id="assignment-1", rule_code="qualification_match")],
    )
    return repository


def test_authorized_dispatcher_can_find_shifts_by_date() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"date": "2026-05-01"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 1
    assert result.data["matches"][0]["shift_ref"] == "shift-1"
    assert result.data["matches"][0]["match_reason"] == "date"


def test_authorized_dispatcher_can_find_assignments_for_employee_and_date() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_assignments",
        input_data={"employee_ref": "employee-1", "date": "2026-05-01"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 1
    assert result.data["matches"][0]["assignment_ref"] == "assignment-1"
    assert result.data["matches"][0]["actor_type"] == "employee"


def test_cross_tenant_shift_is_not_returned() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"shift_plan_ref": "shift-plan-9", "include_archived": True},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 0


def test_cross_tenant_assignment_is_not_returned() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_assignments",
        input_data={"employee_ref": "employee-9", "include_archived": True},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert result.ok is True
    assert result.data["match_count"] == 0


def test_archived_shifts_and_assignments_are_excluded_by_default() -> None:
    repository = _repository()
    shift_result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"include_archived": False},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )
    assignment_result = _service(repository).execute_registered_tool(
        tool_name="planning.find_assignments",
        input_data={"employee_ref": "employee-2", "include_archived": False},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert all(match["shift_ref"] != "shift-archived" for match in shift_result.data["matches"])
    assert assignment_result.data["match_count"] == 0


def test_include_archived_returns_archived_rows_for_internal_user() -> None:
    repository = _repository()
    shift_result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"include_archived": True},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )
    assignment_result = _service(repository).execute_registered_tool(
        tool_name="planning.find_assignments",
        input_data={"employee_ref": "employee-2", "include_archived": True},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert any(match["shift_ref"] == "shift-archived" for match in shift_result.data["matches"])
    assert assignment_result.data["matches"][0]["assignment_status"] == "archived"


def test_assignment_inspection_returns_active_and_cancelled_state_correctly() -> None:
    repository = _repository()
    service = _service(repository)
    active = service.execute_registered_tool(
        tool_name="planning.inspect_assignment",
        input_data={"assignment_ref": "assignment-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )
    cancelled = service.execute_registered_tool(
        tool_name="planning.inspect_assignment",
        input_data={"assignment_ref": "assignment-removed"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert active.data["assignment"]["assignment_status"] == "active"
    assert cancelled.data["assignment"]["assignment_status"] == "archived"
    assert cancelled.data["assignment"]["blocking_reasons"][0]["code"] == "assignment_inactive"


def test_shift_release_inspection_returns_shift_plan_and_planning_record_release_information() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_shift_release_state",
        input_data={"shift_ref": "shift-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    assert result.data["release_state"]["shift_release_state"] == "released"
    assert result.data["release_state"]["shift_plan_ref"] == "shift-plan-1"
    assert result.data["release_state"]["planning_record_ref"] == "planning-record-1"
    assert result.data["release_state"]["planning_record_release_state"] == "released"


def test_shift_visibility_reports_hidden_state_when_visibility_flags_disabled() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_shift_visibility",
        input_data={"shift_ref": "shift-1", "target_audience": "customer_portal"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    assert result.data["visibility"]["visibility_state"] == "not_visible"
    assert result.data["visibility"]["blocking_reasons"][0]["code"] == "visibility_flag_disabled"


def test_shift_visibility_reports_stealth_mode_as_blocker() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_shift_visibility",
        input_data={"shift_ref": "shift-3", "target_audience": "customer_portal"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    codes = {row["code"] for row in result.data["visibility"]["blocking_reasons"]}
    assert "stealth_mode" in codes


def test_assignment_validation_inspection_returns_safe_normalized_summaries() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_assignment_validations",
        input_data={"assignment_ref": "assignment-1"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert result.ok is True
    codes = {row["code"] for row in result.data["validations"]}
    assert "qualification_mismatch" in codes
    assert any(row["override_present"] is True for row in result.data["validations"])


def test_release_validation_inspection_returns_minimum_staffing_failure() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_shift_release_validations",
        input_data={"shift_ref": "shift-2"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.staffing.read")),
    )

    assert result.ok is True
    assert result.data["blocking_count"] >= 1
    assert result.data["release_validations"][0]["code"] == "minimum_staffing"


def test_row_limit_and_audit_records_are_created() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"include_archived": True, "limit": 2},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access", "planning.shift.read")),
    )

    assert result.ok is True
    assert result.data["truncated"] is True
    assert len(result.data["matches"]) == 2
    assert repository.audits[-1].tool_name == "planning.find_shifts"

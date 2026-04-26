"""Read-only assistant tools for safe planning diagnostics."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.schemas import (
    AssistantMissingPermission,
    AssistantPlanningAssignmentInspectInput,
    AssistantPlanningAssignmentInspectItemRead,
    AssistantPlanningAssignmentInspectRead,
    AssistantPlanningAssignmentMatchRead,
    AssistantPlanningAssignmentSearchInput,
    AssistantPlanningAssignmentSearchRead,
    AssistantPlanningAssignmentValidationsRead,
    AssistantPlanningBlockingReasonRead,
    AssistantPlanningReleaseValidationInput,
    AssistantPlanningReleaseValidationItemRead,
    AssistantPlanningReleaseValidationsRead,
    AssistantPlanningShiftMatchRead,
    AssistantPlanningShiftRefInput,
    AssistantPlanningShiftReleaseStateItemRead,
    AssistantPlanningShiftReleaseStateRead,
    AssistantPlanningShiftSearchInput,
    AssistantPlanningShiftSearchRead,
    AssistantPlanningShiftVisibilityInput,
    AssistantPlanningShiftVisibilityItemRead,
    AssistantPlanningShiftVisibilityRead,
    AssistantPlanningValidationInput,
    AssistantPlanningValidationItemRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.iam.authz import enforce_scope
from app.modules.planning.schemas import ShiftListFilter, StaffingFilter
from app.modules.planning.validation_service import PlanningValidationService


PLANNING_SHIFT_READ_PERMISSION = "planning.shift.read"
PLANNING_STAFFING_READ_PERMISSION = "planning.staffing.read"
_VISIBLE_ASSIGNMENT_STATUSES = {"offered", "assigned", "confirmed"}


class AssistantPlanningRepository(Protocol):
    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Any]: ...
    def get_shift(self, tenant_id: str, row_id: str) -> Any | None: ...
    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[Any]: ...
    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[Any]: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Any]: ...
    def get_assignment(self, tenant_id: str, row_id: str) -> Any | None: ...
    def get_demand_group(self, tenant_id: str, row_id: str) -> Any | None: ...
    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[Any]: ...
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[Any]: ...
    def get_employee(self, tenant_id: str, employee_id: str) -> Any | None: ...
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str) -> Any | None: ...
    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None: ...
    def list_employee_qualifications(self, tenant_id: str, employee_id: str) -> list[Any]: ...
    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[Any]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Any]: ...
    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date: date) -> list[Any]: ...
    def list_overlapping_assignments(
        self,
        tenant_id: str,
        *,
        starts_at: datetime,
        ends_at: datetime,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        exclude_assignment_id: str | None = None,
    ) -> list[Any]: ...
    def list_assignments_for_actor_in_window(
        self,
        tenant_id: str,
        *,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        window_start: datetime,
        window_end: datetime,
        exclude_assignment_id: str | None = None,
    ) -> list[Any]: ...
    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str) -> list[Any]: ...


class FindShiftsTool:
    def __init__(self, *, repository: AssistantPlanningRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="planning.find_shifts",
            description="Find visible planning shifts within the current tenant scope.",
            input_schema=AssistantPlanningShiftSearchInput,
            output_schema=AssistantPlanningShiftSearchRead,
            required_permissions=["assistant.chat.access", PLANNING_SHIFT_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
            max_rows=10,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        if context.tenant_id is None:
            payload = AssistantPlanningShiftSearchRead(matches=[], match_count=0, truncated=False).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        window = _resolve_date_window(
            date_value=getattr(input_data, "date", None),
            date_from=getattr(input_data, "date_from", None),
            date_to=getattr(input_data, "date_to", None),
        )
        filters = ShiftListFilter(
            date_from=window[0].date() if window[0] is not None else None,
            date_to=window[1].date() if window[1] is not None else None,
            include_archived=bool(getattr(input_data, "include_archived", False)),
        )
        rows = self.repository.list_shifts(context.tenant_id, filters)
        employee_ref = _clean_ref(getattr(input_data, "employee_ref", None))
        planning_record_ref = _clean_ref(getattr(input_data, "planning_record_ref", None))
        shift_plan_ref = _clean_ref(getattr(input_data, "shift_plan_ref", None))
        customer_ref = _clean_ref(getattr(input_data, "customer_ref", None))

        employee_shift_ids: set[str] | None = None
        if employee_ref is not None:
            employee_shift_ids = {
                row.shift_id
                for row in self.repository.list_assignments(
                    context.tenant_id,
                    StaffingFilter(employee_id=employee_ref, include_archived=bool(getattr(input_data, "include_archived", False))),
                )
            }

        matches: list[AssistantPlanningShiftMatchRead] = []
        for row in rows:
            if window[0] is not None and row.starts_at < window[0]:
                continue
            if window[1] is not None and row.starts_at >= window[1]:
                continue
            if employee_shift_ids is not None and row.id not in employee_shift_ids:
                continue
            if planning_record_ref is not None and _planning_record_ref(row) != planning_record_ref:
                continue
            if shift_plan_ref is not None and getattr(row, "shift_plan_id", None) != shift_plan_ref:
                continue
            if customer_ref is not None and _customer_ref(row) != customer_ref:
                continue
            matches.append(
                AssistantPlanningShiftMatchRead(
                    shift_ref=row.id,
                    shift_plan_ref=getattr(row, "shift_plan_id", None),
                    planning_record_ref=_planning_record_ref(row),
                    customer_ref=_customer_ref(row),
                    starts_at=row.starts_at,
                    ends_at=row.ends_at,
                    status=_shift_status(row),
                    release_state=_normalized_shift_release_state(row),
                    employee_visible=_is_shift_candidate_for_employee_app(row),
                    customer_visible=bool(getattr(row, "customer_visible_flag", False)),
                    subcontractor_visible=bool(getattr(row, "subcontractor_visible_flag", False)),
                    location_label=getattr(row, "location_text", None),
                    match_reason=_shift_match_reason(
                        employee_ref=employee_ref,
                        planning_record_ref=planning_record_ref,
                        shift_plan_ref=shift_plan_ref,
                        customer_ref=customer_ref,
                        date_value=getattr(input_data, "date", None),
                        date_from=getattr(input_data, "date_from", None),
                        date_to=getattr(input_data, "date_to", None),
                    ),
                )
            )

        limit = int(getattr(input_data, "limit", self.definition.max_rows))
        payload = AssistantPlanningShiftSearchRead(
            matches=matches[:limit],
            match_count=len(matches),
            truncated=len(matches) > limit,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class FindAssignmentsTool:
    def __init__(self, *, repository: AssistantPlanningRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="planning.find_assignments",
            description="Find staffing assignments within the current tenant scope.",
            input_schema=AssistantPlanningAssignmentSearchInput,
            output_schema=AssistantPlanningAssignmentSearchRead,
            required_permissions=["assistant.chat.access", PLANNING_STAFFING_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
            max_rows=10,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        if context.tenant_id is None:
            payload = AssistantPlanningAssignmentSearchRead(matches=[], match_count=0, truncated=False).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        include_archived = bool(getattr(input_data, "include_archived", False))
        rows = self.repository.list_assignments(
            context.tenant_id,
            StaffingFilter(
                shift_id=_clean_ref(getattr(input_data, "shift_ref", None)),
                employee_id=_clean_ref(getattr(input_data, "employee_ref", None)),
                include_archived=include_archived,
            ),
        )
        window = _resolve_date_window(
            date_value=getattr(input_data, "date", None),
            date_from=getattr(input_data, "date_from", None),
            date_to=getattr(input_data, "date_to", None),
        )
        requested_status = _clean_ref(getattr(input_data, "assignment_status", None))
        shift_cache: dict[str, Any | None] = {}
        matches: list[AssistantPlanningAssignmentMatchRead] = []
        for row in rows:
            normalized_status = _normalized_assignment_status(row)
            if requested_status is not None and normalized_status != requested_status:
                continue
            shift = shift_cache.setdefault(row.shift_id, self.repository.get_shift(context.tenant_id, row.shift_id))
            if shift is None:
                continue
            if window[0] is not None and shift.starts_at < window[0]:
                continue
            if window[1] is not None and shift.starts_at >= window[1]:
                continue
            matches.append(
                AssistantPlanningAssignmentMatchRead(
                    assignment_ref=row.id,
                    shift_ref=row.shift_id,
                    employee_ref=getattr(row, "employee_id", None),
                    subcontractor_worker_ref=getattr(row, "subcontractor_worker_id", None),
                    actor_type=_assignment_actor_type(row),
                    assignment_status=normalized_status,
                    source_code=_normalized_assignment_source(row),
                    offered_at=getattr(row, "offered_at", None),
                    confirmed_at=getattr(row, "confirmed_at", None),
                    starts_at=getattr(shift, "starts_at", None),
                    ends_at=getattr(shift, "ends_at", None),
                    shift_release_state=_normalized_shift_release_state(shift),
                    is_visible_candidate_for_employee_app=_assignment_visible_candidate(row, shift),
                )
            )

        limit = int(getattr(input_data, "limit", self.definition.max_rows))
        payload = AssistantPlanningAssignmentSearchRead(
            matches=matches[:limit],
            match_count=len(matches),
            truncated=len(matches) > limit,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class InspectAssignmentTool:
    def __init__(self, *, repository: AssistantPlanningRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="planning.inspect_assignment",
            description="Inspect a single planning assignment with a safe operational summary.",
            input_schema=AssistantPlanningAssignmentInspectInput,
            output_schema=AssistantPlanningAssignmentInspectRead,
            required_permissions=["assistant.chat.access", PLANNING_STAFFING_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        assignment = _resolve_assignment(self.repository, context, getattr(input_data, "assignment_ref", ""))
        if assignment is None:
            payload = AssistantPlanningAssignmentInspectRead(found=False, assignment=None, redactions=[]).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        shift = self.repository.get_shift(context.tenant_id or "", assignment.shift_id)
        blocking_reasons: list[AssistantPlanningBlockingReasonRead] = []
        if _normalized_assignment_status(assignment) in {"cancelled", "archived"}:
            blocking_reasons.append(
                AssistantPlanningBlockingReasonRead(
                    code="assignment_inactive",
                    severity="blocking",
                    message="Assignment is not active for downstream visibility.",
                )
            )
        if _assignment_actor_type(assignment) == "subcontractor_worker":
            blocking_reasons.append(
                AssistantPlanningBlockingReasonRead(
                    code="not_employee_assignment",
                    severity="info",
                    message="Assignment targets a subcontractor worker, not an employee app actor.",
                )
            )
        if shift is not None and not _is_shift_candidate_for_employee_app(shift):
            blocking_reasons.append(
                AssistantPlanningBlockingReasonRead(
                    code="shift_not_released",
                    severity="blocking",
                    message="The linked shift is not in a released internal execution state.",
                )
            )

        payload = AssistantPlanningAssignmentInspectRead(
            found=True,
            assignment=AssistantPlanningAssignmentInspectItemRead(
                assignment_ref=assignment.id,
                shift_ref=assignment.shift_id,
                demand_group_ref=getattr(assignment, "demand_group_id", None),
                employee_ref=getattr(assignment, "employee_id", None),
                subcontractor_worker_ref=getattr(assignment, "subcontractor_worker_id", None),
                actor_type=_assignment_actor_type(assignment),
                assignment_status=_normalized_assignment_status(assignment),
                offered_at=getattr(assignment, "offered_at", None),
                confirmed_at=getattr(assignment, "confirmed_at", None),
                team_ref=getattr(assignment, "team_id", None),
                is_active_for_schedule_visibility=_assignment_visible_candidate(assignment, shift),
                blocking_reasons=blocking_reasons,
            ),
            redactions=["assignment_remarks"],
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"assignment_ref": assignment.id, "shift_ref": assignment.shift_id},
        )


class InspectShiftReleaseStateTool:
    def __init__(self, *, repository: AssistantPlanningRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="planning.inspect_shift_release_state",
            description="Inspect normalized release state across shift, shift plan, and planning record.",
            input_schema=AssistantPlanningShiftRefInput,
            output_schema=AssistantPlanningShiftReleaseStateRead,
            required_permissions=["assistant.chat.access", PLANNING_SHIFT_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        shift = _resolve_shift(self.repository, context, getattr(input_data, "shift_ref", ""))
        if shift is None:
            payload = AssistantPlanningShiftReleaseStateRead(found=False, release_state=None).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        planning_record = _planning_record(shift)
        shift_plan = getattr(shift, "shift_plan", None)
        blocking_reasons: list[AssistantPlanningBlockingReasonRead] = []
        if getattr(shift, "release_state", None) != "released":
            blocking_reasons.append(
                AssistantPlanningBlockingReasonRead(
                    code="shift_not_released",
                    severity="blocking",
                    message="Shift release state is below released.",
                )
            )
        if planning_record is not None and getattr(planning_record, "release_state", None) != "released":
            blocking_reasons.append(
                AssistantPlanningBlockingReasonRead(
                    code="planning_record_not_released",
                    severity="warning",
                    message="Planning record release state is below released.",
                )
            )

        payload = AssistantPlanningShiftReleaseStateRead(
            found=True,
            release_state=AssistantPlanningShiftReleaseStateItemRead(
                shift_ref=shift.id,
                shift_status=_shift_status(shift),
                shift_release_state=_normalized_shift_release_state(shift),
                shift_plan_ref=getattr(shift, "shift_plan_id", None),
                shift_plan_status=_resource_status(shift_plan),
                planning_record_ref=_planning_record_ref(shift),
                planning_record_status=_resource_status(planning_record),
                planning_record_release_state=_normalized_parent_release_state(planning_record),
                is_released_for_internal_execution=getattr(shift, "release_state", None) == "released",
                is_released_for_employee_app=_is_shift_candidate_for_employee_app(shift),
                blocking_reasons=blocking_reasons,
            ),
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"shift_ref": shift.id, "planning_record_ref": _planning_record_ref(shift)},
        )


class InspectShiftVisibilityTool:
    def __init__(self, *, repository: AssistantPlanningRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="planning.inspect_shift_visibility",
            description="Inspect planning-level visibility flags for one shift.",
            input_schema=AssistantPlanningShiftVisibilityInput,
            output_schema=AssistantPlanningShiftVisibilityRead,
            required_permissions=["assistant.chat.access", PLANNING_SHIFT_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        shift = _resolve_shift(self.repository, context, getattr(input_data, "shift_ref", ""))
        if shift is None:
            payload = AssistantPlanningShiftVisibilityRead(found=False, visibility=None).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        audience = _normalized_target_audience(getattr(input_data, "target_audience", None))
        visible, state, blocking_reasons = _visibility_summary(shift, audience)
        payload = AssistantPlanningShiftVisibilityRead(
            found=True,
            visibility=AssistantPlanningShiftVisibilityItemRead(
                shift_ref=shift.id,
                target_audience=audience,
                employee_visible=_is_shift_candidate_for_employee_app(shift),
                customer_visible_flag=bool(getattr(shift, "customer_visible_flag", False)),
                subcontractor_visible_flag=bool(getattr(shift, "subcontractor_visible_flag", False)),
                stealth_mode_flag=bool(getattr(shift, "stealth_mode_flag", False)),
                dispatch_output_required=False,
                dispatch_output_present=False,
                visibility_state=state if visible else state,
                blocking_reasons=blocking_reasons,
            ),
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"shift_ref": shift.id},
        )


class InspectAssignmentValidationsTool:
    def __init__(self, *, repository: AssistantPlanningRepository, validation_service: PlanningValidationService) -> None:
        self.repository = repository
        self.validation_service = validation_service
        self.definition = AssistantToolDefinition(
            name="planning.inspect_assignment_validations",
            description="Inspect normalized assignment validation results for one assignment.",
            input_schema=AssistantPlanningValidationInput,
            output_schema=AssistantPlanningAssignmentValidationsRead,
            required_permissions=["assistant.chat.access", PLANNING_STAFFING_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        assignment = _resolve_assignment(self.repository, context, getattr(input_data, "assignment_ref", ""))
        if assignment is None:
            payload = AssistantPlanningAssignmentValidationsRead(found=False).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        validation = self.validation_service.validate_assignment_by_id(context.tenant_id or "", assignment.id)
        override_codes = {row.rule_code for row in self.repository.list_assignment_validation_overrides(context.tenant_id or "", assignment.id)}
        items = [
            AssistantPlanningValidationItemRead(
                code=_normalized_validation_code(issue.rule_code),
                severity=_normalized_severity(issue.severity),
                status=_validation_status(issue.severity, issue.rule_code in override_codes),
                summary=_safe_validation_summary(issue),
                override_present=issue.rule_code in override_codes,
            )
            for issue in validation.issues
        ]
        payload = AssistantPlanningAssignmentValidationsRead(
            found=True,
            validations=items,
            blocking_count=validation.blocking_count,
            warning_count=validation.warning_count,
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"assignment_ref": assignment.id, "shift_ref": assignment.shift_id},
        )


class InspectShiftReleaseValidationsTool:
    def __init__(self, *, repository: AssistantPlanningRepository, validation_service: PlanningValidationService) -> None:
        self.repository = repository
        self.validation_service = validation_service
        self.definition = AssistantToolDefinition(
            name="planning.inspect_shift_release_validations",
            description="Inspect normalized release validations for a shift or planning record.",
            input_schema=AssistantPlanningReleaseValidationInput,
            output_schema=AssistantPlanningReleaseValidationsRead,
            required_permissions=["assistant.chat.access", PLANNING_STAFFING_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="planning_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        _enforce_planning_scope(context)
        shift_ref = _clean_ref(getattr(input_data, "shift_ref", None))
        planning_record_ref = _clean_ref(getattr(input_data, "planning_record_ref", None))
        if shift_ref is None and planning_record_ref is None:
            payload = AssistantPlanningReleaseValidationsRead(found=False).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        issues: list[Any] = []
        entity_refs: dict[str, Any] = {}
        blocking_count = 0
        warning_count = 0
        if shift_ref is not None:
            shift = _resolve_shift(self.repository, context, shift_ref)
            if shift is None:
                payload = AssistantPlanningReleaseValidationsRead(found=False).model_dump(mode="json")
                return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
            if planning_record_ref is not None and _planning_record_ref(shift) != planning_record_ref:
                payload = AssistantPlanningReleaseValidationsRead(found=False).model_dump(mode="json")
                return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
            validation = self.validation_service.validate_shift_release(context.tenant_id or "", shift.id)
            issues = validation.issues
            blocking_count = validation.blocking_count
            warning_count = validation.warning_count
            entity_refs = {"shift_ref": shift.id, "planning_record_ref": _planning_record_ref(shift)}
        else:
            shift_rows = self.repository.list_shifts_for_planning_record(context.tenant_id or "", planning_record_ref or "")
            if not shift_rows:
                payload = AssistantPlanningReleaseValidationsRead(found=False).model_dump(mode="json")
                return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)
            validation = self.validation_service.validate_planning_record_release(context.tenant_id or "", planning_record_ref or "")
            issues = validation.issues
            blocking_count = validation.blocking_count
            warning_count = validation.warning_count
            entity_refs = {"planning_record_ref": planning_record_ref}

        payload = AssistantPlanningReleaseValidationsRead(
            found=True,
            release_validations=[
                AssistantPlanningReleaseValidationItemRead(
                    code=_normalized_validation_code(issue.rule_code),
                    severity=_normalized_severity(issue.severity),
                    status=_validation_status(issue.severity, False),
                    summary=_safe_validation_summary(issue),
                )
                for issue in issues
            ],
            blocking_count=blocking_count,
            warning_count=warning_count,
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload, entity_refs=entity_refs)


def _enforce_planning_scope(context: AssistantToolExecutionContext) -> None:
    enforce_scope(context.auth_context, scope="tenant", tenant_id=context.tenant_id)


def _resolve_date_window(
    *,
    date_value: date | None,
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    if date_value is not None:
        if date_from is not None and date_value < date_from:
            return datetime.combine(date_from, time.min, tzinfo=UTC), datetime.combine(date_from + timedelta(days=1), time.min, tzinfo=UTC)
        if date_to is not None and date_value > date_to:
            return datetime.combine(date_to, time.min, tzinfo=UTC), datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        return (
            datetime.combine(date_value, time.min, tzinfo=UTC),
            datetime.combine(date_value + timedelta(days=1), time.min, tzinfo=UTC),
        )
    start = datetime.combine(date_from, time.min, tzinfo=UTC) if date_from is not None else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC) if date_to is not None else None
    return start, end


def _shift_match_reason(
    *,
    employee_ref: str | None,
    planning_record_ref: str | None,
    shift_plan_ref: str | None,
    customer_ref: str | None,
    date_value: date | None,
    date_from: date | None,
    date_to: date | None,
) -> str:
    reasons = [
        reason
        for reason, active in (
            ("employee", employee_ref is not None),
            ("planning_record", planning_record_ref is not None),
            ("shift_plan", shift_plan_ref is not None),
            ("customer", customer_ref is not None),
            ("date", date_value is not None or date_from is not None or date_to is not None),
        )
        if active
    ]
    if not reasons:
        return "combined"
    if len(reasons) == 1:
        return reasons[0]
    return "combined"


def _resolve_shift(repository: AssistantPlanningRepository, context: AssistantToolExecutionContext, shift_ref: str) -> Any | None:
    cleaned = shift_ref.strip()
    if not cleaned or context.tenant_id is None:
        return None
    return repository.get_shift(context.tenant_id, cleaned)


def _resolve_assignment(repository: AssistantPlanningRepository, context: AssistantToolExecutionContext, assignment_ref: str) -> Any | None:
    cleaned = assignment_ref.strip()
    if not cleaned or context.tenant_id is None:
        return None
    return repository.get_assignment(context.tenant_id, cleaned)


def _clean_ref(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _planning_record(shift: Any) -> Any | None:
    return getattr(getattr(shift, "shift_plan", None), "planning_record", None)


def _planning_record_ref(shift: Any) -> str | None:
    record = _planning_record(shift)
    return getattr(record, "id", None)


def _customer_ref(shift: Any) -> str | None:
    record = _planning_record(shift)
    order = getattr(record, "order", None)
    return getattr(order, "customer_id", None)


def _shift_status(shift: Any) -> str:
    return _resource_status(shift) or "unknown"


def _resource_status(resource: Any | None) -> str | None:
    if resource is None:
        return None
    if getattr(resource, "archived_at", None) is not None:
        return "archived"
    return getattr(resource, "status", None) or "unknown"


def _normalized_shift_release_state(shift: Any) -> str:
    if bool(getattr(shift, "customer_visible_flag", False)):
        return "customer_visible"
    if bool(getattr(shift, "subcontractor_visible_flag", False)):
        return "subcontractor_visible"
    state = getattr(shift, "release_state", None)
    if state == "released":
        return "released"
    if state == "draft":
        return "draft"
    if state in {"release_ready"}:
        return "below_released"
    return "unknown"


def _normalized_parent_release_state(resource: Any | None) -> str | None:
    if resource is None:
        return None
    state = getattr(resource, "release_state", None)
    if state == "released":
        return "released"
    if state == "draft":
        return "draft"
    if state in {"release_ready"}:
        return "below_released"
    return "unknown"


def _normalized_assignment_status(assignment: Any) -> str:
    if getattr(assignment, "archived_at", None) is not None:
        return "archived"
    status_code = getattr(assignment, "assignment_status_code", None)
    if status_code == "removed":
        return "cancelled"
    if status_code == "offered":
        return "offered"
    if status_code == "confirmed":
        return "confirmed"
    if status_code == "assigned":
        return "active"
    return "unknown"


def _normalized_assignment_source(assignment: Any) -> str | None:
    source_code = getattr(assignment, "assignment_source_code", None)
    if source_code == "manual":
        return "manual"
    if source_code == "dispatcher":
        return "staffing_board"
    if source_code in {"subcontractor_release", "portal_allocation"}:
        return "subcontractor_portal"
    if source_code is None:
        return None
    return "unknown"


def _assignment_actor_type(assignment: Any) -> str:
    if getattr(assignment, "employee_id", None):
        return "employee"
    if getattr(assignment, "subcontractor_worker_id", None):
        return "subcontractor_worker"
    return "unknown"


def _assignment_visible_candidate(assignment: Any, shift: Any | None) -> bool:
    if _assignment_actor_type(assignment) != "employee":
        return False
    if _normalized_assignment_status(assignment) not in {"active", "offered", "confirmed"}:
        return False
    return bool(shift is not None and _is_shift_candidate_for_employee_app(shift))


def _is_shift_candidate_for_employee_app(shift: Any) -> bool:
    return getattr(shift, "release_state", None) == "released" and not bool(getattr(shift, "stealth_mode_flag", False))


def _normalized_target_audience(value: str | None) -> str:
    cleaned = (value or "internal").strip()
    if cleaned in {"employee_app", "customer_portal", "subcontractor_portal", "internal"}:
        return cleaned
    return "internal"


def _visibility_summary(shift: Any, audience: str) -> tuple[bool, str, list[AssistantPlanningBlockingReasonRead]]:
    blockers: list[AssistantPlanningBlockingReasonRead] = []
    if bool(getattr(shift, "stealth_mode_flag", False)):
        blockers.append(
            AssistantPlanningBlockingReasonRead(
                code="stealth_mode",
                severity="blocking",
                message="Shift is hidden by stealth mode.",
            )
        )
    if getattr(shift, "release_state", None) != "released":
        blockers.append(
            AssistantPlanningBlockingReasonRead(
                code="shift_not_released",
                severity="blocking",
                message="Shift is not released.",
            )
        )
    if audience == "customer_portal" and not bool(getattr(shift, "customer_visible_flag", False)):
        blockers.append(
            AssistantPlanningBlockingReasonRead(
                code="visibility_flag_disabled",
                severity="blocking",
                message="Customer visibility flag is disabled.",
            )
        )
    if audience == "subcontractor_portal" and not bool(getattr(shift, "subcontractor_visible_flag", False)):
        blockers.append(
            AssistantPlanningBlockingReasonRead(
                code="visibility_flag_disabled",
                severity="blocking",
                message="Subcontractor visibility flag is disabled.",
            )
        )
    visible = not blockers
    if visible:
        return True, "visible", blockers
    return False, "not_visible", blockers


def _normalized_validation_code(rule_code: str) -> str:
    return {
        "qualification_match": "qualification_mismatch",
        "function_match": "function_mismatch",
        "certificate_validity": "certificate_expired",
        "mandatory_documents": "mandatory_document_missing",
        "customer_block": "customer_block",
        "double_booking": "double_booking",
        "rest_period": "rest_period",
        "max_hours": "max_hours",
        "minimum_staffing": "minimum_staffing",
        "assignment_missing": "unknown",
    }.get(rule_code, "unknown")


def _normalized_severity(severity: str) -> str:
    if severity == "block":
        return "blocking"
    if severity in {"warn", "warning"}:
        return "warning"
    return "info"


def _validation_status(severity: str, override_present: bool) -> str:
    if override_present:
        return "overridden"
    if severity == "block":
        return "failed"
    if severity in {"warn", "warning"}:
        return "warning"
    return "passed"


def _safe_validation_summary(issue: Any) -> str:
    rule_code = getattr(issue, "rule_code", "unknown")
    return {
        "qualification_match": "Required qualification match failed.",
        "function_match": "Required function match failed.",
        "certificate_validity": "Required certificate is missing or expired.",
        "mandatory_documents": "Mandatory proof document is missing.",
        "customer_block": "Customer-side employee block is active.",
        "double_booking": "Overlapping assignment detected.",
        "rest_period": "Planned rest period is below policy.",
        "max_hours": "Planned working hours exceed policy.",
        "minimum_staffing": "Minimum staffing coverage is not met.",
        "assignment_missing": "Assignment could not be resolved.",
    }.get(rule_code, "Planning validation produced a safe diagnostic finding.")

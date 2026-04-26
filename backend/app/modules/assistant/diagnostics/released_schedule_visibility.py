"""Read-only released schedule visibility diagnostics for employee self-service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Protocol

from app.modules.assistant.policy import ASSISTANT_DIAGNOSTICS_READ
from app.modules.assistant.schemas import (
    AssistantConfidence,
    AssistantFieldBlockingReasonRead,
    AssistantFieldCheckedRuleRead,
    AssistantFieldReleasedScheduleVisibilityItemRead,
    AssistantFieldReleasedScheduleVisibilityRead,
    AssistantFieldScheduleWindowRead,
    AssistantFieldVisibilityMatchRead,
    AssistantMissingPermission,
)
from app.modules.assistant.tools.employee_tools import (
    EMPLOYEE_READ_PERMISSION,
    EMPLOYEE_SELF_SERVICE_PERMISSION,
    EMPLOYEE_WRITE_PERMISSION,
    _build_mobile_access_summary,
    _employee_status,
    _is_employee_active,
)
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.schemas import ShiftListFilter, StaffingFilter


PLANNING_SHIFT_READ_PERMISSION = "planning.shift.read"
PLANNING_STAFFING_READ_PERMISSION = "planning.staffing.read"
DENIED_PORTAL_ROLES = {"customer_user", "subcontractor_user"}


class ReleasedScheduleVisibilityRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Any | None: ...
    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None): ...  # noqa: ANN001
    def get_user_account(self, tenant_id: str, user_id: str) -> Any | None: ...
    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]: ...
    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> Any | None: ...
    def get_shift(self, tenant_id: str, row_id: str) -> Any | None: ...
    def get_assignment(self, tenant_id: str, row_id: str) -> Any | None: ...
    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[Any]: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Any]: ...
    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Any]: ...


@dataclass(frozen=True, slots=True)
class ReleasedScheduleVisibilityRepositoryAdapter:
    planning_repository: Any
    employee_repository: Any

    def get_employee(self, tenant_id: str, employee_id: str) -> Any | None:
        return self.employee_repository.get_employee(tenant_id, employee_id)

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None):
        return self.employee_repository.find_employee_by_user_id(tenant_id, user_id, exclude_id=exclude_id)

    def get_user_account(self, tenant_id: str, user_id: str) -> Any | None:
        return self.employee_repository.get_user_account(tenant_id, user_id)

    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]:
        return self.employee_repository.list_permission_keys_for_user(user_id, at_time=at_time)

    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> Any | None:
        return self.employee_repository.find_role_assignment(tenant_id, user_id, role_key)

    def get_shift(self, tenant_id: str, row_id: str) -> Any | None:
        return self.planning_repository.get_shift(tenant_id, row_id)

    def get_assignment(self, tenant_id: str, row_id: str) -> Any | None:
        return self.planning_repository.get_assignment(tenant_id, row_id)

    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[Any]:
        return self.planning_repository.list_assignments(tenant_id, filters)

    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Any]:
        return self.planning_repository.list_assignments_in_shift(tenant_id, shift_id)

    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Any]:
        return self.planning_repository.list_shifts(tenant_id, filters)


@dataclass(frozen=True, slots=True)
class ReleasedScheduleVisibilityDiagnostics:
    repository: ReleasedScheduleVisibilityRepository
    released_schedule_service: ReleasedScheduleService

    def inspect(
        self,
        *,
        actor: RequestAuthorizationContext,
        employee_ref: str | None,
        assignment_ref: str | None,
        shift_ref: str | None,
        date_value: date | None,
        date_from: date | None,
        date_to: date | None,
        target_channel: str | None,
    ) -> AssistantFieldReleasedScheduleVisibilityRead:
        target = _normalize_target_channel(target_channel)
        if actor.tenant_id is None:
            return self._unknown_result(target_channel=target, missing_permissions=[])

        actor_kind = _actor_kind(actor)
        if actor_kind == "self_service":
            employee = self.repository.find_employee_by_user_id(actor.tenant_id, actor.user_id)
            if employee is None:
                return self._not_found_result()
            effective_employee_ref = employee.id
        else:
            effective_employee_ref = _clean_ref(employee_ref)

        if assignment_ref is None and shift_ref is None and (effective_employee_ref is None or (date_value is None and date_from is None and date_to is None)):
            return self._not_found_result()

        planning_permissions = actor_kind == "self_service" or _planning_permissions(actor)
        employee_read_allowed = EMPLOYEE_READ_PERMISSION in actor.permission_keys or EMPLOYEE_WRITE_PERMISSION in actor.permission_keys
        employee_mobile_access_allowed = EMPLOYEE_WRITE_PERMISSION in actor.permission_keys or actor_kind == "self_service"

        missing_permissions: list[AssistantMissingPermission] = []
        if actor_kind == "internal" and not planning_permissions:
            missing_permissions.append(
                AssistantMissingPermission(
                    permission=PLANNING_STAFFING_READ_PERMISSION,
                    reason="Planning staffing read permission is required to inspect released schedule visibility.",
                )
            )

        employee = None
        if effective_employee_ref is not None and (employee_read_allowed or actor_kind == "self_service"):
            employee = self.repository.get_employee(actor.tenant_id, effective_employee_ref)
            if actor_kind == "self_service" and (employee is None or employee.user_id != actor.user_id):
                employee = self.repository.find_employee_by_user_id(actor.tenant_id, actor.user_id)
        elif effective_employee_ref is not None and actor_kind == "internal":
            missing_permissions.append(
                AssistantMissingPermission(
                    permission=EMPLOYEE_READ_PERMISSION,
                    reason="Operational employee read permission is required to inspect another employee.",
                )
            )

        if actor_kind == "self_service" and employee is None:
            employee = self.repository.find_employee_by_user_id(actor.tenant_id, actor.user_id)

        if actor_kind == "internal" and assignment_ref is not None and not planning_permissions:
            return self._unknown_result(target_channel=target, missing_permissions=missing_permissions)

        candidate_assignments = self._resolve_candidate_assignments(
            tenant_id=actor.tenant_id,
            assignment_ref=_clean_ref(assignment_ref),
            shift_ref=_clean_ref(shift_ref),
            employee=employee,
            date_value=date_value,
            date_from=date_from,
            date_to=date_to,
            planning_allowed=planning_permissions,
        )
        if actor_kind == "self_service" and employee is not None:
            candidate_assignments = [
                row
                for row in candidate_assignments
                if getattr(row, "employee_id", None) == employee.id
            ]
        matches = [_match_item(employee, row) for row in candidate_assignments]

        if candidate_assignments and len(candidate_assignments) > 1 and _clean_ref(assignment_ref) is None:
            first = candidate_assignments[0]
            shift = self.repository.get_shift(actor.tenant_id, first.shift_id)
            return AssistantFieldReleasedScheduleVisibilityRead(
                found=True,
                visibility=AssistantFieldReleasedScheduleVisibilityItemRead(
                    target_channel=target,
                    employee_ref=getattr(employee, "id", None),
                    assignment_ref=None,
                    shift_ref=_clean_ref(shift_ref) or getattr(shift, "id", None),
                    visible=False,
                    visibility_state="ambiguous",
                    confidence=AssistantConfidence.LOW,
                    schedule_window=AssistantFieldScheduleWindowRead(
                        starts_at=getattr(shift, "starts_at", None),
                        ends_at=getattr(shift, "ends_at", None),
                    ),
                    checked_rules=[],
                    blocking_reasons=[
                        AssistantFieldBlockingReasonRead(
                            code="ambiguous_assignment",
                            severity="warning",
                            message="Multiple assignments match the current employee/date filters.",
                        )
                    ],
                    missing_permissions=missing_permissions,
                ),
                matches=matches[:10],
                redactions=["hr_private_profile", "credential_secrets", "planning_notes"],
            )

        assignment = candidate_assignments[0] if candidate_assignments else None
        shift = self.repository.get_shift(actor.tenant_id, assignment.shift_id) if assignment is not None else self.repository.get_shift(actor.tenant_id, _clean_ref(shift_ref) or "")
        if assignment is None and shift is None:
            return self._not_found_result(matches=matches)

        if employee is None and assignment is not None and getattr(assignment, "employee_id", None) and employee_read_allowed:
            employee = self.repository.get_employee(actor.tenant_id, assignment.employee_id)

        checked_rules: list[AssistantFieldCheckedRuleRead] = []
        blocking_reasons: list[AssistantFieldBlockingReasonRead] = []

        if employee is not None:
            employee_active = _is_employee_active(employee)
            checked_rules.append(
                _checked_rule(
                    "employee_active",
                    "passed" if employee_active else "failed",
                    "blocking",
                    "Employee is active." if employee_active else "Employee is inactive or archived.",
                )
            )
            if not employee_active:
                blocking_reasons.append(_blocking("employee_not_active", "blocking", "Employee is inactive or archived."))
        elif effective_employee_ref is not None:
            checked_rules.append(_checked_rule("employee_active", "unknown", "warning", "Employee record could not be inspected."))

        if employee_mobile_access_allowed and employee is not None:
            access = _build_mobile_access_summary(self.repository, employee)
            linked_user_ok = access.has_linked_user_account
            linked_user_active = access.linked_user_status == "active"
            self_service_enabled = access.self_service_enabled
            checked_rules.extend(
                [
                    _checked_rule(
                        "linked_user_active",
                        "passed" if linked_user_ok and linked_user_active else "failed",
                        "blocking",
                        "Linked user account is active." if linked_user_ok and linked_user_active else "Linked user account is missing or inactive.",
                    ),
                    _checked_rule(
                        "self_service_enabled",
                        "passed" if self_service_enabled else "failed",
                        "blocking",
                        "Employee self-service access is enabled." if self_service_enabled else "Employee self-service access is disabled.",
                    ),
                ]
            )
            if not access.has_linked_user_account:
                blocking_reasons.append(_blocking("missing_access_link", "blocking", "Employee has no linked self-service user account."))
            elif access.linked_user_status != "active":
                blocking_reasons.append(_blocking("inactive_linked_user", "blocking", "Linked self-service user account is inactive."))
            if not access.self_service_enabled:
                blocking_reasons.append(_blocking("self_service_disabled", "blocking", "Employee self-service access is disabled."))
        elif employee is not None:
            missing_permissions.append(
                AssistantMissingPermission(
                    permission=EMPLOYEE_WRITE_PERMISSION,
                    reason="Employee access-link diagnostics require employee write permission in the current repository.",
                )
            )
            checked_rules.extend(
                [
                    _checked_rule("linked_user_active", "unknown", "warning", "Linked self-service user state could not be inspected."),
                    _checked_rule("self_service_enabled", "unknown", "warning", "Employee self-service enablement could not be inspected."),
                ]
            )

        if assignment is not None:
            assignment_employee = getattr(assignment, "employee_id", None)
            is_employee_assignment = bool(assignment_employee) and getattr(assignment, "subcontractor_worker_id", None) is None
            checked_rules.append(
                _checked_rule(
                    "assignment_active",
                    "passed" if _assignment_status_allows_visibility(assignment) else "failed",
                    "blocking",
                    "Assignment status allows schedule visibility." if _assignment_status_allows_visibility(assignment) else "Assignment status does not allow schedule visibility.",
                )
            )
            if not is_employee_assignment:
                blocking_reasons.append(_blocking("unknown", "blocking", "Assignment does not target an internal employee."))
            elif employee is not None and assignment_employee != employee.id:
                blocking_reasons.append(_blocking("unknown", "blocking", "Assignment does not belong to the requested employee."))
            if _assignment_blocking_code(assignment) is not None:
                blocking_reasons.append(
                    _blocking(
                        _assignment_blocking_code(assignment) or "unknown",
                        "blocking",
                        "Assignment is cancelled or archived.",
                    )
                )
        elif shift is not None:
            checked_rules.append(_checked_rule("assignment_active", "unknown", "warning", "No concrete assignment could be resolved for the requested input."))

        if shift is not None:
            shift_released = getattr(shift, "release_state", None) == "released"
            shift_plan = getattr(shift, "shift_plan", None)
            planning_record = getattr(shift_plan, "planning_record", None) if shift_plan is not None else None
            checked_rules.extend(
                [
                    _checked_rule("shift_released", "passed" if shift_released else "failed", "blocking", "Shift is released." if shift_released else "Shift is not released."),
                    _checked_rule(
                        "shift_plan_released",
                        "passed" if getattr(shift_plan, "status", None) != "draft" else "failed",
                        "blocking",
                        "Shift plan is active." if getattr(shift_plan, "status", None) != "draft" else "Shift plan is still draft.",
                    ),
                    _checked_rule(
                        "planning_record_released",
                        "passed" if getattr(planning_record, "release_state", None) == "released" else "failed",
                        "blocking",
                        "Planning record is released." if getattr(planning_record, "release_state", None) == "released" else "Planning record is below released.",
                    ),
                    _checked_rule(
                        "employee_visibility_enabled",
                        "passed" if not bool(getattr(shift, "stealth_mode_flag", False)) else "failed",
                        "blocking",
                        "Shift is not suppressed for employee visibility." if not bool(getattr(shift, "stealth_mode_flag", False)) else "Shift is suppressed by stealth mode.",
                    ),
                ]
            )
            if not shift_released:
                blocking_reasons.append(_blocking("shift_not_released", "blocking", "Shift is not released for employee schedules."))
            if getattr(shift_plan, "status", None) == "draft":
                blocking_reasons.append(_blocking("shift_plan_not_released", "blocking", "Shift plan is still in draft state."))
            if getattr(planning_record, "release_state", None) != "released":
                blocking_reasons.append(_blocking("planning_record_not_released", "blocking", "Planning record is below released."))
            if bool(getattr(shift, "stealth_mode_flag", False)):
                blocking_reasons.append(_blocking("stealth_mode", "blocking", "Shift is hidden by stealth mode."))
        else:
            checked_rules.extend(
                [
                    _checked_rule("shift_released", "unknown", "warning", "Shift could not be resolved."),
                    _checked_rule("shift_plan_released", "unknown", "warning", "Shift plan release state could not be resolved."),
                    _checked_rule("planning_record_released", "unknown", "warning", "Planning record release state could not be resolved."),
                    _checked_rule("employee_visibility_enabled", "unknown", "warning", "Employee visibility flags could not be resolved."),
                ]
            )

        query_match = False
        if employee is not None and shift is not None and assignment is not None and employee.user_id:
            released_context = RequestAuthorizationContext(
                session_id=actor.session_id,
                user_id=employee.user_id,
                tenant_id=actor.tenant_id,
                role_keys=frozenset({"employee_user"}),
                permission_keys=frozenset({EMPLOYEE_SELF_SERVICE_PERMISSION}),
                scopes=actor.scopes,
                request_id=actor.request_id,
            )
            try:
                schedules = self.released_schedule_service.list_employee_schedules(released_context)
            except Exception:
                schedules = None
            if schedules is not None:
                query_match = any(item.id == assignment.id and item.shift_id == shift.id for item in schedules.items)
            else:
                query_match = self._fallback_released_schedule_match(
                    tenant_id=actor.tenant_id,
                    employee_id=employee.id,
                    assignment_id=assignment.id,
                    shift_id=shift.id,
                )
            checked_rules.append(
                _checked_rule(
                    "released_schedule_query_matches",
                    "passed" if query_match else "failed",
                    "blocking",
                    "Released schedule query returned the assignment." if query_match else "Released schedule query did not return the assignment.",
                )
            )
            if not query_match:
                blocking_reasons.append(_blocking("schedule_not_in_released_query", "blocking", "Released schedule query does not include the assignment."))
        else:
            checked_rules.append(
                _checked_rule(
                    "released_schedule_query_matches",
                    "unknown",
                    "warning",
                    "Released schedule query could not be verified for the requested employee.",
                )
            )

        blocking_present = any(reason.severity == "blocking" for reason in blocking_reasons)
        unknown_due_to_permissions = bool(missing_permissions) and actor_kind == "internal" and not blocking_present
        if unknown_due_to_permissions:
            state = "unknown"
            visible = False
            confidence = AssistantConfidence.LOW
        elif blocking_present:
            state = "not_visible"
            visible = False
            confidence = AssistantConfidence.HIGH
        elif assignment is None or shift is None or employee is None or not query_match:
            state = "unknown"
            visible = False
            confidence = AssistantConfidence.LOW
        else:
            state = "visible"
            visible = True
            confidence = AssistantConfidence.HIGH

        return AssistantFieldReleasedScheduleVisibilityRead(
            found=assignment is not None or shift is not None or employee is not None,
            visibility=AssistantFieldReleasedScheduleVisibilityItemRead(
                target_channel=target,
                employee_ref=getattr(employee, "id", None),
                assignment_ref=getattr(assignment, "id", None),
                shift_ref=getattr(shift, "id", None),
                visible=visible,
                visibility_state=state,
                confidence=confidence,
                schedule_window=AssistantFieldScheduleWindowRead(
                    starts_at=getattr(shift, "starts_at", None),
                    ends_at=getattr(shift, "ends_at", None),
                ),
                checked_rules=checked_rules,
                blocking_reasons=blocking_reasons,
                missing_permissions=missing_permissions,
            ),
            matches=matches[:10],
            redactions=["hr_private_profile", "credential_secrets", "planning_notes", "raw_document_storage_keys"],
        )

    def _resolve_candidate_assignments(
        self,
        *,
        tenant_id: str,
        assignment_ref: str | None,
        shift_ref: str | None,
        employee: Any | None,
        date_value: date | None,
        date_from: date | None,
        date_to: date | None,
        planning_allowed: bool,
    ) -> list[Any]:
        if not planning_allowed:
            return []
        if assignment_ref is not None:
            assignment = self.repository.get_assignment(tenant_id, assignment_ref)
            return [assignment] if assignment is not None else []
        if shift_ref is not None:
            rows = self.repository.list_assignments_in_shift(tenant_id, shift_ref)
            if employee is not None:
                rows = [row for row in rows if getattr(row, "employee_id", None) == employee.id]
            return rows
        if employee is None:
            return []
        window_start, window_end = _resolve_date_window(date_value=date_value, date_from=date_from, date_to=date_to)
        rows = self.repository.list_assignments(
            tenant_id,
            StaffingFilter(employee_id=employee.id, include_archived=True),
        )
        result: list[Any] = []
        for row in rows:
            shift = self.repository.get_shift(tenant_id, row.shift_id)
            if shift is None:
                continue
            if window_start is not None and shift.starts_at < window_start:
                continue
            if window_end is not None and shift.starts_at >= window_end:
                continue
            result.append(row)
        return result

    def _fallback_released_schedule_match(
        self,
        *,
        tenant_id: str,
        employee_id: str,
        assignment_id: str,
        shift_id: str,
    ) -> bool:
        rows = self.repository.list_shifts(
            tenant_id,
            ShiftListFilter(release_state="released", include_archived=False),
        )
        for shift in rows:
            if shift.id != shift_id:
                continue
            assignments = [
                row
                for row in self.repository.list_assignments_in_shift(tenant_id, shift.id)
                if getattr(row, "employee_id", None) == employee_id
            ]
            return any(row.id == assignment_id for row in assignments)
        return False

    @staticmethod
    def _unknown_result(
        *,
        target_channel: str,
        missing_permissions: list[AssistantMissingPermission],
    ) -> AssistantFieldReleasedScheduleVisibilityRead:
        return AssistantFieldReleasedScheduleVisibilityRead(
            found=False,
            visibility=AssistantFieldReleasedScheduleVisibilityItemRead(
                target_channel=target_channel,
                visible=False,
                visibility_state="unknown",
                confidence=AssistantConfidence.LOW,
                schedule_window=AssistantFieldScheduleWindowRead(),
                checked_rules=[],
                blocking_reasons=[],
                missing_permissions=missing_permissions,
            ),
            matches=[],
            redactions=["hr_private_profile", "credential_secrets", "planning_notes"],
        )

    @staticmethod
    def _not_found_result(
        matches: list[AssistantFieldVisibilityMatchRead] | None = None,
    ) -> AssistantFieldReleasedScheduleVisibilityRead:
        return AssistantFieldReleasedScheduleVisibilityRead(
            found=False,
            visibility=None,
            matches=matches or [],
            redactions=["hr_private_profile", "credential_secrets", "planning_notes"],
        )


def _actor_kind(context: RequestAuthorizationContext) -> str:
    if "employee_user" in context.role_keys and EMPLOYEE_SELF_SERVICE_PERMISSION in context.permission_keys:
        return "self_service"
    if context.role_keys & DENIED_PORTAL_ROLES:
        return "portal_denied"
    return "internal"


def _planning_permissions(context: RequestAuthorizationContext) -> bool:
    return PLANNING_STAFFING_READ_PERMISSION in context.permission_keys or PLANNING_SHIFT_READ_PERMISSION in context.permission_keys


def _clean_ref(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_target_channel(value: str | None) -> str:
    cleaned = (value or "employee_self_service").strip()
    if cleaned in {"employee_self_service", "mobile_app"}:
        return cleaned
    return "employee_self_service"


def _resolve_date_window(
    *,
    date_value: date | None,
    date_from: date | None,
    date_to: date | None,
) -> tuple[datetime | None, datetime | None]:
    if date_value is not None:
        return (
            datetime.combine(date_value, time.min, tzinfo=UTC),
            datetime.combine(date_value + timedelta(days=1), time.min, tzinfo=UTC),
        )
    return (
        datetime.combine(date_from, time.min, tzinfo=UTC) if date_from is not None else None,
        datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC) if date_to is not None else None,
    )


def _assignment_status_allows_visibility(assignment: Any) -> bool:
    return getattr(assignment, "archived_at", None) is None and getattr(assignment, "assignment_status_code", None) in {"assigned", "offered", "confirmed"}


def _assignment_blocking_code(assignment: Any) -> str | None:
    if getattr(assignment, "archived_at", None) is not None:
        return "assignment_archived"
    if getattr(assignment, "assignment_status_code", None) == "removed":
        return "assignment_cancelled"
    return None


def _match_item(employee: Any | None, assignment: Any) -> AssistantFieldVisibilityMatchRead:
    return AssistantFieldVisibilityMatchRead(
        assignment_ref=getattr(assignment, "id", None),
        shift_ref=getattr(assignment, "shift_id", None),
        employee_ref=getattr(employee, "id", None) or getattr(assignment, "employee_id", None),
    )


def _checked_rule(code: str, status: str, severity: str, summary: str) -> AssistantFieldCheckedRuleRead:
    return AssistantFieldCheckedRuleRead(code=code, status=status, severity=severity, summary=summary)


def _blocking(code: str, severity: str, message: str) -> AssistantFieldBlockingReasonRead:
    return AssistantFieldBlockingReasonRead(code=code, severity=severity, message=message)

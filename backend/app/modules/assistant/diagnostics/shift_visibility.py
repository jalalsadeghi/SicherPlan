"""Deterministic shift visibility diagnostics for assistant message flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
import re
from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.policy import ASSISTANT_DIAGNOSTICS_READ
from app.modules.assistant.schemas import (
    AssistantConfidence,
    AssistantMissingPermission,
    AssistantNavigationLink,
    AssistantShiftVisibilityCauseRead,
    AssistantShiftVisibilityDiagnosticAssignmentRead,
    AssistantShiftVisibilityDiagnosticEntityRead,
    AssistantShiftVisibilityDiagnosticInput,
    AssistantShiftVisibilityDiagnosticRead,
    AssistantShiftVisibilityDiagnosticShiftRead,
    AssistantShiftVisibilityFindingRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolRegistry,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.tools.errors import AssistantToolPermissionDeniedError


DIAGNOSTIC_TOOL_NAME = "assistant.diagnose_employee_shift_visibility"
DENIED_PORTAL_ROLES = {"customer_user", "subcontractor_user"}
MONTHS_DE = {
    "januar": 1,
    "februar": 2,
    "maerz": 3,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}
MONTHS_EN = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class AssistantToolRunner(Protocol):
    def execute_tool(
        self,
        *,
        tool_name: str,
        input_data: dict[str, Any],
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult: ...


@dataclass(frozen=True)
class ShiftVisibilityDiagnosticService:
    tool_runner: AssistantToolRunner

    def run(
        self,
        *,
        input_data: AssistantShiftVisibilityDiagnosticInput,
        context: AssistantToolExecutionContext,
    ) -> AssistantShiftVisibilityDiagnosticRead:
        language = _normalize_language(input_data.question_language)
        if context.role_keys & DENIED_PORTAL_ROLES:
            raise AssistantToolPermissionDeniedError("Portal users may not inspect internal employee shift visibility.")
        if "employee_user" not in context.role_keys and ASSISTANT_DIAGNOSTICS_READ not in context.permission_keys:
            raise AssistantToolPermissionDeniedError("Assistant diagnostics access is required for internal shift visibility diagnostics.")

        if not _has_locator(input_data):
            return self._result(
                language=language,
                status="insufficient_input",
                confidence=AssistantConfidence.LOW,
                summary=_summary(language, "insufficient_input", None),
                findings=[
                    _finding(
                        "unknown",
                        "warning",
                        "not_checked",
                        _message(language, "Please provide an employee, assignment, or shift locator with a date context."),
                    )
                ],
                next_steps=[_message(language, "Provide employee name/reference plus assignment, shift, or date information.")],
            )

        employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
            employee_ref=_clean_ref(input_data.employee_ref),
            display_name=None,
            status=None,
            match_state="unknown",
        )
        assignment_state = AssistantShiftVisibilityDiagnosticAssignmentRead(
            assignment_ref=_clean_ref(input_data.assignment_ref),
            status=None,
            match_state="unknown",
        )
        shift_state = AssistantShiftVisibilityDiagnosticShiftRead(
            shift_ref=_clean_ref(input_data.shift_ref),
            starts_at=None,
            ends_at=None,
            status=None,
            release_state=None,
        )
        findings: list[AssistantShiftVisibilityFindingRead] = []
        links: list[AssistantNavigationLink] = []
        missing_permissions: list[AssistantMissingPermission] = []
        next_steps: list[str] = []

        employee_ref = _clean_ref(input_data.employee_ref)
        employee_name = _clean_text(input_data.employee_name)
        if employee_name and employee_ref is None:
            employee_search = self.tool_runner.execute_tool(
                tool_name="employees.search_employee_by_name",
                input_data={"name": employee_name, "limit": 5},
                context=context,
            )
            if employee_search.ok and employee_search.data is not None:
                matches = employee_search.data.get("matches", [])
                if len(matches) == 1:
                    match = matches[0]
                    employee_ref = match.get("employee_ref")
                    employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
                        employee_ref=employee_ref,
                        display_name=match.get("display_name"),
                        status=match.get("status"),
                        match_state="single",
                    )
                elif len(matches) > 1:
                    employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
                        employee_ref=None,
                        display_name=None,
                        status=None,
                        match_state="multiple",
                    )
                    findings.append(
                        _finding(
                            "multiple_employee_matches",
                            "warning",
                            "warning",
                            _message(language, f"Multiple visible employees match {employee_name}."),
                            "employees.search_employee_by_name",
                        )
                    )
                    next_steps.append(_message(language, "Select the exact employee reference before continuing."))
                    return self._result(
                        language=language,
                        status="ambiguous",
                        confidence=AssistantConfidence.MEDIUM,
                        summary=_summary(language, "multiple_employee_matches", employee_name),
                        employee=employee_state,
                        assignment=assignment_state,
                        shift=shift_state,
                        findings=findings,
                        next_steps=next_steps,
                    )
                else:
                    employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
                        employee_ref=None,
                        display_name=None,
                        status=None,
                        match_state="none",
                    )
                    findings.append(
                        _finding(
                            "employee_not_found_or_not_permitted",
                            "blocking",
                            "failed",
                            _message(language, "No visible employee matched the current input."),
                            "employees.search_employee_by_name",
                        )
                    )
                    return self._result(
                        language=language,
                        status="not_found_or_not_permitted",
                        confidence=AssistantConfidence.MEDIUM,
                        summary=_summary(language, "employee_not_found_or_not_permitted", employee_name),
                        employee=employee_state,
                        assignment=assignment_state,
                        shift=shift_state,
                        findings=findings,
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(employee_search))
                if employee_ref is None and input_data.assignment_ref is None:
                    return self._result(
                        language=language,
                        status="insufficient_permissions",
                        confidence=AssistantConfidence.LOW,
                        summary=_summary(language, "insufficient_permissions", employee_name),
                        employee=employee_state,
                        assignment=assignment_state,
                        shift=shift_state,
                        findings=findings,
                        missing_permissions=missing_permissions,
                    )

        if employee_ref is not None:
            employee_profile = self.tool_runner.execute_tool(
                tool_name="employees.get_employee_operational_profile",
                input_data={"employee_ref": employee_ref},
                context=context,
            )
            if employee_profile.ok and employee_profile.data and employee_profile.data.get("found"):
                employee = employee_profile.data["employee"]
                employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
                    employee_ref=employee.get("employee_ref"),
                    display_name=employee.get("display_name"),
                    status=employee.get("status"),
                    match_state="single",
                )
                status = employee.get("status")
                if status in {"inactive", "archived"}:
                    findings.append(
                        _finding(
                            "employee_inactive",
                            "blocking",
                            "failed",
                            _message(language, "Employee is inactive or archived."),
                            "employees.get_employee_operational_profile",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "employee_active",
                            "info",
                            "passed",
                            _message(language, "Employee is active."),
                            "employees.get_employee_operational_profile",
                        )
                    )
            elif employee_profile.ok:
                employee_state = AssistantShiftVisibilityDiagnosticEntityRead(
                    employee_ref=employee_ref,
                    display_name=None,
                    status=None,
                    match_state="not_permitted",
                )
                findings.append(
                    _finding(
                        "employee_not_found_or_not_permitted",
                        "blocking",
                        "failed",
                        _message(language, "The employee could not be inspected in the current scope."),
                        "employees.get_employee_operational_profile",
                    )
                )
                return self._result(
                    language=language,
                    status="not_found_or_not_permitted",
                    confidence=AssistantConfidence.MEDIUM,
                    summary=_summary(language, "employee_not_found_or_not_permitted", employee_name),
                    employee=employee_state,
                    assignment=assignment_state,
                    shift=shift_state,
                    findings=findings,
                    missing_permissions=_dedupe_missing_permissions(missing_permissions),
                )
            else:
                missing_permissions.extend(_tool_missing_permissions(employee_profile))

            mobile_access = self.tool_runner.execute_tool(
                tool_name="employees.get_employee_mobile_access_status",
                input_data={"employee_ref": employee_ref},
                context=context,
            )
            if mobile_access.ok and mobile_access.data and mobile_access.data.get("found"):
                access = mobile_access.data["mobile_access"]
                if not access.get("has_linked_user_account", False):
                    findings.append(
                        _finding(
                            "missing_access_link",
                            "blocking",
                            "failed",
                            _message(language, "Employee has no linked self-service user account."),
                            "employees.get_employee_mobile_access_status",
                        )
                    )
                elif access.get("linked_user_status") != "active":
                    findings.append(
                        _finding(
                            "inactive_linked_user",
                            "blocking",
                            "failed",
                            _message(language, "Linked self-service user account is inactive."),
                            "employees.get_employee_mobile_access_status",
                        )
                    )
                elif not access.get("self_service_enabled", False):
                    findings.append(
                        _finding(
                            "missing_access_link",
                            "blocking",
                            "failed",
                            _message(language, "Employee self-service access is disabled."),
                            "employees.get_employee_mobile_access_status",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "mobile_access_ready",
                            "info",
                            "passed",
                            _message(language, "Employee self-service/mobile access is ready."),
                            "employees.get_employee_mobile_access_status",
                        )
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(mobile_access))
                findings.append(
                    _finding(
                        "permission_missing",
                        "warning",
                        "not_checked",
                        _message(language, "Mobile access status could not be verified with the current permissions."),
                        "employees.get_employee_mobile_access_status",
                    )
                )

        assignment_ref = _clean_ref(input_data.assignment_ref)
        shift_ref = _clean_ref(input_data.shift_ref)
        assignment_search_input = _assignment_search_input(
            employee_ref=employee_ref,
            shift_ref=shift_ref,
            date_value=input_data.date,
            date_from=input_data.date_from,
            date_to=input_data.date_to,
        )
        if assignment_ref is None and assignment_search_input is not None:
            assignment_search = self.tool_runner.execute_tool(
                tool_name="planning.find_assignments",
                input_data=assignment_search_input,
                context=context,
            )
            if assignment_search.ok and assignment_search.data is not None:
                matches = assignment_search.data.get("matches", [])
                if len(matches) == 1:
                    assignment_ref = matches[0].get("assignment_ref")
                elif len(matches) > 1:
                    assignment_state = AssistantShiftVisibilityDiagnosticAssignmentRead(
                        assignment_ref=None,
                        status=None,
                        match_state="multiple",
                    )
                    findings.append(
                        _finding(
                            "assignment_not_found",
                            "warning",
                            "warning",
                            _message(language, "Multiple assignments match the current employee and date filters."),
                            "planning.find_assignments",
                        )
                    )
                    next_steps.append(_message(language, "Provide the exact assignment or shift reference."))
                    return self._result(
                        language=language,
                        status="ambiguous",
                        confidence=AssistantConfidence.MEDIUM,
                        summary=_summary(language, "multiple_assignment_matches", employee_state.display_name or employee_name),
                        employee=employee_state,
                        assignment=assignment_state,
                        shift=shift_state,
                        findings=findings,
                        missing_permissions=_dedupe_missing_permissions(missing_permissions),
                        next_steps=next_steps,
                    )
                else:
                    findings.append(
                        _finding(
                            "assignment_not_found",
                            "blocking",
                            "failed",
                            _message(language, "No matching assignment was found in the current scope."),
                            "planning.find_assignments",
                        )
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(assignment_search))
                findings.append(
                    _finding(
                        "permission_missing",
                        "warning",
                        "not_checked",
                        _message(language, "Planning assignment visibility could not be checked with the current permissions."),
                        "planning.find_assignments",
                    )
                )

        assignment_date = input_data.date
        if assignment_ref is not None:
            assignment_inspect = self.tool_runner.execute_tool(
                tool_name="planning.inspect_assignment",
                input_data={"assignment_ref": assignment_ref},
                context=context,
            )
            if assignment_inspect.ok and assignment_inspect.data and assignment_inspect.data.get("found"):
                assignment = assignment_inspect.data["assignment"]
                assignment_state = AssistantShiftVisibilityDiagnosticAssignmentRead(
                    assignment_ref=assignment.get("assignment_ref"),
                    status=assignment.get("assignment_status"),
                    match_state="single",
                )
                shift_ref = shift_ref or assignment.get("shift_ref")
                if assignment.get("assignment_status") in {"archived", "cancelled"}:
                    findings.append(
                        _finding(
                            "assignment_cancelled" if assignment.get("assignment_status") == "cancelled" else "assignment_archived",
                            "blocking",
                            "failed",
                            _message(language, "Assignment is cancelled or archived."),
                            "planning.inspect_assignment",
                        )
                    )
                elif assignment.get("actor_type") != "employee":
                    findings.append(
                        _finding(
                            "assignment_is_subcontractor_worker",
                            "blocking",
                            "failed",
                            _message(language, "Assignment does not target an internal employee."),
                            "planning.inspect_assignment",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "assignment_active",
                            "info",
                            "passed",
                            _message(language, "Assignment exists and is active for employee visibility."),
                            "planning.inspect_assignment",
                        )
                    )
            elif assignment_inspect.ok:
                assignment_state = AssistantShiftVisibilityDiagnosticAssignmentRead(
                    assignment_ref=assignment_ref,
                    status=None,
                    match_state="none",
                )
                findings.append(
                    _finding(
                        "assignment_not_found",
                        "blocking",
                        "failed",
                        _message(language, "Assignment was not found in the current scope."),
                        "planning.inspect_assignment",
                    )
                )
            else:
                missing_permissions.extend(_tool_missing_permissions(assignment_inspect))

        if shift_ref is not None:
            shift_release = self.tool_runner.execute_tool(
                tool_name="planning.inspect_shift_release_state",
                input_data={"shift_ref": shift_ref},
                context=context,
            )
            if shift_release.ok and shift_release.data and shift_release.data.get("found"):
                release = shift_release.data["release_state"]
                shift_state = AssistantShiftVisibilityDiagnosticShiftRead(
                    shift_ref=release.get("shift_ref"),
                    starts_at=shift_state.starts_at,
                    ends_at=shift_state.ends_at,
                    status=release.get("shift_status"),
                    release_state=release.get("shift_release_state"),
                )
                if release.get("shift_release_state") != "released":
                    findings.append(
                        _finding(
                            "shift_not_released",
                            "blocking",
                            "failed",
                            _message(language, "Shift release state is below released."),
                            "planning.inspect_shift_release_state",
                        )
                    )
                if release.get("shift_plan_status") == "draft":
                    findings.append(
                        _finding(
                            "shift_plan_not_released",
                            "blocking",
                            "failed",
                            _message(language, "Shift plan is still in draft state."),
                            "planning.inspect_shift_release_state",
                        )
                    )
                if release.get("planning_record_release_state") not in {None, "released"}:
                    findings.append(
                        _finding(
                            "planning_record_not_released",
                            "blocking",
                            "failed",
                            _message(language, "Planning record release state is below released."),
                            "planning.inspect_shift_release_state",
                        )
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(shift_release))

            shift_visibility = self.tool_runner.execute_tool(
                tool_name="planning.inspect_shift_visibility",
                input_data={"shift_ref": shift_ref, "target_audience": "employee_self_service"},
                context=context,
            )
            if shift_visibility.ok and shift_visibility.data and shift_visibility.data.get("found"):
                visibility = shift_visibility.data["visibility"]
                if visibility.get("stealth_mode_flag"):
                    findings.append(
                        _finding(
                            "stealth_mode",
                            "blocking",
                            "failed",
                            _message(language, "Shift is hidden by stealth mode."),
                            "planning.inspect_shift_visibility",
                        )
                    )
                elif visibility.get("visibility_state") == "not_visible":
                    findings.append(
                        _finding(
                            "visibility_flag_disabled",
                            "blocking",
                            "failed",
                            _message(language, "Employee visibility is disabled for the shift."),
                            "planning.inspect_shift_visibility",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            "visibility_flag_enabled",
                            "info",
                            "passed",
                            _message(language, "Employee visibility flags allow the shift."),
                            "planning.inspect_shift_visibility",
                        )
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(shift_visibility))

        readiness_date = assignment_date
        if readiness_date is None and shift_state.starts_at is not None:
            readiness_date = shift_state.starts_at.date()
        if employee_ref is not None and readiness_date is not None:
            readiness = self.tool_runner.execute_tool(
                tool_name="employees.get_employee_readiness_summary",
                input_data={"employee_ref": employee_ref, "date": readiness_date.isoformat()},
                context=context,
            )
            if readiness.ok and readiness.data and readiness.data.get("found"):
                for permission in readiness.data.get("missing_permissions", []):
                    missing_permissions.append(AssistantMissingPermission.model_validate(permission))
                readiness_payload = readiness.data["readiness"]
                if readiness_payload.get("has_active_absence_on_date"):
                    findings.append(
                        _finding(
                            "approved_absence",
                            "blocking",
                            "failed",
                            _message(language, "Employee has an active approved absence on the requested date."),
                            "employees.get_employee_readiness_summary",
                        )
                    )
                qualification = readiness_payload.get("qualification_summary", {})
                if qualification.get("has_missing_required_qualification"):
                    findings.append(
                        _finding(
                            "qualification_mismatch",
                            "blocking",
                            "failed",
                            _message(language, "A required qualification is missing."),
                            "employees.get_employee_readiness_summary",
                        )
                    )
                if qualification.get("has_expired_qualifications"):
                    findings.append(
                        _finding(
                            "certificate_expired",
                            "warning",
                            "failed",
                            _message(language, "At least one required qualification is expired."),
                            "employees.get_employee_readiness_summary",
                        )
                    )
            else:
                missing_permissions.extend(_tool_missing_permissions(readiness))

        if assignment_ref is not None:
            assignment_validations = self.tool_runner.execute_tool(
                tool_name="planning.inspect_assignment_validations",
                input_data={"assignment_ref": assignment_ref},
                context=context,
            )
            if assignment_validations.ok and assignment_validations.data and assignment_validations.data.get("found"):
                for row in assignment_validations.data.get("validations", []):
                    code = row.get("code")
                    if row.get("status") == "failed":
                        mapped = _map_validation_code(code)
                        findings.append(
                            _finding(
                                mapped,
                                row.get("severity", "warning"),
                                "failed",
                                row.get("summary") or _message(language, "A planning validation is blocking visibility."),
                                "planning.inspect_assignment_validations",
                            )
                        )
            else:
                missing_permissions.extend(_tool_missing_permissions(assignment_validations))

        if shift_ref is not None:
            release_validations = self.tool_runner.execute_tool(
                tool_name="planning.inspect_shift_release_validations",
                input_data={"shift_ref": shift_ref},
                context=context,
            )
            if release_validations.ok and release_validations.data and release_validations.data.get("found"):
                for row in release_validations.data.get("release_validations", []):
                    if row.get("status") == "failed":
                        findings.append(
                            _finding(
                                _map_validation_code(row.get("code")),
                                row.get("severity", "warning"),
                                "failed",
                                row.get("summary") or _message(language, "A release validation is blocking visibility."),
                                "planning.inspect_shift_release_validations",
                            )
                        )
            else:
                missing_permissions.extend(_tool_missing_permissions(release_validations))

        visibility_tool = self.tool_runner.execute_tool(
            tool_name="field.inspect_released_schedule_visibility",
            input_data={
                "employee_ref": employee_ref,
                "assignment_ref": assignment_ref,
                "shift_ref": shift_ref,
                "date": input_data.date.isoformat() if input_data.date else None,
                "date_from": input_data.date_from.isoformat() if input_data.date_from else None,
                "date_to": input_data.date_to.isoformat() if input_data.date_to else None,
            },
            context=context,
        )
        if visibility_tool.ok and visibility_tool.data and visibility_tool.data.get("found"):
            visibility = visibility_tool.data["visibility"]
            shift_state.starts_at = _coerce_datetime(visibility.get("schedule_window", {}).get("starts_at"))
            shift_state.ends_at = _coerce_datetime(visibility.get("schedule_window", {}).get("ends_at"))
            if visibility.get("visibility_state") == "visible":
                findings.append(
                    _finding(
                        "released_schedule_visible",
                        "info",
                        "passed",
                        _message(language, "The released schedule query includes this assignment."),
                        "field.inspect_released_schedule_visibility",
                    )
                )
            elif visibility.get("visibility_state") == "ambiguous":
                findings.append(
                    _finding(
                        "released_schedule_not_visible",
                        "warning",
                        "warning",
                        _message(language, "Multiple schedule candidates matched the current input."),
                        "field.inspect_released_schedule_visibility",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "released_schedule_not_visible",
                        "blocking",
                        "failed",
                        _message(language, "The released schedule query does not currently include this assignment."),
                        "field.inspect_released_schedule_visibility",
                    )
                )
                for row in visibility.get("blocking_reasons", []):
                    findings.append(
                        _finding(
                            row.get("code") or "unknown",
                            row.get("severity") or "warning",
                            "failed",
                            row.get("message") or _message(language, "A released schedule visibility blocker was found."),
                            "field.inspect_released_schedule_visibility",
                        )
                    )
            for permission in visibility.get("missing_permissions", []):
                missing_permissions.append(AssistantMissingPermission.model_validate(permission))
        else:
            missing_permissions.extend(_tool_missing_permissions(visibility_tool))

        cause_codes = {cause.code for cause in _rank_causes(findings)}
        for page_id in _candidate_pages(findings, cause_codes):
            link_result = self.tool_runner.execute_tool(
                tool_name="navigation.build_allowed_link",
                input_data={
                    "page_id": page_id,
                    "entity_context": {
                        "employee_id": employee_ref,
                        "shift_id": shift_ref,
                        "assignment_id": assignment_ref,
                        "date": readiness_date.isoformat() if readiness_date else None,
                    },
                    "reason": _link_reason(language, page_id),
                },
                context=context,
            )
            if link_result.ok and link_result.data and link_result.data.get("allowed") and link_result.data.get("link"):
                links.append(AssistantNavigationLink.model_validate(link_result.data["link"]))

        causes = _rank_causes(findings)
        status, confidence = _final_status(findings, missing_permissions)
        if status == "resolved" and not next_steps:
            next_steps.append(_message(language, "No blocking visibility issue was verified in the current scope."))
        if causes and not next_steps:
            next_steps.extend(_next_steps_for_causes(language, causes))

        return self._result(
            language=language,
            status=status,
            confidence=confidence,
            summary=_summary(language, causes[0].code if causes else status, employee_state.display_name or employee_name),
            employee=employee_state,
            assignment=assignment_state,
            shift=shift_state,
            findings=findings,
            causes=causes,
            missing_permissions=_dedupe_missing_permissions(missing_permissions),
            links=links[:3],
            next_steps=next_steps[:4],
        )

    def _result(
        self,
        *,
        language: str,
        status: str,
        confidence: AssistantConfidence,
        summary: str,
        employee: AssistantShiftVisibilityDiagnosticEntityRead | None = None,
        assignment: AssistantShiftVisibilityDiagnosticAssignmentRead | None = None,
        shift: AssistantShiftVisibilityDiagnosticShiftRead | None = None,
        findings: list[AssistantShiftVisibilityFindingRead] | None = None,
        causes: list[AssistantShiftVisibilityCauseRead] | None = None,
        missing_permissions: list[AssistantMissingPermission] | None = None,
        links: list[AssistantNavigationLink] | None = None,
        next_steps: list[str] | None = None,
    ) -> AssistantShiftVisibilityDiagnosticRead:
        del language
        return AssistantShiftVisibilityDiagnosticRead(
            status=status,
            confidence=confidence,
            summary=summary,
            employee=employee or AssistantShiftVisibilityDiagnosticEntityRead(match_state="unknown"),
            assignment=assignment or AssistantShiftVisibilityDiagnosticAssignmentRead(match_state="unknown"),
            shift=shift or AssistantShiftVisibilityDiagnosticShiftRead(),
            findings=findings or [],
            most_likely_causes=causes or [],
            missing_permissions=missing_permissions or [],
            links=links or [],
            next_steps=next_steps or [],
            redactions=["hr_private_profile", "payroll_sensitive_fields", "credential_secrets", "private_planning_notes"],
        )


class DiagnoseEmployeeShiftVisibilityTool:
    def __init__(self, *, diagnostic_service: ShiftVisibilityDiagnosticService) -> None:
        self.diagnostic_service = diagnostic_service
        self.definition = AssistantToolDefinition(
            name=DIAGNOSTIC_TOOL_NAME,
            description="Diagnose why an employee-assigned shift is not visible in employee self-service or the mobile app.",
            input_schema=AssistantShiftVisibilityDiagnosticInput,
            output_schema=AssistantShiftVisibilityDiagnosticRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.EMPLOYEE_SELF_SERVICE,
            redaction_policy="shift_visibility_diagnostic_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        if context.role_keys & DENIED_PORTAL_ROLES:
            raise AssistantToolPermissionDeniedError("Portal users may not inspect internal employee shift visibility.")
        if "employee_user" in context.role_keys and _clean_ref(getattr(input_data, "employee_ref", None)) is not None:
            payload = AssistantShiftVisibilityDiagnosticRead(
                status="not_found_or_not_permitted",
                confidence=AssistantConfidence.MEDIUM,
                summary=_summary("en", "employee_not_found_or_not_permitted", _clean_text(getattr(input_data, "employee_name", None))),
                employee=AssistantShiftVisibilityDiagnosticEntityRead(
                    employee_ref=None,
                    display_name=None,
                    status=None,
                    match_state="not_permitted",
                ),
                assignment=AssistantShiftVisibilityDiagnosticAssignmentRead(
                    assignment_ref=_clean_ref(getattr(input_data, "assignment_ref", None)),
                    status=None,
                    match_state="unknown",
                ),
                shift=AssistantShiftVisibilityDiagnosticShiftRead(
                    shift_ref=_clean_ref(getattr(input_data, "shift_ref", None)),
                ),
                findings=[
                    _finding(
                        "employee_not_found_or_not_permitted",
                        "blocking",
                        "failed",
                        "Employee self-service users may inspect only their own shift visibility.",
                        self.definition.name,
                    )
                ],
                most_likely_causes=[],
                missing_permissions=[],
                links=[],
                next_steps=[],
                redactions=["hr_private_profile", "payroll_sensitive_fields", "credential_secrets", "private_planning_notes"],
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload, redacted_output=payload)
        if "employee_user" not in context.role_keys and ASSISTANT_DIAGNOSTICS_READ not in context.permission_keys:
            payload = AssistantShiftVisibilityDiagnosticRead(
                status="insufficient_permissions",
                confidence=AssistantConfidence.LOW,
                summary=_summary("en", "insufficient_permissions", _clean_text(getattr(input_data, "employee_name", None))),
                employee=AssistantShiftVisibilityDiagnosticEntityRead(
                    employee_ref=_clean_ref(getattr(input_data, "employee_ref", None)),
                    display_name=_clean_text(getattr(input_data, "employee_name", None)),
                    status=None,
                    match_state="unknown",
                ),
                assignment=AssistantShiftVisibilityDiagnosticAssignmentRead(
                    assignment_ref=_clean_ref(getattr(input_data, "assignment_ref", None)),
                    status=None,
                    match_state="unknown",
                ),
                shift=AssistantShiftVisibilityDiagnosticShiftRead(
                    shift_ref=_clean_ref(getattr(input_data, "shift_ref", None)),
                ),
                findings=[
                    _finding(
                        "permission_missing",
                        "warning",
                        "not_checked",
                        "Assistant diagnostics permission is required for this internal visibility check.",
                        self.definition.name,
                    )
                ],
                most_likely_causes=[],
                missing_permissions=[
                    AssistantMissingPermission(
                        permission=ASSISTANT_DIAGNOSTICS_READ,
                        reason="Assistant diagnostics permission is required for internal shift visibility inspection.",
                    )
                ],
                links=[],
                next_steps=["Request assistant diagnostics access or use a permitted internal role."],
                redactions=["hr_private_profile", "payroll_sensitive_fields", "credential_secrets", "private_planning_notes"],
            ).model_dump(mode="json")
            return AssistantToolResult(
                ok=True,
                tool_name=self.definition.name,
                data=payload,
                redacted_output=payload,
            )
        payload = self.diagnostic_service.run(
            input_data=AssistantShiftVisibilityDiagnosticInput.model_validate(
                input_data.model_dump(mode="json")
            ),
            context=context,
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            redacted_output=payload,
            entity_refs={
                key: payload[section].get(key)
                for section, key in (
                    ("employee", "employee_ref"),
                    ("assignment", "assignment_ref"),
                    ("shift", "shift_ref"),
                )
                if payload.get(section, {}).get(key) is not None
            }
            or None,
        )


SHIFT_VISIBILITY_PATTERNS = [
    re.compile(r"\bmarkus\b", re.IGNORECASE),
    re.compile(r"(schicht|shift|شیفت)", re.IGNORECASE),
    re.compile(r"(app|employee app|mitarbeiter app|self-service|اپ)", re.IGNORECASE),
    re.compile(r"(assign|zugewiesen|assigned|sichtbar|visible|angezeigt|display|نمایش)", re.IGNORECASE),
]


def is_shift_visibility_question(message: str, route_context: dict[str, Any] | None = None) -> bool:
    lowered = message.casefold()
    if "weather" in lowered or "sport" in lowered:
        return False
    score = sum(1 for pattern in SHIFT_VISIBILITY_PATTERNS if pattern.search(message))
    if score >= 3:
        return True
    if route_context and route_context.get("page_id") in {"P-04", "E-01", "ES-01"} and score >= 2:
        return True
    return False


def extract_shift_visibility_input(
    *,
    message: str,
    detected_language: str,
    route_context: dict[str, Any] | None,
) -> AssistantShiftVisibilityDiagnosticInput:
    employee_name = _extract_employee_name(message)
    parsed_date = _extract_date(message)
    assignment_ref = _extract_ref(message, "assignment")
    shift_ref = _extract_ref(message, "shift")
    employee_ref = _extract_ref(message, "employee")
    return AssistantShiftVisibilityDiagnosticInput(
        employee_name=employee_name,
        employee_ref=employee_ref,
        date=parsed_date,
        assignment_ref=assignment_ref,
        shift_ref=shift_ref,
        question_language=detected_language,
        route_context=route_context,
    )


def render_shift_visibility_answer(
    diagnostic: AssistantShiftVisibilityDiagnosticRead,
    *,
    response_language: str,
) -> str:
    subject = diagnostic.employee.display_name or diagnostic.employee.employee_ref or _message(response_language, "the employee")
    intro = {
        "fa": f"من {subject} را در محدوده دسترسی فعلی شما بررسی کردم.",
        "de": f"Ich habe {subject} im Rahmen Ihrer aktuellen Berechtigungen geprueft.",
    }.get(response_language, f"I checked {subject} within your current access scope.")
    if diagnostic.most_likely_causes:
        explanation = diagnostic.most_likely_causes[0].explanation
    else:
        explanation = diagnostic.summary
    if diagnostic.next_steps:
        return f"{intro} {explanation} {diagnostic.next_steps[0]}".strip()
    return f"{intro} {explanation}".strip()


def _has_locator(input_data: AssistantShiftVisibilityDiagnosticInput) -> bool:
    employee_locator = bool(_clean_ref(input_data.employee_ref) or _clean_text(input_data.employee_name))
    date_locator = input_data.date is not None or input_data.date_from is not None or input_data.date_to is not None
    if _clean_ref(input_data.assignment_ref):
        return True
    if _clean_ref(input_data.shift_ref) and employee_locator:
        return True
    return employee_locator and date_locator


def _assignment_search_input(
    *,
    employee_ref: str | None,
    shift_ref: str | None,
    date_value: date_type | None,
    date_from: date_type | None,
    date_to: date_type | None,
) -> dict[str, Any] | None:
    payload: dict[str, Any] = {}
    if employee_ref is not None:
        payload["employee_ref"] = employee_ref
    if shift_ref is not None:
        payload["shift_ref"] = shift_ref
    if date_value is not None:
        payload["date"] = date_value.isoformat()
    if date_from is not None:
        payload["date_from"] = date_from.isoformat()
    if date_to is not None:
        payload["date_to"] = date_to.isoformat()
    return payload or None


def _tool_missing_permissions(result: AssistantToolResult) -> list[AssistantMissingPermission]:
    return [AssistantMissingPermission.model_validate(item) for item in result.missing_permissions]


def _rank_causes(findings: list[AssistantShiftVisibilityFindingRead]) -> list[AssistantShiftVisibilityCauseRead]:
    failed_codes = {row.code for row in findings if row.status == "failed"}
    causes: list[AssistantShiftVisibilityCauseRead] = []
    seen: set[str] = set()
    for finding in findings:
        if finding.status not in {"failed", "warning"}:
            continue
        if finding.code in seen:
            continue
        if finding.code in {"employee_active", "assignment_active", "mobile_access_ready", "visibility_flag_enabled", "released_schedule_visible"}:
            continue
        if finding.code in {"released_schedule_not_visible", "schedule_not_in_released_query"} and failed_codes - {finding.code, "released_schedule_not_visible", "schedule_not_in_released_query"}:
            continue
        seen.add(finding.code)
        causes.append(
            AssistantShiftVisibilityCauseRead(
                code=finding.code,
                severity="blocking" if finding.severity == "blocking" else finding.severity,
                explanation=finding.evidence,
            )
        )
    causes.sort(key=_cause_sort_key)
    return causes


def _cause_sort_key(cause: AssistantShiftVisibilityCauseRead) -> tuple[int, str]:
    severity_rank = {"blocking": 0, "warning": 1, "info": 2}.get(cause.severity, 3)
    return (severity_rank, cause.code)


def _final_status(
    findings: list[AssistantShiftVisibilityFindingRead],
    missing_permissions: list[AssistantMissingPermission],
) -> tuple[str, AssistantConfidence]:
    blocking_failures = [row for row in findings if row.status == "failed" and row.severity == "blocking"]
    warnings = [row for row in findings if row.status in {"failed", "warning"} and row.severity != "blocking"]
    if blocking_failures:
        return "likely_cause_found", AssistantConfidence.HIGH
    if warnings:
        return "unknown", AssistantConfidence.MEDIUM
    if missing_permissions:
        return "insufficient_permissions", AssistantConfidence.LOW
    visible = any(row.code == "released_schedule_visible" and row.status == "passed" for row in findings)
    if visible:
        return "resolved", AssistantConfidence.HIGH
    return "unknown", AssistantConfidence.LOW


def _candidate_pages(
    findings: list[AssistantShiftVisibilityFindingRead],
    cause_codes: set[str],
) -> list[str]:
    pages = ["P-04", "P-03", "E-01"]
    if cause_codes & {"missing_access_link", "inactive_linked_user", "employee_inactive"}:
        pages = ["E-01", "ES-01", "P-04"]
    elif cause_codes & {"shift_not_released", "shift_plan_not_released", "planning_record_not_released"}:
        pages = ["P-03", "P-05", "P-04"]
    elif cause_codes & {"stealth_mode", "visibility_flag_disabled"}:
        pages = ["P-03", "P-05"]
    elif any(row.code in {"approved_absence", "qualification_mismatch", "certificate_expired"} for row in findings):
        pages = ["E-01", "P-04"]
    return pages


def _next_steps_for_causes(
    language: str,
    causes: list[AssistantShiftVisibilityCauseRead],
) -> list[str]:
    steps: list[str] = []
    for cause in causes[:2]:
        if cause.code in {"missing_access_link", "inactive_linked_user"}:
            steps.append(_message(language, "Open the employee workspace and verify the linked self-service account."))
        elif cause.code in {"shift_not_released", "shift_plan_not_released", "planning_record_not_released"}:
            steps.append(_message(language, "Open planning and verify the release state before expecting mobile visibility."))
        elif cause.code in {"stealth_mode", "visibility_flag_disabled"}:
            steps.append(_message(language, "Open shift planning and verify the employee visibility flags."))
        elif cause.code in {"approved_absence", "qualification_mismatch", "certificate_expired", "mandatory_document_missing", "customer_block"}:
            steps.append(_message(language, "Review the employee readiness and validation blockers before rechecking visibility."))
    return steps


def _link_reason(language: str, page_id: str) -> str:
    return {
        "fa": f"برای بررسی علت نمایش نشدن شیفت به صفحه {page_id} بروید.",
        "de": f"Zur Pruefung der Schichtsichtbarkeit zu Seite {page_id} wechseln.",
    }.get(language, f"Open {page_id} to inspect the shift visibility cause.")


def _map_validation_code(code: str | None) -> str:
    mapping = {
        "qualification_mismatch": "qualification_mismatch",
        "qualification_match": "qualification_mismatch",
        "missing_document": "mandatory_document_missing",
        "mandatory_document": "mandatory_document_missing",
        "mandatory_documents": "mandatory_document_missing",
        "certificate_validity": "certificate_expired",
        "customer_employee_block": "customer_block",
        "customer_block": "customer_block",
        "double_booking": "double_booking",
        "minimum_staffing": "minimum_staffing_not_met",
    }
    cleaned = (code or "unknown").strip()
    return mapping.get(cleaned, cleaned or "unknown")


def _dedupe_missing_permissions(items: list[AssistantMissingPermission]) -> list[AssistantMissingPermission]:
    deduped: dict[str, AssistantMissingPermission] = {}
    for item in items:
        deduped[item.permission] = item
    return list(deduped.values())


def _summary(language: str, code: str, subject: str | None) -> str:
    target = subject or _message(language, "the employee")
    mapping = {
        "missing_access_link": _message(language, f"The main blocker for {target} is the missing employee self-service access link."),
        "inactive_linked_user": _message(language, f"The main blocker for {target} is an inactive linked self-service user."),
        "shift_not_released": _message(language, f"The main blocker for {target} is that the shift is not released."),
        "shift_plan_not_released": _message(language, f"The main blocker for {target} is that the shift plan is still draft."),
        "planning_record_not_released": _message(language, f"The main blocker for {target} is that the planning record is below released."),
        "approved_absence": _message(language, f"The main blocker for {target} is an approved absence on the requested date."),
        "qualification_mismatch": _message(language, f"The main blocker for {target} is a qualification blocker."),
        "multiple_employee_matches": _message(language, f"There are multiple visible employee matches for {target}."),
        "employee_not_found_or_not_permitted": _message(language, f"No visible employee match could be confirmed for {target}."),
        "insufficient_permissions": _message(language, f"I could not fully inspect {target} with the current permissions."),
        "resolved": _message(language, f"No verified blocker was found for {target} in the current scope."),
        "insufficient_input": _message(language, "The current request does not contain enough shift visibility locators."),
    }
    return mapping.get(code, _message(language, f"I checked {target}, but the result is still inconclusive in the current scope."))


def _finding(
    code: str,
    severity: str,
    status: str,
    evidence: str,
    source_tool: str | None = None,
) -> AssistantShiftVisibilityFindingRead:
    return AssistantShiftVisibilityFindingRead(
        code=code,
        severity=severity,
        status=status,
        evidence=evidence,
        source_tool=source_tool,
    )


def _normalize_language(value: str | None) -> str:
    cleaned = (value or "").strip().casefold()
    if cleaned.startswith("fa"):
        return "fa"
    if cleaned.startswith("de"):
        return "de"
    return "en"


def _message(language: str, text: str) -> str:
    translations = {
        "Please provide an employee, assignment, or shift locator with a date context.": {
            "fa": "لطفاً یک شناسه کارمند، انتساب یا شیفت همراه با تاریخ ارائه کنید.",
            "de": "Bitte geben Sie einen Mitarbeiter-, Zuordnungs- oder Schichtbezug mit Datumsangabe an.",
        },
        "Provide employee name/reference plus assignment, shift, or date information.": {
            "fa": "نام یا شناسه کارمند را همراه با انتساب، شیفت یا تاریخ ارائه کنید.",
            "de": "Bitte geben Sie Mitarbeitername oder -referenz zusammen mit Zuordnung, Schicht oder Datum an.",
        },
        "No visible employee matched the current input.": {
            "fa": "در محدوده فعلی هیچ کارمند قابل مشاهده‌ای با این ورودی پیدا نشد.",
            "de": "Im aktuellen Sichtbereich wurde kein passender sichtbarer Mitarbeiter gefunden.",
        },
        "The employee could not be inspected in the current scope.": {
            "fa": "بررسی کارمند در محدوده فعلی ممکن نبود.",
            "de": "Der Mitarbeiter konnte im aktuellen Bereich nicht geprueft werden.",
        },
        "Employee is inactive or archived.": {
            "fa": "کارمند غیرفعال یا آرشیوشده است.",
            "de": "Der Mitarbeiter ist inaktiv oder archiviert.",
        },
        "Employee is active.": {
            "fa": "کارمند فعال است.",
            "de": "Der Mitarbeiter ist aktiv.",
        },
        "Employee has no linked self-service user account.": {
            "fa": "برای کارمند حساب کاربری Self-Service لینک‌شده وجود ندارد.",
            "de": "Dem Mitarbeiter ist kein Self-Service-Benutzerkonto zugeordnet.",
        },
        "Linked self-service user account is inactive.": {
            "fa": "حساب کاربری Self-Service لینک‌شده غیرفعال است.",
            "de": "Das verknuepfte Self-Service-Benutzerkonto ist inaktiv.",
        },
        "Employee self-service access is disabled.": {
            "fa": "دسترسی Self-Service کارمند غیرفعال است.",
            "de": "Der Employee-Self-Service-Zugang ist deaktiviert.",
        },
        "Employee self-service/mobile access is ready.": {
            "fa": "دسترسی موبایل و Self-Service کارمند آماده است.",
            "de": "Der Employee-Self-Service-/Mobilzugang ist bereit.",
        },
        "Mobile access status could not be verified with the current permissions.": {
            "fa": "با مجوزهای فعلی امکان بررسی وضعیت دسترسی موبایل وجود نداشت.",
            "de": "Der Mobile-Zugangsstatus konnte mit den aktuellen Berechtigungen nicht geprueft werden.",
        },
        "Multiple assignments match the current employee and date filters.": {
            "fa": "چند انتساب با کارمند و بازه تاریخ فعلی مطابقت دارند.",
            "de": "Mehrere Zuordnungen passen zu den aktuellen Mitarbeiter- und Datumsfiltern.",
        },
        "Provide the exact assignment or shift reference.": {
            "fa": "لطفاً شناسه دقیق انتساب یا شیفت را ارائه کنید.",
            "de": "Bitte geben Sie die genaue Zuordnungs- oder Schichtreferenz an.",
        },
        "No matching assignment was found in the current scope.": {
            "fa": "در محدوده فعلی هیچ انتساب مطابقی پیدا نشد.",
            "de": "Im aktuellen Bereich wurde keine passende Zuordnung gefunden.",
        },
        "Planning assignment visibility could not be checked with the current permissions.": {
            "fa": "با مجوزهای فعلی امکان بررسی انتساب‌های برنامه‌ریزی وجود نداشت.",
            "de": "Die Planungszuordnung konnte mit den aktuellen Berechtigungen nicht geprueft werden.",
        },
        "Assignment is cancelled or archived.": {
            "fa": "انتساب لغوشده یا آرشیوشده است.",
            "de": "Die Zuordnung ist storniert oder archiviert.",
        },
        "Assignment does not target an internal employee.": {
            "fa": "این انتساب به یک کارمند داخلی تعلق ندارد.",
            "de": "Diese Zuordnung betrifft keinen internen Mitarbeiter.",
        },
        "Assignment exists and is active for employee visibility.": {
            "fa": "انتساب وجود دارد و برای نمایش کارمند فعال است.",
            "de": "Die Zuordnung existiert und ist fuer die Mitarbeitersicht aktiv.",
        },
        "Assignment was not found in the current scope.": {
            "fa": "انتساب در محدوده فعلی پیدا نشد.",
            "de": "Die Zuordnung wurde im aktuellen Bereich nicht gefunden.",
        },
        "Shift release state is below released.": {
            "fa": "وضعیت انتشار شیفت پایین‌تر از released است.",
            "de": "Der Freigabestatus der Schicht liegt unter released.",
        },
        "Shift plan is still in draft state.": {
            "fa": "پلن شیفت هنوز در وضعیت draft است.",
            "de": "Der Schichtplan ist noch im Entwurfsstatus.",
        },
        "Planning record release state is below released.": {
            "fa": "وضعیت انتشار رکورد برنامه‌ریزی پایین‌تر از released است.",
            "de": "Der Freigabestatus des Planungsdatensatzes liegt unter released.",
        },
        "Shift is hidden by stealth mode.": {
            "fa": "شیفت به‌دلیل Stealth Mode مخفی شده است.",
            "de": "Die Schicht ist durch den Stealth-Modus verborgen.",
        },
        "Employee visibility is disabled for the shift.": {
            "fa": "نمایش کارمند برای این شیفت غیرفعال است.",
            "de": "Die Mitarbeitersichtbarkeit ist fuer diese Schicht deaktiviert.",
        },
        "Employee visibility flags allow the shift.": {
            "fa": "فلگ‌های نمایش کارمند این شیفت را مجاز می‌کنند.",
            "de": "Die Mitarbeitersichtbarkeitsflags erlauben diese Schicht.",
        },
        "Employee has an active approved absence on the requested date.": {
            "fa": "برای کارمند در تاریخ موردنظر غیبت تاییدشده فعال وجود دارد.",
            "de": "Der Mitarbeiter hat am angefragten Datum eine aktive genehmigte Abwesenheit.",
        },
        "A required qualification is missing.": {
            "fa": "یک صلاحیت الزامی وجود ندارد.",
            "de": "Eine erforderliche Qualifikation fehlt.",
        },
        "At least one required qualification is expired.": {
            "fa": "حداقل یک صلاحیت موردنیاز منقضی شده است.",
            "de": "Mindestens eine erforderliche Qualifikation ist abgelaufen.",
        },
        "The released schedule query includes this assignment.": {
            "fa": "این انتساب در کوئری برنامه منتشرشده دیده می‌شود.",
            "de": "Diese Zuordnung ist in der freigegebenen Terminabfrage enthalten.",
        },
        "Multiple schedule candidates matched the current input.": {
            "fa": "چند گزینه برنامه با ورودی فعلی مطابقت دارند.",
            "de": "Mehrere Termin-Kandidaten passen zur aktuellen Eingabe.",
        },
        "The released schedule query does not currently include this assignment.": {
            "fa": "در حال حاضر این انتساب در کوئری برنامه منتشرشده دیده نمی‌شود.",
            "de": "Diese Zuordnung ist aktuell nicht in der freigegebenen Terminabfrage enthalten.",
        },
        "A released schedule visibility blocker was found.": {
            "fa": "یک مانع برای نمایش برنامه منتشرشده پیدا شد.",
            "de": "Es wurde ein Blocker fuer die Sichtbarkeit im freigegebenen Plan gefunden.",
        },
        "No blocking visibility issue was verified in the current scope.": {
            "fa": "در محدوده فعلی هیچ مانع تاییدشده‌ای برای نمایش پیدا نشد.",
            "de": "Im aktuellen Bereich wurde kein verifizierter Sichtbarkeitsblocker gefunden.",
        },
        "Open the employee workspace and verify the linked self-service account.": {
            "fa": "فضای کار کارمندان را باز کنید و حساب Self-Service لینک‌شده را بررسی کنید.",
            "de": "Oeffnen Sie den Mitarbeiterbereich und pruefen Sie das verknuepfte Self-Service-Konto.",
        },
        "Open planning and verify the release state before expecting mobile visibility.": {
            "fa": "برنامه‌ریزی را باز کنید و قبل از انتظار نمایش در موبایل وضعیت انتشار را بررسی کنید.",
            "de": "Oeffnen Sie die Planung und pruefen Sie vor der Mobile-Sichtbarkeit den Freigabestatus.",
        },
        "Open shift planning and verify the employee visibility flags.": {
            "fa": "برنامه‌ریزی شیفت را باز کنید و فلگ‌های نمایش کارمند را بررسی کنید.",
            "de": "Oeffnen Sie die Schichtplanung und pruefen Sie die Mitarbeitersichtbarkeitsflags.",
        },
        "Review the employee readiness and validation blockers before rechecking visibility.": {
            "fa": "قبل از بررسی مجدد نمایش، آماده‌بودن کارمند و موانع اعتبارسنجی را بررسی کنید.",
            "de": "Pruefen Sie vor der erneuten Sichtbarkeitspruefung die Mitarbeiterbereitschaft und Validierungsblocker.",
        },
        "the employee": {"fa": "این کارمند", "de": "den Mitarbeiter"},
    }
    return translations.get(text, {}).get(language, text)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_ref(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    return cleaned[:120] if cleaned else None


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime) or value is None:
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _extract_ref(message: str, kind: str) -> str | None:
    pattern = re.compile(rf"{kind}[\s:_-]*([A-Za-z0-9-]{{4,120}})", re.IGNORECASE)
    match = pattern.search(message)
    if match:
        return match.group(1)
    return None


def _extract_employee_name(message: str) -> str | None:
    named = re.search(r"\b(?:named|namens)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß-]+)", message)
    if named:
        return named.group(1)
    markus = re.search(r"\b(Markus)\b", message, re.IGNORECASE)
    if markus:
        return markus.group(1)
    return None


def _extract_date(message: str) -> date_type | None:
    german = re.search(r"\b(\d{1,2})\.?\s+([A-Za-zÄÖÜäöüß]+)\s+(\d{4})\b", message)
    if german:
        day = int(german.group(1))
        month_name = german.group(2).casefold()
        month = MONTHS_DE.get(month_name) or MONTHS_EN.get(month_name)
        if month is not None:
            return date_type(int(german.group(3)), month, day)
    english = re.search(r"\b([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\b", message)
    if english:
        month = MONTHS_EN.get(english.group(1).casefold())
        if month is not None:
            return date_type(int(english.group(3)), month, int(english.group(2)))
    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", message)
    if iso:
        return date_type(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
    return None

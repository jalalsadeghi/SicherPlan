"""Read-only assistant tools for safe employee diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.schemas import (
    AssistantEmployeeBlockingReasonRead,
    AssistantEmployeeCredentialSummaryRead,
    AssistantEmployeeMobileAccessRead,
    AssistantEmployeeMobileAccessStatusInput,
    AssistantEmployeeMobileAccessStatusRead,
    AssistantEmployeeOperationalProfileInput,
    AssistantEmployeeOperationalProfileItemRead,
    AssistantEmployeeOperationalProfileRead,
    AssistantEmployeeQualificationSummaryRead,
    AssistantEmployeeReadinessInput,
    AssistantEmployeeReadinessItemRead,
    AssistantEmployeeReadinessRead,
    AssistantEmployeeSearchInput,
    AssistantEmployeeSearchMatchRead,
    AssistantEmployeeSearchRead,
    AssistantMissingPermission,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.employees.models import Employee
from app.modules.employees.ops_service import EmployeeOpsService
from app.modules.employees.schemas import (
    EmployeeAbsenceFilter,
    EmployeeAvailabilityRuleFilter,
    EmployeeCredentialFilter,
    EmployeeFilter,
    EmployeeQualificationFilter,
)
from app.modules.iam.authz import enforce_scope


EMPLOYEE_READ_PERMISSION = "employees.employee.read"
EMPLOYEE_WRITE_PERMISSION = "employees.employee.write"
EMPLOYEE_PRIVATE_READ_PERMISSION = "employees.private.read"
EMPLOYEE_SELF_SERVICE_PERMISSION = "portal.employee.access"
ACTIVE_ABSENCE_STATUSES = {"pending", "approved"}
ACTIVE_CREDENTIAL_STATUSES = {"draft", "issued"}
UNAVAILABLE_RULE_KINDS = {"unavailable"}
AVAILABLE_RULE_KINDS = {"availability", "free_wish"}


class AssistantEmployeeRepository(Protocol):
    def list_employees(self, tenant_id: str, filters: EmployeeFilter | None = None) -> list[Employee]: ...
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> Employee | None: ...
    def get_user_account(self, tenant_id: str, user_id: str) -> Any | None: ...
    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]: ...
    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> Any | None: ...
    def list_employee_qualifications(self, tenant_id: str, filters: EmployeeQualificationFilter | None = None) -> list[Any]: ...
    def list_absences(self, tenant_id: str, filters: EmployeeAbsenceFilter | None = None) -> list[Any]: ...
    def list_availability_rules(self, tenant_id: str, filters: EmployeeAvailabilityRuleFilter | None = None) -> list[Any]: ...
    def list_credentials(self, tenant_id: str, filters: EmployeeCredentialFilter | None = None) -> list[Any]: ...


class SearchEmployeeByNameTool:
    def __init__(self, *, repository: AssistantEmployeeRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="employees.search_employee_by_name",
            description="Find visible employees by name within the current tenant scope.",
            input_schema=AssistantEmployeeSearchInput,
            output_schema=AssistantEmployeeSearchRead,
            required_permissions=["assistant.chat.access", EMPLOYEE_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="employee_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
            max_rows=5,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        enforce_scope(context.auth_context, scope="tenant", tenant_id=context.tenant_id)
        filters = EmployeeFilter(
            search=getattr(input_data, "name", None),
            include_archived=bool(getattr(input_data, "include_archived", False)),
        )
        rows = self.repository.list_employees(context.tenant_id or "", filters)
        needle = (getattr(input_data, "name", None) or "").strip()
        limit = int(getattr(input_data, "limit", 5))

        matches = [
            AssistantEmployeeSearchMatchRead(
                employee_ref=row.id,
                display_name=_display_name(row),
                personnel_no=row.personnel_no,
                status=_employee_status(row),
                is_active=_is_employee_active(row),
                visibility_scope="visible_to_current_user",
                match_confidence=_match_confidence(row, needle),
            )
            for row in rows
        ]
        matches.sort(key=lambda item: _confidence_rank(item.match_confidence))
        payload = AssistantEmployeeSearchRead(
            matches=matches[:limit],
            match_count=len(matches),
            truncated=len(matches) > limit,
            safe_message_key=None if matches else "assistant.employee.not_found_or_not_permitted",
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class GetEmployeeOperationalProfileTool:
    def __init__(self, *, repository: AssistantEmployeeRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="employees.get_employee_operational_profile",
            description="Return a minimal operational employee profile for assistant diagnostics.",
            input_schema=AssistantEmployeeOperationalProfileInput,
            output_schema=AssistantEmployeeOperationalProfileRead,
            required_permissions=["assistant.chat.access", EMPLOYEE_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="employee_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        employee = _resolve_employee(self.repository, context, getattr(input_data, "employee_ref", ""))
        if employee is None:
            payload = AssistantEmployeeOperationalProfileRead(
                found=False,
                employee=None,
                redactions=["hr_private_profile", "payroll_sensitive_fields"],
            ).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        user = self.repository.get_user_account(employee.tenant_id, employee.user_id) if employee.user_id else None
        payload = AssistantEmployeeOperationalProfileRead(
            found=True,
            employee=AssistantEmployeeOperationalProfileItemRead(
                employee_ref=employee.id,
                display_name=_display_name(employee),
                personnel_no=employee.personnel_no,
                status=_employee_status(employee),
                is_active=_is_employee_active(employee),
                default_branch_ref=employee.default_branch_id,
                default_mandate_ref=employee.default_mandate_id,
                has_user_link=bool(employee.user_id and user is not None),
                user_status=_safe_user_status(user),
                operational_notes_available=bool((employee.notes or "").strip()),
            ),
            redactions=["hr_private_profile", "payroll_sensitive_fields"],
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"employee_ref": employee.id},
        )


class GetEmployeeMobileAccessStatusTool:
    def __init__(self, *, repository: AssistantEmployeeRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="employees.get_employee_mobile_access_status",
            description="Return safe status-only employee self-service/mobile access readiness.",
            input_schema=AssistantEmployeeMobileAccessStatusInput,
            output_schema=AssistantEmployeeMobileAccessStatusRead,
            required_permissions=["assistant.chat.access", EMPLOYEE_WRITE_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="employee_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        employee = _resolve_employee(self.repository, context, getattr(input_data, "employee_ref", ""))
        if employee is None:
            payload = AssistantEmployeeMobileAccessStatusRead(found=False, mobile_access=None).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        diagnostics = _build_mobile_access_summary(self.repository, employee)
        payload = AssistantEmployeeMobileAccessStatusRead(
            found=True,
            mobile_access=diagnostics,
            missing_permissions=[],
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"employee_ref": employee.id},
        )


class GetEmployeeReadinessSummaryTool:
    def __init__(self, *, repository: AssistantEmployeeRepository) -> None:
        self.repository = repository
        self.definition = AssistantToolDefinition(
            name="employees.get_employee_readiness_summary",
            description="Return a summary of operational readiness signals for an employee.",
            input_schema=AssistantEmployeeReadinessInput,
            output_schema=AssistantEmployeeReadinessRead,
            required_permissions=["assistant.chat.access", EMPLOYEE_READ_PERMISSION],
            scope_behavior=AssistantToolScopeBehavior.TENANT,
            redaction_policy="employee_operational_safe",
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        employee = _resolve_employee(self.repository, context, getattr(input_data, "employee_ref", ""))
        if employee is None:
            payload = AssistantEmployeeReadinessRead(found=False, readiness=None, missing_permissions=[]).model_dump(mode="json")
            return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

        check_date = _parse_date(getattr(input_data, "date", None))
        include_qualifications = bool(getattr(input_data, "include_qualifications", True))
        include_absences = bool(getattr(input_data, "include_absences", True))
        include_availability = bool(getattr(input_data, "include_availability", True))

        missing_permissions: list[AssistantMissingPermission] = []
        has_active_absence = False
        if include_absences and check_date is not None:
            if EMPLOYEE_PRIVATE_READ_PERMISSION in context.permission_keys:
                has_active_absence = _has_active_absence_on_date(self.repository, employee, check_date)
            else:
                missing_permissions.append(
                    AssistantMissingPermission(
                        permission=EMPLOYEE_PRIVATE_READ_PERMISSION,
                        reason="Absence details require HR-private read permission.",
                    )
                )

        qualification_summary = AssistantEmployeeQualificationSummaryRead(
            has_expired_qualifications=False,
            has_missing_required_qualification=False,
            details_redacted=True,
        )
        if include_qualifications:
            qualification_summary = _build_qualification_summary(self.repository, employee, check_date)

        credential_summary = _build_credential_summary(self.repository, employee, check_date)
        availability_summary = _build_availability_summary(self.repository, employee, check_date, include_availability)

        blocking_reasons: list[AssistantEmployeeBlockingReasonRead] = []
        if has_active_absence:
            blocking_reasons.append(
                AssistantEmployeeBlockingReasonRead(
                    code="active_absence",
                    severity="blocking",
                    message="Employee has an active absence on the requested date.",
                )
            )
        if availability_summary == "unavailable":
            blocking_reasons.append(
                AssistantEmployeeBlockingReasonRead(
                    code="unavailable_on_date",
                    severity="warning",
                    message="Employee is marked unavailable on the requested date.",
                )
            )
        if qualification_summary.has_expired_qualifications:
            blocking_reasons.append(
                AssistantEmployeeBlockingReasonRead(
                    code="expired_qualification",
                    severity="warning",
                    message="One or more employee qualifications are expired.",
                )
            )

        payload = AssistantEmployeeReadinessRead(
            found=True,
            readiness=AssistantEmployeeReadinessItemRead(
                employee_status=_employee_status(employee),
                has_active_absence_on_date=has_active_absence,
                availability_summary=availability_summary,
                qualification_summary=qualification_summary,
                credential_summary=credential_summary,
                blocking_reasons=blocking_reasons,
            ),
            missing_permissions=missing_permissions,
        ).model_dump(mode="json")
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=payload,
            entity_refs={"employee_ref": employee.id},
        )


def _resolve_employee(
    repository: AssistantEmployeeRepository,
    context: AssistantToolExecutionContext,
    employee_ref: str,
) -> Employee | None:
    cleaned = employee_ref.strip()
    if not cleaned or context.tenant_id is None:
        return None
    employee = repository.get_employee(context.tenant_id, cleaned)
    if employee is None:
        return None
    if EMPLOYEE_READ_PERMISSION in context.permission_keys or EMPLOYEE_WRITE_PERMISSION in context.permission_keys:
        enforce_scope(context.auth_context, scope="tenant", tenant_id=context.tenant_id)
        return employee
    if EMPLOYEE_SELF_SERVICE_PERMISSION in context.permission_keys and "employee_user" in context.role_keys:
        return employee if employee.user_id == context.user_id else None
    return None


def _display_name(employee: Employee) -> str:
    preferred = (employee.preferred_name or "").strip()
    if preferred:
        return preferred
    return f"{employee.first_name} {employee.last_name}".strip()


def _employee_status(employee: Employee) -> str:
    if employee.archived_at is not None:
        return "archived"
    return employee.status or "unknown"


def _is_employee_active(employee: Employee) -> bool:
    return employee.archived_at is None and employee.status == "active"


def _match_confidence(employee: Employee, needle: str) -> str:
    value = needle.strip().casefold()
    if not value:
        return "low"
    full_name = f"{employee.first_name} {employee.last_name}".strip().casefold()
    preferred_name = (employee.preferred_name or "").strip().casefold()
    personnel_no = employee.personnel_no.casefold()
    if value in {full_name, preferred_name, personnel_no}:
        return "exact"
    if full_name.startswith(value) or preferred_name.startswith(value) or personnel_no.startswith(value):
        return "high"
    tokens = {token for token in value.split() if token}
    haystack = " ".join([full_name, preferred_name, personnel_no])
    if tokens and all(token in haystack for token in tokens):
        return "medium"
    return "low"


def _confidence_rank(value: str) -> int:
    order = {"exact": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(value, 9)


def _safe_user_status(user: Any | None) -> str | None:
    if user is None:
        return None
    status = getattr(user, "status", None)
    if not isinstance(status, str) or not status.strip():
        return "unknown"
    return status


def _build_mobile_access_summary(
    repository: AssistantEmployeeRepository,
    employee: Employee,
) -> AssistantEmployeeMobileAccessRead:
    now = datetime.now(UTC)
    user = repository.get_user_account(employee.tenant_id, employee.user_id) if employee.user_id else None
    assignment = repository.find_role_assignment(employee.tenant_id, user.id, "employee_user") if user is not None else None
    permission_keys = set(repository.list_permission_keys_for_user(user.id, at_time=now)) if user is not None else set()

    user_exists = user is not None
    user_status_active = bool(user and user.status == "active")
    user_not_archived = bool(user and user.archived_at is None)
    is_password_login_enabled = bool(user and user.is_password_login_enabled)
    has_password_hash = bool(user and (user.password_hash or "").strip())
    employee_linked = bool(employee.user_id and user_exists)
    employee_status_active = employee.status == "active"
    employee_not_archived = employee.archived_at is None
    role_assignment_active = bool(assignment and assignment.status == "active" and assignment.archived_at is None)
    portal_employee_access_granted = EMPLOYEE_SELF_SERVICE_PERMISSION in permission_keys
    can_mobile_login = all(
        (
            user_exists,
            user_status_active,
            user_not_archived,
            is_password_login_enabled,
            has_password_hash,
            employee_linked,
            employee_status_active,
            employee_not_archived,
            role_assignment_active,
            portal_employee_access_granted,
        )
    )

    blocking_reasons: list[AssistantEmployeeBlockingReasonRead] = []
    if not employee_linked:
        blocking_reasons.append(_blocking("missing_access_link", "blocking", "Employee has no linked user account."))
    if user_exists and not user_status_active:
        blocking_reasons.append(_blocking("inactive_user", "blocking", "Linked user account is inactive."))
    if user_exists and not user_not_archived:
        blocking_reasons.append(_blocking("inactive_user", "blocking", "Linked user account is archived."))
    if user_exists and not is_password_login_enabled:
        blocking_reasons.append(_blocking("self_service_disabled", "blocking", "Password login is disabled for the linked user account."))
    if user_exists and not has_password_hash:
        blocking_reasons.append(_blocking("self_service_disabled", "blocking", "Linked user account has no password set."))
    if not employee_status_active or not employee_not_archived:
        blocking_reasons.append(_blocking("inactive_employee", "blocking", "Employee is inactive or archived."))
    if user_exists and not role_assignment_active:
        blocking_reasons.append(_blocking("missing_role_assignment", "blocking", "Employee user role assignment is missing or inactive."))
    if user_exists and not portal_employee_access_granted:
        blocking_reasons.append(_blocking("self_service_disabled", "blocking", "Employee self-service permission is not granted."))

    return AssistantEmployeeMobileAccessRead(
        has_linked_user_account=employee_linked,
        linked_user_status=_safe_user_status(user),
        self_service_enabled=portal_employee_access_granted and is_password_login_enabled,
        mobile_context_available=employee_linked and employee_status_active and employee_not_archived,
        can_receive_released_schedules=can_mobile_login,
        blocking_reasons=blocking_reasons,
    )


def _blocking(code: str, severity: str, message: str) -> AssistantEmployeeBlockingReasonRead:
    return AssistantEmployeeBlockingReasonRead(code=code, severity=severity, message=message)


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        return None


def _has_active_absence_on_date(repository: AssistantEmployeeRepository, employee: Employee, target: date) -> bool:
    rows = repository.list_absences(
        employee.tenant_id,
        EmployeeAbsenceFilter(employee_id=employee.id, include_archived=False),
    )
    for row in rows:
        if row.status not in ACTIVE_ABSENCE_STATUSES:
            continue
        if row.starts_on <= target <= row.ends_on:
            return True
    return False


def _build_qualification_summary(
    repository: AssistantEmployeeRepository,
    employee: Employee,
    target: date | None,
) -> AssistantEmployeeQualificationSummaryRead:
    rows = repository.list_employee_qualifications(
        employee.tenant_id,
        EmployeeQualificationFilter(employee_id=employee.id, include_archived=False, include_expired=True),
    )
    cutoff = target or date.today()
    has_expired = any(row.valid_until is not None and row.valid_until < cutoff for row in rows)
    return AssistantEmployeeQualificationSummaryRead(
        has_expired_qualifications=has_expired,
        has_missing_required_qualification=False,
        details_redacted=True,
    )


def _build_credential_summary(
    repository: AssistantEmployeeRepository,
    employee: Employee,
    target: date | None,
) -> AssistantEmployeeCredentialSummaryRead:
    rows = repository.list_credentials(
        employee.tenant_id,
        EmployeeCredentialFilter(employee_id=employee.id, include_archived=False),
    )
    if target is None:
        active = any(row.status in ACTIVE_CREDENTIAL_STATUSES and (row.archived_at is None) for row in rows)
        expired = any(row.valid_until is not None and row.valid_until < date.today() for row in rows)
    else:
        active = any(
            row.status in ACTIVE_CREDENTIAL_STATUSES
            and row.valid_from <= target
            and (row.valid_until is None or row.valid_until >= target)
            for row in rows
        )
        expired = any(row.valid_until is not None and row.valid_until < target for row in rows)
    return AssistantEmployeeCredentialSummaryRead(
        has_active_credential=active,
        has_expired_credential=expired,
        details_redacted=True,
    )


def _build_availability_summary(
    repository: AssistantEmployeeRepository,
    employee: Employee,
    target: date | None,
    include_availability: bool,
) -> str:
    if not include_availability:
        return "not_checked"
    if target is None:
        return "not_checked"
    target_start = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
    target_end = datetime.combine(target, datetime.max.time(), tzinfo=UTC)
    rows = repository.list_availability_rules(
        employee.tenant_id,
        EmployeeAvailabilityRuleFilter(employee_id=employee.id, include_archived=False),
    )
    overlapping = [row for row in rows if row.starts_at <= target_end and row.ends_at >= target_start and row.status == "active"]
    if any(row.rule_kind in UNAVAILABLE_RULE_KINDS for row in overlapping):
        return "unavailable"
    if any(row.rule_kind in AVAILABLE_RULE_KINDS for row in overlapping):
        return "available"
    return "unknown"

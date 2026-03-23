"""Own-record employee self-service APIs for mobile-ready availability and controlled updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from app.errors import ApiException
from app.modules.core.models import Address
from app.modules.core.schemas import AddressRead
from app.modules.employees.availability_service import EmployeeAvailabilityService
from app.modules.employees.models import Employee, EmployeeAddressHistory
from app.modules.employees.schemas import (
    EmployeeAbsenceFilter,
    EmployeeAbsenceRead,
    EmployeeAddressHistoryRead,
    EmployeeAvailabilityRuleCreate,
    EmployeeAvailabilityRuleFilter,
    EmployeeAvailabilityRuleRead,
    EmployeeAvailabilityRuleUpdate,
    EmployeeEventApplicationCreate,
    EmployeeEventApplicationFilter,
    EmployeeEventApplicationRead,
    EmployeeEventApplicationUpdate,
    EmployeeMobileContextRead,
    EmployeeSelfServiceAddressUpdate,
    EmployeeSelfServiceAvailabilityRuleCreate,
    EmployeeSelfServiceAvailabilityRuleUpdate,
    EmployeeSelfServiceEventApplicationCancel,
    EmployeeSelfServiceEventApplicationCreate,
    EmployeeSelfServiceProfileRead,
    EmployeeSelfServiceProfileUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


ALLOWED_SELF_SERVICE_RULE_KINDS = {"availability", "free_wish"}


class EmployeeSelfServiceRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> Employee | None: ...
    def update_employee(self, row: Employee) -> Employee: ...
    def list_employee_address_history(self, tenant_id: str, employee_id: str) -> list[EmployeeAddressHistory]: ...
    def get_employee_address_history(self, tenant_id: str, employee_id: str, history_id: str) -> EmployeeAddressHistory | None: ...
    def create_address(self, row: Address) -> Address: ...
    def create_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory: ...
    def update_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory: ...


@dataclass(frozen=True, slots=True)
class SelfServiceEmployeeContext:
    employee: Employee


class EmployeeSelfService:
    def __init__(
        self,
        *,
        repository: EmployeeSelfServiceRepository,
        availability_service: EmployeeAvailabilityService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.availability_service = availability_service
        self.audit_service = audit_service

    def get_profile(self, context: RequestAuthorizationContext) -> EmployeeSelfServiceProfileRead:
        employee_context = self._resolve_employee(context)
        home_address = self._current_home_address(employee_context.employee.tenant_id, employee_context.employee.id)
        return EmployeeSelfServiceProfileRead(
            employee_id=employee_context.employee.id,
            tenant_id=employee_context.employee.tenant_id,
            personnel_no=employee_context.employee.personnel_no,
            first_name=employee_context.employee.first_name,
            last_name=employee_context.employee.last_name,
            preferred_name=employee_context.employee.preferred_name,
            work_email=employee_context.employee.work_email,
            mobile_phone=employee_context.employee.mobile_phone,
            active_home_address=AddressRead.model_validate(home_address.address) if home_address and home_address.address else None,
        )

    def get_mobile_context(self, context: RequestAuthorizationContext) -> EmployeeMobileContextRead:
        employee_context = self._resolve_employee(context)
        employee = employee_context.employee
        return EmployeeMobileContextRead(
            tenant_id=employee.tenant_id,
            user_id=context.user_id,
            employee_id=employee.id,
            personnel_no=employee.personnel_no,
            full_name=f"{employee.first_name} {employee.last_name}".strip(),
            preferred_name=employee.preferred_name,
            work_email=employee.work_email,
            mobile_phone=employee.mobile_phone,
            default_branch_id=employee.default_branch_id,
            default_mandate_id=employee.default_mandate_id,
            locale="de",
            timezone="Europe/Berlin",
            app_role="employee",
            role_keys=sorted(context.role_keys),
            has_schedule_access=True,
            has_document_access=True,
            has_notice_access="platform.info.read" in context.permission_keys,
            has_time_capture_access=True,
            has_watchbook_access=True,
            has_patrol_access=True,
        )

    def update_profile(
        self,
        payload: EmployeeSelfServiceProfileUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeSelfServiceProfileRead:
        employee_context = self._resolve_employee(context)
        row = employee_context.employee
        before = self._profile_snapshot(row)
        if payload.preferred_name is not None:
            row.preferred_name = self._normalize_optional(payload.preferred_name)
        if payload.work_email is not None:
            row.work_email = self._normalize_optional(payload.work_email)
        if payload.mobile_phone is not None:
            row.mobile_phone = self._normalize_optional(payload.mobile_phone)
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_employee(row)
        self._record_event(
            context,
            event_type="employees.self_service.profile_updated",
            entity_type="hr.employee",
            entity_id=updated.id,
            tenant_id=updated.tenant_id,
            before_json=before,
            after_json=self._profile_snapshot(updated),
        )
        return self.get_profile(context)

    def update_current_address(
        self,
        payload: EmployeeSelfServiceAddressUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAddressHistoryRead:
        employee_context = self._resolve_employee(context)
        current = self._current_home_address(employee_context.employee.tenant_id, employee_context.employee.id)
        new_address = self.repository.create_address(
            Address(
                street_line_1=payload.address.street_line_1,
                street_line_2=payload.address.street_line_2,
                postal_code=payload.address.postal_code,
                city=payload.address.city,
                state=payload.address.state,
                country_code=payload.address.country_code,
            )
        )
        if current is not None and current.valid_from >= payload.effective_from:
            raise ApiException(
                409,
                "employees.self_service.address.invalid_effective_date",
                "errors.employees.self_service.address.invalid_effective_date",
            )
        if current is not None:
            current.valid_to = payload.effective_from - timedelta(days=1)
            current.updated_by_user_id = context.user_id
            current.version_no += 1
            self.repository.update_address_history(current)
        created = self.repository.create_address_history(
            EmployeeAddressHistory(
                tenant_id=employee_context.employee.tenant_id,
                employee_id=employee_context.employee.id,
                address_id=new_address.id,
                address_type="home",
                valid_from=payload.effective_from,
                valid_to=None,
                is_primary=True,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.self_service.address_updated",
            entity_type="hr.employee_address_history",
            entity_id=created.id,
            tenant_id=created.tenant_id,
            after_json={"employee_id": created.employee_id, "address_id": created.address_id, "valid_from": created.valid_from.isoformat()},
        )
        return EmployeeAddressHistoryRead.model_validate(created)

    def list_availability_rules(self, context: RequestAuthorizationContext) -> list[EmployeeAvailabilityRuleRead]:
        employee_context = self._resolve_employee(context)
        rows = self.availability_service.list_availability_rules(
            employee_context.employee.tenant_id,
            EmployeeAvailabilityRuleFilter(employee_id=employee_context.employee.id),
            self._self_service_authorization_context(context),
        )
        return [row for row in rows if row.rule_kind in ALLOWED_SELF_SERVICE_RULE_KINDS]

    def create_availability_rule(
        self,
        payload: EmployeeSelfServiceAvailabilityRuleCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAvailabilityRuleRead:
        employee_context = self._resolve_employee(context)
        if payload.rule_kind not in ALLOWED_SELF_SERVICE_RULE_KINDS:
            raise ApiException(
                400,
                "employees.self_service.availability_rule.invalid_kind",
                "errors.employees.self_service.availability_rule.invalid_kind",
            )
        return self.availability_service.create_availability_rule(
            employee_context.employee.tenant_id,
            EmployeeAvailabilityRuleCreate(
                tenant_id=employee_context.employee.tenant_id,
                employee_id=employee_context.employee.id,
                rule_kind=payload.rule_kind,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                recurrence_type=payload.recurrence_type,
                weekday_mask=payload.weekday_mask,
                notes=payload.notes,
            ),
            self._self_service_authorization_context(context),
        )

    def update_availability_rule(
        self,
        rule_id: str,
        payload: EmployeeSelfServiceAvailabilityRuleUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAvailabilityRuleRead:
        employee_context = self._resolve_employee(context)
        existing = {
            row.id: row
            for row in self.availability_service.list_availability_rules(
                employee_context.employee.tenant_id,
                EmployeeAvailabilityRuleFilter(employee_id=employee_context.employee.id),
                self._self_service_authorization_context(context),
            )
            if row.rule_kind in ALLOWED_SELF_SERVICE_RULE_KINDS
        }.get(rule_id)
        if existing is None:
            raise ApiException(
                404,
                "employees.self_service.availability_rule.not_found",
                "errors.employees.self_service.availability_rule.not_found",
            )
        return self.availability_service.update_availability_rule(
            employee_context.employee.tenant_id,
            rule_id,
            EmployeeAvailabilityRuleUpdate(
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                recurrence_type=payload.recurrence_type,
                weekday_mask=payload.weekday_mask,
                notes=payload.notes,
                status=payload.status,
                version_no=payload.version_no,
            ),
            self._self_service_authorization_context(context),
        )

    def list_absences(self, context: RequestAuthorizationContext) -> list[EmployeeAbsenceRead]:
        employee_context = self._resolve_employee(context)
        return self.availability_service.list_absences(
            employee_context.employee.tenant_id,
            EmployeeAbsenceFilter(employee_id=employee_context.employee.id),
            self._self_service_private_context(context),
        )

    def list_event_applications(self, context: RequestAuthorizationContext) -> list[EmployeeEventApplicationRead]:
        employee_context = self._resolve_employee(context)
        return self.availability_service.list_event_applications(
            employee_context.employee.tenant_id,
            EmployeeEventApplicationFilter(employee_id=employee_context.employee.id),
            self._self_service_authorization_context(context),
        )

    def create_event_application(
        self,
        payload: EmployeeSelfServiceEventApplicationCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeEventApplicationRead:
        employee_context = self._resolve_employee(context)
        return self.availability_service.create_event_application(
            employee_context.employee.tenant_id,
            EmployeeEventApplicationCreate(
                tenant_id=employee_context.employee.tenant_id,
                employee_id=employee_context.employee.id,
                planning_record_id=payload.planning_record_id,
                note=payload.note,
            ),
            self._self_service_authorization_context(context),
        )

    def cancel_event_application(
        self,
        application_id: str,
        payload: EmployeeSelfServiceEventApplicationCancel,
        context: RequestAuthorizationContext,
    ) -> EmployeeEventApplicationRead:
        employee_context = self._resolve_employee(context)
        owned = {
            row.id: row
            for row in self.availability_service.list_event_applications(
                employee_context.employee.tenant_id,
                EmployeeEventApplicationFilter(employee_id=employee_context.employee.id),
                self._self_service_authorization_context(context),
            )
        }.get(application_id)
        if owned is None:
            raise ApiException(
                404,
                "employees.self_service.event_application.not_found",
                "errors.employees.self_service.event_application.not_found",
            )
        return self.availability_service.update_event_application(
            employee_context.employee.tenant_id,
            application_id,
            EmployeeEventApplicationUpdate(
                status="withdrawn",
                decision_note=payload.decision_note,
                version_no=payload.version_no,
            ),
            self._self_service_authorization_context(context),
        )

    def _resolve_employee(self, context: RequestAuthorizationContext) -> SelfServiceEmployeeContext:
        self._require_portal_employee_access(context)
        employee = self.repository.find_employee_by_user_id(context.tenant_id, context.user_id)
        if employee is None:
            raise ApiException(
                404,
                "employees.self_service.employee_not_found",
                "errors.employees.self_service.employee_not_found",
            )
        if employee.archived_at is not None or employee.status != "active":
            raise ApiException(
                409,
                "employees.self_service.employee_inactive",
                "errors.employees.self_service.employee_inactive",
            )
        return SelfServiceEmployeeContext(employee=employee)

    def _require_portal_employee_access(self, context: RequestAuthorizationContext) -> None:
        if "employee_user" not in context.role_keys or "portal.employee.access" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "portal.employee.access"},
            )

    @staticmethod
    def _self_service_authorization_context(context: RequestAuthorizationContext) -> RequestAuthorizationContext:
        return RequestAuthorizationContext(
            session_id=context.session_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            role_keys=context.role_keys,
            permission_keys=context.permission_keys | frozenset({"employees.employee.read", "employees.employee.write"}),
            scopes=context.scopes,
            request_id=context.request_id,
        )

    @staticmethod
    def _self_service_private_context(context: RequestAuthorizationContext) -> RequestAuthorizationContext:
        return RequestAuthorizationContext(
            session_id=context.session_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            role_keys=context.role_keys,
            permission_keys=context.permission_keys | frozenset({"employees.private.read"}),
            scopes=context.scopes,
            request_id=context.request_id,
        )

    def _current_home_address(self, tenant_id: str, employee_id: str) -> EmployeeAddressHistory | None:
        rows = [
            row
            for row in self.repository.list_employee_address_history(tenant_id, employee_id)
            if row.address_type == "home" and row.archived_at is None and row.valid_to is None
        ]
        rows.sort(key=lambda row: row.valid_from, reverse=True)
        return rows[0] if rows else None

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @staticmethod
    def _profile_snapshot(row: Employee) -> dict[str, object]:
        return {
            "preferred_name": row.preferred_name,
            "work_email": row.work_email,
            "mobile_phone": row.mobile_phone,
            "version_no": row.version_no,
        }

    def _record_event(
        self,
        context: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=context.user_id,
                session_id=context.session_id,
                request_id=context.request_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
        )

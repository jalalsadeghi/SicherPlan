"""Service layer for employee availability, absences, leave balances, and event applications."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import (
    EMPLOYEE_ABSENCE_STATUSES,
    EMPLOYEE_ABSENCE_TYPES,
    EMPLOYEE_AVAILABILITY_RECURRENCE_TYPES,
    EMPLOYEE_AVAILABILITY_RULE_KINDS,
    EMPLOYEE_EVENT_APPLICATION_STATUSES,
    Employee,
    EmployeeAbsence,
    EmployeeAvailabilityRule,
    EmployeeEventApplication,
    EmployeeLeaveBalance,
)
from app.modules.employees.schemas import (
    EmployeeAbsenceCreate,
    EmployeeAbsenceFilter,
    EmployeeAbsenceRead,
    EmployeeAbsenceUpdate,
    EmployeeAvailabilityRuleCreate,
    EmployeeAvailabilityRuleFilter,
    EmployeeAvailabilityRuleRead,
    EmployeeAvailabilityRuleUpdate,
    EmployeeEventApplicationCreate,
    EmployeeEventApplicationFilter,
    EmployeeEventApplicationRead,
    EmployeeEventApplicationUpdate,
    EmployeeLeaveBalanceFilter,
    EmployeeLeaveBalanceRead,
    EmployeeLeaveBalanceUpsert,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope


ACTIVE_ABSENCE_STATUSES = {"pending", "approved"}
VACATION_ABSENCE_TYPE = "vacation"
DECIMAL_ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class PlanningRecordReference:
    planning_record_id: str


class EmployeeAvailabilityRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def list_availability_rules(
        self,
        tenant_id: str,
        filters: EmployeeAvailabilityRuleFilter | None = None,
    ) -> list[EmployeeAvailabilityRule]: ...
    def get_availability_rule(self, tenant_id: str, rule_id: str) -> EmployeeAvailabilityRule | None: ...
    def create_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule: ...
    def update_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule: ...
    def list_absences(self, tenant_id: str, filters: EmployeeAbsenceFilter | None = None) -> list[EmployeeAbsence]: ...
    def get_absence(self, tenant_id: str, absence_id: str) -> EmployeeAbsence | None: ...
    def create_absence(self, row: EmployeeAbsence) -> EmployeeAbsence: ...
    def update_absence(self, row: EmployeeAbsence) -> EmployeeAbsence: ...
    def list_leave_balances(
        self,
        tenant_id: str,
        filters: EmployeeLeaveBalanceFilter | None = None,
    ) -> list[EmployeeLeaveBalance]: ...
    def get_leave_balance(self, tenant_id: str, balance_id: str) -> EmployeeLeaveBalance | None: ...
    def get_leave_balance_for_year(self, tenant_id: str, employee_id: str, balance_year: int) -> EmployeeLeaveBalance | None: ...
    def create_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance: ...
    def update_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance: ...
    def list_event_applications(
        self,
        tenant_id: str,
        filters: EmployeeEventApplicationFilter | None = None,
    ) -> list[EmployeeEventApplication]: ...
    def get_event_application(self, tenant_id: str, application_id: str) -> EmployeeEventApplication | None: ...
    def find_event_application(
        self,
        tenant_id: str,
        employee_id: str,
        planning_record_id: str,
        *,
        exclude_id: str | None = None,
    ) -> EmployeeEventApplication | None: ...
    def create_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication: ...
    def update_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication: ...


class EmployeeAvailabilityService:
    def __init__(self, repository: EmployeeAvailabilityRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_availability_rules(
        self,
        tenant_id: str,
        filters: EmployeeAvailabilityRuleFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeAvailabilityRuleRead]:
        self._require_employee_read(tenant_id, context)
        rows = self.repository.list_availability_rules(tenant_id, filters or EmployeeAvailabilityRuleFilter())
        return [EmployeeAvailabilityRuleRead.model_validate(row) for row in rows]

    def create_availability_rule(
        self,
        tenant_id: str,
        payload: EmployeeAvailabilityRuleCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAvailabilityRuleRead:
        self._require_employee_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.availability_rule.tenant_mismatch",
                "errors.employees.availability_rule.tenant_mismatch",
            )
        self._require_employee(tenant_id, payload.employee_id)
        self._validate_availability_payload(payload.rule_kind, payload.starts_at, payload.ends_at, payload.recurrence_type, payload.weekday_mask)
        row = self.repository.create_availability_rule(
            EmployeeAvailabilityRule(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                rule_kind=payload.rule_kind,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                recurrence_type=payload.recurrence_type,
                weekday_mask=payload.weekday_mask,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.availability_rule.created",
            entity_type="hr.employee_availability_rule",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._availability_snapshot(row),
            metadata_json={"employee_id": row.employee_id},
        )
        return EmployeeAvailabilityRuleRead.model_validate(row)

    def update_availability_rule(
        self,
        tenant_id: str,
        rule_id: str,
        payload: EmployeeAvailabilityRuleUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAvailabilityRuleRead:
        self._require_employee_write(tenant_id, context)
        row = self._require_availability_rule(tenant_id, rule_id)
        before = self._availability_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "availability_rule")
        next_kind = payload.rule_kind if payload.rule_kind is not None else row.rule_kind
        next_starts_at = payload.starts_at if payload.starts_at is not None else row.starts_at
        next_ends_at = payload.ends_at if payload.ends_at is not None else row.ends_at
        next_recurrence = payload.recurrence_type if payload.recurrence_type is not None else row.recurrence_type
        next_mask = payload.weekday_mask if payload.weekday_mask is not None else row.weekday_mask
        self._validate_availability_payload(next_kind, next_starts_at, next_ends_at, next_recurrence, next_mask)
        row.rule_kind = next_kind
        row.starts_at = next_starts_at
        row.ends_at = next_ends_at
        row.recurrence_type = next_recurrence
        row.weekday_mask = next_mask
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_availability_rule(row)
        self._record_event(
            context,
            event_type="employees.availability_rule.updated",
            entity_type="hr.employee_availability_rule",
            entity_id=rule_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._availability_snapshot(updated),
            metadata_json={"employee_id": row.employee_id},
        )
        return EmployeeAvailabilityRuleRead.model_validate(updated)

    def list_absences(
        self,
        tenant_id: str,
        filters: EmployeeAbsenceFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeAbsenceRead]:
        self._require_private_read(tenant_id, context)
        rows = self.repository.list_absences(tenant_id, filters or EmployeeAbsenceFilter())
        return [EmployeeAbsenceRead.model_validate(row) for row in rows]

    def create_absence(
        self,
        tenant_id: str,
        payload: EmployeeAbsenceCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAbsenceRead:
        self._require_private_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.absence.tenant_mismatch", "errors.employees.absence.tenant_mismatch")
        self._require_employee(tenant_id, payload.employee_id)
        self._validate_absence_payload(payload.absence_type, payload.starts_on, payload.ends_on)
        self._ensure_absence_overlap_free(
            tenant_id,
            payload.employee_id,
            payload.starts_on,
            payload.ends_on,
            status="pending",
            exclude_id=None,
        )
        row = self.repository.create_absence(
            EmployeeAbsence(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                absence_type=payload.absence_type,
                starts_on=payload.starts_on,
                ends_on=payload.ends_on,
                quantity_days=self._date_span_days(payload.starts_on, payload.ends_on),
                status="pending",
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._recalculate_leave_balances(tenant_id, row.employee_id, {payload.starts_on.year, payload.ends_on.year}, context.user_id)
        self._record_event(
            context,
            event_type="employees.absence.created",
            entity_type="hr.employee_absence",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._absence_snapshot(row),
            metadata_json={"employee_id": row.employee_id},
        )
        return EmployeeAbsenceRead.model_validate(row)

    def update_absence(
        self,
        tenant_id: str,
        absence_id: str,
        payload: EmployeeAbsenceUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAbsenceRead:
        self._require_private_write(tenant_id, context)
        row = self._require_absence(tenant_id, absence_id)
        before = self._absence_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "absence")
        next_type = payload.absence_type if payload.absence_type is not None else row.absence_type
        next_starts = payload.starts_on if payload.starts_on is not None else row.starts_on
        next_ends = payload.ends_on if payload.ends_on is not None else row.ends_on
        next_status = payload.status if payload.status is not None else row.status
        self._validate_absence_payload(next_type, next_starts, next_ends)
        self._ensure_absence_overlap_free(
            tenant_id,
            row.employee_id,
            next_starts,
            next_ends,
            status=next_status,
            exclude_id=absence_id,
        )
        old_years = {row.starts_on.year, row.ends_on.year}
        row.absence_type = next_type
        row.starts_on = next_starts
        row.ends_on = next_ends
        row.quantity_days = self._date_span_days(next_starts, next_ends)
        row.notes = self._effective_optional(payload.notes, row.notes)
        row.decision_note = self._effective_optional(payload.decision_note, row.decision_note)
        if payload.status is not None:
            row.status = payload.status
            if payload.status == "approved":
                row.approved_by_user_id = context.user_id
                row.approved_at = datetime.now(UTC)
            elif payload.status in {"rejected", "cancelled"}:
                row.approved_by_user_id = None
                row.approved_at = None
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_absence(row)
        affected_years = old_years | {updated.starts_on.year, updated.ends_on.year}
        self._recalculate_leave_balances(tenant_id, updated.employee_id, affected_years, context.user_id)
        event_type = "employees.absence.updated" if before["status"] == updated.status else "employees.absence.status_changed"
        self._record_event(
            context,
            event_type=event_type,
            entity_type="hr.employee_absence",
            entity_id=absence_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._absence_snapshot(updated),
            metadata_json={"employee_id": updated.employee_id},
        )
        return EmployeeAbsenceRead.model_validate(updated)

    def list_leave_balances(
        self,
        tenant_id: str,
        filters: EmployeeLeaveBalanceFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeLeaveBalanceRead]:
        self._require_private_read(tenant_id, context)
        rows = self.repository.list_leave_balances(tenant_id, filters or EmployeeLeaveBalanceFilter())
        return [EmployeeLeaveBalanceRead.model_validate(row) for row in rows]

    def upsert_leave_balance(
        self,
        tenant_id: str,
        payload: EmployeeLeaveBalanceUpsert,
        context: RequestAuthorizationContext,
    ) -> EmployeeLeaveBalanceRead:
        self._require_private_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.leave_balance.tenant_mismatch",
                "errors.employees.leave_balance.tenant_mismatch",
            )
        self._require_employee(tenant_id, payload.employee_id)
        if payload.balance_year < 2000:
            raise ApiException(400, "employees.leave_balance.invalid_year", "errors.employees.leave_balance.invalid_year")
        existing = self.repository.get_leave_balance_for_year(tenant_id, payload.employee_id, payload.balance_year)
        if existing is None:
            row = self.repository.create_leave_balance(
                EmployeeLeaveBalance(
                    tenant_id=tenant_id,
                    employee_id=payload.employee_id,
                    balance_year=payload.balance_year,
                    entitlement_days=Decimal(str(payload.entitlement_days)),
                    carry_over_days=Decimal(str(payload.carry_over_days)),
                    manual_adjustment_days=Decimal(str(payload.manual_adjustment_days)),
                    consumed_days=DECIMAL_ZERO,
                    pending_days=DECIMAL_ZERO,
                    notes=self._normalize_optional(payload.notes),
                    created_by_user_id=context.user_id,
                    updated_by_user_id=context.user_id,
                )
            )
            self._recalculate_leave_balances(tenant_id, row.employee_id, {row.balance_year}, context.user_id)
            self._record_event(
                context,
                event_type="employees.leave_balance.created",
                entity_type="hr.employee_leave_balance",
                entity_id=row.id,
                tenant_id=tenant_id,
                after_json=self._leave_balance_snapshot(row),
                metadata_json={"employee_id": row.employee_id},
            )
            return EmployeeLeaveBalanceRead.model_validate(self._require_leave_balance(tenant_id, row.id))
        before = self._leave_balance_snapshot(existing)
        existing.entitlement_days = Decimal(str(payload.entitlement_days))
        existing.carry_over_days = Decimal(str(payload.carry_over_days))
        existing.manual_adjustment_days = Decimal(str(payload.manual_adjustment_days))
        existing.notes = self._normalize_optional(payload.notes)
        existing.updated_by_user_id = context.user_id
        existing.version_no += 1
        updated = self.repository.update_leave_balance(existing)
        self._recalculate_leave_balances(tenant_id, updated.employee_id, {updated.balance_year}, context.user_id)
        refreshed = self.repository.get_leave_balance_for_year(tenant_id, updated.employee_id, updated.balance_year) or updated
        self._record_event(
            context,
            event_type="employees.leave_balance.updated",
            entity_type="hr.employee_leave_balance",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._leave_balance_snapshot(refreshed),
            metadata_json={"employee_id": updated.employee_id},
        )
        return EmployeeLeaveBalanceRead.model_validate(refreshed)

    def list_event_applications(
        self,
        tenant_id: str,
        filters: EmployeeEventApplicationFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeEventApplicationRead]:
        self._require_employee_read(tenant_id, context)
        rows = self.repository.list_event_applications(tenant_id, filters or EmployeeEventApplicationFilter())
        return [EmployeeEventApplicationRead.model_validate(row) for row in rows]

    def create_event_application(
        self,
        tenant_id: str,
        payload: EmployeeEventApplicationCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeEventApplicationRead:
        self._require_employee_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.event_application.tenant_mismatch",
                "errors.employees.event_application.tenant_mismatch",
            )
        self._require_employee(tenant_id, payload.employee_id)
        self._validate_planning_reference(payload.planning_record_id)
        duplicate = self.repository.find_event_application(tenant_id, payload.employee_id, payload.planning_record_id)
        if duplicate is not None:
            raise ApiException(
                409,
                "employees.event_application.duplicate",
                "errors.employees.event_application.duplicate",
            )
        row = self.repository.create_event_application(
            EmployeeEventApplication(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                planning_record_id=payload.planning_record_id,
                note=self._normalize_optional(payload.note),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.event_application.created",
            entity_type="hr.employee_event_application",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._event_application_snapshot(row),
            metadata_json={"employee_id": row.employee_id, "planning_reference_validation": "deferred"},
        )
        return EmployeeEventApplicationRead.model_validate(row)

    def update_event_application(
        self,
        tenant_id: str,
        application_id: str,
        payload: EmployeeEventApplicationUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeEventApplicationRead:
        self._require_employee_write(tenant_id, context)
        row = self._require_event_application(tenant_id, application_id)
        before = self._event_application_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "event_application")
        if payload.note is not None:
            row.note = self._normalize_optional(payload.note)
        if payload.decision_note is not None:
            row.decision_note = self._normalize_optional(payload.decision_note)
        if payload.status is not None:
            if payload.status not in EMPLOYEE_EVENT_APPLICATION_STATUSES:
                raise ApiException(
                    400,
                    "employees.event_application.invalid_status",
                    "errors.employees.event_application.invalid_status",
                )
            row.status = payload.status
            if payload.status in {"approved", "rejected"}:
                row.decided_by_user_id = context.user_id
                row.decided_at = datetime.now(UTC)
            elif payload.status == "withdrawn":
                row.decided_by_user_id = None
                row.decided_at = None
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_event_application(row)
        self._record_event(
            context,
            event_type="employees.event_application.updated",
            entity_type="hr.employee_event_application",
            entity_id=application_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._event_application_snapshot(updated),
            metadata_json={"employee_id": updated.employee_id, "planning_reference_validation": "deferred"},
        )
        return EmployeeEventApplicationRead.model_validate(updated)

    def _recalculate_leave_balances(
        self,
        tenant_id: str,
        employee_id: str,
        years: set[int],
        actor_user_id: str | None,
    ) -> None:
        all_absences = self.repository.list_absences(
            tenant_id,
            EmployeeAbsenceFilter(employee_id=employee_id, include_archived=False),
        )
        for year in years:
            balance = self.repository.get_leave_balance_for_year(tenant_id, employee_id, year)
            if balance is None:
                balance = self.repository.create_leave_balance(
                    EmployeeLeaveBalance(
                        tenant_id=tenant_id,
                        employee_id=employee_id,
                        balance_year=year,
                        entitlement_days=DECIMAL_ZERO,
                        carry_over_days=DECIMAL_ZERO,
                        manual_adjustment_days=DECIMAL_ZERO,
                        consumed_days=DECIMAL_ZERO,
                        pending_days=DECIMAL_ZERO,
                        created_by_user_id=actor_user_id,
                        updated_by_user_id=actor_user_id,
                    )
                )
            consumed = DECIMAL_ZERO
            pending = DECIMAL_ZERO
            for absence in all_absences:
                if absence.absence_type != VACATION_ABSENCE_TYPE:
                    continue
                days_in_year = self._absence_days_in_year(absence.starts_on, absence.ends_on, year)
                if days_in_year == DECIMAL_ZERO:
                    continue
                if absence.status == "approved":
                    consumed += days_in_year
                elif absence.status == "pending":
                    pending += days_in_year
            balance.consumed_days = consumed
            balance.pending_days = pending
            balance.updated_by_user_id = actor_user_id
            balance.version_no += 1
            self.repository.update_leave_balance(balance)

    def _ensure_absence_overlap_free(
        self,
        tenant_id: str,
        employee_id: str,
        starts_on: date,
        ends_on: date,
        *,
        status: str,
        exclude_id: str | None,
    ) -> None:
        if status not in ACTIVE_ABSENCE_STATUSES:
            return
        existing_rows = self.repository.list_absences(
            tenant_id,
            EmployeeAbsenceFilter(employee_id=employee_id, include_archived=False),
        )
        for existing in existing_rows:
            if existing.id == exclude_id or existing.status not in ACTIVE_ABSENCE_STATUSES:
                continue
            if existing.starts_on <= ends_on and starts_on <= existing.ends_on:
                raise ApiException(409, "employees.absence.overlap", "errors.employees.absence.overlap")

    def _validate_availability_payload(
        self,
        rule_kind: str,
        starts_at: datetime,
        ends_at: datetime,
        recurrence_type: str,
        weekday_mask: str | None,
    ) -> None:
        if rule_kind not in EMPLOYEE_AVAILABILITY_RULE_KINDS:
            raise ApiException(
                400,
                "employees.availability_rule.invalid_kind",
                "errors.employees.availability_rule.invalid_kind",
            )
        if ends_at <= starts_at:
            raise ApiException(
                400,
                "employees.availability_rule.invalid_window",
                "errors.employees.availability_rule.invalid_window",
            )
        if recurrence_type not in EMPLOYEE_AVAILABILITY_RECURRENCE_TYPES:
            raise ApiException(
                400,
                "employees.availability_rule.invalid_recurrence",
                "errors.employees.availability_rule.invalid_recurrence",
            )
        if recurrence_type == "none" and weekday_mask is not None:
            raise ApiException(
                400,
                "employees.availability_rule.invalid_recurrence_mask",
                "errors.employees.availability_rule.invalid_recurrence_mask",
            )
        if recurrence_type == "weekly":
            if weekday_mask is None or len(weekday_mask) != 7 or any(char not in {"0", "1"} for char in weekday_mask):
                raise ApiException(
                    400,
                    "employees.availability_rule.invalid_recurrence_mask",
                    "errors.employees.availability_rule.invalid_recurrence_mask",
                )
            if weekday_mask == "0000000":
                raise ApiException(
                    400,
                    "employees.availability_rule.invalid_recurrence_mask",
                    "errors.employees.availability_rule.invalid_recurrence_mask",
                )

    def _validate_absence_payload(self, absence_type: str, starts_on: date, ends_on: date) -> None:
        if absence_type not in EMPLOYEE_ABSENCE_TYPES:
            raise ApiException(400, "employees.absence.invalid_type", "errors.employees.absence.invalid_type")
        if ends_on < starts_on:
            raise ApiException(400, "employees.absence.invalid_window", "errors.employees.absence.invalid_window")

    @staticmethod
    def _validate_planning_reference(planning_record_id: str) -> PlanningRecordReference:
        if not planning_record_id:
            raise ApiException(
                400,
                "employees.event_application.planning_record_required",
                "errors.employees.event_application.planning_record_required",
            )
        return PlanningRecordReference(planning_record_id=planning_record_id)

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        employee = self.repository.get_employee(tenant_id, employee_id)
        if employee is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return employee

    def _require_availability_rule(self, tenant_id: str, rule_id: str) -> EmployeeAvailabilityRule:
        row = self.repository.get_availability_rule(tenant_id, rule_id)
        if row is None:
            raise ApiException(
                404,
                "employees.availability_rule.not_found",
                "errors.employees.availability_rule.not_found",
            )
        return row

    def _require_absence(self, tenant_id: str, absence_id: str) -> EmployeeAbsence:
        row = self.repository.get_absence(tenant_id, absence_id)
        if row is None:
            raise ApiException(404, "employees.absence.not_found", "errors.employees.absence.not_found")
        return row

    def _require_leave_balance(self, tenant_id: str, balance_id: str) -> EmployeeLeaveBalance:
        row = self.repository.get_leave_balance(tenant_id, balance_id)
        if row is None:
            raise ApiException(
                404,
                "employees.leave_balance.not_found",
                "errors.employees.leave_balance.not_found",
            )
        return row

    def _require_event_application(self, tenant_id: str, application_id: str) -> EmployeeEventApplication:
        row = self.repository.get_event_application(tenant_id, application_id)
        if row is None:
            raise ApiException(
                404,
                "employees.event_application.not_found",
                "errors.employees.event_application.not_found",
            )
        return row

    @staticmethod
    def _require_version(current: int, incoming: int | None, resource: str) -> None:
        if incoming is None or incoming != current:
            raise ApiException(
                409,
                f"employees.{resource}.stale_version",
                f"errors.employees.{resource}.stale_version",
            )

    @staticmethod
    def _date_span_days(starts_on: date, ends_on: date) -> Decimal:
        return Decimal((ends_on - starts_on).days + 1).quantize(Decimal("0.00"))

    @staticmethod
    def _absence_days_in_year(starts_on: date, ends_on: date, year: int) -> Decimal:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        overlap_start = max(starts_on, year_start)
        overlap_end = min(ends_on, year_end)
        if overlap_end < overlap_start:
            return DECIMAL_ZERO
        return Decimal((overlap_end - overlap_start).days + 1).quantize(Decimal("0.00"))

    def _require_employee_read(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.read" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.read"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_employee_write(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.write" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.write"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_private_read(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.private.read" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.private.read"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_private_write(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.private.write" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.private.write"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _effective_optional(value: str | None, current: str | None) -> str | None:
        if value is None:
            return current
        normalized = value.strip()
        return normalized or None

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
        metadata_json: dict[str, object] | None = None,
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
            metadata_json=metadata_json,
        )

    @staticmethod
    def _availability_snapshot(row: EmployeeAvailabilityRule) -> dict[str, object]:
        return {
            "employee_id": row.employee_id,
            "rule_kind": row.rule_kind,
            "starts_at": row.starts_at.isoformat(),
            "ends_at": row.ends_at.isoformat(),
            "recurrence_type": row.recurrence_type,
            "weekday_mask": row.weekday_mask,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _absence_snapshot(row: EmployeeAbsence) -> dict[str, object]:
        return {
            "employee_id": row.employee_id,
            "absence_type": row.absence_type,
            "starts_on": row.starts_on.isoformat(),
            "ends_on": row.ends_on.isoformat(),
            "quantity_days": str(row.quantity_days),
            "status": row.status,
            "approved_by_user_id": row.approved_by_user_id,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "version_no": row.version_no,
        }

    @staticmethod
    def _leave_balance_snapshot(row: EmployeeLeaveBalance) -> dict[str, object]:
        return {
            "employee_id": row.employee_id,
            "balance_year": row.balance_year,
            "entitlement_days": str(row.entitlement_days),
            "carry_over_days": str(row.carry_over_days),
            "manual_adjustment_days": str(row.manual_adjustment_days),
            "consumed_days": str(row.consumed_days),
            "pending_days": str(row.pending_days),
            "version_no": row.version_no,
        }

    @staticmethod
    def _event_application_snapshot(row: EmployeeEventApplication) -> dict[str, object]:
        return {
            "employee_id": row.employee_id,
            "planning_record_id": row.planning_record_id,
            "status": row.status,
            "applied_at": row.applied_at.isoformat() if row.applied_at else None,
            "decided_by_user_id": row.decided_by_user_id,
            "decided_at": row.decided_at.isoformat() if row.decided_at else None,
            "version_no": row.version_no,
        }

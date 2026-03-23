"""Shared planning validation engine for staffing assignments and release gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import Assignment, DemandGroup, Shift
from app.modules.planning.schemas import (
    AssignmentValidationRead,
    PlanningRecordReleaseValidationRead,
    PlanningValidationResult,
    ShiftReleaseValidationRead,
)


@dataclass(frozen=True)
class ValidationPolicy:
    severity: str
    override_allowed: bool
    enabled: bool = True


@dataclass(frozen=True)
class ValidationActor:
    actor_type: str
    actor_id: str
    subcontractor_id: str | None = None


class PlanningValidationRepository(Protocol):
    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None: ...
    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None: ...
    def get_demand_group(self, tenant_id: str, row_id: str) -> DemandGroup | None: ...
    def get_assignment(self, tenant_id: str, row_id: str) -> Assignment | None: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Assignment]: ...
    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[DemandGroup]: ...
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...
    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[Shift]: ...
    def get_employee(self, tenant_id: str, employee_id: str): ...
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str): ...
    def list_employee_qualifications(self, tenant_id: str, employee_id: str) -> list[object]: ...
    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[object]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...
    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date: date) -> list[object]: ...
    def list_overlapping_assignments(
        self,
        tenant_id: str,
        *,
        starts_at: datetime,
        ends_at: datetime,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        exclude_assignment_id: str | None = None,
    ) -> list[Assignment]: ...
    def list_assignments_for_actor_in_window(
        self,
        tenant_id: str,
        *,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        window_start: datetime,
        window_end: datetime,
        exclude_assignment_id: str | None = None,
    ) -> list[Assignment]: ...
    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str) -> list[object]: ...


class PlanningValidationService:
    POLICY_KEY = "planning.validation_policy"
    DEFAULT_POLICIES: dict[str, ValidationPolicy] = {
        "qualification_match": ValidationPolicy(severity="block", override_allowed=False),
        "function_match": ValidationPolicy(severity="block", override_allowed=False),
        "certificate_validity": ValidationPolicy(severity="block", override_allowed=True),
        "mandatory_documents": ValidationPolicy(severity="block", override_allowed=True),
        "customer_block": ValidationPolicy(severity="block", override_allowed=False),
        "double_booking": ValidationPolicy(severity="block", override_allowed=False),
        "rest_period": ValidationPolicy(severity="warn", override_allowed=False),
        "max_hours": ValidationPolicy(severity="warn", override_allowed=False),
        "earnings_threshold": ValidationPolicy(severity="info", override_allowed=False, enabled=False),
        "minimum_staffing": ValidationPolicy(severity="block", override_allowed=False),
    }

    def __init__(self, repository: PlanningValidationRepository) -> None:
        self.repository = repository

    def validate_assignment_by_id(self, tenant_id: str, assignment_id: str) -> AssignmentValidationRead:
        assignment = self.repository.get_assignment(tenant_id, assignment_id)
        if assignment is None:
            return AssignmentValidationRead(
                tenant_id=tenant_id,
                assignment_id=assignment_id,
                shift_id="",
                blocking_count=1,
                warning_count=0,
                issues=[
                    PlanningValidationResult(
                        rule_code="assignment_missing",
                        severity="block",
                        message_key="errors.planning.assignment.not_found",
                        assignment_id=assignment_id,
                        shift_id="",
                    )
                ],
            )
        issues = self.validate_assignment(
            tenant_id,
            shift_id=assignment.shift_id,
            demand_group_id=assignment.demand_group_id,
            employee_id=assignment.employee_id,
            subcontractor_worker_id=assignment.subcontractor_worker_id,
            assignment_id=assignment.id,
        )
        return self._assignment_result(tenant_id, assignment.id, assignment.shift_id, issues)

    def validate_assignment(
        self,
        tenant_id: str,
        *,
        shift_id: str,
        demand_group_id: str,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        assignment_id: str | None = None,
    ) -> list[PlanningValidationResult]:
        shift = self.repository.get_shift(tenant_id, shift_id)
        demand_group = self.repository.get_demand_group(tenant_id, demand_group_id)
        if shift is None or demand_group is None:
            return []
        actor = self._actor(tenant_id, employee_id, subcontractor_worker_id)
        if actor is None:
            return []
        issues: list[PlanningValidationResult] = []
        issues.extend(self._validate_function_and_qualification(tenant_id, shift, demand_group, actor, assignment_id))
        issues.extend(self._validate_certificate_validity(tenant_id, shift, demand_group, actor, assignment_id))
        issues.extend(self._validate_mandatory_documents(tenant_id, shift, demand_group, actor, assignment_id))
        issues.extend(self._validate_customer_block(tenant_id, shift, actor, assignment_id))
        issues.extend(self._validate_double_booking(tenant_id, shift, actor, assignment_id))
        issues.extend(self._validate_rest_period(tenant_id, shift, actor, assignment_id))
        issues.extend(self._validate_max_hours(tenant_id, shift, actor, assignment_id))
        issues.extend(self._validate_earnings_threshold(tenant_id, shift, actor, assignment_id))
        return self._apply_overrides(tenant_id, assignment_id, issues)

    def validate_shift_release(self, tenant_id: str, shift_id: str) -> ShiftReleaseValidationRead:
        shift = self.repository.get_shift(tenant_id, shift_id)
        issues: list[PlanningValidationResult] = []
        if shift is not None:
            issues.extend(self._validate_minimum_staffing(tenant_id, shift))
        return ShiftReleaseValidationRead(
            tenant_id=tenant_id,
            shift_id=shift_id,
            blocking_count=sum(1 for issue in issues if issue.severity == "block"),
            warning_count=sum(1 for issue in issues if issue.severity == "warn"),
            issues=issues,
        )

    def validate_planning_record_release(self, tenant_id: str, planning_record_id: str) -> PlanningRecordReleaseValidationRead:
        issues: list[PlanningValidationResult] = []
        for shift in self.repository.list_shifts_for_planning_record(tenant_id, planning_record_id):
            issues.extend(self._validate_minimum_staffing(tenant_id, shift))
        return PlanningRecordReleaseValidationRead(
            tenant_id=tenant_id,
            planning_record_id=planning_record_id,
            blocking_count=sum(1 for issue in issues if issue.severity == "block"),
            warning_count=sum(1 for issue in issues if issue.severity == "warn"),
            issues=issues,
        )

    def has_blocking_issues(self, issues: list[PlanningValidationResult]) -> bool:
        return any(issue.severity == "block" for issue in issues)

    def blocking_issue_codes(self, issues: list[PlanningValidationResult]) -> list[str]:
        return [issue.rule_code for issue in issues if issue.severity == "block"]

    def policy_for(self, tenant_id: str, rule_code: str) -> ValidationPolicy:
        policies_json = self.repository.get_tenant_setting_value(tenant_id, self.POLICY_KEY) or {}
        rules_json = policies_json.get("rules") if isinstance(policies_json.get("rules"), dict) else {}
        raw = rules_json.get(rule_code) if isinstance(rules_json, dict) else None
        fallback = self.DEFAULT_POLICIES[rule_code]
        if not isinstance(raw, dict):
            return fallback
        severity = raw.get("severity") if raw.get("severity") in {"block", "warn", "info"} else fallback.severity
        override_allowed = bool(raw.get("override_allowed", fallback.override_allowed))
        enabled = bool(raw.get("enabled", fallback.enabled))
        return ValidationPolicy(severity=severity, override_allowed=override_allowed, enabled=enabled)

    def _actor(self, tenant_id: str, employee_id: str | None, subcontractor_worker_id: str | None) -> ValidationActor | None:
        if employee_id is not None:
            employee = self.repository.get_employee(tenant_id, employee_id)
            if employee is None:
                return None
            return ValidationActor(actor_type="employee", actor_id=employee_id)
        if subcontractor_worker_id is not None:
            worker = self.repository.get_subcontractor_worker(tenant_id, subcontractor_worker_id)
            if worker is None:
                return None
            return ValidationActor(actor_type="subcontractor_worker", actor_id=subcontractor_worker_id, subcontractor_id=worker.subcontractor_id)
        return None

    def _validate_function_and_qualification(
        self,
        tenant_id: str,
        shift: Shift,
        demand_group: DemandGroup,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        issues: list[PlanningValidationResult] = []
        if actor.actor_type == "employee":
            rows = self.repository.list_employee_qualifications(tenant_id, actor.actor_id)
            if not any(row.record_kind == "function" and row.function_type_id == demand_group.function_type_id and self._is_active_window(row, shift) for row in rows):
                issues.append(self._issue(tenant_id, "function_match", shift, demand_group, actor, assignment_id))
            if demand_group.qualification_type_id is not None and not any(
                row.record_kind == "qualification"
                and row.qualification_type_id == demand_group.qualification_type_id
                and self._is_active_window(row, shift)
                for row in rows
            ):
                issues.append(self._issue(tenant_id, "qualification_match", shift, demand_group, actor, assignment_id))
            return issues

        if demand_group.qualification_type_id is not None:
            rows = self.repository.list_worker_qualifications(tenant_id, actor.actor_id)
            if not any(row.qualification_type_id == demand_group.qualification_type_id and self._is_active_window(row, shift) for row in rows):
                issues.append(self._issue(tenant_id, "qualification_match", shift, demand_group, actor, assignment_id))
        return issues

    def _validate_certificate_validity(
        self,
        tenant_id: str,
        shift: Shift,
        demand_group: DemandGroup,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        if demand_group.qualification_type_id is None:
            return []
        rows = (
            self.repository.list_employee_qualifications(tenant_id, actor.actor_id)
            if actor.actor_type == "employee"
            else self.repository.list_worker_qualifications(tenant_id, actor.actor_id)
        )
        for row in rows:
            if getattr(row, "qualification_type_id", None) != demand_group.qualification_type_id:
                continue
            qualification_type = getattr(row, "qualification_type", None)
            if qualification_type is None or not getattr(qualification_type, "expiry_required", False):
                continue
            if row.valid_until is None or row.valid_until < shift.starts_at.date():
                return [self._issue(tenant_id, "certificate_validity", shift, demand_group, actor, assignment_id, metadata={"valid_until": row.valid_until.isoformat() if row.valid_until else None})]
        return []

    def _validate_mandatory_documents(
        self,
        tenant_id: str,
        shift: Shift,
        demand_group: DemandGroup,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        if demand_group.qualification_type_id is None:
            return []
        rows = (
            self.repository.list_employee_qualifications(tenant_id, actor.actor_id)
            if actor.actor_type == "employee"
            else self.repository.list_worker_qualifications(tenant_id, actor.actor_id)
        )
        owner_type = "hr.employee_qualification" if actor.actor_type == "employee" else "partner.subcontractor_worker_qualification"
        for row in rows:
            if getattr(row, "qualification_type_id", None) != demand_group.qualification_type_id:
                continue
            qualification_type = getattr(row, "qualification_type", None)
            if qualification_type is None or not getattr(qualification_type, "proof_required", False):
                continue
            if not self.repository.list_documents_for_owner(tenant_id, owner_type, row.id):
                return [self._issue(tenant_id, "mandatory_documents", shift, demand_group, actor, assignment_id, metadata={"owner_type": owner_type, "owner_id": row.id})]
        return []

    def _validate_customer_block(
        self,
        tenant_id: str,
        shift: Shift,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        if actor.actor_type != "employee":
            return []
        customer_id = self._customer_id_for_shift(tenant_id, shift)
        if customer_id is None:
            return []
        blocks = self.repository.list_customer_employee_blocks(tenant_id, customer_id, actor.actor_id, shift.starts_at.date())
        if blocks:
            return [self._issue(tenant_id, "customer_block", shift, None, actor, assignment_id, metadata={"customer_id": customer_id})]
        return []

    def _validate_double_booking(
        self,
        tenant_id: str,
        shift: Shift,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        overlaps = self.repository.list_overlapping_assignments(
            tenant_id,
            starts_at=shift.starts_at,
            ends_at=shift.ends_at,
            employee_id=actor.actor_id if actor.actor_type == "employee" else None,
            subcontractor_worker_id=actor.actor_id if actor.actor_type == "subcontractor_worker" else None,
            exclude_assignment_id=assignment_id,
        )
        if overlaps:
            return [self._issue(tenant_id, "double_booking", shift, None, actor, assignment_id, metadata={"overlap_assignment_id": overlaps[0].id})]
        return []

    def _validate_rest_period(
        self,
        tenant_id: str,
        shift: Shift,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        min_rest_hours = 11
        rows = self.repository.list_assignments_for_actor_in_window(
            tenant_id,
            employee_id=actor.actor_id if actor.actor_type == "employee" else None,
            subcontractor_worker_id=actor.actor_id if actor.actor_type == "subcontractor_worker" else None,
            window_start=shift.starts_at - timedelta(hours=min_rest_hours),
            window_end=shift.ends_at + timedelta(hours=min_rest_hours),
            exclude_assignment_id=assignment_id,
        )
        for row in rows:
            other_shift = self.repository.get_shift(tenant_id, row.shift_id)
            if other_shift is None:
                continue
            rest_gap = min(abs((shift.starts_at - other_shift.ends_at).total_seconds()), abs((other_shift.starts_at - shift.ends_at).total_seconds()))
            if rest_gap < min_rest_hours * 3600:
                return [self._issue(tenant_id, "rest_period", shift, None, actor, assignment_id, metadata={"other_shift_id": other_shift.id, "min_rest_hours": min_rest_hours})]
        return []

    def _validate_max_hours(
        self,
        tenant_id: str,
        shift: Shift,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        max_hours = 12
        window_start = shift.starts_at - timedelta(hours=24)
        rows = self.repository.list_assignments_for_actor_in_window(
            tenant_id,
            employee_id=actor.actor_id if actor.actor_type == "employee" else None,
            subcontractor_worker_id=actor.actor_id if actor.actor_type == "subcontractor_worker" else None,
            window_start=window_start,
            window_end=shift.ends_at,
            exclude_assignment_id=assignment_id,
        )
        total_seconds = (shift.ends_at - shift.starts_at).total_seconds()
        for row in rows:
            other_shift = self.repository.get_shift(tenant_id, row.shift_id)
            if other_shift is not None:
                total_seconds += max((other_shift.ends_at - other_shift.starts_at).total_seconds(), 0)
        if total_seconds > max_hours * 3600:
            return [self._issue(tenant_id, "max_hours", shift, None, actor, assignment_id, metadata={"limit_hours": max_hours, "planned_hours": round(total_seconds / 3600, 2)})]
        return []

    def _validate_earnings_threshold(
        self,
        tenant_id: str,
        shift: Shift,
        actor: ValidationActor,
        assignment_id: str | None,
    ) -> list[PlanningValidationResult]:
        policy = self.policy_for(tenant_id, "earnings_threshold")
        if not policy.enabled:
            return [
                PlanningValidationResult(
                    rule_code="earnings_threshold",
                    severity="info",
                    message_key="errors.planning.validation.earnings_threshold_unavailable",
                    actor_type=actor.actor_type,
                    actor_id=actor.actor_id,
                    assignment_id=assignment_id,
                    shift_id=shift.id,
                    policy_code=self.POLICY_KEY,
                    override_allowed=False,
                    metadata={"provider_state": "unavailable"},
                )
            ]
        return []

    def _validate_minimum_staffing(self, tenant_id: str, shift: Shift) -> list[PlanningValidationResult]:
        assignments = [row for row in self.repository.list_assignments_in_shift(tenant_id, shift.id) if row.assignment_status_code != "removed"]
        releases = [row for row in self.repository.list_subcontractor_releases_for_shift(tenant_id, shift.id) if row.release_status_code != "revoked"]
        release_by_group: dict[str | None, int] = {}
        for row in releases:
            release_by_group[row.demand_group_id] = release_by_group.get(row.demand_group_id, 0) + row.released_qty
        issues: list[PlanningValidationResult] = []
        for group in self.repository.list_demand_groups_in_shift(tenant_id, shift.id):
            assigned_count = sum(1 for row in assignments if row.demand_group_id == group.id)
            released_count = release_by_group.get(group.id, 0)
            if assigned_count + released_count < group.min_qty:
                issues.append(
                    self._issue(
                        tenant_id,
                        "minimum_staffing",
                        shift,
                        group,
                        None,
                        None,
                        metadata={
                            "assigned_count": assigned_count,
                            "released_partner_qty": released_count,
                            "required_min_qty": group.min_qty,
                        },
                    )
                )
        return issues

    def _customer_id_for_shift(self, tenant_id: str, shift: Shift) -> str | None:
        shift_plan = getattr(shift, "shift_plan", None)
        if shift_plan is None:
            return None
        planning_record = getattr(shift_plan, "planning_record", None)
        if planning_record is None:
            planning_record = None
        if planning_record is None:
            return None
        order = getattr(planning_record, "order", None)
        return getattr(order, "customer_id", None)

    def _apply_overrides(
        self,
        tenant_id: str,
        assignment_id: str | None,
        issues: list[PlanningValidationResult],
    ) -> list[PlanningValidationResult]:
        if assignment_id is None:
            return issues
        overridden = {row.rule_code for row in self.repository.list_assignment_validation_overrides(tenant_id, assignment_id)}
        result: list[PlanningValidationResult] = []
        for issue in issues:
            if issue.rule_code in overridden and issue.override_allowed and issue.severity == "block":
                result.append(issue.model_copy(update={"severity": "warn", "metadata": issue.metadata | {"overridden": True}}))
            else:
                result.append(issue)
        return result

    def _assignment_result(self, tenant_id: str, assignment_id: str, shift_id: str, issues: list[PlanningValidationResult]) -> AssignmentValidationRead:
        return AssignmentValidationRead(
            tenant_id=tenant_id,
            assignment_id=assignment_id,
            shift_id=shift_id,
            blocking_count=sum(1 for issue in issues if issue.severity == "block"),
            warning_count=sum(1 for issue in issues if issue.severity == "warn"),
            info_count=sum(1 for issue in issues if issue.severity == "info"),
            issues=issues,
        )

    def _issue(
        self,
        tenant_id: str,
        rule_code: str,
        shift: Shift,
        demand_group: DemandGroup | None,
        actor: ValidationActor | None,
        assignment_id: str | None,
        *,
        metadata: dict[str, object] | None = None,
    ) -> PlanningValidationResult:
        policy = self.policy_for(tenant_id, rule_code)
        severity = policy.severity if policy.enabled else "info"
        return PlanningValidationResult(
            rule_code=rule_code,
            severity=severity,
            message_key=f"errors.planning.validation.{rule_code}",
            actor_type=actor.actor_type if actor else None,
            actor_id=actor.actor_id if actor else None,
            assignment_id=assignment_id,
            shift_id=shift.id,
            demand_group_id=demand_group.id if demand_group else None,
            source_refs={
                "shift_id": shift.id,
                "demand_group_id": demand_group.id if demand_group else None,
                "actor_type": actor.actor_type if actor else None,
                "actor_id": actor.actor_id if actor else None,
            },
            policy_code=self.POLICY_KEY,
            override_allowed=policy.override_allowed and severity == "block",
            metadata=metadata or {},
        )

    @staticmethod
    def _is_active_window(row, shift: Shift) -> bool:  # noqa: ANN001
        if getattr(row, "archived_at", None) is not None:
            return False
        valid_until = getattr(row, "valid_until", None)
        if valid_until is not None and valid_until < shift.starts_at.date():
            return False
        status = getattr(row, "status", "active")
        return status == "active"

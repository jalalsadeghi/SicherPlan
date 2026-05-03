"""Service layer for planning staffing entities, board commands, releases, and coverage."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import UUID

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import Assignment, AssignmentValidationOverride, DemandGroup, Shift, SubcontractorRelease, Team, TeamMember
from app.modules.planning.schemas import (
    AssignmentStepApplyItemResult,
    AssignmentStepApplyRequest,
    AssignmentStepApplyResult,
    AssignmentStepCandidateDayStatusRead,
    AssignmentStepCandidateQueryResult,
    AssignmentStepCandidateRead,
    AssignmentStepCellRead,
    AssignmentStepDaySummaryRead,
    AssignmentStepDemandGroupMatch,
    AssignmentStepDemandGroupSummaryRead,
    AssignmentStepExistingAssignmentRead,
    AssignmentStepOrderSummaryRead,
    AssignmentStepScopeRequest,
    AssignmentStepShiftPlanSummaryRead,
    AssignmentStepSnapshotRead,
    AssignmentValidationOverrideCreate,
    AssignmentValidationOverrideRead,
    AssignmentValidationRead,
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    CoverageDemandGroupItem,
    CoverageFilter,
    CoverageShiftItem,
    DemandGroupBulkApplyRequest,
    DemandGroupBulkApplyResult,
    DemandGroupBulkApplyShiftResult,
    DemandGroupBulkTemplate,
    DemandGroupBulkUpdateItemResult,
    DemandGroupBulkUpdatePatch,
    DemandGroupBulkUpdateRequest,
    DemandGroupBulkUpdateResult,
    DemandGroupCreate,
    DemandGroupRead,
    DemandGroupUpdate,
    PlanningRecordReleaseValidationRead,
    PlanningValidationResult,
    StaffingAssignCommand,
    StaffingBoardAssignmentItem,
    StaffingBoardDemandGroupItem,
    StaffingBoardFilter,
    StaffingBoardShiftItem,
    StaffingCommandResult,
    StaffingFilter,
    StaffingSubstituteCommand,
    StaffingUnassignCommand,
    SubcontractorReleaseCreate,
    SubcontractorReleaseRead,
    SubcontractorReleaseUpdate,
    TeamCreate,
    TeamMemberCreate,
    TeamMemberRead,
    TeamMemberUpdate,
    TeamRead,
    TeamUpdate,
    ShiftListFilter,
    ShiftReleaseValidationRead,
)
from app.modules.planning.validation_service import PlanningValidationService


class StaffingRepository(Protocol):
    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None: ...
    def list_shifts_by_ids(self, tenant_id: str, shift_ids: list[str]) -> list[Shift]: ...
    def get_shift_plan(self, tenant_id: str, row_id: str): ...
    def get_customer_order(self, tenant_id: str, order_id: str): ...
    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Shift]: ...
    def list_employees(self, tenant_id: str) -> list[object]: ...
    def list_subcontractor_workers(self, tenant_id: str) -> list[object]: ...
    def list_board_shifts(self, tenant_id: str, filters: StaffingBoardFilter) -> list[dict[str, object]]: ...
    def get_function_type(self, tenant_id: str, function_type_id: str): ...
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str): ...
    def get_planning_record(self, tenant_id: str, planning_record_id: str): ...
    def get_employee(self, tenant_id: str, employee_id: str): ...
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str): ...
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str): ...
    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter) -> list[DemandGroup]: ...
    def list_demand_groups_for_shifts(self, tenant_id: str, shift_ids: list[str], *, include_archived: bool = False) -> list[DemandGroup]: ...
    def get_demand_group(self, tenant_id: str, row_id: str) -> DemandGroup | None: ...
    def create_demand_group(self, tenant_id: str, payload: DemandGroupCreate, actor_user_id: str | None) -> DemandGroup: ...
    def update_demand_group(self, tenant_id: str, row_id: str, payload: DemandGroupUpdate, actor_user_id: str | None) -> DemandGroup | None: ...
    def bulk_update_demand_groups(self, tenant_id: str, updates: list[tuple[str, DemandGroupUpdate]], actor_user_id: str | None) -> list[DemandGroup]: ...
    def list_teams(self, tenant_id: str, filters: StaffingFilter) -> list[Team]: ...
    def get_team(self, tenant_id: str, row_id: str) -> Team | None: ...
    def create_team(self, tenant_id: str, payload: TeamCreate, actor_user_id: str | None) -> Team: ...
    def update_team(self, tenant_id: str, row_id: str, payload: TeamUpdate, actor_user_id: str | None) -> Team | None: ...
    def list_team_members(self, tenant_id: str, filters: StaffingFilter) -> list[TeamMember]: ...
    def get_team_member(self, tenant_id: str, row_id: str) -> TeamMember | None: ...
    def create_team_member(self, tenant_id: str, payload: TeamMemberCreate, actor_user_id: str | None) -> TeamMember: ...
    def update_team_member(self, tenant_id: str, row_id: str, payload: TeamMemberUpdate, actor_user_id: str | None) -> TeamMember | None: ...
    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[Assignment]: ...
    def get_assignment(self, tenant_id: str, row_id: str) -> Assignment | None: ...
    def create_assignment(self, tenant_id: str, payload: AssignmentCreate, actor_user_id: str | None) -> Assignment: ...
    def update_assignment(self, tenant_id: str, row_id: str, payload: AssignmentUpdate, actor_user_id: str | None) -> Assignment | None: ...
    def list_subcontractor_releases(self, tenant_id: str, filters: StaffingFilter) -> list[SubcontractorRelease]: ...
    def get_subcontractor_release(self, tenant_id: str, row_id: str) -> SubcontractorRelease | None: ...
    def create_subcontractor_release(self, tenant_id: str, payload: SubcontractorReleaseCreate, actor_user_id: str | None) -> SubcontractorRelease: ...
    def update_subcontractor_release(self, tenant_id: str, row_id: str, payload: SubcontractorReleaseUpdate, actor_user_id: str | None) -> SubcontractorRelease | None: ...
    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str) -> list[AssignmentValidationOverride]: ...
    def create_assignment_validation_override(self, row: AssignmentValidationOverride) -> AssignmentValidationOverride: ...
    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None: ...
    def list_employee_qualifications(self, tenant_id: str, employee_id: str) -> list[object]: ...
    def list_employee_qualifications_for_employees(self, tenant_id: str, employee_ids: list[str]) -> list[object]: ...
    def list_employee_absences(self, tenant_id: str, employee_id: str) -> list[object]: ...
    def list_employee_absences_for_employees(self, tenant_id: str, employee_ids: list[str]) -> list[object]: ...
    def list_employee_availability_rules(self, tenant_id: str, employee_id: str) -> list[object]: ...
    def list_employee_availability_rules_for_employees(self, tenant_id: str, employee_ids: list[str]) -> list[object]: ...
    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[object]: ...
    def list_worker_qualifications_for_workers(self, tenant_id: str, worker_ids: list[str]) -> list[object]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...
    def list_documents_for_owners(self, tenant_id: str, owner_type: str, owner_ids: list[str]) -> list[object]: ...
    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date): ...  # noqa: ANN001
    def list_customer_employee_blocks_for_customer(self, tenant_id: str, customer_id: str, employee_ids: list[str], *, date_from: date, date_to: date) -> list[object]: ...
    def list_overlapping_assignments(self, tenant_id: str, *, starts_at: datetime, ends_at: datetime, employee_id: str | None, subcontractor_worker_id: str | None, exclude_assignment_id: str | None = None) -> list[Assignment]: ...
    def list_assignments_for_actor_in_window(self, tenant_id: str, *, employee_id: str | None, subcontractor_worker_id: str | None, window_start: datetime, window_end: datetime, exclude_assignment_id: str | None = None) -> list[Assignment]: ...
    def list_assignments_for_actors_in_window(self, tenant_id: str, *, employee_ids: list[str], subcontractor_worker_ids: list[str], window_start: datetime, window_end: datetime) -> list[Assignment]: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Assignment]: ...
    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[DemandGroup]: ...
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[SubcontractorRelease]: ...
    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[Shift]: ...
    def list_team_members_for_actors(self, tenant_id: str, *, employee_ids: list[str], subcontractor_worker_ids: list[str], include_archived: bool = False) -> list[TeamMember]: ...


@dataclass(frozen=True)
class _ActorChoice:
    employee_id: str | None
    subcontractor_worker_id: str | None


@dataclass(frozen=True)
class _AssignmentStepTarget:
    shift: Shift
    demand_group: DemandGroup


class _CachedAssignmentStepRepository:
    def __init__(self, base: StaffingRepository) -> None:
        self._base = base
        self._cache: dict[tuple[object, ...], object] = {}
        self._preloaded_shifts: dict[str, Shift] = {}
        self._preloaded_team_members: dict[tuple[str, str], list[TeamMember]] = {}
        self._preloaded_employee_qualifications: dict[str, list[object]] = {}
        self._preloaded_employee_absences: dict[str, list[object]] = {}
        self._preloaded_employee_availability_rules: dict[str, list[object]] = {}
        self._preloaded_worker_qualifications: dict[str, list[object]] = {}
        self._preloaded_documents: dict[tuple[str, str], list[object]] = {}
        self._preloaded_customer_blocks: dict[tuple[str, str], list[object]] = {}
        self._preloaded_actor_assignments: dict[tuple[str, str], list[Assignment]] = {}

    def _memoize_call(self, key: tuple[object, ...], fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def prime_candidate_context(
        self,
        tenant_id: str,
        *,
        employee_ids: list[str],
        worker_ids: list[str],
        customer_id: str | None,
        window_start: datetime,
        window_end: datetime,
        known_shifts: list[Shift],
    ) -> None:
        for shift in known_shifts:
            self._preloaded_shifts[shift.id] = shift
        for employee_id in employee_ids:
            self._preloaded_employee_qualifications.setdefault(employee_id, [])
            self._preloaded_employee_absences.setdefault(employee_id, [])
            self._preloaded_employee_availability_rules.setdefault(employee_id, [])
            self._preloaded_customer_blocks.setdefault((customer_id or "", employee_id), [])
            self._preloaded_actor_assignments.setdefault(("employee", employee_id), [])
        for worker_id in worker_ids:
            self._preloaded_worker_qualifications.setdefault(worker_id, [])
            self._preloaded_actor_assignments.setdefault(("subcontractor_worker", worker_id), [])

        for row in self._base.list_employee_qualifications_for_employees(tenant_id, employee_ids):
            self._preloaded_employee_qualifications.setdefault(row.employee_id, []).append(row)

        for row in self._base.list_employee_absences_for_employees(tenant_id, employee_ids):
            self._preloaded_employee_absences.setdefault(row.employee_id, []).append(row)

        for row in self._base.list_employee_availability_rules_for_employees(tenant_id, employee_ids):
            self._preloaded_employee_availability_rules.setdefault(row.employee_id, []).append(row)

        for row in self._base.list_worker_qualifications_for_workers(tenant_id, worker_ids):
            worker_id = getattr(row, "worker_id", None) or getattr(row, "subcontractor_worker_id", None)
            if worker_id is not None:
                self._preloaded_worker_qualifications.setdefault(worker_id, []).append(row)

        employee_owner_ids = [
            row.id
            for rows in self._preloaded_employee_qualifications.values()
            for row in rows
            if getattr(row, "record_kind", None) == "qualification"
        ]
        for document in self._base.list_documents_for_owners(
            tenant_id,
            "hr.employee_qualification",
            employee_owner_ids,
        ):
            for link in getattr(document, "links", []) or []:
                if getattr(link, "owner_type", None) == "hr.employee_qualification":
                    self._preloaded_documents.setdefault(("hr.employee_qualification", link.owner_id), []).append(document)

        worker_owner_ids = [
            row.id
            for rows in self._preloaded_worker_qualifications.values()
            for row in rows
        ]
        for document in self._base.list_documents_for_owners(
            tenant_id,
            "partner.subcontractor_worker_qualification",
            worker_owner_ids,
        ):
            for link in getattr(document, "links", []) or []:
                if getattr(link, "owner_type", None) == "partner.subcontractor_worker_qualification":
                    self._preloaded_documents.setdefault(("partner.subcontractor_worker_qualification", link.owner_id), []).append(document)

        if customer_id is not None and employee_ids:
            for row in self._base.list_customer_employee_blocks_for_customer(
                tenant_id,
                customer_id,
                employee_ids,
                date_from=window_start.date(),
                date_to=window_end.date(),
            ):
                self._preloaded_customer_blocks.setdefault((customer_id, row.employee_id), []).append(row)

        actor_assignments = self._base.list_assignments_for_actors_in_window(
            tenant_id,
            employee_ids=employee_ids,
            subcontractor_worker_ids=worker_ids,
            window_start=window_start,
            window_end=window_end,
        )
        extra_shift_ids: set[str] = set()
        for row in actor_assignments:
            if row.employee_id is not None:
                self._preloaded_actor_assignments.setdefault(("employee", row.employee_id), []).append(row)
            if row.subcontractor_worker_id is not None:
                self._preloaded_actor_assignments.setdefault(("subcontractor_worker", row.subcontractor_worker_id), []).append(row)
            if row.shift_id not in self._preloaded_shifts:
                extra_shift_ids.add(row.shift_id)
        for shift in self._base.list_shifts_by_ids(tenant_id, sorted(extra_shift_ids)):
            self._preloaded_shifts[shift.id] = shift

    def get_shift(self, tenant_id: str, row_id: str):
        if row_id in self._preloaded_shifts:
            return self._preloaded_shifts[row_id]
        key = ("get_shift", tenant_id, row_id)
        return self._memoize_call(key, lambda: self._base.get_shift(tenant_id, row_id))

    def get_employee(self, tenant_id: str, employee_id: str):
        key = ("get_employee", tenant_id, employee_id)
        return self._memoize_call(key, lambda: self._base.get_employee(tenant_id, employee_id))

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str):
        key = ("get_subcontractor_worker", tenant_id, worker_id)
        return self._memoize_call(key, lambda: self._base.get_subcontractor_worker(tenant_id, worker_id))

    def get_demand_group(self, tenant_id: str, row_id: str):
        key = ("get_demand_group", tenant_id, row_id)
        return self._memoize_call(key, lambda: self._base.get_demand_group(tenant_id, row_id))

    def get_tenant_setting_value(self, tenant_id: str, key_name: str):
        key = ("get_tenant_setting_value", tenant_id, key_name)
        return self._memoize_call(key, lambda: self._base.get_tenant_setting_value(tenant_id, key_name))

    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter):
        key = ("list_demand_groups", tenant_id, filters.model_dump_json())
        return self._memoize_call(key, lambda: self._base.list_demand_groups(tenant_id, filters))

    def list_employee_qualifications(self, tenant_id: str, employee_id: str):
        if employee_id in self._preloaded_employee_qualifications:
            return self._preloaded_employee_qualifications[employee_id]
        key = ("list_employee_qualifications", tenant_id, employee_id)
        return self._memoize_call(key, lambda: self._base.list_employee_qualifications(tenant_id, employee_id))

    def list_employee_absences(self, tenant_id: str, employee_id: str):
        if employee_id in self._preloaded_employee_absences:
            return self._preloaded_employee_absences[employee_id]
        key = ("list_employee_absences", tenant_id, employee_id)
        return self._memoize_call(key, lambda: self._base.list_employee_absences(tenant_id, employee_id))

    def list_employee_availability_rules(self, tenant_id: str, employee_id: str):
        if employee_id in self._preloaded_employee_availability_rules:
            return self._preloaded_employee_availability_rules[employee_id]
        key = ("list_employee_availability_rules", tenant_id, employee_id)
        return self._memoize_call(key, lambda: self._base.list_employee_availability_rules(tenant_id, employee_id))

    def list_worker_qualifications(self, tenant_id: str, worker_id: str):
        if worker_id in self._preloaded_worker_qualifications:
            return self._preloaded_worker_qualifications[worker_id]
        key = ("list_worker_qualifications", tenant_id, worker_id)
        return self._memoize_call(key, lambda: self._base.list_worker_qualifications(tenant_id, worker_id))

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        preloaded_key = (owner_type, owner_id)
        if preloaded_key in self._preloaded_documents:
            return self._preloaded_documents[preloaded_key]
        key = ("list_documents_for_owner", tenant_id, owner_type, owner_id)
        return self._memoize_call(key, lambda: self._base.list_documents_for_owner(tenant_id, owner_type, owner_id))

    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date):
        preloaded_key = (customer_id, employee_id)
        if preloaded_key in self._preloaded_customer_blocks:
            return [
                row
                for row in self._preloaded_customer_blocks[preloaded_key]
                if getattr(row, "effective_from", on_date) <= on_date
                and (getattr(row, "effective_to", None) is None or getattr(row, "effective_to", None) >= on_date)
            ]
        key = ("list_customer_employee_blocks", tenant_id, customer_id, employee_id, on_date)
        return self._memoize_call(
            key,
            lambda: self._base.list_customer_employee_blocks(tenant_id, customer_id, employee_id, on_date),
        )

    def list_overlapping_assignments(
        self,
        tenant_id: str,
        *,
        starts_at: datetime,
        ends_at: datetime,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        exclude_assignment_id: str | None = None,
    ):
        key = (
            "list_overlapping_assignments",
            tenant_id,
            starts_at,
            ends_at,
            employee_id,
            subcontractor_worker_id,
            exclude_assignment_id,
        )
        actor_key = ("employee", employee_id) if employee_id is not None else ("subcontractor_worker", subcontractor_worker_id or "")
        if actor_key in self._preloaded_actor_assignments:
            return [
                row
                for row in self._preloaded_actor_assignments[actor_key]
                if (exclude_assignment_id is None or row.id != exclude_assignment_id)
                and (shift := self.get_shift(tenant_id, row.shift_id)) is not None
                and getattr(shift, "archived_at", None) is None
                and shift.starts_at < ends_at
                and shift.ends_at > starts_at
            ]
        return self._memoize_call(
            key,
            lambda: self._base.list_overlapping_assignments(
                tenant_id,
                starts_at=starts_at,
                ends_at=ends_at,
                employee_id=employee_id,
                subcontractor_worker_id=subcontractor_worker_id,
                exclude_assignment_id=exclude_assignment_id,
            ),
        )

    def list_assignments_for_actor_in_window(
        self,
        tenant_id: str,
        *,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        window_start: datetime,
        window_end: datetime,
        exclude_assignment_id: str | None = None,
    ):
        key = (
            "list_assignments_for_actor_in_window",
            tenant_id,
            employee_id,
            subcontractor_worker_id,
            window_start,
            window_end,
            exclude_assignment_id,
        )
        actor_key = ("employee", employee_id) if employee_id is not None else ("subcontractor_worker", subcontractor_worker_id or "")
        if actor_key in self._preloaded_actor_assignments:
            return [
                row
                for row in self._preloaded_actor_assignments[actor_key]
                if (exclude_assignment_id is None or row.id != exclude_assignment_id)
                and (shift := self.get_shift(tenant_id, row.shift_id)) is not None
                and getattr(shift, "archived_at", None) is None
                and shift.starts_at < window_end
                and shift.ends_at > window_start
            ]
        return self._memoize_call(
            key,
            lambda: self._base.list_assignments_for_actor_in_window(
                tenant_id,
                employee_id=employee_id,
                subcontractor_worker_id=subcontractor_worker_id,
                window_start=window_start,
                window_end=window_end,
                exclude_assignment_id=exclude_assignment_id,
            ),
        )

    def list_team_members(self, tenant_id: str, filters: StaffingFilter):
        if filters.employee_id is not None:
            return [
                row
                for row in self._preloaded_team_members.get(("employee", filters.employee_id), [])
                if filters.include_archived or getattr(row, "archived_at", None) is None
                if filters.team_id is None or row.team_id == filters.team_id
            ]
        if filters.subcontractor_worker_id is not None:
            return [
                row
                for row in self._preloaded_team_members.get(("subcontractor_worker", filters.subcontractor_worker_id), [])
                if filters.include_archived or getattr(row, "archived_at", None) is None
                if filters.team_id is None or row.team_id == filters.team_id
            ]
        key = ("list_team_members", tenant_id, filters.model_dump_json())
        return self._memoize_call(key, lambda: self._base.list_team_members(tenant_id, filters))

    def __getattr__(self, name: str):
        return getattr(self._base, name)


class StaffingService:
    ASSIGNMENT_STATUSES = frozenset({"offered", "assigned", "confirmed", "removed"})
    ASSIGNMENT_SOURCES = frozenset({"dispatcher", "subcontractor_release", "portal_allocation", "manual"})
    RELEASE_STATUSES = frozenset({"draft", "released", "revoked"})
    _SKIP_SNAPSHOT_VALUE = object()

    def __init__(self, repository: StaffingRepository, *, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service
        self.validation_service = PlanningValidationService(repository)

    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[DemandGroupRead]:
        return [self._read_demand_group(tenant_id, row) for row in self.repository.list_demand_groups(tenant_id, filters)]

    def get_demand_group(self, tenant_id: str, demand_group_id: str, _actor: RequestAuthorizationContext) -> DemandGroupRead:
        return self._read_demand_group(tenant_id, self._require_demand_group(tenant_id, demand_group_id))

    def create_demand_group(self, tenant_id: str, payload: DemandGroupCreate, actor: RequestAuthorizationContext) -> DemandGroupRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift = self._require_shift(tenant_id, payload.shift_id)
        self._validate_demand_group(payload.min_qty, payload.target_qty)
        self._require_function(tenant_id, payload.function_type_id)
        if payload.qualification_type_id is not None:
            self._require_qualification(tenant_id, payload.qualification_type_id)
        row = self.repository.create_demand_group(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.demand_group.created", "ops.demand_group", row.id, tenant_id, after_json=self._snapshot(row) | {"shift_plan_id": shift.shift_plan_id})
        return self._read_demand_group(tenant_id, row)

    def bulk_apply_demand_groups(
        self,
        tenant_id: str,
        payload: DemandGroupBulkApplyRequest,
        actor: RequestAuthorizationContext,
    ) -> DemandGroupBulkApplyResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        if payload.apply_mode not in {"create_missing", "upsert_matching"}:
            raise ApiException(400, "planning.demand_group.bulk_apply.invalid_mode", "errors.planning.demand_group.bulk_apply.invalid_mode")
        if payload.date_from is not None and payload.date_to is not None and payload.date_to < payload.date_from:
            raise ApiException(400, "planning.demand_group.bulk_apply.invalid_date_window", "errors.planning.demand_group.bulk_apply.invalid_date_window")

        shift_plan = self._require_shift_plan(tenant_id, payload.shift_plan_id)
        if payload.shift_series_id is not None and all(series.id != payload.shift_series_id for series in getattr(shift_plan, "series_rows", [])):
            raise ApiException(404, "planning.shift_series.not_found", "errors.planning.shift_series.not_found")

        normalized_templates = self._normalize_bulk_templates(payload.demand_groups)
        for template in normalized_templates:
            self._validate_demand_group(template.min_qty, template.target_qty)
            self._require_function(tenant_id, template.function_type_id)
            if template.qualification_type_id is not None:
                self._require_qualification(tenant_id, template.qualification_type_id)

        candidate_shifts = self.repository.list_shifts(
            tenant_id,
            ShiftListFilter(shift_plan_id=payload.shift_plan_id, include_archived=False),
        )
        target_shifts = [
            shift
            for shift in candidate_shifts
            if shift.source_kind_code == "generated"
            and (payload.shift_series_id is None or shift.shift_series_id == payload.shift_series_id)
            and self._shift_in_bulk_date_window(shift, payload.date_from, payload.date_to)
        ]
        if not target_shifts:
            raise ApiException(
                404,
                "planning.demand_group.bulk_apply.no_target_shifts",
                "errors.planning.demand_group.bulk_apply.no_target_shifts",
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        affected_ids: list[str] = []
        shift_results: list[DemandGroupBulkApplyShiftResult] = []

        for shift in target_shifts:
            shift_created_count = 0
            shift_updated_count = 0
            shift_skipped_count = 0
            existing_groups = self.repository.list_demand_groups(
                tenant_id,
                StaffingFilter(shift_id=shift.id, include_archived=True),
            )
            existing_by_sort = {group.sort_order: group for group in existing_groups}
            for template in normalized_templates:
                matching_group = existing_by_sort.get(template.sort_order)
                if matching_group is None:
                    row = self.repository.create_demand_group(
                        tenant_id,
                        DemandGroupCreate(
                            tenant_id=tenant_id,
                            shift_id=shift.id,
                            function_type_id=template.function_type_id,
                            qualification_type_id=template.qualification_type_id,
                            min_qty=template.min_qty,
                            target_qty=template.target_qty,
                            mandatory_flag=template.mandatory_flag,
                            sort_order=template.sort_order,
                            remark=template.remark,
                        ),
                        actor.user_id,
                    )
                    created_count += 1
                    shift_created_count += 1
                    affected_ids.append(row.id)
                    existing_by_sort[row.sort_order] = row
                    self._record_event(
                        actor,
                        "planning.demand_group.created",
                        "ops.demand_group",
                        row.id,
                        tenant_id,
                        after_json=self._snapshot(row) | {"shift_plan_id": shift.shift_plan_id},
                    )
                    continue

                if payload.apply_mode == "create_missing":
                    skipped_count += 1
                    shift_skipped_count += 1
                    continue

                before_json = self._snapshot(matching_group)
                row = self.repository.update_demand_group(
                    tenant_id,
                    matching_group.id,
                    DemandGroupUpdate(
                        function_type_id=template.function_type_id,
                        qualification_type_id=template.qualification_type_id,
                        min_qty=template.min_qty,
                        target_qty=template.target_qty,
                        mandatory_flag=template.mandatory_flag,
                        sort_order=template.sort_order,
                        remark=template.remark,
                        status="active",
                        archived_at=None,
                        version_no=matching_group.version_no,
                    ),
                    actor.user_id,
                )
                if row is None:
                    raise self._not_found("demand_group")
                updated_count += 1
                shift_updated_count += 1
                affected_ids.append(row.id)
                existing_by_sort[row.sort_order] = row
                self._record_event(
                    actor,
                    "planning.demand_group.updated",
                    "ops.demand_group",
                    row.id,
                    tenant_id,
                    before_json=before_json,
                    after_json=self._snapshot(row) | {"shift_plan_id": shift.shift_plan_id},
                )
            shift_results.append(
                DemandGroupBulkApplyShiftResult(
                    shift_id=shift.id,
                    created_count=shift_created_count,
                    updated_count=shift_updated_count,
                    skipped_count=shift_skipped_count,
                )
            )

        return DemandGroupBulkApplyResult(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            apply_mode=payload.apply_mode,
            target_shift_count=len(target_shifts),
            template_count=len(normalized_templates),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            affected_demand_group_ids=affected_ids,
            results=shift_results,
        )

    def bulk_update_demand_groups(
        self,
        tenant_id: str,
        payload: DemandGroupBulkUpdateRequest,
        actor: RequestAuthorizationContext,
    ) -> DemandGroupBulkUpdateResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        if payload.date_from is not None and payload.date_to is not None and payload.date_to < payload.date_from:
            raise ApiException(400, "planning.demand_group.bulk_update.invalid_date_window", "errors.planning.demand_group.bulk_update.invalid_date_window")
        if not payload.patch.model_fields_set:
            raise ApiException(
                400,
                "planning.demand_group.bulk_update.empty_patch",
                "errors.planning.demand_group.bulk_update.empty_patch",
                details={"reason_codes": ["empty_patch"]},
            )

        shift_plan = self._require_shift_plan(tenant_id, payload.shift_plan_id)
        if payload.shift_series_id is not None and all(series.id != payload.shift_series_id for series in getattr(shift_plan, "series_rows", [])):
            raise ApiException(404, "planning.shift_series.not_found", "errors.planning.shift_series.not_found")

        if payload.match.target_qty is not None:
            self._validate_demand_group(payload.match.min_qty or 0, payload.match.target_qty)
        self._validate_bulk_update_patch(tenant_id, payload.patch)

        target_shifts = self._resolve_bulk_target_shifts(
            tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        if payload.expected_target_shift_count is not None and payload.expected_target_shift_count != len(target_shifts):
            raise ApiException(
                409,
                "planning.demand_group.bulk_update.target_shift_mismatch",
                "errors.planning.demand_group.bulk_update.target_shift_mismatch",
                details={
                    "reason_codes": ["target_shift_mismatch"],
                    "expected_target_shift_count": payload.expected_target_shift_count,
                    "current_target_shift_count": len(target_shifts),
                },
            )

        matched_groups = self._collect_matching_demand_groups(tenant_id, target_shifts, payload.match)
        if not matched_groups:
            raise ApiException(
                404,
                "planning.demand_group.bulk_update.no_matching_demand_groups",
                "errors.planning.demand_group.bulk_update.no_matching_demand_groups",
                details={"reason_codes": ["no_matching_demand_groups"]},
            )

        if payload.expected_demand_group_ids is not None:
            expected_ids = sorted(payload.expected_demand_group_ids)
            current_ids = sorted(group.id for group in matched_groups)
            if current_ids != expected_ids:
                raise ApiException(
                    409,
                    "planning.demand_group.bulk_update.expected_set_mismatch",
                    "errors.planning.demand_group.bulk_update.expected_set_mismatch",
                    details={
                        "reason_codes": ["expected_demand_group_ids_mismatch"],
                        "expected_demand_group_ids": expected_ids,
                        "current_demand_group_ids": current_ids,
                    },
                )

        self._assert_demand_group_groups_editable(tenant_id, matched_groups)
        self._validate_bulk_update_sort_order_conflicts(tenant_id, matched_groups, payload.patch)

        updates: list[tuple[str, DemandGroupUpdate]] = []
        item_results: list[DemandGroupBulkUpdateItemResult] = []
        before_snapshots: dict[str, dict[str, object]] = {}
        shift_plan_ids: dict[str, str] = {}
        for group in matched_groups:
            before_snapshots[group.id] = self._snapshot(group)
            shift = self._require_shift(tenant_id, group.shift_id)
            shift_plan_ids[group.id] = shift.shift_plan_id
            next_min_qty = self._field_value(payload.patch, "min_qty", group.min_qty)
            next_target_qty = self._field_value(payload.patch, "target_qty", group.target_qty)
            self._validate_demand_group(next_min_qty, next_target_qty)
            update_payload = payload.patch.model_dump(exclude_unset=True)
            update_payload["version_no"] = group.version_no
            updates.append(
                (
                    group.id,
                    DemandGroupUpdate(**update_payload),
                )
            )
            item_results.append(
                DemandGroupBulkUpdateItemResult(
                    demand_group_id=group.id,
                    shift_id=group.shift_id,
                    outcome_code="updated",
                )
            )

        rows = self.repository.bulk_update_demand_groups(tenant_id, updates, actor.user_id)
        updated_ids = [row.id for row in rows]
        for row in rows:
            self._record_event(
                actor,
                "planning.demand_group.bulk_updated",
                "ops.demand_group",
                row.id,
                tenant_id,
                before_json=before_snapshots[row.id],
                after_json=self._snapshot(row) | {"shift_plan_id": shift_plan_ids[row.id]},
            )

        return DemandGroupBulkUpdateResult(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            matched_count=len(matched_groups),
            updated_count=len(rows),
            skipped_count=0,
            conflict_count=0,
            updated_demand_group_ids=updated_ids,
            results=item_results,
        )

    def update_demand_group(self, tenant_id: str, demand_group_id: str, payload: DemandGroupUpdate, actor: RequestAuthorizationContext) -> DemandGroupRead:
        current = self._require_demand_group(tenant_id, demand_group_id)
        before_json = self._snapshot(current)
        self._assert_demand_group_groups_editable(tenant_id, [current])
        min_qty = self._field_value(payload, "min_qty", current.min_qty)
        target_qty = self._field_value(payload, "target_qty", current.target_qty)
        self._validate_demand_group(min_qty, target_qty)
        function_type_id = self._field_value(payload, "function_type_id", current.function_type_id)
        qualification_type_id = self._field_value(payload, "qualification_type_id", current.qualification_type_id)
        self._require_function(tenant_id, function_type_id)
        if qualification_type_id is not None:
            self._require_qualification(tenant_id, qualification_type_id)
        row = self.repository.update_demand_group(tenant_id, demand_group_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("demand_group")
        self._record_event(actor, "planning.demand_group.updated", "ops.demand_group", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read_demand_group(tenant_id, row)

    def list_teams(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[TeamRead]:
        return [self._read_team(row) for row in self.repository.list_teams(tenant_id, filters)]

    def get_team(self, tenant_id: str, team_id: str, _actor: RequestAuthorizationContext) -> TeamRead:
        return self._read_team(self._require_team(tenant_id, team_id))

    def create_team(self, tenant_id: str, payload: TeamCreate, actor: RequestAuthorizationContext) -> TeamRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        self._validate_team_scope(tenant_id, payload.planning_record_id, payload.shift_id)
        row = self.repository.create_team(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.team.created", "ops.team", row.id, tenant_id, after_json=self._snapshot(row))
        return self._read_team(self._require_team(tenant_id, row.id))

    def update_team(self, tenant_id: str, team_id: str, payload: TeamUpdate, actor: RequestAuthorizationContext) -> TeamRead:
        current = self._require_team(tenant_id, team_id)
        before_json = self._snapshot(current)
        planning_record_id = self._field_value(payload, "planning_record_id", current.planning_record_id)
        shift_id = self._field_value(payload, "shift_id", current.shift_id)
        self._validate_team_scope(tenant_id, planning_record_id, shift_id)
        row = self.repository.update_team(tenant_id, team_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("team")
        self._record_event(actor, "planning.team.updated", "ops.team", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read_team(self._require_team(tenant_id, team_id))

    def list_team_members(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[TeamMemberRead]:
        return [TeamMemberRead.model_validate(row) for row in self.repository.list_team_members(tenant_id, filters)]

    def create_team_member(self, tenant_id: str, payload: TeamMemberCreate, actor: RequestAuthorizationContext) -> TeamMemberRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        team = self._require_team(tenant_id, payload.team_id)
        choice = self._validate_actor_choice(payload.employee_id, payload.subcontractor_worker_id, code_prefix="planning.team_member")
        self._validate_team_member_actor(tenant_id, choice, team)
        self._validate_team_member_window(payload.valid_from, payload.valid_to)
        self._validate_team_lead(tenant_id, payload.team_id, payload.is_team_lead, None)
        row = self.repository.create_team_member(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.team_member.created", "ops.team_member", row.id, tenant_id, after_json=self._snapshot(row))
        return TeamMemberRead.model_validate(row)

    def update_team_member(self, tenant_id: str, team_member_id: str, payload: TeamMemberUpdate, actor: RequestAuthorizationContext) -> TeamMemberRead:
        current = self._require_team_member(tenant_id, team_member_id)
        team = self._require_team(tenant_id, current.team_id)
        before_json = self._snapshot(current)
        choice = self._validate_actor_choice(
            self._field_value(payload, "employee_id", current.employee_id),
            self._field_value(payload, "subcontractor_worker_id", current.subcontractor_worker_id),
            code_prefix="planning.team_member",
        )
        self._validate_team_member_actor(tenant_id, choice, team)
        valid_from = self._field_value(payload, "valid_from", current.valid_from)
        valid_to = self._field_value(payload, "valid_to", current.valid_to)
        self._validate_team_member_window(valid_from, valid_to)
        self._validate_team_lead(
            tenant_id,
            current.team_id,
            self._field_value(payload, "is_team_lead", current.is_team_lead),
            exclude_member_id=team_member_id,
        )
        row = self.repository.update_team_member(tenant_id, team_member_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("team_member")
        self._record_event(actor, "planning.team_member.updated", "ops.team_member", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return TeamMemberRead.model_validate(row)

    def list_assignments(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[AssignmentRead]:
        return [AssignmentRead.model_validate(row) for row in self.repository.list_assignments(tenant_id, filters)]

    def get_assignment(self, tenant_id: str, assignment_id: str, _actor: RequestAuthorizationContext) -> AssignmentRead:
        return AssignmentRead.model_validate(self._require_assignment(tenant_id, assignment_id))

    def get_assignment_validations(self, tenant_id: str, assignment_id: str, _actor: RequestAuthorizationContext) -> AssignmentValidationRead:
        self._require_assignment(tenant_id, assignment_id)
        return self.validation_service.validate_assignment_by_id(tenant_id, assignment_id)

    def get_shift_release_validations(self, tenant_id: str, shift_id: str, _actor: RequestAuthorizationContext) -> ShiftReleaseValidationRead:
        self._require_shift(tenant_id, shift_id)
        return self.validation_service.validate_shift_release(tenant_id, shift_id)

    def get_planning_record_release_validations(
        self,
        tenant_id: str,
        planning_record_id: str,
        _actor: RequestAuthorizationContext,
    ) -> PlanningRecordReleaseValidationRead:
        self._require_planning_record(tenant_id, planning_record_id)
        return self.validation_service.validate_planning_record_release(tenant_id, planning_record_id)

    def list_assignment_validation_overrides(
        self,
        tenant_id: str,
        assignment_id: str,
        _actor: RequestAuthorizationContext,
    ) -> list[AssignmentValidationOverrideRead]:
        self._require_assignment(tenant_id, assignment_id)
        return [AssignmentValidationOverrideRead.model_validate(row) for row in self.repository.list_assignment_validation_overrides(tenant_id, assignment_id)]

    def create_assignment_validation_override(
        self,
        tenant_id: str,
        assignment_id: str,
        payload: AssignmentValidationOverrideCreate,
        actor: RequestAuthorizationContext,
    ) -> AssignmentValidationOverrideRead:
        assignment = self._require_assignment(tenant_id, assignment_id)
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        validations = self.validation_service.validate_assignment_by_id(tenant_id, assignment_id)
        issue = next((row for row in validations.issues if row.rule_code == payload.rule_code), None)
        if issue is None:
            raise ApiException(404, "planning.assignment_validation.rule_not_found", "errors.planning.assignment_validation.rule_not_found")
        if issue.severity != "block" or not issue.override_allowed:
            raise ApiException(409, "planning.assignment_validation.override_not_allowed", "errors.planning.assignment_validation.override_not_allowed")
        row = self.repository.create_assignment_validation_override(
            AssignmentValidationOverride(
                tenant_id=tenant_id,
                assignment_id=assignment.id,
                rule_code=payload.rule_code,
                reason_text=payload.reason_text.strip(),
                created_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            "planning.assignment.validation_override.created",
            "ops.assignment_validation_override",
            row.id,
            tenant_id,
            after_json={"assignment_id": assignment_id, "rule_code": row.rule_code, "reason_text": row.reason_text},
        )
        return AssignmentValidationOverrideRead.model_validate(row)

    def create_assignment(self, tenant_id: str, payload: AssignmentCreate, actor: RequestAuthorizationContext) -> AssignmentRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        validation_results = self._validate_assignment_payload(tenant_id, payload)
        if self.validation_service.has_blocking_issues(validation_results):
            raise ApiException(
                409,
                "planning.assignment.blocked_by_validation",
                "errors.planning.assignment.blocked_by_validation",
                {"issues": [issue.model_dump() for issue in validation_results]},
            )
        row = self._create_assignment_row(tenant_id, payload, actor)
        return AssignmentRead.model_validate(row)

    def update_assignment(self, tenant_id: str, assignment_id: str, payload: AssignmentUpdate, actor: RequestAuthorizationContext) -> AssignmentRead:
        current = self._require_assignment(tenant_id, assignment_id)
        before_json = self._snapshot(current)
        choice = self._validate_actor_choice(
            self._field_value(payload, "employee_id", current.employee_id),
            self._field_value(payload, "subcontractor_worker_id", current.subcontractor_worker_id),
            code_prefix="planning.assignment",
        )
        shift = self._require_shift(tenant_id, current.shift_id)
        demand_group = self._require_demand_group(tenant_id, current.demand_group_id)
        team_id = self._field_value(payload, "team_id", current.team_id)
        candidate_payload = AssignmentCreate(
            tenant_id=tenant_id,
            shift_id=current.shift_id,
            demand_group_id=current.demand_group_id,
            team_id=team_id,
            employee_id=choice.employee_id,
            subcontractor_worker_id=choice.subcontractor_worker_id,
            assignment_status_code=self._field_value(payload, "assignment_status_code", current.assignment_status_code),
            assignment_source_code=self._field_value(payload, "assignment_source_code", current.assignment_source_code),
            offered_at=self._field_value(payload, "offered_at", current.offered_at),
            confirmed_at=self._field_value(payload, "confirmed_at", current.confirmed_at),
            remarks=self._field_value(payload, "remarks", current.remarks),
        )
        self._validate_assignment_shape(
            tenant_id,
            shift=shift,
            demand_group=demand_group,
            team_id=team_id,
            actor_choice=choice,
            assignment_status_code=self._field_value(payload, "assignment_status_code", current.assignment_status_code),
            assignment_source_code=self._field_value(payload, "assignment_source_code", current.assignment_source_code),
            exclude_assignment_id=assignment_id,
        )
        validation_results = self._validate_assignment_payload(tenant_id, candidate_payload, assignment_id)
        if self.validation_service.has_blocking_issues(validation_results):
            raise ApiException(
                409,
                "planning.assignment.blocked_by_validation",
                "errors.planning.assignment.blocked_by_validation",
                {"issues": [issue.model_dump() for issue in validation_results]},
            )
        row = self.repository.update_assignment(tenant_id, assignment_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("assignment")
        self._record_event(actor, "planning.assignment.updated", "ops.assignment", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return AssignmentRead.model_validate(row)

    def assign(self, tenant_id: str, payload: StaffingAssignCommand, actor: RequestAuthorizationContext) -> StaffingCommandResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        assignment_payload = AssignmentCreate(
            tenant_id=payload.tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            team_id=payload.team_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            assignment_status_code="confirmed" if payload.confirmed_at else "assigned",
            assignment_source_code=payload.assignment_source_code,
            offered_at=payload.offered_at,
            confirmed_at=payload.confirmed_at,
            remarks=payload.remarks,
        )
        validation_results = self._validate_assignment_payload(tenant_id, assignment_payload)
        if self.validation_service.has_blocking_issues(validation_results):
            return StaffingCommandResult(
                tenant_id=tenant_id,
                shift_id=payload.shift_id,
                outcome_code="blocked",
                validation_codes=self.validation_service.blocking_issue_codes(validation_results),
                validation_results=validation_results,
                conflict_code="validation_blocked",
            )
        row = self._create_assignment_row(tenant_id, assignment_payload, actor)
        return StaffingCommandResult(
            tenant_id=tenant_id,
            shift_id=row.shift_id,
            assignment_id=row.id,
            outcome_code="assigned",
            validation_codes=[issue.rule_code for issue in validation_results],
            validation_results=validation_results,
            assignment=AssignmentRead.model_validate(row),
        )

    def unassign(self, tenant_id: str, payload: StaffingUnassignCommand, actor: RequestAuthorizationContext) -> StaffingCommandResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        current = self._require_assignment(tenant_id, payload.assignment_id)
        if payload.version_no != current.version_no:
            raise ApiException(409, "planning.assignment.stale_version", "errors.planning.assignment.stale_version")
        before_json = self._snapshot(current)
        row = self.repository.update_assignment(
            tenant_id,
            payload.assignment_id,
            AssignmentUpdate(
                assignment_status_code="removed",
                remarks=payload.remarks if payload.remarks is not None else current.remarks,
                version_no=payload.version_no,
            ),
            actor.user_id,
        )
        if row is None:
            raise self._not_found("assignment")
        self._record_event(actor, "planning.assignment.unassigned", "ops.assignment", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return StaffingCommandResult(
            tenant_id=tenant_id,
            shift_id=row.shift_id,
            assignment_id=row.id,
            outcome_code="unassigned",
            assignment=AssignmentRead.model_validate(row),
        )

    def substitute(self, tenant_id: str, payload: StaffingSubstituteCommand, actor: RequestAuthorizationContext) -> StaffingCommandResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        current = self._require_assignment(tenant_id, payload.assignment_id)
        if payload.version_no != current.version_no:
            raise ApiException(409, "planning.assignment.stale_version", "errors.planning.assignment.stale_version")
        self.unassign(
            tenant_id,
            StaffingUnassignCommand(
                tenant_id=tenant_id,
                assignment_id=current.id,
                version_no=current.version_no,
                remarks=payload.remarks,
            ),
            actor,
        )
        replacement = self.assign(
            tenant_id,
            StaffingAssignCommand(
                tenant_id=tenant_id,
                shift_id=current.shift_id,
                demand_group_id=current.demand_group_id,
                team_id=payload.replacement_team_id,
                employee_id=payload.replacement_employee_id,
                subcontractor_worker_id=payload.replacement_subcontractor_worker_id,
                assignment_source_code=payload.assignment_source_code,
                remarks=payload.remarks,
            ),
            actor,
        )
        return replacement.model_copy(update={"outcome_code": "substituted"})

    def list_subcontractor_releases(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[SubcontractorReleaseRead]:
        return [SubcontractorReleaseRead.model_validate(row) for row in self.repository.list_subcontractor_releases(tenant_id, filters)]

    def create_subcontractor_release(self, tenant_id: str, payload: SubcontractorReleaseCreate, actor: RequestAuthorizationContext) -> SubcontractorReleaseRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift = self._require_shift(tenant_id, payload.shift_id)
        demand_group = self._require_demand_group(tenant_id, payload.demand_group_id) if payload.demand_group_id is not None else None
        if demand_group is not None and demand_group.shift_id != shift.id:
            raise ApiException(400, "planning.subcontractor_release.scope_mismatch", "errors.planning.subcontractor_release.scope_mismatch")
        self._require_subcontractor(tenant_id, payload.subcontractor_id)
        self._validate_release_qty(tenant_id, shift.id, payload.demand_group_id, payload.subcontractor_id, payload.released_qty)
        row = self.repository.create_subcontractor_release(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.subcontractor_release.created", "ops.subcontractor_release", row.id, tenant_id, after_json=self._snapshot(row))
        return SubcontractorReleaseRead.model_validate(row)

    def update_subcontractor_release(self, tenant_id: str, release_id: str, payload: SubcontractorReleaseUpdate, actor: RequestAuthorizationContext) -> SubcontractorReleaseRead:
        current = self._require_subcontractor_release(tenant_id, release_id)
        before_json = self._snapshot(current)
        demand_group_id = self._field_value(payload, "demand_group_id", current.demand_group_id)
        released_qty = self._field_value(payload, "released_qty", current.released_qty)
        self._validate_release_qty(tenant_id, current.shift_id, demand_group_id, current.subcontractor_id, released_qty, exclude_release_id=release_id)
        row = self.repository.update_subcontractor_release(tenant_id, release_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("subcontractor_release")
        self._record_event(actor, "planning.subcontractor_release.updated", "ops.subcontractor_release", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return SubcontractorReleaseRead.model_validate(row)

    def staffing_board(self, tenant_id: str, filters: StaffingBoardFilter, _actor: RequestAuthorizationContext) -> list[StaffingBoardShiftItem]:
        shift_rows = [StaffingBoardShiftItem(**row) for row in self.repository.list_board_shifts(tenant_id, filters)]
        if not shift_rows:
            return []
        shift_ids = [row.id for row in shift_rows]
        demand_groups = self.repository.list_demand_groups(tenant_id, StaffingFilter(include_archived=False))
        assignments = self.repository.list_assignments(tenant_id, StaffingFilter(include_archived=False))
        releases = self.repository.list_subcontractor_releases(tenant_id, StaffingFilter(include_archived=False))
        groups_by_shift: dict[str, list[DemandGroup]] = defaultdict(list)
        assignments_by_shift: dict[str, list[Assignment]] = defaultdict(list)
        releases_by_key: dict[str, int] = defaultdict(int)
        for row in demand_groups:
            if row.shift_id in shift_ids:
                groups_by_shift[row.shift_id].append(row)
        for row in assignments:
            if row.shift_id in shift_ids and row.assignment_status_code != "removed":
                assignments_by_shift[row.shift_id].append(row)
        for row in releases:
            if row.shift_id in shift_ids and row.release_status_code != "revoked":
                releases_by_key[row.demand_group_id or ""] += row.released_qty
        result: list[StaffingBoardShiftItem] = []
        for row in shift_rows:
            demand_items: list[StaffingBoardDemandGroupItem] = []
            for group in groups_by_shift[row.id]:
                group_assignments = [assignment for assignment in assignments_by_shift[row.id] if assignment.demand_group_id == group.id]
                assigned_count = len(group_assignments)
                confirmed_count = sum(1 for assignment in group_assignments if assignment.confirmed_at is not None or assignment.assignment_status_code == "confirmed")
                demand_items.append(
                    StaffingBoardDemandGroupItem(
                        id=group.id,
                        shift_id=row.id,
                        function_type_id=group.function_type_id,
                        qualification_type_id=group.qualification_type_id,
                        min_qty=group.min_qty,
                        target_qty=group.target_qty,
                        mandatory_flag=group.mandatory_flag,
                        assigned_count=assigned_count,
                        confirmed_count=confirmed_count,
                        released_partner_qty=releases_by_key.get(group.id, 0),
                    )
                )
            assignment_items = [
                StaffingBoardAssignmentItem(
                    id=assignment.id,
                    shift_id=assignment.shift_id,
                    demand_group_id=assignment.demand_group_id,
                    team_id=assignment.team_id,
                    employee_id=assignment.employee_id,
                    subcontractor_worker_id=assignment.subcontractor_worker_id,
                    assignment_status_code=assignment.assignment_status_code,
                    assignment_source_code=assignment.assignment_source_code,
                    confirmed_at=assignment.confirmed_at,
                )
                for assignment in assignments_by_shift[row.id]
            ]
            result.append(row.model_copy(update={"demand_groups": demand_items, "assignments": assignment_items}))
        return result

    def coverage(self, tenant_id: str, filters: CoverageFilter, actor: RequestAuthorizationContext) -> list[CoverageShiftItem]:
        board_filters = StaffingBoardFilter(
            customer_id=filters.customer_id,
            planning_record_id=filters.planning_record_id,
            shift_plan_id=filters.shift_plan_id,
            order_id=filters.order_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            planning_mode_code=filters.planning_mode_code,
            workforce_scope_code=filters.workforce_scope_code,
            release_state=filters.release_state,
            visibility_state=filters.visibility_state,
            confirmation_state=filters.confirmation_state,
            function_type_id=filters.function_type_id,
            qualification_type_id=filters.qualification_type_id,
        )
        rows = self.staffing_board(tenant_id, board_filters, actor)
        result: list[CoverageShiftItem] = []
        for row in rows:
            if filters.function_type_id is not None:
                group_rows = [group for group in row.demand_groups if group.function_type_id == filters.function_type_id]
            else:
                group_rows = row.demand_groups
            if filters.qualification_type_id is not None:
                group_rows = [group for group in group_rows if group.qualification_type_id == filters.qualification_type_id]
            if filters.confirmation_state == "confirmed_only":
                assignment_count = sum(group.confirmed_count for group in group_rows)
            else:
                assignment_count = sum(group.assigned_count for group in group_rows)
            confirmed_count = sum(group.confirmed_count for group in group_rows)
            min_qty = sum(group.min_qty for group in group_rows)
            target_qty = sum(group.target_qty for group in group_rows)
            released_qty = sum(group.released_partner_qty for group in group_rows)
            demand_items = [
                CoverageDemandGroupItem(
                    demand_group_id=group.id,
                    function_type_id=group.function_type_id,
                    qualification_type_id=group.qualification_type_id,
                    min_qty=group.min_qty,
                    target_qty=group.target_qty,
                    assigned_count=group.assigned_count,
                    confirmed_count=group.confirmed_count,
                    released_partner_qty=group.released_partner_qty,
                    coverage_state=self._coverage_state(group.min_qty, group.target_qty, group.assigned_count, group.confirmed_count, group.released_partner_qty),
                )
                for group in group_rows
            ]
            result.append(
                CoverageShiftItem(
                    shift_id=row.id,
                    planning_record_id=row.planning_record_id,
                    shift_plan_id=row.shift_plan_id,
                    order_id=row.order_id,
                    order_no=row.order_no,
                    planning_record_name=row.planning_record_name,
                    planning_mode_code=row.planning_mode_code,
                    workforce_scope_code=row.workforce_scope_code,
                    starts_at=row.starts_at,
                    ends_at=row.ends_at,
                    shift_type_code=row.shift_type_code,
                    location_text=row.location_text,
                    meeting_point=row.meeting_point,
                    min_required_qty=min_qty,
                    target_required_qty=target_qty,
                    assigned_count=assignment_count,
                    confirmed_count=confirmed_count,
                    released_partner_qty=released_qty,
                    coverage_state=self._coverage_state(min_qty, target_qty, assignment_count, confirmed_count, released_qty),
                    demand_groups=demand_items,
                )
            )
        return result

    def get_assignment_step_snapshot(
        self,
        tenant_id: str,
        payload: AssignmentStepScopeRequest,
        actor: RequestAuthorizationContext,
    ) -> AssignmentStepSnapshotRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift_plan, target_shifts, project_start, project_end, active_months, selected_series = self._resolve_assignment_step_scope(
            tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        groups_by_shift = self._assignment_step_groups_by_shift(tenant_id, target_shifts)
        order_summary = self._build_assignment_step_order_summary(shift_plan)
        demand_group_summaries = self._build_assignment_step_demand_group_summaries(target_shifts, groups_by_shift)
        day_summaries = self._build_assignment_step_day_summaries(target_shifts, groups_by_shift)
        cells = self._build_assignment_step_cells(tenant_id, target_shifts, groups_by_shift, payload.demand_group_match)
        candidates: list[AssignmentStepCandidateRead] = []
        default_signature = demand_group_summaries[0].signature_key if demand_group_summaries else None
        candidates_included = False
        if payload.demand_group_match is not None and target_shifts:
            caching_repository = _CachedAssignmentStepRepository(self.repository)
            candidates = self._list_assignment_step_candidates(
                tenant_id,
                shift_plan=shift_plan,
                target_shifts=target_shifts,
                groups_by_shift=groups_by_shift,
                demand_group_match=payload.demand_group_match,
                actor_kind=payload.actor_kind,
                team_id=payload.team_id,
                employee_group_id=payload.employee_group_id,
                search=payload.search,
                repository=caching_repository,
                candidate_limit=payload.candidate_limit,
                candidate_offset=payload.candidate_offset,
                include_day_statuses=payload.include_day_statuses,
            )
            candidates_included = True
        lock_reason_codes = sorted({
            reason
            for shift in target_shifts
            for reason in self._assignment_step_lock_reason_codes(tenant_id, shift, repository=self.repository)
        })
        default_month = self._normalize_month_start(payload.active_month or project_start)
        return AssignmentStepSnapshotRead(
            tenant_id=tenant_id,
            order=order_summary,
            shift_plan=AssignmentStepShiftPlanSummaryRead(
                shift_plan_id=shift_plan.id,
                shift_plan_name=shift_plan.name,
                shift_series_id=getattr(selected_series, "id", None),
                shift_series_label=getattr(selected_series, "label", None),
                workforce_scope_code=shift_plan.workforce_scope_code,
                planning_from=shift_plan.planning_from,
                planning_to=shift_plan.planning_to,
                project_start=project_start,
                project_end=project_end,
                default_month=default_month,
                active_months=active_months,
            ),
            generated_shift_count=len(target_shifts),
            demand_group_summary_count=len(demand_group_summaries),
            default_demand_group_signature=default_signature,
            candidates_included=candidates_included,
            editable_flag=not bool(lock_reason_codes),
            lock_reason_codes=lock_reason_codes,
            demand_group_summaries=demand_group_summaries,
            day_summaries=day_summaries,
            calendar_cells=cells,
            candidates=candidates,
        )

    def list_assignment_step_candidates(
        self,
        tenant_id: str,
        payload: AssignmentStepScopeRequest,
        actor: RequestAuthorizationContext,
    ) -> AssignmentStepCandidateQueryResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift_plan, target_shifts, _, _, _, _ = self._resolve_assignment_step_scope(
            tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        if payload.demand_group_match is None or not target_shifts:
            return AssignmentStepCandidateQueryResult(
                tenant_id=tenant_id,
                shift_plan_id=payload.shift_plan_id,
                shift_series_id=payload.shift_series_id,
                generated_shift_count=len(target_shifts),
                candidates=[],
            )
        groups_by_shift = self._assignment_step_groups_by_shift(tenant_id, target_shifts)
        caching_repository = _CachedAssignmentStepRepository(self.repository)
        if payload.candidate_limit is None and payload.candidate_offset == 0:
            paged_candidates = self._list_assignment_step_candidates(
                tenant_id,
                shift_plan=shift_plan,
                target_shifts=target_shifts,
                groups_by_shift=groups_by_shift,
                demand_group_match=payload.demand_group_match,
                actor_kind=payload.actor_kind,
                team_id=payload.team_id,
                employee_group_id=payload.employee_group_id,
                search=payload.search,
                repository=caching_repository,
                candidate_limit=None,
                candidate_offset=0,
                include_day_statuses=payload.include_day_statuses,
            )
            total_candidate_count = len(paged_candidates)
        else:
            all_candidates = self._list_assignment_step_candidates(
                tenant_id,
                shift_plan=shift_plan,
                target_shifts=target_shifts,
                groups_by_shift=groups_by_shift,
                demand_group_match=payload.demand_group_match,
                actor_kind=payload.actor_kind,
                team_id=payload.team_id,
                employee_group_id=payload.employee_group_id,
                search=payload.search,
                repository=caching_repository,
                candidate_limit=None,
                candidate_offset=0,
                include_day_statuses=False,
            )
            total_candidate_count = len(all_candidates)
            paged_candidates = self._list_assignment_step_candidates(
                tenant_id,
                shift_plan=shift_plan,
                target_shifts=target_shifts,
                groups_by_shift=groups_by_shift,
                demand_group_match=payload.demand_group_match,
                actor_kind=payload.actor_kind,
                team_id=payload.team_id,
                employee_group_id=payload.employee_group_id,
                search=payload.search,
                repository=caching_repository,
                candidate_limit=payload.candidate_limit,
                candidate_offset=payload.candidate_offset,
                include_day_statuses=payload.include_day_statuses,
            )
        return AssignmentStepCandidateQueryResult(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            generated_shift_count=len(target_shifts),
            total_candidate_count=total_candidate_count,
            candidate_limit=payload.candidate_limit,
            candidate_offset=payload.candidate_offset,
            candidates=paged_candidates,
        )

    def preview_assignment_step_apply(
        self,
        tenant_id: str,
        payload: AssignmentStepApplyRequest,
        actor: RequestAuthorizationContext,
    ) -> AssignmentStepApplyResult:
        return self._assignment_step_apply(tenant_id, payload, actor, preview_only=True)

    def apply_assignment_step(
        self,
        tenant_id: str,
        payload: AssignmentStepApplyRequest,
        actor: RequestAuthorizationContext,
    ) -> AssignmentStepApplyResult:
        return self._assignment_step_apply(tenant_id, payload, actor, preview_only=False)

    def _assignment_step_apply(
        self,
        tenant_id: str,
        payload: AssignmentStepApplyRequest,
        actor: RequestAuthorizationContext,
        *,
        preview_only: bool,
    ) -> AssignmentStepApplyResult:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift_plan, target_shifts, _, _, _, _ = self._resolve_assignment_step_scope(
            tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            date_from=None,
            date_to=None,
        )
        choice = self._validate_actor_choice(payload.employee_id, payload.subcontractor_worker_id, code_prefix="planning.assignment_step")
        actor_kind = "employee" if choice.employee_id is not None else "subcontractor_worker"
        actor_id = choice.employee_id or choice.subcontractor_worker_id or ""
        target_shift_set = set(payload.target_shift_ids)
        scoped_shift_ids = {shift.id for shift in target_shifts}
        groups_by_shift = self._assignment_step_groups_by_shift(tenant_id, target_shifts)
        caching_repository = _CachedAssignmentStepRepository(self.repository)
        unknown_shift_ids = sorted(target_shift_set - scoped_shift_ids)
        if unknown_shift_ids:
            raise ApiException(
                400,
                "planning.assignment_step.invalid_target_shifts",
                "errors.planning.assignment_step.invalid_target_shifts",
                details={"reason_codes": ["invalid_target_shift_ids"], "target_shift_ids": unknown_shift_ids},
            )

        results: list[AssignmentStepApplyItemResult] = []
        created_ids: list[str] = []
        accepted_count = 0
        rejected_count = 0
        demand_group_match = payload.demand_group_match
        for shift in [row for row in target_shifts if row.id in target_shift_set]:
            matched_group = self._find_matching_demand_group_for_shift(shift, demand_group_match, groups_by_shift)
            if matched_group is None:
                results.append(
                    AssignmentStepApplyItemResult(
                        shift_id=shift.id,
                        occurrence_date=self._shift_occurrence_date(shift),
                        outcome_code="rejected",
                        reason_codes=["demand_group_not_found"],
                    )
                )
                rejected_count += 1
                if payload.stop_on_first_rejection and not preview_only:
                    break
                continue
            lock_reason_codes = self._assignment_step_lock_reason_codes(tenant_id, shift, repository=caching_repository)
            if lock_reason_codes:
                results.append(
                    AssignmentStepApplyItemResult(
                        shift_id=shift.id,
                        demand_group_id=matched_group.id,
                        occurrence_date=self._shift_occurrence_date(shift),
                        outcome_code="rejected",
                        reason_codes=lock_reason_codes,
                    )
                )
                rejected_count += 1
                if payload.stop_on_first_rejection and not preview_only:
                    break
                continue

            candidate_payload = AssignmentCreate(
                tenant_id=tenant_id,
                shift_id=shift.id,
                demand_group_id=matched_group.id,
                team_id=payload.team_id,
                employee_id=choice.employee_id,
                subcontractor_worker_id=choice.subcontractor_worker_id,
                assignment_status_code="confirmed" if payload.confirmed_at else "assigned",
                assignment_source_code=payload.assignment_source_code,
                offered_at=payload.offered_at,
                confirmed_at=payload.confirmed_at,
                remarks=payload.remarks,
            )
            outcome = self._evaluate_assignment_step_payload(
                tenant_id,
                shift,
                matched_group,
                candidate_payload,
                repository=caching_repository,
            )
            if not outcome["eligible_flag"]:
                results.append(
                    AssignmentStepApplyItemResult(
                        shift_id=shift.id,
                        demand_group_id=matched_group.id,
                        occurrence_date=self._shift_occurrence_date(shift),
                        outcome_code="rejected",
                        reason_codes=outcome["reason_codes"],
                        warning_codes=outcome["warning_codes"],
                        validation_results=outcome["validation_results"],
                    )
                )
                rejected_count += 1
                if payload.stop_on_first_rejection and not preview_only:
                    break
                continue

            assignment_read: AssignmentRead | None = None
            assignment_id: str | None = None
            if not preview_only:
                row = self._create_assignment_row(tenant_id, candidate_payload, actor)
                assignment_read = AssignmentRead.model_validate(row)
                assignment_id = row.id
                created_ids.append(row.id)
            accepted_count += 1
            results.append(
                AssignmentStepApplyItemResult(
                    shift_id=shift.id,
                    demand_group_id=matched_group.id,
                    occurrence_date=self._shift_occurrence_date(shift),
                    outcome_code="accepted" if preview_only else "created",
                    assignment_id=assignment_id,
                    warning_codes=outcome["warning_codes"],
                    validation_results=outcome["validation_results"],
                    assignment=assignment_read,
                )
            )

        return AssignmentStepApplyResult(
            tenant_id=tenant_id,
            shift_plan_id=shift_plan.id,
            shift_series_id=payload.shift_series_id,
            actor_kind=actor_kind,
            actor_id=actor_id,
            requested_count=len(payload.target_shift_ids),
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            created_assignment_ids=created_ids,
            results=results,
        )

    def _resolve_assignment_step_scope(
        self,
        tenant_id: str,
        *,
        shift_plan_id: str,
        shift_series_id: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> tuple[object, list[Shift], date, date, list[date], object | None]:
        shift_plan = self._require_shift_plan(tenant_id, shift_plan_id)
        selected_series = None
        if shift_series_id is not None:
            selected_series = next((row for row in getattr(shift_plan, "series_rows", []) if row.id == shift_series_id), None)
            if selected_series is None:
                raise ApiException(404, "planning.shift_series.not_found", "errors.planning.shift_series.not_found")
        target_shifts = [
            shift
            for shift in self.repository.list_shifts(tenant_id, ShiftListFilter(shift_plan_id=shift_plan_id, include_archived=False))
            if shift.source_kind_code == "generated"
            and (shift_series_id is None or shift.shift_series_id == shift_series_id)
            and self._shift_in_bulk_date_window(shift, date_from, date_to)
        ]
        if target_shifts:
            project_start = min(self._shift_occurrence_date(shift) for shift in target_shifts)
            project_end = max(self._shift_occurrence_date(shift) for shift in target_shifts)
        elif selected_series is not None:
            project_start = selected_series.date_from
            project_end = selected_series.date_to
        else:
            project_start = shift_plan.planning_from
            project_end = shift_plan.planning_to
        active_months = self._month_range(project_start, project_end)
        return shift_plan, target_shifts, project_start, project_end, active_months, selected_series

    def _build_assignment_step_order_summary(self, shift_plan) -> AssignmentStepOrderSummaryRead:  # noqa: ANN001
        planning_record = getattr(shift_plan, "planning_record", None)
        order = getattr(planning_record, "order", None)
        if planning_record is None:
            planning_record = self.repository.get_planning_record(shift_plan.tenant_id, shift_plan.planning_record_id)
        if order is None and planning_record is not None:
            order = getattr(planning_record, "order", None) or self.repository.get_customer_order(shift_plan.tenant_id, planning_record.order_id)
        if planning_record is None or order is None:
            raise ApiException(404, "planning.shift_plan.context_missing", "errors.planning.shift_plan.context_missing")
        return AssignmentStepOrderSummaryRead(
            order_id=order.id,
            order_no=order.order_no,
            customer_id=order.customer_id,
            planning_record_id=planning_record.id,
            planning_record_name=planning_record.name,
            planning_mode_code=planning_record.planning_mode_code,
        )

    def _assignment_step_groups_by_shift(
        self,
        tenant_id: str,
        target_shifts: list[Shift],
    ) -> dict[str, list[DemandGroup]]:
        shift_ids = [shift.id for shift in target_shifts]
        list_for_shifts = getattr(self.repository, "list_demand_groups_for_shifts", None)
        if callable(list_for_shifts):
            groups = list_for_shifts(tenant_id, shift_ids, include_archived=False)
        else:
            groups = [
                group
                for shift in target_shifts
                for group in self.repository.list_demand_groups(
                    tenant_id,
                    StaffingFilter(shift_id=shift.id, include_archived=False),
                )
            ]
        grouped: dict[str, list[DemandGroup]] = defaultdict(list)
        for group in groups:
            grouped[group.shift_id].append(group)
        return grouped

    def _build_assignment_step_demand_group_summaries(
        self,
        target_shifts: list[Shift],
        groups_by_shift: dict[str, list[DemandGroup]],
    ) -> list[AssignmentStepDemandGroupSummaryRead]:
        grouped: dict[str, dict[str, object]] = {}
        for shift in target_shifts:
            for group in groups_by_shift.get(shift.id, []):
                key = self._assignment_step_signature_key(group)
                assigned_count = sum(1 for row in getattr(group, "assignments", []) if row.assignment_status_code != "removed")
                confirmed_count = sum(1 for row in getattr(group, "assignments", []) if row.assignment_status_code == "confirmed")
                released_partner_qty = sum(
                    row.released_qty
                    for row in getattr(group, "subcontractor_releases", [])
                    if row.release_status_code != "revoked"
                )
                bucket = grouped.setdefault(
                    key,
                    {
                        "group": group,
                        "matched_shift_count": 0,
                        "assigned_count": 0,
                        "confirmed_count": 0,
                        "released_partner_qty": 0,
                        "min_qty": 0,
                        "target_qty": 0,
                    },
                )
                bucket["matched_shift_count"] += 1
                bucket["assigned_count"] += assigned_count
                bucket["confirmed_count"] += confirmed_count
                bucket["released_partner_qty"] += released_partner_qty
                bucket["min_qty"] += group.min_qty
                bucket["target_qty"] += group.target_qty
        rows: list[AssignmentStepDemandGroupSummaryRead] = []
        for key, bucket in grouped.items():
            group = bucket["group"]
            remaining_open_qty = max(0, bucket["target_qty"] - bucket["assigned_count"])
            rows.append(
                AssignmentStepDemandGroupSummaryRead(
                    signature_key=key,
                    function_type_id=group.function_type_id,
                    qualification_type_id=group.qualification_type_id,
                    min_qty=group.min_qty,
                    target_qty=group.target_qty,
                    mandatory_flag=group.mandatory_flag,
                    sort_order=group.sort_order,
                    remark=group.remark,
                    matched_shift_count=bucket["matched_shift_count"],
                    assigned_count=bucket["assigned_count"],
                    confirmed_count=bucket["confirmed_count"],
                    released_partner_qty=bucket["released_partner_qty"],
                    remaining_open_qty=remaining_open_qty,
                    coverage_state=self._coverage_state(
                        bucket["min_qty"],
                        bucket["target_qty"],
                        bucket["assigned_count"],
                        bucket["confirmed_count"],
                        bucket["released_partner_qty"],
                    ),
                )
            )
        return sorted(rows, key=lambda row: (row.sort_order, row.signature_key))

    def _build_assignment_step_day_summaries(
        self,
        target_shifts: list[Shift],
        groups_by_shift: dict[str, list[DemandGroup]],
    ) -> list[AssignmentStepDaySummaryRead]:
        buckets: dict[date, list[str]] = defaultdict(list)
        for shift in target_shifts:
            states = []
            for group in groups_by_shift.get(shift.id, []):
                assigned_count = sum(1 for row in getattr(group, "assignments", []) if row.assignment_status_code != "removed")
                confirmed_count = sum(1 for row in getattr(group, "assignments", []) if row.assignment_status_code == "confirmed")
                released_partner_qty = sum(
                    row.released_qty
                    for row in getattr(group, "subcontractor_releases", [])
                    if row.release_status_code != "revoked"
                )
                states.append(self._coverage_state(group.min_qty, group.target_qty, assigned_count, confirmed_count, released_partner_qty))
            buckets[self._shift_occurrence_date(shift)].append("red" if "red" in states else "yellow" if "yellow" in states else "green")
        result: list[AssignmentStepDaySummaryRead] = []
        for occurrence_date in sorted(buckets):
            day_states = buckets[occurrence_date]
            fully_covered_count = sum(1 for state in day_states if state == "green")
            warning_count = sum(1 for state in day_states if state == "yellow")
            blocked_count = sum(1 for state in day_states if state == "red")
            overall_state = "blocked" if blocked_count else "warning" if warning_count else "fully_covered"
            result.append(
                AssignmentStepDaySummaryRead(
                    occurrence_date=occurrence_date,
                    total_shifts=len(day_states),
                    fully_covered_count=fully_covered_count,
                    warning_count=warning_count,
                    blocked_count=blocked_count,
                    overall_state=overall_state,
                    active_flag=True,
                )
            )
        return result

    def _build_assignment_step_cells(
        self,
        tenant_id: str,
        target_shifts: list[Shift],
        groups_by_shift: dict[str, list[DemandGroup]],
        demand_group_match: AssignmentStepDemandGroupMatch | None,
    ) -> list[AssignmentStepCellRead]:
        cells: list[AssignmentStepCellRead] = []
        for shift in target_shifts:
            lock_reason_codes = self._assignment_step_lock_reason_codes(tenant_id, shift, repository=self.repository)
            demand_groups = groups_by_shift.get(shift.id, [])
            if demand_group_match is not None:
                demand_groups = [row for row in demand_groups if self._demand_group_matches_signature(row, demand_group_match)]
            for group in demand_groups:
                assigned_rows = [row for row in getattr(group, "assignments", []) if row.assignment_status_code != "removed"]
                confirmed_count = sum(1 for row in assigned_rows if row.assignment_status_code == "confirmed")
                released_partner_qty = sum(
                    row.released_qty
                    for row in getattr(group, "subcontractor_releases", [])
                    if row.release_status_code != "revoked"
                )
                existing_assignments = [
                    AssignmentStepExistingAssignmentRead(
                        assignment_id=row.id,
                        shift_id=row.shift_id,
                        demand_group_id=row.demand_group_id,
                        assignment_status_code=row.assignment_status_code,
                        actor_kind="employee" if row.employee_id is not None else "subcontractor_worker",
                        actor_id=row.employee_id or row.subcontractor_worker_id or "",
                        personnel_ref=self._assignment_actor_ref(row),
                        display_name=self._assignment_actor_name(row),
                        team_id=row.team_id,
                    )
                    for row in assigned_rows
                ]
                cells.append(
                    AssignmentStepCellRead(
                        shift_id=shift.id,
                        demand_group_id=group.id,
                        occurrence_date=self._shift_occurrence_date(shift),
                        starts_at=shift.starts_at,
                        ends_at=shift.ends_at,
                        shift_type_code=shift.shift_type_code,
                        function_type_id=group.function_type_id,
                        qualification_type_id=group.qualification_type_id,
                        min_qty=group.min_qty,
                        target_qty=group.target_qty,
                        assigned_count=len(assigned_rows),
                        confirmed_count=confirmed_count,
                        released_partner_qty=released_partner_qty,
                        remaining_open_qty=max(0, group.target_qty - len(assigned_rows)),
                        coverage_state=self._coverage_state(group.min_qty, group.target_qty, len(assigned_rows), confirmed_count, released_partner_qty),
                        editable_flag=not bool(lock_reason_codes),
                        existing_assignments=existing_assignments,
                    )
                )
        return sorted(cells, key=lambda row: (row.occurrence_date, row.starts_at, row.demand_group_id))

    def _list_assignment_step_candidates(
        self,
        tenant_id: str,
        *,
        shift_plan,
        target_shifts: list[Shift],
        groups_by_shift: dict[str, list[DemandGroup]],
        demand_group_match: AssignmentStepDemandGroupMatch,
        actor_kind: str | None,
        team_id: str | None,
        employee_group_id: str | None,
        search: str | None,
        repository: StaffingRepository,
        candidate_limit: int | None = None,
        candidate_offset: int = 0,
        include_day_statuses: bool = True,
    ) -> list[AssignmentStepCandidateRead]:
        search_term = (search or "").strip().lower()
        include_employees = shift_plan.workforce_scope_code in {"internal", "mixed"} and actor_kind in {None, "employee"}
        include_workers = shift_plan.workforce_scope_code in {"subcontractor", "mixed"} and actor_kind in {None, "subcontractor_worker"}
        employees = repository.list_employees(tenant_id) if include_employees else []
        workers = repository.list_subcontractor_workers(tenant_id) if include_workers else []
        team_members = repository.list_team_members_for_actors(
            tenant_id,
            employee_ids=[row.id for row in employees],
            subcontractor_worker_ids=[row.id for row in workers],
            include_archived=False,
        )
        team_ids_by_actor: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in team_members:
            if row.employee_id is not None:
                team_ids_by_actor[("employee", row.employee_id)].append(row.team_id)
            if row.subcontractor_worker_id is not None:
                team_ids_by_actor[("subcontractor_worker", row.subcontractor_worker_id)].append(row.team_id)

        filtered_employees = [
            employee
            for employee in employees
            if self._candidate_matches_common_filters(
                actor_kind="employee",
                actor=employee,
                team_id=team_id,
                employee_group_id=employee_group_id,
                search_term=search_term,
                repository=repository,
                preloaded_team_ids=team_ids_by_actor.get(("employee", employee.id), []),
            )
        ]
        filtered_workers = [
            worker
            for worker in workers
            if self._candidate_matches_common_filters(
                actor_kind="subcontractor_worker",
                actor=worker,
                team_id=team_id,
                employee_group_id=employee_group_id,
                search_term=search_term,
                repository=repository,
                preloaded_team_ids=team_ids_by_actor.get(("subcontractor_worker", worker.id), []),
            )
        ]
        targets = self._build_assignment_step_targets(target_shifts, groups_by_shift, demand_group_match)
        if not targets:
            return []
        if isinstance(repository, _CachedAssignmentStepRepository):
            order_summary = self._build_assignment_step_order_summary(shift_plan)
            repository.prime_candidate_context(
                tenant_id,
                employee_ids=[row.id for row in filtered_employees],
                worker_ids=[row.id for row in filtered_workers],
                customer_id=order_summary.customer_id,
                window_start=min(target.shift.starts_at for target in targets) - timedelta(hours=24),
                window_end=max(target.shift.ends_at for target in targets) + timedelta(hours=11),
                known_shifts=target_shifts,
            )

        summaries: list[tuple[str, str, object]] = []
        if include_employees:
            for employee in filtered_employees:
                candidate = self._build_assignment_step_candidate_read(
                    tenant_id,
                    targets,
                    repository=repository,
                    include_day_statuses=False,
                    team_ids=team_ids_by_actor.get(("employee", employee.id), []),
                    employee=employee,
                )
                summaries.append(("employee", employee.id, candidate))
        if include_workers:
            for worker in filtered_workers:
                candidate = self._build_assignment_step_candidate_read(
                    tenant_id,
                    targets,
                    repository=repository,
                    include_day_statuses=False,
                    team_ids=team_ids_by_actor.get(("subcontractor_worker", worker.id), []),
                    worker=worker,
                )
                summaries.append(("subcontractor_worker", worker.id, candidate))
        ranked = sorted(
            [row for _, _, row in summaries],
            key=lambda row: (
                -row.eligible_day_count,
                -row.suitability_score,
                row.blocked_day_count,
                row.last_name.lower(),
                row.first_name.lower(),
                row.personnel_ref.lower(),
            ),
        )
        if candidate_offset:
            ranked = ranked[candidate_offset:]
        if candidate_limit is not None:
            ranked = ranked[:candidate_limit]
        if not include_day_statuses:
            return ranked

        employees_by_id = {row.id: row for row in filtered_employees}
        workers_by_id = {row.id: row for row in filtered_workers}
        return [
            self._build_assignment_step_candidate_read(
                tenant_id,
                targets,
                repository=repository,
                include_day_statuses=True,
                team_ids=candidate.team_ids,
                employee=employees_by_id.get(candidate.actor_id) if candidate.actor_kind == "employee" else None,
                worker=workers_by_id.get(candidate.actor_id) if candidate.actor_kind == "subcontractor_worker" else None,
            )
            for candidate in ranked
        ]

    def _build_assignment_step_targets(
        self,
        target_shifts: list[Shift],
        groups_by_shift: dict[str, list[DemandGroup]],
        demand_group_match: AssignmentStepDemandGroupMatch,
    ) -> list[_AssignmentStepTarget]:
        targets: list[_AssignmentStepTarget] = []
        for shift in target_shifts:
            matched_group = self._find_matching_demand_group_for_shift(shift, demand_group_match, groups_by_shift)
            if matched_group is not None:
                targets.append(_AssignmentStepTarget(shift=shift, demand_group=matched_group))
        return targets

    def _build_assignment_step_candidate_read(
        self,
        tenant_id: str,
        targets: list[_AssignmentStepTarget],
        *,
        repository: StaffingRepository,
        include_day_statuses: bool,
        team_ids: list[str],
        employee=None,  # noqa: ANN001
        worker=None,  # noqa: ANN001
    ) -> AssignmentStepCandidateRead:
        actor_kind = "employee" if employee is not None else "subcontractor_worker"
        actor_id = employee.id if employee is not None else worker.id
        personnel_ref = employee.personnel_no if employee is not None else worker.worker_no
        first_name = employee.first_name if employee is not None else worker.first_name
        last_name = employee.last_name if employee is not None else worker.last_name
        display_name = f"{first_name} {last_name}".strip()
        employee_group_ids = self._employee_group_ids(employee) if employee is not None else []
        day_statuses: list[AssignmentStepCandidateDayStatusRead] = []
        eligible_day_count = 0
        warning_day_count = 0
        blocked_day_count = 0
        availability_day_count = 0
        conflict_day_count = 0
        top_reason_counter: dict[str, int] = defaultdict(int)
        function_match_flag = False
        qualification_match_flag = False
        for target in targets:
            shift = target.shift
            matched_group = target.demand_group
            candidate_payload = AssignmentCreate(
                tenant_id=tenant_id,
                shift_id=shift.id,
                demand_group_id=matched_group.id,
                employee_id=employee.id if employee is not None else None,
                subcontractor_worker_id=worker.id if worker is not None else None,
                assignment_source_code="dispatcher",
            )
            outcome = self._evaluate_assignment_step_payload(tenant_id, shift, matched_group, candidate_payload, repository=repository, employee=employee)
            reason_codes = outcome["reason_codes"]
            warning_codes = outcome["warning_codes"]
            for code in reason_codes:
                top_reason_counter[code] += 1
            function_match_flag = function_match_flag or "function_match" not in reason_codes
            qualification_match_flag = qualification_match_flag or "qualification_match" not in reason_codes
            if outcome["eligible_flag"]:
                eligible_day_count += 1
                if warning_codes:
                    warning_day_count += 1
                else:
                    availability_day_count += 1
            else:
                blocked_day_count += 1
                if any(code in {"employee_absence", "employee_unavailable", "double_booking", "rest_period"} for code in reason_codes):
                    conflict_day_count += 1
            if include_day_statuses:
                day_statuses.append(
                    AssignmentStepCandidateDayStatusRead(
                        shift_id=shift.id,
                        demand_group_id=matched_group.id,
                        occurrence_date=self._shift_occurrence_date(shift),
                        eligible_flag=outcome["eligible_flag"],
                        warning_flag=bool(warning_codes),
                        reason_codes=reason_codes,
                        warning_codes=warning_codes,
                        validation_results=outcome["validation_results"],
                    )
                )
        suitability_score = (eligible_day_count * 100) - (blocked_day_count * 20) - (conflict_day_count * 10) + (10 if qualification_match_flag else 0) + (5 if function_match_flag else 0)
        return AssignmentStepCandidateRead(
            actor_kind=actor_kind,
            actor_id=actor_id,
            personnel_ref=personnel_ref,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            subcontractor_id=getattr(worker, "subcontractor_id", None),
            team_ids=team_ids,
            employee_group_ids=employee_group_ids,
            qualification_match_flag=qualification_match_flag,
            function_match_flag=function_match_flag,
            eligible_day_count=eligible_day_count,
            warning_day_count=warning_day_count,
            blocked_day_count=blocked_day_count,
            availability_day_count=availability_day_count,
            conflict_day_count=conflict_day_count,
            suitability_score=suitability_score,
            top_reason_codes=[code for code, _ in sorted(top_reason_counter.items(), key=lambda item: (-item[1], item[0]))[:5]],
            day_statuses=day_statuses,
        )

    def _evaluate_assignment_step_payload(
        self,
        tenant_id: str,
        shift: Shift,
        demand_group: DemandGroup,
        payload: AssignmentCreate,
        *,
        repository: StaffingRepository,
        employee=None,  # noqa: ANN001
    ) -> dict[str, object]:
        reason_codes: list[str] = []
        warning_codes: list[str] = []
        validation_results: list[PlanningValidationResult] = []
        try:
            choice = self._validate_actor_choice(payload.employee_id, payload.subcontractor_worker_id, code_prefix="planning.assignment")
            self._validate_assignment_shape(
                tenant_id,
                shift=shift,
                demand_group=demand_group,
                team_id=payload.team_id,
                actor_choice=choice,
                assignment_status_code=payload.assignment_status_code,
                assignment_source_code=payload.assignment_source_code,
            )
        except ApiException as exc:
            reason_codes.extend(self._reason_codes_from_exception(exc))
            return {
                "eligible_flag": False,
                "reason_codes": sorted(set(reason_codes)),
                "warning_codes": [],
                "validation_results": [],
            }

        employee_id = getattr(employee, "id", None) or payload.employee_id
        if employee_id is not None:
            reason_codes.extend(self._employee_unavailability_reason_codes(tenant_id, employee_id, shift, repository=repository))

        validation_results = PlanningValidationService(repository).validate_assignment(
            tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            assignment_id=None,
        )
        blocking = [issue.rule_code for issue in validation_results if issue.severity == "block"]
        warnings = [issue.rule_code for issue in validation_results if issue.severity == "warn"]
        reason_codes.extend(blocking)
        warning_codes.extend(warnings)
        return {
            "eligible_flag": not bool(blocking or reason_codes),
            "reason_codes": sorted(set(reason_codes)),
            "warning_codes": sorted(set(warning_codes)),
            "validation_results": validation_results,
        }

    def _candidate_matches_common_filters(
        self,
        *,
        actor_kind: str,
        actor,  # noqa: ANN001
        team_id: str | None,
        employee_group_id: str | None,
        search_term: str,
        repository: StaffingRepository,
        preloaded_team_ids: list[str] | None = None,
    ) -> bool:
        if search_term:
            haystack = " ".join(
                value
                for value in (
                    getattr(actor, "personnel_no", None),
                    getattr(actor, "worker_no", None),
                    getattr(actor, "first_name", None),
                    getattr(actor, "last_name", None),
                    getattr(actor, "preferred_name", None),
                )
                if value
            ).lower()
            if search_term not in haystack:
                return False
        if actor_kind == "employee" and employee_group_id is not None:
            if employee_group_id not in self._employee_group_ids(actor):
                return False
        candidate_team_ids = preloaded_team_ids
        if candidate_team_ids is None:
            candidate_team_ids = self._candidate_team_ids(getattr(actor, "tenant_id", ""), actor_kind, actor.id, repository=repository)
        if team_id is not None and team_id not in candidate_team_ids:
            return False
        return True

    def _candidate_team_ids(self, tenant_id: str, actor_kind: str, actor_id: str, *, repository: StaffingRepository) -> list[str]:
        rows = repository.list_team_members(
            tenant_id,
            StaffingFilter(
                employee_id=actor_id if actor_kind == "employee" else None,
                subcontractor_worker_id=actor_id if actor_kind == "subcontractor_worker" else None,
                include_archived=False,
            ),
        )
        return [row.team_id for row in rows if row.archived_at is None]

    @staticmethod
    def _employee_group_ids(employee) -> list[str]:  # noqa: ANN001
        result: list[str] = []
        for membership in getattr(employee, "group_memberships", []) or []:
            if getattr(membership, "archived_at", None) is not None or getattr(membership, "status", None) != "active":
                continue
            result.append(membership.group_id)
        return result

    def _find_matching_demand_group_for_shift(
        self,
        shift: Shift,
        match: AssignmentStepDemandGroupMatch,
        groups_by_shift: dict[str, list[DemandGroup]],
    ) -> DemandGroup | None:
        for group in groups_by_shift.get(shift.id, []):
            if self._demand_group_matches_signature(group, match):
                return group
        return None

    def _employee_unavailability_reason_codes(self, tenant_id: str, employee_id: str, shift: Shift, *, repository: StaffingRepository) -> list[str]:
        reason_codes: list[str] = []
        shift_date = self._shift_occurrence_date(shift)
        for absence in repository.list_employee_absences(tenant_id, employee_id):
            if absence.archived_at is not None or absence.status not in {"pending", "approved"}:
                continue
            if absence.starts_on <= shift_date <= absence.ends_on:
                reason_codes.append("employee_absence")
                break
        for rule in repository.list_employee_availability_rules(tenant_id, employee_id):
            if getattr(rule, "archived_at", None) is not None or getattr(rule, "status", "active") != "active":
                continue
            if getattr(rule, "rule_kind", None) != "unavailable":
                continue
            if self._availability_rule_matches_shift(rule, shift):
                reason_codes.append("employee_unavailable")
                break
        return reason_codes

    @staticmethod
    def _availability_rule_matches_shift(rule, shift: Shift) -> bool:  # noqa: ANN001
        recurrence_type = getattr(rule, "recurrence_type", "none")
        if recurrence_type == "weekly":
            weekday_mask = getattr(rule, "weekday_mask", None) or ""
            weekday_index = shift.starts_at.weekday()
            if len(weekday_mask) <= weekday_index or weekday_mask[weekday_index] != "1":
                return False
            shift_start = shift.starts_at.timetz().replace(tzinfo=None)
            shift_end = shift.ends_at.timetz().replace(tzinfo=None)
            return rule.starts_at.time() <= shift_end and rule.ends_at.time() >= shift_start
        return rule.starts_at < shift.ends_at and rule.ends_at > shift.starts_at

    def _assignment_step_lock_reason_codes(
        self,
        tenant_id: str,
        shift: Shift,
        *,
        repository: StaffingRepository,
    ) -> list[str]:
        reason_codes: list[str] = []
        if shift.release_state != "draft":
            reason_codes.append("shift_released")
        if shift.customer_visible_flag:
            reason_codes.append("customer_visible")
        if shift.subcontractor_visible_flag:
            reason_codes.append("subcontractor_visible")
        output_documents = [
            row
            for row in repository.list_documents_for_owner(tenant_id, "ops.shift", shift.id)
            if getattr(row, "metadata", {}).get("generated_kind") == "planning_output"
        ]
        if output_documents:
            reason_codes.append("deployment_outputs_exist")
        return sorted(set(reason_codes))

    @staticmethod
    def _reason_codes_from_exception(exc: ApiException) -> list[str]:
        detail_codes = exc.details.get("reason_codes") if isinstance(exc.details.get("reason_codes"), list) else None
        if detail_codes:
            return [str(code) for code in detail_codes]
        return [exc.code]

    @staticmethod
    def _shift_occurrence_date(shift: Shift) -> date:
        return shift.occurrence_date or shift.starts_at.date()

    @staticmethod
    def _normalize_month_start(value: date) -> date:
        return date(value.year, value.month, 1)

    def _month_range(self, start_date: date, end_date: date) -> list[date]:
        months: list[date] = []
        current = self._normalize_month_start(start_date)
        last = self._normalize_month_start(end_date)
        while current <= last:
            months.append(current)
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return months

    @staticmethod
    def _assignment_step_signature_key(group: DemandGroup) -> str:
        remark = (group.remark or "").strip()
        return "|".join(
            [
                group.function_type_id,
                group.qualification_type_id or "",
                str(group.min_qty),
                str(group.target_qty),
                "1" if group.mandatory_flag else "0",
                str(group.sort_order),
                remark,
            ]
        )

    @staticmethod
    def _assignment_actor_ref(row: Assignment) -> str:
        if row.employee is not None:
            return getattr(row.employee, "personnel_no", row.employee_id or "")
        if row.subcontractor_worker is not None:
            return getattr(row.subcontractor_worker, "worker_no", row.subcontractor_worker_id or "")
        return row.employee_id or row.subcontractor_worker_id or ""

    @staticmethod
    def _assignment_actor_name(row: Assignment) -> str:
        actor = row.employee or row.subcontractor_worker
        if actor is None:
            return ""
        return f"{getattr(actor, 'first_name', '')} {getattr(actor, 'last_name', '')}".strip()

    def _validate_assignment_payload(self, tenant_id: str, payload: AssignmentCreate, assignment_id: str | None = None) -> list[PlanningValidationResult]:
        return self.validation_service.validate_assignment(
            tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            assignment_id=assignment_id,
        )

    def _create_assignment_row(self, tenant_id: str, payload: AssignmentCreate, actor: RequestAuthorizationContext) -> Assignment:
        shift = self._require_shift(tenant_id, payload.shift_id)
        demand_group = self._require_demand_group(tenant_id, payload.demand_group_id)
        if demand_group.shift_id != shift.id:
            raise ApiException(400, "planning.assignment.scope_mismatch", "errors.planning.assignment.scope_mismatch")
        choice = self._validate_actor_choice(payload.employee_id, payload.subcontractor_worker_id, code_prefix="planning.assignment")
        self._validate_assignment_shape(
            tenant_id,
            shift=shift,
            demand_group=demand_group,
            team_id=payload.team_id,
            actor_choice=choice,
            assignment_status_code=payload.assignment_status_code,
            assignment_source_code=payload.assignment_source_code,
        )
        row = self.repository.create_assignment(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.assignment.created", "ops.assignment", row.id, tenant_id, after_json=self._snapshot(row))
        return row

    def _validate_demand_group(self, min_qty: int, target_qty: int) -> None:
        if target_qty < min_qty:
            raise ApiException(400, "planning.demand_group.invalid_qty_window", "errors.planning.demand_group.invalid_qty_window")

    def _normalize_bulk_templates(self, demand_groups: list[DemandGroupBulkTemplate]) -> list[DemandGroupBulkTemplate]:
        normalized: list[DemandGroupBulkTemplate] = []
        used_sort_orders: set[int] = set()
        next_sort_order = 10
        for template in demand_groups:
            sort_order = template.sort_order
            if sort_order is None:
                while next_sort_order in used_sort_orders:
                    next_sort_order += 10
                sort_order = next_sort_order
                next_sort_order += 10
            if sort_order in used_sort_orders:
                raise ApiException(
                    409,
                    "planning.demand_group.bulk_apply.duplicate_sort_order",
                    "errors.planning.demand_group.bulk_apply.duplicate_sort_order",
                )
            used_sort_orders.add(sort_order)
            normalized.append(template.model_copy(update={"sort_order": sort_order}))
        return normalized

    def _validate_bulk_update_patch(self, tenant_id: str, patch: DemandGroupBulkUpdatePatch) -> None:
        if "function_type_id" in patch.model_fields_set and patch.function_type_id is None:
            raise ApiException(
                400,
                "planning.demand_group.bulk_update.function_type_required",
                "errors.planning.demand_group.bulk_update.function_type_required",
                details={"reason_codes": ["function_type_required"]},
            )
        function_type_id = patch.function_type_id
        if function_type_id is not None:
            self._require_function(tenant_id, function_type_id)
        qualification_type_id = patch.qualification_type_id
        if qualification_type_id is not None:
            self._require_qualification(tenant_id, qualification_type_id)
        if "status" in patch.model_fields_set and patch.status not in {None, "active", "archived"}:
            raise ApiException(
                400,
                "planning.demand_group.bulk_update.invalid_status",
                "errors.planning.demand_group.bulk_update.invalid_status",
                details={"reason_codes": ["invalid_status"]},
            )

    def _resolve_bulk_target_shifts(
        self,
        tenant_id: str,
        *,
        shift_plan_id: str,
        shift_series_id: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> list[Shift]:
        candidate_shifts = self.repository.list_shifts(
            tenant_id,
            ShiftListFilter(shift_plan_id=shift_plan_id, include_archived=False),
        )
        target_shifts = [
            shift
            for shift in candidate_shifts
            if shift.source_kind_code == "generated"
            and (shift_series_id is None or shift.shift_series_id == shift_series_id)
            and self._shift_in_bulk_date_window(shift, date_from, date_to)
        ]
        if not target_shifts:
            raise ApiException(
                404,
                "planning.demand_group.bulk_update.no_target_shifts",
                "errors.planning.demand_group.bulk_update.no_target_shifts",
                details={"reason_codes": ["no_target_shifts"]},
            )
        return target_shifts

    def _collect_matching_demand_groups(self, tenant_id: str, target_shifts: list[Shift], match) -> list[DemandGroup]:  # noqa: ANN001
        matched: list[DemandGroup] = []
        for shift in target_shifts:
            for group in self.repository.list_demand_groups(tenant_id, StaffingFilter(shift_id=shift.id, include_archived=False)):
                if group.status != "active":
                    continue
                if self._demand_group_matches_signature(group, match):
                    matched.append(group)
        return matched

    @staticmethod
    def _demand_group_matches_signature(group: DemandGroup, match) -> bool:  # noqa: ANN001
        if group.function_type_id != match.function_type_id:
            return False
        if "qualification_type_id" in match.model_fields_set and group.qualification_type_id != match.qualification_type_id:
            return False
        if "min_qty" in match.model_fields_set and group.min_qty != match.min_qty:
            return False
        if "target_qty" in match.model_fields_set and group.target_qty != match.target_qty:
            return False
        if "mandatory_flag" in match.model_fields_set and group.mandatory_flag != match.mandatory_flag:
            return False
        if "sort_order" in match.model_fields_set and group.sort_order != match.sort_order:
            return False
        if "remark" in match.model_fields_set and (group.remark or None) != (match.remark or None):
            return False
        return True

    def _validate_bulk_update_sort_order_conflicts(
        self,
        tenant_id: str,
        matched_groups: list[DemandGroup],
        patch: DemandGroupBulkUpdatePatch,
    ) -> None:
        desired_by_shift: dict[str, set[int]] = defaultdict(set)
        matched_ids = {group.id for group in matched_groups}
        sort_order_changed = "sort_order" in patch.model_fields_set
        for group in matched_groups:
            desired_sort_order = self._field_value(patch, "sort_order", group.sort_order)
            if desired_sort_order in desired_by_shift[group.shift_id]:
                raise ApiException(
                    409,
                    "planning.demand_group.bulk_update.sort_order_conflict",
                    "errors.planning.demand_group.bulk_update.sort_order_conflict",
                    details={"reason_codes": ["duplicate_sort_order_in_shift"]},
                )
            desired_by_shift[group.shift_id].add(desired_sort_order)
            if not sort_order_changed:
                continue
            for row in self.repository.list_demand_groups(tenant_id, StaffingFilter(shift_id=group.shift_id, include_archived=False)):
                if row.id in matched_ids:
                    continue
                if row.sort_order == desired_sort_order:
                    raise ApiException(
                        409,
                        "planning.demand_group.bulk_update.sort_order_conflict",
                        "errors.planning.demand_group.bulk_update.sort_order_conflict",
                        details={
                            "reason_codes": ["sort_order_conflict"],
                            "shift_id": group.shift_id,
                            "conflict_demand_group_id": row.id,
                        },
                    )

    def _assert_demand_group_groups_editable(self, tenant_id: str, demand_groups: list[DemandGroup]) -> None:
        state = self._collect_demand_group_editability_state(tenant_id, demand_groups, include_deployment_outputs=True)
        reason_codes = state["reason_codes"]
        downstream_counts = state["downstream_counts"]

        if reason_codes:
            raise ApiException(
                409,
                "planning.demand_group.edit_blocked",
                "errors.planning.demand_group.edit_blocked",
                details={
                    "reason_codes": sorted(reason_codes),
                    "downstream_counts": downstream_counts,
                },
            )

    def _collect_demand_group_editability_state(
        self,
        tenant_id: str,
        demand_groups: list[DemandGroup],
        *,
        include_deployment_outputs: bool,
    ) -> dict[str, object]:
        reason_codes: set[str] = set()
        downstream_counts = {
            "assignment_count": 0,
            "subcontractor_release_count": 0,
            "released_shift_count": 0,
            "customer_visible_shift_count": 0,
            "subcontractor_visible_shift_count": 0,
            "deployment_output_count": 0,
        }
        seen_shift_ids: set[str] = set()

        for demand_group in demand_groups:
            active_assignments = [
                row
                for row in getattr(demand_group, "assignments", [])
                if getattr(row, "archived_at", None) is None and getattr(row, "assignment_status_code", None) != "removed"
            ]
            if active_assignments:
                reason_codes.add("assignments_exist")
                downstream_counts["assignment_count"] += len(active_assignments)

            active_releases = [
                row
                for row in getattr(demand_group, "subcontractor_releases", [])
                if getattr(row, "archived_at", None) is None and getattr(row, "release_status_code", None) != "revoked"
            ]
            if active_releases:
                reason_codes.add("subcontractor_releases_exist")
                downstream_counts["subcontractor_release_count"] += len(active_releases)

            if demand_group.shift_id in seen_shift_ids:
                continue
            seen_shift_ids.add(demand_group.shift_id)
            shift = getattr(demand_group, "shift", None) or self._require_shift(tenant_id, demand_group.shift_id)
            if shift.release_state != "draft":
                reason_codes.add("shift_released")
                downstream_counts["released_shift_count"] += 1
            if shift.customer_visible_flag:
                reason_codes.add("customer_visible")
                downstream_counts["customer_visible_shift_count"] += 1
            if shift.subcontractor_visible_flag:
                reason_codes.add("subcontractor_visible")
                downstream_counts["subcontractor_visible_shift_count"] += 1
            if not include_deployment_outputs:
                continue

            output_documents = [
                row
                for row in self.repository.list_documents_for_owner(tenant_id, "ops.shift", shift.id)
                if getattr(row, "metadata", {}).get("generated_kind") == "planning_output"
            ]
            if output_documents:
                reason_codes.add("deployment_outputs_exist")
                downstream_counts["deployment_output_count"] += len(output_documents)

        return {
            "downstream_counts": downstream_counts,
            "reason_codes": sorted(reason_codes),
        }

    def _read_demand_group(self, tenant_id: str, row: DemandGroup) -> DemandGroupRead:
        base = DemandGroupRead.model_validate(row)
        state = self._collect_demand_group_editability_state(
            tenant_id,
            [row],
            include_deployment_outputs=False,
        )
        downstream_counts = state["downstream_counts"]
        reason_codes = state["reason_codes"]
        return base.model_copy(
            update={
                "active_assignment_count": downstream_counts["assignment_count"],
                "active_subcontractor_release_count": downstream_counts["subcontractor_release_count"],
                "edit_block_reason_codes": reason_codes,
                "editable_flag": not bool(reason_codes),
            }
        )

    def _validate_team_scope(self, tenant_id: str, planning_record_id: str | None, shift_id: str | None) -> None:
        if planning_record_id is None and shift_id is None:
            raise ApiException(400, "planning.team.invalid_scope", "errors.planning.team.invalid_scope")
        planning_record = self._require_planning_record(tenant_id, planning_record_id) if planning_record_id is not None else None
        shift = self._require_shift(tenant_id, shift_id) if shift_id is not None else None
        if planning_record is not None and shift is not None:
            shift_plan = self.repository.get_shift_plan(tenant_id, shift.shift_plan_id)
            if shift_plan is None or shift_plan.planning_record_id != planning_record.id:
                raise ApiException(400, "planning.team.scope_mismatch", "errors.planning.team.scope_mismatch")

    def _validate_team_member_actor(self, tenant_id: str, choice: _ActorChoice, team: Team) -> None:
        if choice.employee_id is not None:
            self._require_employee(tenant_id, choice.employee_id)
        if choice.subcontractor_worker_id is not None:
            self._require_subcontractor_worker(tenant_id, choice.subcontractor_worker_id)
        if team.shift_id is not None:
            self._require_shift(tenant_id, team.shift_id)

    def _validate_team_member_window(self, valid_from: datetime, valid_to: datetime | None) -> None:
        if valid_to is not None and valid_to < valid_from:
            raise ApiException(400, "planning.team_member.invalid_window", "errors.planning.team_member.invalid_window")

    def _validate_assignment_shape(
        self,
        tenant_id: str,
        *,
        shift: Shift,
        demand_group: DemandGroup,
        team_id: str | None,
        actor_choice: _ActorChoice,
        assignment_status_code: str,
        assignment_source_code: str,
        exclude_assignment_id: str | None = None,
    ) -> None:
        if assignment_status_code not in self.ASSIGNMENT_STATUSES:
            raise ApiException(400, "planning.assignment.invalid_status", "errors.planning.assignment.invalid_status")
        if assignment_source_code not in self.ASSIGNMENT_SOURCES:
            raise ApiException(400, "planning.assignment.invalid_source", "errors.planning.assignment.invalid_source")
        shift_plan = self.repository.get_shift_plan(tenant_id, shift.shift_plan_id)
        workforce_scope_code = getattr(shift_plan, "workforce_scope_code", None)
        if workforce_scope_code == "internal" and actor_choice.subcontractor_worker_id is not None:
            raise ApiException(
                409,
                "planning.assignment.actor_kind_scope_mismatch",
                "errors.planning.assignment.actor_kind_scope_mismatch",
                details={"reason_codes": ["actor_kind_scope_mismatch"]},
            )
        if workforce_scope_code == "subcontractor" and actor_choice.employee_id is not None:
            raise ApiException(
                409,
                "planning.assignment.actor_kind_scope_mismatch",
                "errors.planning.assignment.actor_kind_scope_mismatch",
                details={"reason_codes": ["actor_kind_scope_mismatch"]},
            )
        if team_id is not None:
            team = self._require_team(tenant_id, team_id)
            if team.shift_id is not None and team.shift_id != shift.id:
                raise ApiException(400, "planning.assignment.team_scope_mismatch", "errors.planning.assignment.team_scope_mismatch")
            if team.planning_record_id is not None and shift_plan and team.planning_record_id != shift_plan.planning_record_id:
                raise ApiException(400, "planning.assignment.team_scope_mismatch", "errors.planning.assignment.team_scope_mismatch")
        if actor_choice.employee_id is not None:
            self._require_employee(tenant_id, actor_choice.employee_id)
        if actor_choice.subcontractor_worker_id is not None:
            worker = self._require_subcontractor_worker(tenant_id, actor_choice.subcontractor_worker_id)
            self._validate_worker_release_capacity(tenant_id, shift.id, demand_group.id, worker.subcontractor_id, exclude_assignment_id)
        for row in self.repository.list_assignments(tenant_id, StaffingFilter(shift_id=shift.id, include_archived=False)):
            if exclude_assignment_id is not None and row.id == exclude_assignment_id:
                continue
            if row.assignment_status_code == "removed":
                continue
            if actor_choice.employee_id is not None and row.employee_id == actor_choice.employee_id:
                raise ApiException(409, "planning.assignment.duplicate_actor", "errors.planning.assignment.duplicate_actor")
            if actor_choice.subcontractor_worker_id is not None and row.subcontractor_worker_id == actor_choice.subcontractor_worker_id:
                raise ApiException(409, "planning.assignment.duplicate_actor", "errors.planning.assignment.duplicate_actor")

    def _validate_release_qty(
        self,
        tenant_id: str,
        shift_id: str,
        demand_group_id: str | None,
        subcontractor_id: str,
        released_qty: int,
        *,
        exclude_release_id: str | None = None,
    ) -> None:
        assigned_qty = 0
        for assignment in self.repository.list_assignments(tenant_id, StaffingFilter(shift_id=shift_id, demand_group_id=demand_group_id, include_archived=False)):
            if assignment.assignment_status_code == "removed" or assignment.subcontractor_worker_id is None:
                continue
            worker = self.repository.get_subcontractor_worker(tenant_id, assignment.subcontractor_worker_id)
            if worker is not None and worker.subcontractor_id == subcontractor_id:
                assigned_qty += 1
        active_other_release_qty = 0
        for row in self.repository.list_subcontractor_releases(tenant_id, StaffingFilter(shift_id=shift_id, demand_group_id=demand_group_id, subcontractor_id=subcontractor_id, include_archived=False)):
            if exclude_release_id is not None and row.id == exclude_release_id:
                continue
            if row.release_status_code != "revoked":
                active_other_release_qty += row.released_qty
        if released_qty < assigned_qty:
            raise ApiException(400, "planning.subcontractor_release.invalid_qty_window", "errors.planning.subcontractor_release.invalid_qty_window")
        if active_other_release_qty and exclude_release_id is None:
            raise ApiException(409, "planning.subcontractor_release.duplicate_active", "errors.planning.subcontractor_release.duplicate_active")

    def _validate_worker_release_capacity(
        self,
        tenant_id: str,
        shift_id: str,
        demand_group_id: str,
        subcontractor_id: str,
        exclude_assignment_id: str | None,
    ) -> None:
        releases = [
            row
            for row in self.repository.list_subcontractor_releases(
                tenant_id,
                StaffingFilter(shift_id=shift_id, demand_group_id=demand_group_id, subcontractor_id=subcontractor_id, include_archived=False),
            )
            if row.release_status_code != "revoked"
        ]
        if not releases:
            raise ApiException(400, "planning.assignment.release_required", "errors.planning.assignment.release_required")
        assigned_qty = 0
        for row in self.repository.list_assignments(tenant_id, StaffingFilter(shift_id=shift_id, demand_group_id=demand_group_id, include_archived=False)):
            if exclude_assignment_id is not None and row.id == exclude_assignment_id:
                continue
            if row.assignment_status_code == "removed" or row.subcontractor_worker_id is None:
                continue
            worker = self.repository.get_subcontractor_worker(tenant_id, row.subcontractor_worker_id)
            if worker is not None and worker.subcontractor_id == subcontractor_id:
                assigned_qty += 1
        if assigned_qty >= sum(row.released_qty for row in releases):
            raise ApiException(400, "planning.assignment.release_capacity_exceeded", "errors.planning.assignment.release_capacity_exceeded")

    def _validate_team_lead(self, tenant_id: str, team_id: str, is_team_lead: bool, exclude_member_id: str | None) -> None:
        if not is_team_lead:
            return
        for row in self.repository.list_team_members(tenant_id, StaffingFilter(team_id=team_id, include_archived=False)):
            if exclude_member_id is not None and row.id == exclude_member_id:
                continue
            if row.archived_at is None and row.is_team_lead:
                raise ApiException(409, "planning.team_member.duplicate_lead", "errors.planning.team_member.duplicate_lead")

    def _coverage_state(self, min_qty: int, target_qty: int, assigned_count: int, confirmed_count: int, released_partner_qty: int) -> str:
        if target_qty > 0 and assigned_count >= target_qty and confirmed_count >= min(target_qty, assigned_count):
            return "green"
        if assigned_count + released_partner_qty >= min_qty:
            return "yellow"
        return "red"

    def _read_team(self, row: Team) -> TeamRead:
        return TeamRead.model_validate(row)

    @staticmethod
    def _shift_in_bulk_date_window(shift: Shift, date_from: date | None, date_to: date | None) -> bool:
        shift_date = shift.occurrence_date or shift.starts_at.date()
        if date_from is not None and shift_date < date_from:
            return False
        if date_to is not None and shift_date > date_to:
            return False
        return True

    def _require_shift(self, tenant_id: str, shift_id: str) -> Shift:
        row = self.repository.get_shift(tenant_id, shift_id)
        if row is None:
            raise self._not_found("shift")
        return row

    def _require_shift_plan(self, tenant_id: str, shift_plan_id: str):
        row = self.repository.get_shift_plan(tenant_id, shift_plan_id)
        if row is None:
            raise self._not_found("shift_plan")
        return row

    def _require_demand_group(self, tenant_id: str, demand_group_id: str) -> DemandGroup:
        row = self.repository.get_demand_group(tenant_id, demand_group_id)
        if row is None:
            raise self._not_found("demand_group")
        return row

    def _require_team(self, tenant_id: str, team_id: str) -> Team:
        row = self.repository.get_team(tenant_id, team_id)
        if row is None:
            raise self._not_found("team")
        return row

    def _require_team_member(self, tenant_id: str, team_member_id: str) -> TeamMember:
        row = self.repository.get_team_member(tenant_id, team_member_id)
        if row is None:
            raise self._not_found("team_member")
        return row

    def _require_assignment(self, tenant_id: str, assignment_id: str) -> Assignment:
        row = self.repository.get_assignment(tenant_id, assignment_id)
        if row is None:
            raise self._not_found("assignment")
        return row

    def _require_subcontractor_release(self, tenant_id: str, release_id: str) -> SubcontractorRelease:
        row = self.repository.get_subcontractor_release(tenant_id, release_id)
        if row is None:
            raise self._not_found("subcontractor_release")
        return row

    def _require_planning_record(self, tenant_id: str, planning_record_id: str | None):
        if planning_record_id is None:
            return None
        row = self.repository.get_planning_record(tenant_id, planning_record_id)
        if row is None:
            raise self._not_found("planning_record")
        return row

    def _require_function(self, tenant_id: str, function_type_id: str) -> None:
        if self.repository.get_function_type(tenant_id, function_type_id) is None:
            raise ApiException(404, "planning.demand_group.function_type_not_found", "errors.planning.demand_group.function_type_not_found")

    def _require_qualification(self, tenant_id: str, qualification_type_id: str) -> None:
        if self.repository.get_qualification_type(tenant_id, qualification_type_id) is None:
            raise ApiException(404, "planning.demand_group.qualification_type_not_found", "errors.planning.demand_group.qualification_type_not_found")

    def _require_employee(self, tenant_id: str, employee_id: str):
        row = self.repository.get_employee(tenant_id, employee_id)
        if row is None:
            raise ApiException(404, "planning.assignment.employee_not_found", "errors.planning.assignment.employee_not_found")
        return row

    def _require_subcontractor(self, tenant_id: str, subcontractor_id: str):
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise ApiException(404, "planning.subcontractor_release.subcontractor_not_found", "errors.planning.subcontractor_release.subcontractor_not_found")
        return row

    def _require_subcontractor_worker(self, tenant_id: str, worker_id: str):
        row = self.repository.get_subcontractor_worker(tenant_id, worker_id)
        if row is None:
            raise ApiException(404, "planning.assignment.subcontractor_worker_not_found", "errors.planning.assignment.subcontractor_worker_not_found")
        return row

    def _validate_actor_choice(self, employee_id: str | None, subcontractor_worker_id: str | None, *, code_prefix: str) -> _ActorChoice:
        if (employee_id is None and subcontractor_worker_id is None) or (
            employee_id is not None and subcontractor_worker_id is not None
        ):
            raise ApiException(400, f"{code_prefix}.invalid_actor_choice", f"errors.{code_prefix}.invalid_actor_choice")
        return _ActorChoice(employee_id=employee_id, subcontractor_worker_id=subcontractor_worker_id)

    def _require_tenant_scope(self, path_tenant_id: str, payload_tenant_id: str | None) -> None:
        if payload_tenant_id is not None and payload_tenant_id != path_tenant_id:
            raise ApiException(400, "planning.staffing.scope_mismatch", "errors.planning.staffing.scope_mismatch")

    def _field_value(self, payload, field_name: str, current):  # noqa: ANN001
        if field_name in payload.model_fields_set:
            return getattr(payload, field_name)
        return current

    def _not_found(self, code: str) -> ApiException:
        return ApiException(404, f"planning.{code}.not_found", f"errors.planning.{code}.not_found")

    @classmethod
    def _snapshot(cls, row) -> dict[str, object]:  # noqa: ANN001
        try:
            mapper = sa_inspect(row).mapper
        except NoInspectionAvailable:
            source_items = vars(row).items()
        else:
            source_items = ((attribute.key, getattr(row, attribute.key)) for attribute in mapper.column_attrs)

        data: dict[str, object] = {}
        for key, value in source_items:
            if key.startswith("_"):
                continue
            serialized = cls._json_safe_snapshot_value(value)
            if serialized is cls._SKIP_SNAPSHOT_VALUE:
                continue
            data[key] = serialized
        return data

    @classmethod
    def _json_safe_snapshot_value(cls, value: object) -> object:
        if value is None or isinstance(value, bool | int | float | str):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime | date | time):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return cls._json_safe_snapshot_value(value.value)
        if isinstance(value, dict):
            result: dict[str, object] = {}
            for key, item in value.items():
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result[str(key)] = serialized
            return result
        if isinstance(value, list | tuple):
            result: list[object] = []
            for item in value:
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result.append(serialized)
            return result
        if isinstance(value, set):
            result: list[object] = []
            for item in sorted(value, key=repr):
                serialized = cls._json_safe_snapshot_value(item)
                if serialized is cls._SKIP_SNAPSHOT_VALUE:
                    continue
                result.append(serialized)
            return result
        return cls._SKIP_SNAPSHOT_VALUE

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                user_id=actor.user_id,
                tenant_id=tenant_id,
                request_id=actor.request_id,
                session_id=actor.session_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json or {},
            after_json=after_json or {},
            metadata_json={"source": "planning.staffing"},
        )

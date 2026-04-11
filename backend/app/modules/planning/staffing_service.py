"""Service layer for planning staffing entities, board commands, releases, and coverage."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import Assignment, AssignmentValidationOverride, DemandGroup, Shift, SubcontractorRelease, Team, TeamMember
from app.modules.planning.schemas import (
    AssignmentValidationOverrideCreate,
    AssignmentValidationOverrideRead,
    AssignmentValidationRead,
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    CoverageDemandGroupItem,
    CoverageFilter,
    CoverageShiftItem,
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
    ShiftReleaseValidationRead,
)
from app.modules.planning.validation_service import PlanningValidationService


class StaffingRepository(Protocol):
    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None: ...
    def get_shift_plan(self, tenant_id: str, row_id: str): ...
    def list_board_shifts(self, tenant_id: str, filters: StaffingBoardFilter) -> list[dict[str, object]]: ...
    def get_function_type(self, tenant_id: str, function_type_id: str): ...
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str): ...
    def get_planning_record(self, tenant_id: str, planning_record_id: str): ...
    def get_employee(self, tenant_id: str, employee_id: str): ...
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str): ...
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str): ...
    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter) -> list[DemandGroup]: ...
    def get_demand_group(self, tenant_id: str, row_id: str) -> DemandGroup | None: ...
    def create_demand_group(self, tenant_id: str, payload: DemandGroupCreate, actor_user_id: str | None) -> DemandGroup: ...
    def update_demand_group(self, tenant_id: str, row_id: str, payload: DemandGroupUpdate, actor_user_id: str | None) -> DemandGroup | None: ...
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
    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[object]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...
    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date): ...  # noqa: ANN001
    def list_overlapping_assignments(self, tenant_id: str, *, starts_at: datetime, ends_at: datetime, employee_id: str | None, subcontractor_worker_id: str | None, exclude_assignment_id: str | None = None) -> list[Assignment]: ...
    def list_assignments_for_actor_in_window(self, tenant_id: str, *, employee_id: str | None, subcontractor_worker_id: str | None, window_start: datetime, window_end: datetime, exclude_assignment_id: str | None = None) -> list[Assignment]: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Assignment]: ...
    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[DemandGroup]: ...
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[SubcontractorRelease]: ...
    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[Shift]: ...


@dataclass(frozen=True)
class _ActorChoice:
    employee_id: str | None
    subcontractor_worker_id: str | None


class StaffingService:
    ASSIGNMENT_STATUSES = frozenset({"offered", "assigned", "confirmed", "removed"})
    ASSIGNMENT_SOURCES = frozenset({"dispatcher", "subcontractor_release", "portal_allocation", "manual"})
    RELEASE_STATUSES = frozenset({"draft", "released", "revoked"})

    def __init__(self, repository: StaffingRepository, *, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service
        self.validation_service = PlanningValidationService(repository)

    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter, _actor: RequestAuthorizationContext) -> list[DemandGroupRead]:
        return [DemandGroupRead.model_validate(row) for row in self.repository.list_demand_groups(tenant_id, filters)]

    def get_demand_group(self, tenant_id: str, demand_group_id: str, _actor: RequestAuthorizationContext) -> DemandGroupRead:
        return DemandGroupRead.model_validate(self._require_demand_group(tenant_id, demand_group_id))

    def create_demand_group(self, tenant_id: str, payload: DemandGroupCreate, actor: RequestAuthorizationContext) -> DemandGroupRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift = self._require_shift(tenant_id, payload.shift_id)
        self._validate_demand_group(payload.min_qty, payload.target_qty)
        self._require_function(tenant_id, payload.function_type_id)
        if payload.qualification_type_id is not None:
            self._require_qualification(tenant_id, payload.qualification_type_id)
        row = self.repository.create_demand_group(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.demand_group.created", "ops.demand_group", row.id, tenant_id, after_json=self._snapshot(row) | {"shift_plan_id": shift.shift_plan_id})
        return DemandGroupRead.model_validate(row)

    def update_demand_group(self, tenant_id: str, demand_group_id: str, payload: DemandGroupUpdate, actor: RequestAuthorizationContext) -> DemandGroupRead:
        current = self._require_demand_group(tenant_id, demand_group_id)
        before_json = self._snapshot(current)
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
        return DemandGroupRead.model_validate(row)

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
        if team_id is not None:
            team = self._require_team(tenant_id, team_id)
            if team.shift_id is not None and team.shift_id != shift.id:
                raise ApiException(400, "planning.assignment.team_scope_mismatch", "errors.planning.assignment.team_scope_mismatch")
            shift_plan = self.repository.get_shift_plan(tenant_id, shift.shift_plan_id)
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

    def _require_shift(self, tenant_id: str, shift_id: str) -> Shift:
        row = self.repository.get_shift(tenant_id, shift_id)
        if row is None:
            raise self._not_found("shift")
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

    def _snapshot(self, row) -> dict[str, object]:  # noqa: ANN001
        data: dict[str, object] = {}
        for key, value in row.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        return data

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

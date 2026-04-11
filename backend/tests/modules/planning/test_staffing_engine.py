from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.models import Assignment, AssignmentValidationOverride, DemandGroup, Shift, ShiftPlan, ShiftTemplate, SubcontractorRelease, Team, TeamMember
from app.modules.planning.schemas import (
    AssignmentCreate,
    CoverageFilter,
    DemandGroupCreate,
    ShiftCreate,
    ShiftPlanCreate,
    ShiftTemplateCreate,
    StaffingAssignCommand,
    StaffingBoardFilter,
    StaffingFilter,
    StaffingSubstituteCommand,
    SubcontractorReleaseCreate,
    TeamCreate,
    TeamMemberCreate,
)
from app.modules.planning.shift_service import ShiftPlanningService
from app.modules.planning.staffing_service import StaffingService
from tests.modules.planning.test_ops_master_foundation import RecordingAuditRepository, _context
from tests.modules.planning.test_shift_planning import FakeShiftPlanningRepository


@dataclass
class FakeStaffingRepository(FakeShiftPlanningRepository):
    demand_groups: dict[str, DemandGroup] = field(default_factory=dict)
    teams: dict[str, Team] = field(default_factory=dict)
    team_members: dict[str, TeamMember] = field(default_factory=dict)
    assignments: dict[str, Assignment] = field(default_factory=dict)
    subcontractor_releases: dict[str, SubcontractorRelease] = field(default_factory=dict)
    employees: dict[str, object] = field(default_factory=dict)
    subcontractors: dict[str, object] = field(default_factory=dict)
    subcontractor_workers: dict[str, object] = field(default_factory=dict)
    function_types: dict[str, object] = field(default_factory=dict)
    qualification_types: dict[str, object] = field(default_factory=dict)
    tenant_settings: dict[str, dict[str, object]] = field(default_factory=dict)
    employee_qualifications: dict[str, list[object]] = field(default_factory=dict)
    worker_qualifications: dict[str, list[object]] = field(default_factory=dict)
    owner_documents: dict[tuple[str, str, str], list[object]] = field(default_factory=dict)
    customer_employee_blocks: list[object] = field(default_factory=list)
    assignment_validation_overrides: dict[str, list[AssignmentValidationOverride]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        now = datetime.now(UTC)
        self.function_types["function-1"] = SimpleNamespace(id="function-1", tenant_id=self.tenant_id, status="active")
        self.function_types["function-2"] = SimpleNamespace(id="function-2", tenant_id=self.tenant_id, status="active")
        self.qualification_types["qualification-1"] = SimpleNamespace(
            id="qualification-1",
            tenant_id=self.tenant_id,
            status="active",
            expiry_required=True,
            proof_required=True,
        )
        self.employees["employee-1"] = SimpleNamespace(id="employee-1", tenant_id=self.tenant_id, status="active")
        self.employees["employee-2"] = SimpleNamespace(id="employee-2", tenant_id=self.tenant_id, status="active")
        self.subcontractors["sub-1"] = SimpleNamespace(id="sub-1", tenant_id=self.tenant_id, status="active")
        self.subcontractors["sub-2"] = SimpleNamespace(id="sub-2", tenant_id=self.tenant_id, status="active")
        self.subcontractor_workers["worker-1"] = SimpleNamespace(
            id="worker-1",
            tenant_id=self.tenant_id,
            subcontractor_id="sub-1",
            status="active",
            created_at=now,
            updated_at=now,
        )
        self.employee_qualifications["employee-1"] = [
            SimpleNamespace(
                id="eq-function-1",
                tenant_id=self.tenant_id,
                employee_id="employee-1",
                record_kind="function",
                function_type_id="function-1",
                qualification_type_id=None,
                valid_until=None,
                archived_at=None,
                status="active",
                qualification_type=None,
            ),
            SimpleNamespace(
                id="eq-qualification-1",
                tenant_id=self.tenant_id,
                employee_id="employee-1",
                record_kind="qualification",
                function_type_id=None,
                qualification_type_id="qualification-1",
                valid_until=date(2026, 12, 31),
                archived_at=None,
                status="active",
                qualification_type=self.qualification_types["qualification-1"],
            ),
        ]
        self.employee_qualifications["employee-2"] = [
            SimpleNamespace(
                id="eq-function-2",
                tenant_id=self.tenant_id,
                employee_id="employee-2",
                record_kind="function",
                function_type_id="function-1",
                qualification_type_id=None,
                valid_until=None,
                archived_at=None,
                status="active",
                qualification_type=None,
            )
        ]
        self.worker_qualifications["worker-1"] = [
            SimpleNamespace(
                id="wq-1",
                tenant_id=self.tenant_id,
                subcontractor_worker_id="worker-1",
                qualification_type_id="qualification-1",
                valid_until=date(2026, 12, 31),
                archived_at=None,
                status="active",
                qualification_type=self.qualification_types["qualification-1"],
            )
        ]
        self.owner_documents[("tenant-1", "hr.employee_qualification", "eq-qualification-1")] = [SimpleNamespace(id="doc-1")]
        self.owner_documents[("tenant-1", "partner.subcontractor_worker_qualification", "wq-1")] = [SimpleNamespace(id="doc-2")]
        self.subcontractor_workers["worker-2"] = SimpleNamespace(
            id="worker-2",
            tenant_id=self.tenant_id,
            subcontractor_id="sub-1",
            status="active",
            created_at=now,
            updated_at=now,
        )
        self.subcontractor_workers["worker-3"] = SimpleNamespace(
            id="worker-3",
            tenant_id=self.tenant_id,
            subcontractor_id="sub-2",
            status="active",
            created_at=now,
            updated_at=now,
        )

    def get_function_type(self, tenant_id: str, function_type_id: str):
        row = self.function_types.get(function_type_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str):
        row = self.qualification_types.get(qualification_type_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_employee(self, tenant_id: str, employee_id: str):
        row = self.employees.get(employee_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str):
        row = self.subcontractors.get(subcontractor_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str):
        row = self.subcontractor_workers.get(worker_id)
        return row if row and row.tenant_id == tenant_id else None

    def get_shift(self, tenant_id: str, row_id: str):
        row = super().get_shift(tenant_id, row_id)
        if row is None:
            return None
        shift_plan = self.shift_plans.get(row.shift_plan_id)
        planning_record = self.planning_records.get(shift_plan.planning_record_id) if shift_plan is not None else None
        order = self.orders.get(planning_record.order_id) if planning_record is not None else None
        row.shift_plan = shift_plan
        if shift_plan is not None:
            shift_plan.planning_record = planning_record
        if planning_record is not None:
            planning_record.order = order
        return row

    def get_tenant_setting_value(self, tenant_id: str, key: str):
        return self.tenant_settings.get((tenant_id, key))

    def list_employee_qualifications(self, tenant_id: str, employee_id: str):
        return [
            row
            for row in self.employee_qualifications.get(employee_id, [])
            if getattr(row, "tenant_id", tenant_id) == tenant_id
        ]

    def list_worker_qualifications(self, tenant_id: str, worker_id: str):
        return [
            row
            for row in self.worker_qualifications.get(worker_id, [])
            if getattr(row, "tenant_id", tenant_id) == tenant_id
        ]

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        return list(self.owner_documents.get((tenant_id, owner_type, owner_id), []))

    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date: date):
        result = []
        for row in self.customer_employee_blocks:
            if row.tenant_id != tenant_id or row.customer_id != customer_id or row.employee_id != employee_id:
                continue
            if row.archived_at is not None or row.status != "active":
                continue
            if row.effective_from and row.effective_from > on_date:
                continue
            if row.effective_to and row.effective_to < on_date:
                continue
            result.append(row)
        return result

    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter):
        rows = [row for row in self.demand_groups.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        if filters.demand_group_id is not None:
            rows = [row for row in rows if row.id == filters.demand_group_id]
        for row in rows:
            row.assignments = [item for item in self.assignments.values() if item.demand_group_id == row.id]
            row.subcontractor_releases = [item for item in self.subcontractor_releases.values() if item.demand_group_id == row.id]
        return sorted(rows, key=lambda row: (row.sort_order, row.id))

    def get_demand_group(self, tenant_id: str, row_id: str):
        rows = [row for row in self.list_demand_groups(tenant_id, StaffingFilter(include_archived=True)) if row.id == row_id]
        return rows[0] if rows else None

    def create_demand_group(self, tenant_id: str, payload, actor_user_id: str | None):
        row = DemandGroup(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            min_qty=payload.min_qty,
            target_qty=payload.target_qty,
            mandatory_flag=payload.mandatory_flag,
            sort_order=payload.sort_order,
            remark=payload.remark,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.assignments = []
        row.subcontractor_releases = []
        self.demand_groups[row.id] = row
        return row

    def update_demand_group(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_demand_group(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.demand_group.stale_version", "errors.planning.demand_group.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_teams(self, tenant_id: str, filters: StaffingFilter):
        rows = [row for row in self.teams.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.planning_record_id is not None:
            rows = [row for row in rows if row.planning_record_id == filters.planning_record_id]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        if filters.team_id is not None:
            rows = [row for row in rows if row.id == filters.team_id]
        for row in rows:
            row.members = [item for item in self.team_members.values() if item.team_id == row.id]
            row.assignments = [item for item in self.assignments.values() if item.team_id == row.id]
        return sorted(rows, key=lambda row: row.name)

    def get_team(self, tenant_id: str, row_id: str):
        rows = [row for row in self.list_teams(tenant_id, StaffingFilter(include_archived=True)) if row.id == row_id]
        return rows[0] if rows else None

    def create_team(self, tenant_id: str, payload, actor_user_id: str | None):
        row = Team(
            tenant_id=tenant_id,
            planning_record_id=payload.planning_record_id,
            shift_id=payload.shift_id,
            name=payload.name,
            role_label=payload.role_label,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.members = []
        row.assignments = []
        self.teams[row.id] = row
        return row

    def update_team(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_team(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.team.stale_version", "errors.planning.team.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_team_members(self, tenant_id: str, filters: StaffingFilter):
        rows = [row for row in self.team_members.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.team_id is not None:
            rows = [row for row in rows if row.team_id == filters.team_id]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.subcontractor_worker_id is not None:
            rows = [row for row in rows if row.subcontractor_worker_id == filters.subcontractor_worker_id]
        return sorted(rows, key=lambda row: (row.valid_from, row.id))

    def get_team_member(self, tenant_id: str, row_id: str):
        row = self.team_members.get(row_id)
        return row if row and row.tenant_id == tenant_id else None

    def create_team_member(self, tenant_id: str, payload, actor_user_id: str | None):
        row = TeamMember(
            tenant_id=tenant_id,
            team_id=payload.team_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            role_label=payload.role_label,
            is_team_lead=payload.is_team_lead,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.team_members[row.id] = row
        return row

    def update_team_member(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_team_member(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.team_member.stale_version", "errors.planning.team_member.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_assignments(self, tenant_id: str, filters: StaffingFilter):
        rows = [row for row in self.assignments.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        if filters.demand_group_id is not None:
            rows = [row for row in rows if row.demand_group_id == filters.demand_group_id]
        if filters.team_id is not None:
            rows = [row for row in rows if row.team_id == filters.team_id]
        if filters.employee_id is not None:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        if filters.subcontractor_worker_id is not None:
            rows = [row for row in rows if row.subcontractor_worker_id == filters.subcontractor_worker_id]
        if filters.assignment_status_code is not None:
            rows = [row for row in rows if row.assignment_status_code == filters.assignment_status_code]
        return sorted(rows, key=lambda row: (row.created_at, row.id))

    def get_assignment(self, tenant_id: str, row_id: str):
        row = self.assignments.get(row_id)
        return row if row and row.tenant_id == tenant_id else None

    def create_assignment(self, tenant_id: str, payload, actor_user_id: str | None):
        row = Assignment(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            team_id=payload.team_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            assignment_status_code=payload.assignment_status_code,
            assignment_source_code=payload.assignment_source_code,
            offered_at=payload.offered_at,
            confirmed_at=payload.confirmed_at,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.validation_overrides = []
        self.assignments[row.id] = row
        return row

    def update_assignment(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_assignment(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.assignment.stale_version", "errors.planning.assignment.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_subcontractor_releases(self, tenant_id: str, filters: StaffingFilter):
        rows = [row for row in self.subcontractor_releases.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_id is not None:
            rows = [row for row in rows if row.shift_id == filters.shift_id]
        if filters.demand_group_id is not None:
            rows = [row for row in rows if row.demand_group_id == filters.demand_group_id]
        if filters.subcontractor_id is not None:
            rows = [row for row in rows if row.subcontractor_id == filters.subcontractor_id]
        return sorted(rows, key=lambda row: (row.created_at, row.id))

    def get_subcontractor_release(self, tenant_id: str, row_id: str):
        row = self.subcontractor_releases.get(row_id)
        return row if row and row.tenant_id == tenant_id else None

    def create_subcontractor_release(self, tenant_id: str, payload, actor_user_id: str | None):
        row = SubcontractorRelease(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            subcontractor_id=payload.subcontractor_id,
            released_qty=payload.released_qty,
            release_status_code=payload.release_status_code,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.subcontractor_releases[row.id] = row
        return row

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
        rows = []
        for row in self.assignments.values():
            if row.tenant_id != tenant_id or row.assignment_status_code == "removed":
                continue
            if exclude_assignment_id is not None and row.id == exclude_assignment_id:
                continue
            if employee_id is not None and row.employee_id != employee_id:
                continue
            if subcontractor_worker_id is not None and row.subcontractor_worker_id != subcontractor_worker_id:
                continue
            other_shift = self.get_shift(tenant_id, row.shift_id)
            if other_shift is None or other_shift.archived_at is not None:
                continue
            if other_shift.starts_at < ends_at and other_shift.ends_at > starts_at:
                rows.append(row)
        return sorted(rows, key=lambda row: row.id)

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
        return self.list_overlapping_assignments(
            tenant_id,
            starts_at=window_start,
            ends_at=window_end,
            employee_id=employee_id,
            subcontractor_worker_id=subcontractor_worker_id,
            exclude_assignment_id=exclude_assignment_id,
        )

    def list_assignments_in_shift(self, tenant_id: str, shift_id: str):
        return [
            row
            for row in self.assignments.values()
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str):
        return [
            row
            for row in self.demand_groups.values()
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str):
        return [
            row
            for row in self.subcontractor_releases.values()
            if row.tenant_id == tenant_id and row.shift_id == shift_id and row.archived_at is None
        ]

    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str):
        return [
            row
            for row in self.shifts.values()
            if row.tenant_id == tenant_id
            and self.shift_plans[row.shift_plan_id].planning_record_id == planning_record_id
            and row.archived_at is None
        ]

    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str):
        return list(self.assignment_validation_overrides.get(assignment_id, []))

    def create_assignment_validation_override(self, row: AssignmentValidationOverride):
        self._stamp(row)
        self.assignment_validation_overrides.setdefault(row.assignment_id, []).append(row)
        assignment = self.assignments.get(row.assignment_id)
        if assignment is not None:
            assignment.validation_overrides = self.assignment_validation_overrides[row.assignment_id]
        return row

    def delete_shift(self, tenant_id: str, row_id: str) -> None:
        self.shifts.pop(row_id, None)

    def update_subcontractor_release(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_subcontractor_release(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.subcontractor_release.stale_version", "errors.planning.subcontractor_release.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_board_shifts(self, tenant_id: str, filters: StaffingBoardFilter):
        rows = []
        visibility_state = getattr(filters, "visibility_state", None)
        for shift in self.shifts.values():
            if shift.tenant_id != tenant_id or shift.archived_at is not None:
                continue
            if shift.starts_at < filters.date_from or shift.starts_at >= filters.date_to:
                continue
            if filters.shift_id is not None and shift.id != filters.shift_id:
                continue
            shift_plan = self.shift_plans[shift.shift_plan_id]
            planning_record = self.planning_records[shift_plan.planning_record_id]
            order = self.orders[planning_record.order_id]
            if filters.shift_plan_id is not None and shift_plan.id != filters.shift_plan_id:
                continue
            if filters.planning_record_id is not None and planning_record.id != filters.planning_record_id:
                continue
            if filters.order_id is not None and order.id != filters.order_id:
                continue
            if filters.planning_mode_code is not None and planning_record.planning_mode_code != filters.planning_mode_code:
                continue
            if filters.workforce_scope_code is not None and shift_plan.workforce_scope_code != filters.workforce_scope_code:
                continue
            if filters.release_state is not None and shift.release_state != filters.release_state:
                continue
            if visibility_state == "customer" and not shift.customer_visible_flag:
                continue
            if visibility_state == "subcontractor" and not shift.subcontractor_visible_flag:
                continue
            if visibility_state == "stealth" and not shift.stealth_mode_flag:
                continue
            rows.append(
                {
                    "id": shift.id,
                    "tenant_id": tenant_id,
                    "planning_record_id": planning_record.id,
                    "shift_plan_id": shift_plan.id,
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "planning_record_name": planning_record.name,
                    "planning_mode_code": planning_record.planning_mode_code,
                    "workforce_scope_code": shift_plan.workforce_scope_code,
                    "starts_at": shift.starts_at,
                    "ends_at": shift.ends_at,
                    "shift_type_code": shift.shift_type_code,
                    "release_state": shift.release_state,
                    "status": shift.status,
                    "location_text": shift.location_text,
                    "meeting_point": shift.meeting_point,
                }
            )
        return sorted(rows, key=lambda row: (row["starts_at"], row["id"]))


class StaffingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeStaffingRepository()
        self.audit_repository = RecordingAuditRepository()
        self.shift_service = ShiftPlanningService(self.repository, audit_service=AuditService(self.audit_repository))
        self.service = StaffingService(self.repository, audit_service=AuditService(self.audit_repository))
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type("RequirementPayload", (), {"customer_id": "customer-1", "code": "REQ-1", "label": "Objekt", "default_planning_mode_code": "site", "description": None})(),
            "user-1",
        )
        self.repository.sites["site-1"] = SimpleNamespace(id="site-1", tenant_id="tenant-1", customer_id="customer-1")
        order = self.repository.create_customer_order(
            "tenant-1",
            type("OrderPayload", (), {
                "customer_id": "customer-1",
                "requirement_type_id": requirement.id,
                "patrol_route_id": None,
                "order_no": "ORD-1",
                "title": "Objektschutz",
                "service_category_code": "site",
                "security_concept_text": None,
                "service_from": date(2026, 4, 1),
                "service_to": date(2026, 4, 30),
                "release_state": "draft",
                "notes": None,
            })(),
            "user-1",
        )
        planning_record = self.repository.create_planning_record(
            "tenant-1",
            type("RecordPayload", (), {
                "order_id": order.id,
                "parent_planning_record_id": None,
                "dispatcher_user_id": "dispatcher-1",
                "planning_mode_code": "site",
                "name": "April Site",
                "planning_from": date(2026, 4, 1),
                "planning_to": date(2026, 4, 30),
                "release_state": "draft",
                "notes": None,
            })(),
            "user-1",
        )
        self.repository.create_site_plan_detail(
            "tenant-1",
            planning_record.id,
            type("SiteDetailPayload", (), {"site_id": "site-1", "watchbook_scope_note": None})(),
        )
        template = self.shift_service.create_shift_template(
            "tenant-1",
            ShiftTemplateCreate(
                tenant_id="tenant-1",
                code="TPL-1",
                label="Tag",
                local_start_time=time(8, 0),
                local_end_time=time(16, 0),
                default_break_minutes=30,
                shift_type_code="site_day",
            ),
            _context("planning.shift.write"),
        )
        shift_plan = self.shift_service.create_shift_plan(
            "tenant-1",
            ShiftPlanCreate(
                tenant_id="tenant-1",
                planning_record_id=planning_record.id,
                name="Objektschutz April",
                workforce_scope_code="mixed",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 30),
            ),
            _context("planning.shift.write"),
        )
        shift = self.shift_service.create_shift(
            "tenant-1",
            ShiftCreate(
                tenant_id="tenant-1",
                shift_plan_id=shift_plan.id,
                starts_at=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
                ends_at=datetime(2026, 4, 5, 16, 0, tzinfo=UTC),
                break_minutes=30,
                shift_type_code=template.shift_type_code,
                source_kind_code="manual",
            ),
            _context("planning.shift.write"),
        )
        self.shift_id = shift.id
        self.planning_record_id = planning_record.id
        self.shift_plan_id = shift_plan.id

    def test_demand_group_requires_target_ge_min(self) -> None:
        with self.assertRaises(ApiException) as caught:
            self.service.create_demand_group(
                "tenant-1",
                DemandGroupCreate(
                    tenant_id="tenant-1",
                    shift_id=self.shift_id,
                    function_type_id="function-1",
                    min_qty=2,
                    target_qty=1,
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.code, "planning.demand_group.invalid_qty_window")

    def test_team_member_requires_exactly_one_actor(self) -> None:
        team = self.service.create_team(
            "tenant-1",
            TeamCreate(tenant_id="tenant-1", planning_record_id=self.planning_record_id, shift_id=self.shift_id, name="Alpha"),
            _context("planning.staffing.write"),
        )
        with self.assertRaises(ApiException) as caught:
            self.service.create_team_member(
                "tenant-1",
                TeamMemberCreate(
                    tenant_id="tenant-1",
                    team_id=team.id,
                    employee_id="employee-1",
                    subcontractor_worker_id="worker-1",
                    valid_from=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.code, "planning.team_member.invalid_actor_choice")

    def test_assignment_duplicate_actor_on_same_shift_is_blocked(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=2,
            ),
            _context("planning.staffing.write"),
        )
        self.service.create_assignment(
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        result = self.service.assign(
            "tenant-1",
            StaffingAssignCommand(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        self.assertEqual(result.outcome_code, "blocked")
        self.assertIn("double_booking", result.validation_codes)

    def test_substitute_marks_old_removed_and_creates_new_assignment(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        created = self.service.assign(
            "tenant-1",
            StaffingAssignCommand(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=demand.id, employee_id="employee-1"),
            _context("planning.staffing.write"),
        )
        result = self.service.substitute(
            "tenant-1",
            StaffingSubstituteCommand(
                tenant_id="tenant-1",
                assignment_id=created.assignment_id,
                version_no=created.assignment.version_no,
                replacement_employee_id="employee-2",
            ),
            _context("planning.staffing.write"),
        )
        previous = self.repository.get_assignment("tenant-1", created.assignment_id)
        self.assertEqual(previous.assignment_status_code, "removed")
        self.assertEqual(result.outcome_code, "substituted")
        self.assertEqual(result.assignment.employee_id, "employee-2")

    def test_subcontractor_release_is_required_and_capacity_is_enforced(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=2,
            ),
            _context("planning.staffing.write"),
        )
        with self.assertRaises(ApiException) as caught:
            self.service.assign(
                "tenant-1",
                StaffingAssignCommand(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=demand.id, subcontractor_worker_id="worker-1"),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.code, "planning.assignment.release_required")

        self.service.create_subcontractor_release(
            "tenant-1",
            SubcontractorReleaseCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                subcontractor_id="sub-1",
                released_qty=1,
                release_status_code="released",
            ),
            _context("planning.staffing.write"),
        )
        self.service.assign(
            "tenant-1",
            StaffingAssignCommand(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=demand.id, subcontractor_worker_id="worker-1"),
            _context("planning.staffing.write"),
        )
        with self.assertRaises(ApiException) as second:
            self.service.assign(
                "tenant-1",
                StaffingAssignCommand(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=demand.id, subcontractor_worker_id="worker-2"),
                _context("planning.staffing.write"),
            )
        self.assertEqual(second.exception.code, "planning.assignment.release_capacity_exceeded")

    def test_duplicate_team_lead_is_blocked(self) -> None:
        team = self.service.create_team(
            "tenant-1",
            TeamCreate(tenant_id="tenant-1", planning_record_id=self.planning_record_id, shift_id=self.shift_id, name="Leadteam"),
            _context("planning.staffing.write"),
        )
        self.service.create_team_member(
            "tenant-1",
            TeamMemberCreate(
                tenant_id="tenant-1",
                team_id=team.id,
                employee_id="employee-1",
                is_team_lead=True,
                valid_from=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
            ),
            _context("planning.staffing.write"),
        )
        with self.assertRaises(ApiException) as caught:
            self.service.create_team_member(
                "tenant-1",
                TeamMemberCreate(
                    tenant_id="tenant-1",
                    team_id=team.id,
                    employee_id="employee-2",
                    is_team_lead=True,
                    valid_from=datetime(2026, 4, 5, 8, 0, tzinfo=UTC),
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.code, "planning.team_member.duplicate_lead")

    def test_coverage_derives_red_yellow_and_green_states(self) -> None:
        red = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(tenant_id="tenant-1", shift_id=self.shift_id, function_type_id="function-1", min_qty=2, target_qty=3, sort_order=10),
            _context("planning.staffing.write"),
        )
        yellow = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(tenant_id="tenant-1", shift_id=self.shift_id, function_type_id="function-1", min_qty=1, target_qty=2, sort_order=20),
            _context("planning.staffing.write"),
        )
        green = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(tenant_id="tenant-1", shift_id=self.shift_id, function_type_id="function-1", min_qty=1, target_qty=1, sort_order=30),
            _context("planning.staffing.write"),
        )
        self.service.create_subcontractor_release(
            "tenant-1",
            SubcontractorReleaseCreate(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=yellow.id, subcontractor_id="sub-1", released_qty=1, release_status_code="released"),
            _context("planning.staffing.write"),
        )
        self.service.assign(
            "tenant-1",
            StaffingAssignCommand(tenant_id="tenant-1", shift_id=self.shift_id, demand_group_id=green.id, employee_id="employee-1", confirmed_at=datetime(2026, 4, 5, 7, 0, tzinfo=UTC)),
            _context("planning.staffing.write"),
        )
        coverage = self.service.coverage(
            "tenant-1",
            CoverageFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
            ),
            _context("planning.staffing.read"),
        )
        demand_states = {item.demand_group_id: item.coverage_state for item in coverage[0].demand_groups}
        self.assertEqual(demand_states[red.id], "red")
        self.assertEqual(demand_states[yellow.id], "yellow")
        self.assertEqual(demand_states[green.id], "green")

    def test_staffing_board_without_visibility_state_does_not_crash(self) -> None:
        rows = self.service.staffing_board(
            "tenant-1",
            StaffingBoardFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
            ),
            _context("planning.staffing.read"),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, self.shift_id)

    def test_coverage_without_visibility_state_does_not_crash(self) -> None:
        rows = self.service.coverage(
            "tenant-1",
            CoverageFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
            ),
            _context("planning.staffing.read"),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shift_id, self.shift_id)

    def test_staffing_board_supports_customer_visibility_filter(self) -> None:
        shift = self.repository.get_shift("tenant-1", self.shift_id)
        assert shift is not None
        shift.customer_visible_flag = True

        rows = self.service.staffing_board(
            "tenant-1",
            StaffingBoardFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
                visibility_state="customer",
            ),
            _context("planning.staffing.read"),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, self.shift_id)

    def test_staffing_board_supports_subcontractor_visibility_filter(self) -> None:
        shift = self.repository.get_shift("tenant-1", self.shift_id)
        assert shift is not None
        shift.subcontractor_visible_flag = True

        rows = self.service.staffing_board(
            "tenant-1",
            StaffingBoardFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
                visibility_state="subcontractor",
            ),
            _context("planning.staffing.read"),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, self.shift_id)

    def test_coverage_passes_visibility_state_through_to_staffing_board(self) -> None:
        shift = self.repository.get_shift("tenant-1", self.shift_id)
        assert shift is not None
        shift.customer_visible_flag = True

        rows = self.service.coverage(
            "tenant-1",
            CoverageFilter(
                date_from=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
                visibility_state="customer",
            ),
            _context("planning.staffing.read"),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].shift_id, self.shift_id)

    def test_employee_function_mismatch_blocks_assignment(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-2",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        with self.assertRaises(ApiException) as caught:
            self.service.create_assignment(
                "tenant-1",
                AssignmentCreate(
                    tenant_id="tenant-1",
                    shift_id=self.shift_id,
                    demand_group_id=demand.id,
                    employee_id="employee-1",
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.code, "planning.assignment.blocked_by_validation")
        self.assertEqual(caught.exception.details["issues"][0]["rule_code"], "function_match")

    def test_employee_qualification_expiry_on_shift_boundary_is_enforced(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        self.repository.employee_qualifications["employee-1"][1].valid_until = self.repository.get_shift("tenant-1", self.shift_id).starts_at.date()
        assignment = self.service.create_assignment(
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        self.assertEqual(assignment.employee_id, "employee-1")

        overlapping_shift = self.shift_service.create_shift(
            "tenant-1",
            ShiftCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan_id,
                starts_at=datetime(2026, 4, 6, 8, 0, tzinfo=UTC),
                ends_at=datetime(2026, 4, 6, 16, 0, tzinfo=UTC),
                break_minutes=30,
                shift_type_code="site_day",
                source_kind_code="manual",
            ),
            _context("planning.shift.write"),
        )
        second_demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=overlapping_shift.id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        self.repository.employee_qualifications["employee-1"][1].valid_until = date(2026, 4, 5)
        with self.assertRaises(ApiException) as caught:
            self.service.create_assignment(
                "tenant-1",
                AssignmentCreate(
                    tenant_id="tenant-1",
                    shift_id=overlapping_shift.id,
                    demand_group_id=second_demand.id,
                    employee_id="employee-1",
                ),
                _context("planning.staffing.write"),
            )
        self.assertIn("certificate_validity", {issue["rule_code"] for issue in caught.exception.details["issues"]})

    def test_worker_missing_mandatory_proof_blocks_assignment(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        self.service.create_subcontractor_release(
            "tenant-1",
            SubcontractorReleaseCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                subcontractor_id="sub-1",
                released_qty=1,
                release_status_code="released",
            ),
            _context("planning.staffing.write"),
        )
        self.repository.owner_documents[("tenant-1", "partner.subcontractor_worker_qualification", "wq-1")] = []
        with self.assertRaises(ApiException) as caught:
            self.service.create_assignment(
                "tenant-1",
                AssignmentCreate(
                    tenant_id="tenant-1",
                    shift_id=self.shift_id,
                    demand_group_id=demand.id,
                    subcontractor_worker_id="worker-1",
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.details["issues"][0]["rule_code"], "mandatory_documents")

    def test_customer_block_blocks_assignment(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        self.repository.customer_employee_blocks.append(
            SimpleNamespace(
                tenant_id="tenant-1",
                customer_id="customer-1",
                employee_id="employee-1",
                effective_from=date(2026, 4, 1),
                effective_to=date(2026, 4, 30),
                status="active",
                archived_at=None,
            )
        )
        with self.assertRaises(ApiException) as caught:
            self.service.create_assignment(
                "tenant-1",
                AssignmentCreate(
                    tenant_id="tenant-1",
                    shift_id=self.shift_id,
                    demand_group_id=demand.id,
                    employee_id="employee-1",
                ),
                _context("planning.staffing.write"),
            )
        self.assertEqual(caught.exception.details["issues"][0]["rule_code"], "customer_block")

    def test_double_booking_and_rest_max_hour_rules_are_reported(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        first = self.service.create_assignment(
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        overlapping_shift = self.shift_service.create_shift(
            "tenant-1",
            ShiftCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan_id,
                starts_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
                ends_at=datetime(2026, 4, 5, 20, 0, tzinfo=UTC),
                break_minutes=30,
                shift_type_code="site_night",
                source_kind_code="manual",
            ),
            _context("planning.shift.write"),
        )
        second_demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=overlapping_shift.id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        issues = self.service._validate_assignment_payload(  # noqa: SLF001
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=overlapping_shift.id,
                demand_group_id=second_demand.id,
                employee_id="employee-1",
            ),
        )
        rule_codes = {issue.rule_code for issue in issues}
        self.assertIn("double_booking", rule_codes)
        self.assertIn("rest_period", rule_codes)
        self.assertIn("max_hours", rule_codes)

    def test_shift_release_and_planning_record_release_are_gated_by_minimum_staffing(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=2,
                target_qty=2,
            ),
            _context("planning.staffing.write"),
        )
        self.service.create_assignment(
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        shift_validations = self.service.get_shift_release_validations("tenant-1", self.shift_id, _context("planning.staffing.read"))
        self.assertEqual(shift_validations.issues[0].rule_code, "minimum_staffing")
        with self.assertRaises(ApiException) as caught:
            self.repository.planning_records[self.planning_record_id].version_no = 1
            from app.modules.planning.schemas import PlanningRecordReleaseStateUpdate
            from app.modules.planning.planning_record_service import PlanningRecordService

            PlanningRecordService(self.repository, document_repository=self.repository, validation_service=self.service.validation_service).set_planning_record_release_state(
                "tenant-1",
                self.planning_record_id,
                PlanningRecordReleaseStateUpdate(release_state="release_ready", version_no=1),
                _context("planning.record.write"),
            )
        self.assertEqual(caught.exception.code, "planning.planning_record.blocked_by_validation")

    def test_earnings_threshold_falls_back_to_info_when_provider_is_disabled(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        issues = self.service._validate_assignment_payload(  # noqa: SLF001
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
        )
        earnings = next(issue for issue in issues if issue.rule_code == "earnings_threshold")
        self.assertEqual(earnings.severity, "info")
        self.assertEqual(earnings.message_key, "errors.planning.validation.earnings_threshold_unavailable")

    def test_validation_override_is_append_only_and_demotes_overrideable_block(self) -> None:
        demand = self.service.create_demand_group(
            "tenant-1",
            DemandGroupCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            _context("planning.staffing.write"),
        )
        assignment = self.service.create_assignment(
            "tenant-1",
            AssignmentCreate(
                tenant_id="tenant-1",
                shift_id=self.shift_id,
                demand_group_id=demand.id,
                employee_id="employee-1",
            ),
            _context("planning.staffing.write"),
        )
        self.repository.employee_qualifications["employee-1"][1].valid_until = date(2026, 4, 4)
        before = self.service.get_assignment_validations("tenant-1", assignment.id, _context("planning.staffing.read"))
        cert_issue = next(issue for issue in before.issues if issue.rule_code == "certificate_validity")
        self.assertEqual(cert_issue.severity, "block")
        self.assertEqual(cert_issue.override_allowed, True)
        override = self.service.create_assignment_validation_override(
            "tenant-1",
            assignment.id,
            type("Payload", (), {"tenant_id": "tenant-1", "rule_code": "certificate_validity", "reason_text": "Dokument ist zur Verlaengerung eingereicht."})(),
            _context("planning.staffing.override"),
        )
        self.assertEqual(override.rule_code, "certificate_validity")
        self.assertEqual(len(self.service.list_assignment_validation_overrides("tenant-1", assignment.id, _context("planning.staffing.read"))), 1)
        after = self.service.get_assignment_validations("tenant-1", assignment.id, _context("planning.staffing.read"))
        overridden_issue = next(issue for issue in after.issues if issue.rule_code == "certificate_validity")
        self.assertEqual(overridden_issue.severity, "warn")
        self.assertEqual(overridden_issue.metadata["overridden"], True)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.errors import ApiException
from app.modules.employees.schemas import EmployeeReleasedScheduleResponseRequest
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.schemas import (
    AssignmentCreate,
    CustomerOrderCreate,
    DemandGroupCreate,
    PlanningRecordCreate,
    RequirementTypeCreate,
    ShiftCreate,
    ShiftPlanCreate,
    ShiftReleaseStateUpdate,
    ShiftTemplateCreate,
)
from app.modules.planning.shift_service import ShiftPlanningService
from app.modules.planning.staffing_service import StaffingService
from app.modules.planning.validation_service import PlanningValidationService
from tests.modules.planning.test_ops_master_foundation import _context
from tests.modules.planning.test_staffing_engine import FakeStaffingRepository


class EmployeeScheduleResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeStaffingRepository()
        self.actor = _context()
        self.repo.employees["employee-1"].user_id = self.actor.user_id
        self.repo.find_employee_by_user_id = lambda tenant_id, user_id, exclude_id=None: (  # type: ignore[attr-defined]
            self.repo.employees["employee-1"]
            if (
                tenant_id == self.repo.tenant_id
                and user_id == self.repo.employees["employee-1"].user_id
            )
            else None
        )
        self.shift_service = ShiftPlanningService(self.repo, validation_service=PlanningValidationService(self.repo))
        self.staffing_service = StaffingService(self.repo)
        requirement_type = self.repo.create_requirement_type(
            self.repo.tenant_id,
            RequirementTypeCreate(
                tenant_id=self.repo.tenant_id,
                customer_id="customer-1",
                code="REQ-RESP",
                label="Response",
                default_planning_mode_code="site",
            ),
            self.actor.user_id,
        )
        order = self.repo.create_customer_order(
            self.repo.tenant_id,
            CustomerOrderCreate(
                tenant_id=self.repo.tenant_id,
                customer_id="customer-1",
                requirement_type_id=requirement_type.id,
                patrol_route_id=None,
                order_no="ORD-RESP",
                title="Response Order",
                service_category_code="object_security",
                security_concept_text=None,
                service_from=date(2026, 4, 1),
                service_to=date(2026, 4, 2),
            ),
            self.actor.user_id,
        )
        planning_record = self.repo.create_planning_record(
            self.repo.tenant_id,
            PlanningRecordCreate(
                tenant_id=self.repo.tenant_id,
                order_id=order.id,
                parent_planning_record_id=None,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="site",
                name="Response Plan",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 2),
            ),
            self.actor.user_id,
        )
        template = self.shift_service.create_shift_template(
            self.repo.tenant_id,
            ShiftTemplateCreate(
                tenant_id=self.repo.tenant_id,
                code="RESP",
                label="Response",
                local_start_time=datetime(2026, 4, 1, 8, 0, tzinfo=UTC).timetz(),
                local_end_time=datetime(2026, 4, 1, 16, 0, tzinfo=UTC).timetz(),
                shift_type_code="site_day",
            ),
            self.actor,
        )
        plan = self.shift_service.create_shift_plan(
            self.repo.tenant_id,
            ShiftPlanCreate(
                tenant_id=self.repo.tenant_id,
                planning_record_id=planning_record.id,
                name="Response Shift Plan",
                workforce_scope_code="internal",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 2),
            ),
            self.actor,
        )
        self.shift = self.shift_service.create_shift(
            self.repo.tenant_id,
            ShiftCreate(
                tenant_id=self.repo.tenant_id,
                shift_plan_id=plan.id,
                starts_at=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
                ends_at=datetime(2026, 4, 1, 16, 0, tzinfo=UTC),
                break_minutes=30,
                shift_type_code=template.shift_type_code,
                location_text="HQ",
                meeting_point="Gate 1",
            ),
            self.actor,
        )
        demand_group = self.staffing_service.create_demand_group(
            self.repo.tenant_id,
            DemandGroupCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            self.actor,
        )
        self.assignment = self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=demand_group.id,
                employee_id="employee-1",
                assignment_status_code="assigned",
                assignment_source_code="dispatcher",
            ),
            self.actor,
        )
        self.shift_service.set_shift_release_state(
            self.repo.tenant_id,
            self.shift.id,
            ShiftReleaseStateUpdate(release_state="released", version_no=self.shift.version_no),
            self.actor,
        )
        self.service = ReleasedScheduleService(self.repo)

    def test_confirm_employee_assignment_updates_confirmation_state(self) -> None:
        updated = self.service.respond_employee_assignment(
            self.actor,
            self.assignment.id,
            EmployeeReleasedScheduleResponseRequest(response_code="confirm", version_no=self.assignment.version_no),
        )
        self.assertEqual(updated.assignment_status, "confirmed")
        self.assertEqual(updated.confirmation_status, "confirmed")

    def test_decline_requires_own_assignment(self) -> None:
        self.repo.employees["employee-1"].user_id = "other-user"
        with self.assertRaises(ApiException) as raised:
            self.service.respond_employee_assignment(
                self.actor,
                self.assignment.id,
                EmployeeReleasedScheduleResponseRequest(response_code="decline", version_no=self.assignment.version_no),
            )
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.message_key, "errors.employees.self_service.employee_not_found")


if __name__ == "__main__":
    unittest.main()

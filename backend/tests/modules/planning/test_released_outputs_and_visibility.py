from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.customers.schemas import CustomerPortalContextRead
from app.modules.customers.schemas import CustomerPortalContactRead, CustomerPortalCustomerRead
from app.modules.employees.schemas import EmployeeReleasedScheduleCollectionRead
from app.modules.planning.communication_service import PlanningCommunicationService
from app.modules.planning.output_service import PlanningOutputService
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.schemas import (
    AssignmentCreate,
    CustomerOrderCreate,
    DemandGroupCreate,
    PlanningDispatchCreate,
    PlanningOutputGenerateRequest,
    PlanningRecordCreate,
    RequirementTypeCreate,
    ShiftCreate,
    ShiftPlanCreate,
    ShiftReleaseStateUpdate,
    ShiftTemplateCreate,
    ShiftVisibilityUpdate,
    ShiftUpdate,
    SubcontractorReleaseCreate,
)
from app.modules.planning.shift_service import ShiftPlanningService
from app.modules.planning.staffing_service import StaffingService
from app.modules.planning.validation_service import PlanningValidationService
from app.modules.subcontractors.schemas import SubcontractorPortalContextRead
from app.modules.subcontractors.schemas import SubcontractorPortalCompanyRead, SubcontractorPortalContactRead
from tests.modules.planning.test_ops_master_foundation import _context
from tests.modules.planning.test_staffing_engine import FakeStaffingRepository


@dataclass
class FakeDocumentService:
    repository: FakeStaffingRepository
    documents: dict[str, object] = field(default_factory=dict)

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            title=payload.title,
            metadata_json=dict(payload.metadata_json),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            current_version_no=0,
            versions=[],
            links=[],
            document_type=None,
        )
        self.documents[row.id] = row
        return row

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = self.documents[document_id]
        link = SimpleNamespace(
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            relation_type=payload.relation_type,
            label=payload.label,
        )
        document.links.append(link)
        self.repository.owner_documents.setdefault((tenant_id, payload.owner_type, payload.owner_id), []).append(document)
        return link

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = self.documents[document_id]
        version = SimpleNamespace(
            version_no=document.current_version_no + 1,
            file_name=payload.file_name,
            content_type=payload.content_type,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=payload.is_revision_safe_pdf,
            metadata_json=dict(payload.metadata_json),
        )
        document.current_version_no = version.version_no
        document.updated_at = version.uploaded_at
        document.versions.append(version)
        return version


@dataclass
class FakeCommunicationService:
    messages: dict[str, object] = field(default_factory=dict)
    templates: dict[tuple[str, str, str, str], object] = field(default_factory=dict)

    def upsert_template(self, tenant_id: str, payload, actor):  # noqa: ANN001
        key = (tenant_id, payload.channel, payload.template_key, payload.language_code)
        self.templates[key] = payload
        return payload

    def render_outbound_message(self, tenant_id: str, payload, actor):  # noqa: ANN001
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            channel=payload.channel,
            template_key=payload.template_key,
            language_code=payload.language_code,
            subject_rendered=f"{payload.placeholders.get('shift_label')} {payload.placeholders.get('schedule_date')}",
            body_rendered=str(payload.placeholders),
            recipients=[
                SimpleNamespace(
                    id=str(uuid4()),
                    recipient_kind=item.recipient_kind,
                    destination=item.destination,
                    display_name=item.display_name,
                    metadata_json=item.metadata_json,
                )
                for item in payload.recipients
            ],
            metadata_json=dict(payload.metadata_json),
            related_entity_type=payload.related_entity_type,
            related_entity_id=payload.related_entity_id,
            delivery_attempts=[],
        )
        self.messages[row.id] = row
        return row

    def get_outbound_message(self, tenant_id: str, message_id: str, actor):  # noqa: ANN001
        return self.messages[message_id]


class ReleasedOutputsAndVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeStaffingRepository()
        shift_service = ShiftPlanningService(self.repo, validation_service=PlanningValidationService(self.repo))
        self.staffing_service = StaffingService(self.repo)
        actor = _context()
        self.repo.employees["employee-1"].user_id = actor.user_id
        self.repo.find_employee_by_user_id = lambda tenant_id, user_id, exclude_id=None: (  # type: ignore[attr-defined]
            self.repo.employees["employee-1"]
            if tenant_id == self.repo.tenant_id and user_id == actor.user_id
            else None
        )
        requirement_type = self.repo.create_requirement_type(
            self.repo.tenant_id,
            RequirementTypeCreate(
                tenant_id=self.repo.tenant_id,
                customer_id="customer-1",
                code="REQ-1",
                label="Objektschutz",
                default_planning_mode_code="site",
            ),
            actor.user_id,
        )
        order = self.repo.create_customer_order(
            self.repo.tenant_id,
            CustomerOrderCreate(
                tenant_id=self.repo.tenant_id,
                customer_id="customer-1",
                requirement_type_id=requirement_type.id,
                patrol_route_id=None,
                order_no="ORD-1",
                title="Order",
                service_category_code="guarding",
                security_concept_text=None,
                service_from=date(2026, 4, 1),
                service_to=date(2026, 4, 5),
            ),
            actor.user_id,
        )
        planning_record = self.repo.create_planning_record(
            self.repo.tenant_id,
            PlanningRecordCreate(
                tenant_id=self.repo.tenant_id,
                order_id=order.id,
                parent_planning_record_id=None,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="site",
                name="Planning One",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 5),
            ),
            actor.user_id,
        )
        template = shift_service.create_shift_template(
            self.repo.tenant_id,
            ShiftTemplateCreate(
                tenant_id=self.repo.tenant_id,
                code="DAY",
                label="Day",
                local_start_time=datetime(2026, 4, 1, 8, 0, tzinfo=UTC).timetz(),
                local_end_time=datetime(2026, 4, 1, 16, 0, tzinfo=UTC).timetz(),
                shift_type_code="guard",
            ),
            actor,
        )
        plan = shift_service.create_shift_plan(
            self.repo.tenant_id,
            ShiftPlanCreate(
                tenant_id=self.repo.tenant_id,
                planning_record_id=planning_record.id,
                name="Plan A",
                workforce_scope_code="mixed",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 5),
            ),
            actor,
        )
        self.shift = shift_service.create_shift(
            self.repo.tenant_id,
            ShiftCreate(
                tenant_id=self.repo.tenant_id,
                shift_plan_id=plan.id,
                starts_at=datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
                ends_at=datetime(2026, 4, 2, 16, 0, tzinfo=UTC),
                break_minutes=30,
                shift_type_code=template.shift_type_code,
                location_text="HQ",
                meeting_point="Gate 1",
            ),
            actor,
        )
        self.demand_group = self.staffing_service.create_demand_group(
            self.repo.tenant_id,
            DemandGroupCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=1,
            ),
            actor,
        )
        self.shift_service = shift_service
        self.actor = actor

    def test_release_and_visibility_are_validation_gated(self) -> None:
        with self.assertRaises(ApiException):
            self.shift_service.set_shift_release_state(
                self.repo.tenant_id,
                self.shift.id,
                ShiftReleaseStateUpdate(release_state="released", version_no=self.shift.version_no),
                self.actor,
            )

        assignment = self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                employee_id="employee-1",
                assignment_status_code="assigned",
                assignment_source_code="dispatcher",
            ),
            self.actor,
        )
        self.assertIsNotNone(assignment.id)

        released = self.shift_service.set_shift_release_state(
            self.repo.tenant_id,
            self.shift.id,
            ShiftReleaseStateUpdate(release_state="released", version_no=1),
            self.actor,
        )
        self.assertEqual(released.release_state, "released")

        visible = self.shift_service.update_shift_visibility(
            self.repo.tenant_id,
            self.shift.id,
            ShiftVisibilityUpdate(customer_visible_flag=True, subcontractor_visible_flag=True, version_no=released.version_no),
            self.actor,
        )
        self.assertTrue(visible.customer_visible_flag)
        self.assertTrue(visible.subcontractor_visible_flag)

        revoked = self.shift_service.set_shift_release_state(
            self.repo.tenant_id,
            self.shift.id,
            ShiftReleaseStateUpdate(release_state="draft", version_no=visible.version_no),
            self.actor,
        )
        self.assertFalse(revoked.customer_visible_flag)
        self.assertFalse(revoked.subcontractor_visible_flag)

    def test_output_generation_requires_release_and_links_docs(self) -> None:
        service = PlanningOutputService(self.repo, document_service=FakeDocumentService(self.repo))
        with self.assertRaises(ApiException):
            service.generate_shift_output(
                self.repo.tenant_id,
                self.shift.id,
                PlanningOutputGenerateRequest(tenant_id=self.repo.tenant_id, variant_code="deployment_plan"),
                self.actor,
            )

        self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                employee_id="employee-1",
                assignment_status_code="assigned",
                assignment_source_code="dispatcher",
            ),
            self.actor,
        )
        self.shift_service.set_shift_release_state(
            self.repo.tenant_id,
            self.shift.id,
            ShiftReleaseStateUpdate(release_state="released", version_no=1),
            self.actor,
        )
        self.shift_service.update_shift_visibility(
            self.repo.tenant_id,
            self.shift.id,
            ShiftVisibilityUpdate(customer_visible_flag=True, version_no=2),
            self.actor,
        )

        output = service.generate_shift_output(
            self.repo.tenant_id,
            self.shift.id,
            PlanningOutputGenerateRequest(tenant_id=self.repo.tenant_id, variant_code="deployment_plan", audience_code="customer"),
            self.actor,
        )
        self.assertEqual(output.content_type, "application/pdf")
        self.assertEqual(len(service.list_shift_outputs(self.repo.tenant_id, self.shift.id, self.actor)), 1)

    def test_dispatch_preview_redacts_subcontractor_audience_in_stealth_mode(self) -> None:
        self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                employee_id="employee-1",
                assignment_status_code="assigned",
                assignment_source_code="dispatcher",
            ),
            self.actor,
        )
        self.shift_service.update_shift(
            self.repo.tenant_id,
            self.shift.id,
            ShiftUpdate(stealth_mode_flag=True, version_no=1),
            self.actor,
        )
        message_service = PlanningCommunicationService(self.repo, communication_service=FakeCommunicationService())
        preview = message_service.preview_message(
            self.repo.tenant_id,
            PlanningDispatchCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                audience_codes=["assigned_employees", "subcontractor_release"],
            ),
            self.actor,
        )
        self.assertTrue(preview.redacted)

    def test_released_schedule_contracts_are_scoped(self) -> None:
        self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                employee_id="employee-1",
                assignment_status_code="confirmed",
                assignment_source_code="dispatcher",
                confirmed_at=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
            ),
            self.actor,
        )
        self.staffing_service.create_subcontractor_release(
            self.repo.tenant_id,
            SubcontractorReleaseCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                subcontractor_id="sub-1",
                released_qty=1,
                release_status_code="released",
            ),
            self.actor,
        )
        self.staffing_service.create_assignment(
            self.repo.tenant_id,
            AssignmentCreate(
                tenant_id=self.repo.tenant_id,
                shift_id=self.shift.id,
                demand_group_id=self.demand_group.id,
                subcontractor_worker_id="worker-1",
                assignment_status_code="assigned",
                assignment_source_code="dispatcher",
            ),
            self.actor,
        )
        released = self.shift_service.set_shift_release_state(
            self.repo.tenant_id,
            self.shift.id,
            ShiftReleaseStateUpdate(release_state="released", version_no=1),
            self.actor,
        )
        self.shift_service.update_shift_visibility(
            self.repo.tenant_id,
            self.shift.id,
            ShiftVisibilityUpdate(customer_visible_flag=True, subcontractor_visible_flag=True, version_no=released.version_no),
            self.actor,
        )
        service = ReleasedScheduleService(self.repo)
        customer_rows = service.list_customer_schedules(
            CustomerPortalContextRead(
                tenant_id=self.repo.tenant_id,
                user_id=self.actor.user_id,
                customer_id="customer-1",
                contact_id="contact-1",
                customer=CustomerPortalCustomerRead(
                    id="customer-1",
                    tenant_id=self.repo.tenant_id,
                    customer_number="C-1",
                    name="C",
                    status="active",
                ),
                contact=CustomerPortalContactRead(
                    id="contact-1",
                    tenant_id=self.repo.tenant_id,
                    customer_id="customer-1",
                    full_name="Name",
                    function_label=None,
                    email=None,
                    phone=None,
                    mobile=None,
                    status="active",
                ),
                scopes=[],
            )
        )
        self.assertEqual(len(customer_rows.items), 1)
        self.assertEqual(customer_rows.items[0].documents, [])

        subcontractor_rows = service.list_subcontractor_schedules(
            SubcontractorPortalContextRead(
                tenant_id=self.repo.tenant_id,
                user_id=self.actor.user_id,
                subcontractor_id="sub-1",
                contact_id="contact-1",
                company=SubcontractorPortalCompanyRead(
                    id="sub-1",
                    tenant_id=self.repo.tenant_id,
                    subcontractor_number="S-1",
                    legal_name="Sub 1 GmbH",
                    display_name="Sub 1",
                    status="active",
                ),
                contact=SubcontractorPortalContactRead(
                    id="contact-1",
                    tenant_id=self.repo.tenant_id,
                    subcontractor_id="sub-1",
                    full_name="Name",
                    function_label=None,
                    email=None,
                    phone=None,
                    mobile=None,
                    portal_enabled=True,
                    status="active",
                ),
                scopes=[],
            )
        )
        self.assertEqual(len(subcontractor_rows.items), 1)

        employee_rows: EmployeeReleasedScheduleCollectionRead = service.list_employee_schedules(self.actor)
        self.assertEqual(len(employee_rows.items), 1)


if __name__ == "__main__":
    unittest.main()

"""Planning-owned released schedule read models for portals and employee self-service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.schemas import (
    CustomerPortalCollectionSourceRead,
    CustomerPortalContextRead,
    CustomerPortalDocumentRefRead,
    CustomerPortalScheduleCollectionRead,
    CustomerPortalScheduleListItemRead,
)
from app.modules.employees.schemas import (
    EmployeeReleasedScheduleResponseRequest,
    EmployeeReleasedScheduleCollectionRead,
    EmployeeReleasedScheduleDocumentRead,
    EmployeeReleasedScheduleRead,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.subcontractors.schemas import (
    SubcontractorPortalCollectionSourceRead,
    SubcontractorPortalContextRead,
    SubcontractorPortalDocumentRefRead,
    SubcontractorPortalScheduleCollectionRead,
    SubcontractorPortalScheduleRead,
)


class ReleasedScheduleRepository(Protocol):
    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[object]: ...
    def list_shifts(self, tenant_id: str, filters): ...  # noqa: ANN001
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...
    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None): ...  # noqa: ANN001
    def get_assignment(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def update_assignment(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None): ...  # noqa: ANN001
    def get_shift(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str): ...  # noqa: ANN001


@dataclass(frozen=True, slots=True)
class ReleasedScheduleService:
    repository: ReleasedScheduleRepository
    audit_service: AuditService | None = None

    def list_customer_schedules(self, context: CustomerPortalContextRead) -> CustomerPortalScheduleCollectionRead:
        from app.modules.planning.schemas import ShiftListFilter

        rows = self.repository.list_shifts(context.tenant_id, ShiftListFilter(release_state="released", include_archived=False))
        items: list[CustomerPortalScheduleListItemRead] = []
        for shift in rows:
            order = shift.shift_plan.planning_record.order
            if order.customer_id != context.customer_id or not shift.customer_visible_flag:
                continue
            items.append(
                CustomerPortalScheduleListItemRead(
                    id=shift.id,
                    customer_id=context.customer_id,
                    order_id=order.id,
                    schedule_date=shift.starts_at.date(),
                    shift_label=shift.shift_type_code,
                    site_label=shift.location_text,
                    released_at=shift.released_at or shift.updated_at,
                    status=shift.status,
                    documents=[self._customer_doc(item) for item in self.repository.list_documents_for_owner(context.tenant_id, "ops.shift", shift.id)],
                )
            )
        return CustomerPortalScheduleCollectionRead(
            customer_id=context.customer_id,
            source=CustomerPortalCollectionSourceRead(
                domain_key="schedules",
                source_module_key="planning",
                availability_status="ready",
                released_only=True,
                customer_scoped=True,
                docs_backed_outputs=True,
                message_key="portalCustomer.datasets.schedules.pending",
            ),
            items=items,
        )

    def list_subcontractor_schedules(self, context: SubcontractorPortalContextRead) -> SubcontractorPortalScheduleCollectionRead:
        from app.modules.planning.schemas import ShiftListFilter

        rows = self.repository.list_shifts(context.tenant_id, ShiftListFilter(release_state="released", include_archived=False))
        items: list[SubcontractorPortalScheduleRead] = []
        for shift in rows:
            if not shift.subcontractor_visible_flag:
                continue
            matching_assignments = [
                row
                for row in self.repository.list_assignments_in_shift(context.tenant_id, shift.id)
                if (
                    getattr(row, "subcontractor_worker_id", None) is not None
                    and getattr(
                        self.repository.get_subcontractor_worker(context.tenant_id, row.subcontractor_worker_id),
                        "subcontractor_id",
                        None,
                    )
                    == context.subcontractor_id
                )
            ]
            if not matching_assignments:
                continue
            confirmation_status = "confirmed" if any(row.confirmed_at is not None for row in matching_assignments) else "assigned"
            items.append(
                SubcontractorPortalScheduleRead(
                    id=shift.id,
                    subcontractor_id=context.subcontractor_id,
                    position_id=shift.id,
                    shift_label=shift.shift_type_code,
                    schedule_date=shift.starts_at.date(),
                    work_start=shift.starts_at,
                    work_end=shift.ends_at,
                    location_label="redacted" if shift.stealth_mode_flag else shift.location_text,
                    confirmation_status=confirmation_status,
                    documents=[self._subcontractor_doc(item) for item in self.repository.list_documents_for_owner(context.tenant_id, "ops.shift", shift.id)],
                )
            )
        return SubcontractorPortalScheduleCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=SubcontractorPortalCollectionSourceRead(
                domain_key="schedules",
                source_module_key="planning",
                availability_status="ready",
                released_only=True,
                subcontractor_scoped=True,
                docs_backed_outputs=True,
                message_key="portalSubcontractor.datasets.schedules.pending",
            ),
            items=items,
        )

    def list_employee_schedules(self, context: RequestAuthorizationContext) -> EmployeeReleasedScheduleCollectionRead:
        from app.modules.planning.schemas import ShiftListFilter

        employee = self.repository.find_employee_by_user_id(context.tenant_id, context.user_id)
        if employee is None:
            raise ApiException(404, "employees.self_service.employee_not_found", "errors.employees.self_service.employee_not_found")
        rows = self.repository.list_shifts(context.tenant_id, ShiftListFilter(release_state="released", include_archived=False))
        items: list[EmployeeReleasedScheduleRead] = []
        for shift in rows:
            assignments = [
                row
                for row in self.repository.list_assignments_in_shift(context.tenant_id, shift.id)
                if row.employee_id == employee.id
            ]
            if not assignments:
                continue
            assignment = assignments[0]
            items.append(self._employee_schedule_item(employee.id, shift, assignment, context.tenant_id))
        return EmployeeReleasedScheduleCollectionRead(employee_id=employee.id, tenant_id=context.tenant_id, items=items)

    def respond_employee_assignment(
        self,
        context: RequestAuthorizationContext,
        assignment_id: str,
        payload: EmployeeReleasedScheduleResponseRequest,
    ) -> EmployeeReleasedScheduleRead:
        from app.modules.planning.schemas import AssignmentUpdate

        employee = self.repository.find_employee_by_user_id(context.tenant_id, context.user_id)
        if employee is None:
            raise ApiException(404, "employees.self_service.employee_not_found", "errors.employees.self_service.employee_not_found")
        assignment = self.repository.get_assignment(context.tenant_id, assignment_id)
        if assignment is None or assignment.employee_id != employee.id:
            raise ApiException(404, "planning.assignment.not_found", "errors.planning.assignment.not_found")
        shift = self.repository.get_shift(context.tenant_id, assignment.shift_id)
        if shift is None or shift.release_state != "released":
            raise ApiException(409, "planning.assignment.release_required", "errors.planning.assignment.release_required")
        if assignment.assignment_status_code == "removed":
            raise ApiException(409, "planning.assignment.invalid_status", "errors.planning.assignment.invalid_status")
        response_code = payload.response_code.strip().lower()
        if response_code not in {"confirm", "decline"}:
            raise ApiException(400, "planning.assignment.response_invalid", "errors.planning.assignment.response_invalid")
        updated = self.repository.update_assignment(
            context.tenant_id,
            assignment_id,
            AssignmentUpdate(
                assignment_status_code="confirmed" if response_code == "confirm" else "offered",
                confirmed_at=datetime.now(UTC) if response_code == "confirm" else None,
                remarks=payload.note,
                version_no=payload.version_no,
            ),
            context.user_id,
        )
        if updated is None:
            raise ApiException(404, "planning.assignment.not_found", "errors.planning.assignment.not_found")
        if self.audit_service is not None:
            self.audit_service.record_business_event(
                actor=AuditActor(
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    session_id=context.session_id,
                    request_id=context.request_id,
                ),
                event_type=f"planning.assignment.employee_{response_code}",
                entity_type="ops.assignment",
                entity_id=assignment_id,
                tenant_id=context.tenant_id,
                after_json={
                    "assignment_status_code": updated.assignment_status_code,
                    "confirmed_at": updated.confirmed_at.isoformat() if updated.confirmed_at is not None else None,
                    "response_code": response_code,
                },
            )
        return self._employee_schedule_item(employee.id, shift, updated, context.tenant_id)

    def _employee_schedule_item(self, employee_id: str, shift, assignment, tenant_id: str) -> EmployeeReleasedScheduleRead:  # noqa: ANN001
        return EmployeeReleasedScheduleRead(
            id=assignment.id,
            employee_id=employee_id,
            shift_id=shift.id,
            planning_record_id=shift.shift_plan.planning_record_id,
            order_id=shift.shift_plan.planning_record.order_id if shift.shift_plan.planning_record is not None else None,
            site_id=shift.shift_plan.planning_record.site_detail.site_id
            if shift.shift_plan.planning_record is not None and shift.shift_plan.planning_record.site_detail is not None
            else None,
            schedule_date=shift.starts_at.date(),
            shift_label=shift.shift_type_code,
            work_start=shift.starts_at,
            work_end=shift.ends_at,
            location_label=shift.location_text,
            meeting_point=shift.meeting_point,
            assignment_status=assignment.assignment_status_code,
            confirmation_status="confirmed" if assignment.confirmed_at is not None else "assigned",
            documents=[self._employee_doc(item) for item in self.repository.list_documents_for_owner(tenant_id, "ops.shift", shift.id)],
        )

    @staticmethod
    def _customer_doc(document) -> CustomerPortalDocumentRefRead:  # noqa: ANN001
        version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
        return CustomerPortalDocumentRefRead(
            document_id=document.id,
            title=document.title,
            document_type_key=document.document_type.key if document.document_type is not None else None,
            file_name=version.file_name if version is not None else None,
            content_type=version.content_type if version is not None else None,
            current_version_no=document.current_version_no,
            is_name_masked=True,
        )

    @staticmethod
    def _subcontractor_doc(document) -> SubcontractorPortalDocumentRefRead:  # noqa: ANN001
        version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
        return SubcontractorPortalDocumentRefRead(
            document_id=document.id,
            title=document.title,
            file_name=version.file_name if version is not None else None,
            content_type=version.content_type if version is not None else None,
            current_version_no=document.current_version_no,
        )

    @staticmethod
    def _employee_doc(document) -> EmployeeReleasedScheduleDocumentRead:  # noqa: ANN001
        version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
        return EmployeeReleasedScheduleDocumentRead(
            document_id=document.id,
            title=document.title,
            file_name=version.file_name if version is not None else None,
            content_type=version.content_type if version is not None else None,
            current_version_no=document.current_version_no,
        )

"""Employee mobile-specific own-record document and credential reads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.schemas import (
    EmployeeMobileCredentialCollectionRead,
    EmployeeMobileCredentialRead,
    EmployeeMobileDocumentCollectionRead,
    EmployeeMobileDocumentRead,
)
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.platform_services.docs_service import DocumentDownload, DocumentService


class EmployeeMobileReadRepository(Protocol):
    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None): ...  # noqa: ANN001
    def list_credentials(self, tenant_id: str, filters): ...  # noqa: ANN001
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...


@dataclass(frozen=True, slots=True)
class EmployeeMobileReadService:
    repository: EmployeeMobileReadRepository
    released_schedule_service: ReleasedScheduleService
    document_service: DocumentService

    def list_documents(self, context: RequestAuthorizationContext) -> EmployeeMobileDocumentCollectionRead:
        employee = self._require_employee(context)
        items: list[EmployeeMobileDocumentRead] = []
        seen: set[str] = set()

        for document in self.repository.list_documents_for_owner(context.tenant_id, "hr.employee", employee.id):
            mapped = self._map_document(document, owner_type="hr.employee", owner_id=employee.id, shift_id=None, schedule_date=None)
            items.append(mapped)
            seen.add(mapped.document_id)

        schedules = self.released_schedule_service.list_employee_schedules(context)
        for schedule in schedules.items:
            for document in schedule.documents:
                if document.document_id in seen:
                    continue
                items.append(
                    EmployeeMobileDocumentRead(
                        document_id=document.document_id,
                        owner_type="ops.shift",
                        owner_id=schedule.shift_id,
                        relation_type=document.relation_type,
                        title=document.title,
                        file_name=document.file_name,
                        content_type=document.content_type,
                        current_version_no=document.current_version_no,
                        linked_at=None,
                        schedule_date=schedule.schedule_date,
                        shift_id=schedule.shift_id,
                    )
                )
                seen.add(document.document_id)

        items.sort(key=lambda row: ((row.schedule_date.isoformat() if row.schedule_date else ""), row.title.lower()), reverse=True)
        return EmployeeMobileDocumentCollectionRead(employee_id=employee.id, tenant_id=context.tenant_id, items=items)

    def download_document(
        self,
        context: RequestAuthorizationContext,
        document_id: str,
        version_no: int,
    ) -> DocumentDownload:
        documents = self.list_documents(context)
        if not any(item.document_id == document_id for item in documents.items):
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return self.document_service.download_document_version(context.tenant_id, document_id, version_no, context)

    def list_credentials(self, context: RequestAuthorizationContext) -> EmployeeMobileCredentialCollectionRead:
        from app.modules.employees.schemas import EmployeeCredentialFilter

        employee = self._require_employee(context)
        items: list[EmployeeMobileCredentialRead] = []
        employee_documents = {
            document.id: document
            for document in self.repository.list_documents_for_owner(context.tenant_id, "hr.employee", employee.id)
        }
        for row in self.repository.list_credentials(
            context.tenant_id,
            EmployeeCredentialFilter(employee_id=employee.id, include_archived=False),
        ):
            badge_document = next(
                (
                    document
                    for document in employee_documents.values()
                    if (document.metadata_json or {}).get("credential_id") == row.id
                    and any(link.owner_type == "hr.employee" and link.relation_type == "badge_output" for link in document.links)
                ),
                None,
            )
            latest_version = None
            if badge_document is not None and badge_document.versions:
                latest_version = max(badge_document.versions, key=lambda version: version.version_no)
            items.append(
                EmployeeMobileCredentialRead(
                    credential_id=row.id,
                    credential_no=row.credential_no,
                    credential_type=row.credential_type,
                    encoded_value=row.encoded_value,
                    valid_from=row.valid_from,
                    valid_until=row.valid_until,
                    status=row.status,
                    badge_document_id=badge_document.id if badge_document is not None else None,
                    badge_file_name=latest_version.file_name if latest_version is not None else None,
                )
            )
        return EmployeeMobileCredentialCollectionRead(employee_id=employee.id, tenant_id=context.tenant_id, items=items)

    def _require_employee(self, context: RequestAuthorizationContext):
        employee = self.repository.find_employee_by_user_id(context.tenant_id, context.user_id)
        if employee is None or employee.archived_at is not None or employee.status != "active":
            raise ApiException(404, "employees.self_service.employee_not_found", "errors.employees.self_service.employee_not_found")
        return employee

    @staticmethod
    def _map_document(document, *, owner_type: str, owner_id: str, shift_id: str | None, schedule_date) -> EmployeeMobileDocumentRead:  # noqa: ANN001
        latest_version = max(document.versions, key=lambda version: version.version_no) if document.versions else None
        relation_type = "attachment"
        linked_at = None
        for link in document.links:
            if link.owner_type == owner_type and link.owner_id == owner_id:
                relation_type = link.relation_type
                linked_at = getattr(link, "linked_at", None)
                break
        return EmployeeMobileDocumentRead(
            document_id=document.id,
            owner_type=owner_type,
            owner_id=owner_id,
            relation_type=relation_type,
            title=document.title,
            file_name=latest_version.file_name if latest_version is not None else None,
            content_type=latest_version.content_type if latest_version is not None else None,
            current_version_no=document.current_version_no if document.current_version_no > 0 else None,
            linked_at=linked_at,
            schedule_date=schedule_date,
            shift_id=shift_id,
        )

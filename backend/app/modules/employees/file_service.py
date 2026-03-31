"""Employee file helpers for docs-backed profile photo and attachment retrieval."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import Employee
from app.modules.employees.schemas import (
    EmployeeDocumentLinkCreate,
    EmployeeDocumentListItemRead,
    EmployeeDocumentUploadCreate,
    EmployeeDocumentVersionCreate as EmployeeDocumentVersionAdd,
    EmployeePhotoRead,
    EmployeePhotoUpload,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.platform_services.docs_models import Document
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


class EmployeeFileEmployeeRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...


class EmployeeFileDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...
    def get_document(self, tenant_id: str, document_id: str) -> Document | None: ...


class EmployeeFileService:
    PROFILE_PHOTO_RELATION_TYPE = "profile_photo"

    def __init__(
        self,
        *,
        employee_repository: EmployeeFileEmployeeRepository,
        document_repository: EmployeeFileDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.employee_repository = employee_repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_documents(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeDocumentListItemRead]:
        self._require_employee_read_scope(tenant_id, employee_id, context)
        return [
            self._map_document(document, link)
            for document in self.document_repository.list_documents_for_owner(tenant_id, "hr.employee", employee_id)
            if (link := self._pick_generic_employee_link(document, employee_id)) is not None
        ]

    def upload_employee_document(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeDocumentUploadCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeDocumentListItemRead:
        self._require_employee_write_scope(tenant_id, employee_id, context)
        title = payload.title.strip()
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                document_type_key=self._normalize_optional(payload.document_type_key),
                source_module="employees",
                source_label="employee_document",
                metadata_json={"employee_id": employee_id, "kind": "employee_document"},
            ),
            context,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=payload.file_name,
                content_type=payload.content_type,
                content_base64=payload.content_base64,
                is_revision_safe_pdf=payload.is_revision_safe_pdf,
                metadata_json={"kind": "employee_document"},
            ),
            context,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="hr.employee",
                owner_id=employee_id,
                relation_type=payload.relation_type.strip(),
                label=self._normalize_optional(payload.label) or title,
                metadata_json={"kind": "employee_document"},
            ),
            context,
        )
        uploaded = self._require_generic_employee_document(tenant_id, employee_id, document.id)
        self._record_event(
            context,
            event_type="employees.document.uploaded",
            entity_id=employee_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": document.id, "relation_type": payload.relation_type.strip()},
        )
        return self._map_document(uploaded, self._pick_generic_employee_link(uploaded, employee_id))

    def link_employee_document(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeDocumentLinkCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeDocumentListItemRead:
        self._require_employee_write_scope(tenant_id, employee_id, context)
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="hr.employee",
                owner_id=employee_id,
                relation_type=payload.relation_type.strip(),
                label=self._normalize_optional(payload.label),
                metadata_json={"kind": "employee_document"},
            ),
            context,
        )
        linked = self._require_generic_employee_document(tenant_id, employee_id, payload.document_id)
        self._record_event(
            context,
            event_type="employees.document.linked",
            entity_id=employee_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": payload.document_id, "relation_type": payload.relation_type.strip()},
        )
        return self._map_document(linked, self._pick_generic_employee_link(linked, employee_id))

    def add_employee_document_version(
        self,
        tenant_id: str,
        employee_id: str,
        document_id: str,
        payload: EmployeeDocumentVersionAdd,
        context: RequestAuthorizationContext,
    ) -> EmployeeDocumentListItemRead:
        self._require_employee_write_scope(tenant_id, employee_id, context)
        document = self._require_generic_employee_document(tenant_id, employee_id, document_id)
        self.document_service.add_document_version(
            tenant_id,
            document_id,
            DocumentVersionCreate(
                file_name=payload.file_name,
                content_type=payload.content_type,
                content_base64=payload.content_base64,
                is_revision_safe_pdf=payload.is_revision_safe_pdf,
                metadata_json={"kind": "employee_document"},
            ),
            context,
        )
        refreshed = self._require_generic_employee_document(tenant_id, employee_id, document_id)
        self._record_event(
            context,
            event_type="employees.document.version_added",
            entity_id=employee_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": document_id},
        )
        return self._map_document(refreshed, self._pick_generic_employee_link(refreshed, employee_id))

    def get_profile_photo(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> EmployeePhotoRead | None:
        self._require_employee_read_scope(tenant_id, employee_id, context)
        return self._pick_profile_photo(self.document_repository.list_documents_for_owner(tenant_id, "hr.employee", employee_id), employee_id)

    def upsert_profile_photo(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeePhotoUpload,
        context: RequestAuthorizationContext,
    ) -> EmployeePhotoRead:
        self._require_employee_write_scope(tenant_id, employee_id, context)
        existing_documents = self.document_repository.list_documents_for_owner(tenant_id, "hr.employee", employee_id)
        existing_photo = self._pick_profile_photo(existing_documents, employee_id)
        title = (payload.title or "").strip() or "Profilfoto"

        if existing_photo is None:
            document = self.document_service.create_document(
                tenant_id,
                DocumentCreate(
                    tenant_id=tenant_id,
                    title=title,
                    source_module="employees",
                    source_label="profile_photo",
                    metadata_json={"employee_id": employee_id, "kind": "profile_photo"},
                ),
                context,
            )
            self.document_service.add_document_version(
                tenant_id,
                document.id,
                DocumentVersionCreate(
                    file_name=payload.file_name,
                    content_type=payload.content_type,
                    content_base64=payload.content_base64,
                    metadata_json={"kind": "profile_photo"},
                ),
                context,
            )
            self.document_service.add_document_link(
                tenant_id,
                document.id,
                DocumentLinkCreate(
                    owner_type="hr.employee",
                    owner_id=employee_id,
                    relation_type=self.PROFILE_PHOTO_RELATION_TYPE,
                    label=title,
                    metadata_json={"kind": "profile_photo"},
                ),
                context,
            )
        else:
            self.document_service.add_document_version(
                tenant_id,
                existing_photo.document_id,
                DocumentVersionCreate(
                    file_name=payload.file_name,
                    content_type=payload.content_type,
                    content_base64=payload.content_base64,
                    metadata_json={"kind": "profile_photo"},
                ),
                context,
            )

        refreshed = self.document_repository.list_documents_for_owner(tenant_id, "hr.employee", employee_id)
        photo = self._pick_profile_photo(refreshed, employee_id)
        if photo is None:
            raise ApiException(500, "employees.photo.write_failed", "errors.employees.photo.write_failed")
        self._record_event(
            context,
            event_type="employees.photo.updated",
            entity_id=employee_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": photo.document_id, "current_version_no": photo.current_version_no},
        )
        return photo

    def _require_employee_read_scope(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> None:
        if "employees.employee.read" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.read"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)

    def _require_employee_write_scope(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> None:
        if "employees.employee.write" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.write"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        employee = self.employee_repository.get_employee(tenant_id, employee_id)
        if employee is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return employee

    def _record_event(
        self,
        context: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_id: str,
        tenant_id: str,
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
            entity_type="hr.employee",
            entity_id=entity_id,
            tenant_id=tenant_id,
            metadata_json=metadata_json,
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        normalized = (value or "").strip()
        return normalized or None

    def _require_generic_employee_document(self, tenant_id: str, employee_id: str, document_id: str) -> Document:
        document = self.document_repository.get_document(tenant_id, document_id)
        if document is None:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        if self._pick_generic_employee_link(document, employee_id) is None:
            raise ApiException(404, "employees.document.not_linked", "errors.employees.document.not_linked")
        return document

    def _pick_generic_employee_link(self, document: Document, employee_id: str):
        links = [
            link
            for link in document.links
            if link.owner_type == "hr.employee"
            and link.owner_id == employee_id
            and link.relation_type != self.PROFILE_PHOTO_RELATION_TYPE
        ]
        links.sort(key=lambda item: item.linked_at, reverse=True)
        return links[0] if links else None

    @classmethod
    def _pick_profile_photo(cls, documents: list[Document], employee_id: str) -> EmployeePhotoRead | None:
        photo_documents = [
            document
            for document in documents
            if any(
                link.owner_type == "hr.employee"
                and link.owner_id == employee_id
                and link.relation_type == cls.PROFILE_PHOTO_RELATION_TYPE
                for link in document.links
            )
        ]
        if not photo_documents:
            return None
        photo_documents.sort(key=lambda document: document.updated_at, reverse=True)
        document = photo_documents[0]
        link = next(
            link
            for link in sorted(document.links, key=lambda item: item.linked_at, reverse=True)
            if link.owner_type == "hr.employee"
            and link.owner_id == employee_id
            and link.relation_type == cls.PROFILE_PHOTO_RELATION_TYPE
        )
        return EmployeePhotoRead(**EmployeeFileService._map_document(document, link).model_dump())

    @staticmethod
    def _map_document(document: Document, link=None) -> EmployeeDocumentListItemRead:
        latest_version = max(document.versions, key=lambda version: version.version_no) if document.versions else None
        employee_links = [item for item in document.links if item.owner_type == "hr.employee"]
        employee_links.sort(key=lambda link: link.linked_at, reverse=True)
        resolved_link = link or (employee_links[0] if employee_links else None)
        return EmployeeDocumentListItemRead(
            document_id=document.id,
            relation_type=resolved_link.relation_type if resolved_link else "attachment",
            label=resolved_link.label if resolved_link else None,
            title=document.title,
            document_type_key=document.document_type.key if document.document_type else None,
            file_name=latest_version.file_name if latest_version else None,
            content_type=latest_version.content_type if latest_version else None,
            current_version_no=document.current_version_no if document.current_version_no > 0 else None,
            linked_at=resolved_link.linked_at if resolved_link else None,
        )

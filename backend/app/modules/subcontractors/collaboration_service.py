"""Subcontractor history, attachments, and explicit lifecycle controls."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentVersion
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.subcontractors.policy import (
    enforce_subcontractor_internal_read_access,
    enforce_subcontractor_internal_write_access,
)
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorHistoryEntry,
)
from app.modules.subcontractors.schemas import (
    SubcontractorHistoryAttachmentLinkCreate,
    SubcontractorHistoryAttachmentRead,
    SubcontractorHistoryEntryCreate,
    SubcontractorHistoryEntryRead,
    SubcontractorLifecycleTransitionRequest,
    SubcontractorRead,
)


class SubcontractorCollaborationRepository(Protocol):
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def get_contact(self, tenant_id: str, subcontractor_id: str, contact_id: str) -> SubcontractorContact | None: ...
    def save_subcontractor(self, row: Subcontractor) -> Subcontractor: ...
    def list_history_entries(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorHistoryEntry]: ...
    def get_history_entry(self, tenant_id: str, subcontractor_id: str, history_entry_id: str) -> SubcontractorHistoryEntry | None: ...
    def create_history_entry(self, row: SubcontractorHistoryEntry) -> SubcontractorHistoryEntry: ...


class SubcontractorHistoryDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...


class SubcontractorCollaborationService:
    ENTRY_TYPES = frozenset(
        {
            "processing_note",
            "invoice_discussion",
            "manual_commentary",
            "portal_enablement_note",
            "lifecycle_event",
        }
    )

    def __init__(
        self,
        repository: SubcontractorCollaborationRepository,
        *,
        document_repository: SubcontractorHistoryDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_history(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorHistoryEntryRead]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return [
            SubcontractorHistoryEntryRead.model_validate(row).model_copy(
                update={"attachments": self._history_attachments(tenant_id, row.id)}
            )
            for row in self.repository.list_history_entries(tenant_id, subcontractor_id)
        ]

    def create_history_entry(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorHistoryEntryCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorHistoryEntryRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.history_tenant_mismatch", "errors.subcontractors.history_entry.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.validation.history_company_mismatch",
                "errors.subcontractors.history_entry.subcontractor_mismatch",
            )
        if payload.entry_type not in self.ENTRY_TYPES:
            raise ApiException(400, "subcontractors.validation.history_type_invalid", "errors.subcontractors.history_entry.invalid_type")
        if payload.related_contact_id is not None:
            contact = self.repository.get_contact(tenant_id, subcontractor_id, payload.related_contact_id)
            if contact is None:
                raise ApiException(404, "subcontractors.history_contact.not_found", "errors.subcontractors.history_entry.contact_not_found")

        row = self.repository.create_history_entry(
            SubcontractorHistoryEntry(
                tenant_id=tenant_id,
                subcontractor_id=subcontractor_id,
                entry_type=payload.entry_type,
                title=payload.title,
                body=payload.body,
                occurred_at=payload.occurred_at or datetime.now(UTC),
                actor_user_id=actor.user_id,
                related_contact_id=payload.related_contact_id,
                metadata_json=payload.metadata_json,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.history.created",
            entity_type="partner.subcontractor_history_entry",
            entity_id=row.id,
            tenant_id=tenant_id,
            metadata_json={"entry_type": row.entry_type, "subcontractor_id": subcontractor_id},
        )
        return SubcontractorHistoryEntryRead.model_validate(row).model_copy(
            update={"attachments": self._history_attachments(tenant_id, row.id)}
        )

    def link_history_attachment(
        self,
        tenant_id: str,
        subcontractor_id: str,
        history_entry_id: str,
        payload: SubcontractorHistoryAttachmentLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorHistoryAttachmentRead]:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        history_entry = self.repository.get_history_entry(tenant_id, subcontractor_id, history_entry_id)
        if history_entry is None:
            raise ApiException(404, "subcontractors.history_entry.not_found", "errors.subcontractors.history_entry.not_found")
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="partner.subcontractor_history_entry",
                owner_id=history_entry_id,
                relation_type="attachment",
                label=payload.label,
            ),
            actor,
        )
        self._record_event(
            actor,
            event_type="subcontractors.history.attachment_linked",
            entity_type="partner.subcontractor_history_entry",
            entity_id=history_entry_id,
            tenant_id=tenant_id,
            metadata_json={"subcontractor_id": subcontractor_id, "document_id": payload.document_id},
        )
        return self._history_attachments(tenant_id, history_entry_id)

    def archive_subcontractor(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorLifecycleTransitionRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorRead:
        row = self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        before = self._subcontractor_snapshot(row)
        self._require_version(row.version_no, payload.version_no)
        if row.archived_at is not None or row.status == "archived":
            raise ApiException(409, "subcontractors.lifecycle.archive_not_allowed", "errors.subcontractors.lifecycle.archive_not_allowed")
        row.status = "archived"
        row.archived_at = datetime.now(UTC)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.save_subcontractor(row)
        self._record_history(
            tenant_id,
            subcontractor_id,
            actor,
            entry_type="lifecycle_event",
            title="Subunternehmer archiviert",
            body="Der Subunternehmer wurde archiviert.",
            metadata_json={"lifecycle_action": "archive"},
        )
        self._record_event(
            actor,
            event_type="subcontractors.company.archived",
            entity_type="partner.subcontractor",
            entity_id=subcontractor_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._subcontractor_snapshot(updated),
        )
        return SubcontractorRead.model_validate(updated)

    def reactivate_subcontractor(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorLifecycleTransitionRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorRead:
        row = self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        before = self._subcontractor_snapshot(row)
        self._require_version(row.version_no, payload.version_no)
        if row.archived_at is None and row.status != "archived":
            raise ApiException(
                409,
                "subcontractors.lifecycle.reactivate_not_allowed",
                "errors.subcontractors.lifecycle.reactivate_not_allowed",
            )
        row.status = "active"
        row.archived_at = None
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.save_subcontractor(row)
        self._record_history(
            tenant_id,
            subcontractor_id,
            actor,
            entry_type="lifecycle_event",
            title="Subunternehmer reaktiviert",
            body="Der Subunternehmer wurde reaktiviert.",
            metadata_json={"lifecycle_action": "reactivate"},
        )
        self._record_event(
            actor,
            event_type="subcontractors.company.reactivated",
            entity_type="partner.subcontractor",
            entity_id=subcontractor_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._subcontractor_snapshot(updated),
        )
        return SubcontractorRead.model_validate(updated)

    def _history_attachments(self, tenant_id: str, history_entry_id: str) -> list[SubcontractorHistoryAttachmentRead]:
        attachments: list[SubcontractorHistoryAttachmentRead] = []
        for document in self.document_repository.list_documents_for_owner(
            tenant_id,
            "partner.subcontractor_history_entry",
            history_entry_id,
        ):
            current_version = self._current_document_version(document)
            attachments.append(
                SubcontractorHistoryAttachmentRead(
                    document_id=document.id,
                    title=document.title,
                    document_type_key=document.document_type.key if document.document_type else None,
                    file_name=current_version.file_name if current_version else None,
                    content_type=current_version.content_type if current_version else None,
                    current_version_no=document.current_version_no,
                )
            )
        return attachments

    def _require_subcontractor_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise ApiException(404, "subcontractors.subcontractor.not_found", "errors.subcontractors.subcontractor.not_found")
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=row)
        return row

    def _require_subcontractor_for_write(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        enforce_subcontractor_internal_write_access(actor, tenant_id=tenant_id)
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise ApiException(404, "subcontractors.subcontractor.not_found", "errors.subcontractors.subcontractor.not_found")
        return row

    @staticmethod
    def _require_version(current_version: int, payload_version: int) -> None:
        if payload_version != current_version:
            raise ApiException(409, "subcontractors.conflict.stale_version", "errors.subcontractors.subcontractor.stale_version")

    def _record_history(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
        *,
        entry_type: str,
        title: str,
        body: str,
        metadata_json: dict[str, object] | None = None,
        related_contact_id: str | None = None,
    ) -> None:
        self.repository.create_history_entry(
            SubcontractorHistoryEntry(
                tenant_id=tenant_id,
                subcontractor_id=subcontractor_id,
                entry_type=entry_type,
                title=title,
                body=body,
                occurred_at=datetime.now(UTC),
                actor_user_id=actor.user_id,
                related_contact_id=related_contact_id,
                metadata_json=metadata_json or {},
            )
        )

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
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
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
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
    def _current_document_version(document: Document) -> DocumentVersion | None:
        if not document.versions:
            return None
        return next(
            (version for version in document.versions if version.version_no == document.current_version_no),
            max(document.versions, key=lambda version: version.version_no),
        )

    @staticmethod
    def _subcontractor_snapshot(row: Subcontractor) -> dict[str, object]:
        return {
            "status": row.status,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
            "version_no": row.version_no,
        }

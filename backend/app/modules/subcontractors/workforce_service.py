"""Partner worker, qualification, proof, and credential maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import EMPLOYEE_CREDENTIAL_STATUSES, EMPLOYEE_CREDENTIAL_TYPES, QualificationType
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentVersion
from app.modules.platform_services.docs_schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentVersionCreate,
)
from app.modules.platform_services.docs_service import DocumentService
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.policy import (
    enforce_subcontractor_internal_read_access,
    enforce_subcontractor_internal_write_access,
)
from app.modules.subcontractors.schemas import (
    SubcontractorPortalContextRead,
    SubcontractorPortalQualificationTypeOptionRead,
    SubcontractorPortalWorkerCreate,
    SubcontractorPortalWorkerQualificationCreate,
    SubcontractorPortalWorkerQualificationUpdate,
    SubcontractorPortalWorkerRead,
    SubcontractorPortalWorkerUpdate,
    SubcontractorWorkerCreate,
    SubcontractorWorkerCredentialCreate,
    SubcontractorWorkerCredentialRead,
    SubcontractorWorkerCredentialUpdate,
    SubcontractorWorkerFilter,
    SubcontractorWorkerListItem,
    SubcontractorWorkerQualificationCreate,
    SubcontractorWorkerQualificationProofLinkCreate,
    SubcontractorWorkerQualificationProofRead,
    SubcontractorWorkerQualificationProofUpload,
    SubcontractorWorkerQualificationRead,
    SubcontractorWorkerQualificationUpdate,
    SubcontractorWorkerRead,
    SubcontractorWorkerUpdate,
)


@dataclass(frozen=True, slots=True)
class _ResolvedQualificationType:
    qualification_type: QualificationType
    valid_until: date | None


class SubcontractorWorkforceRepository(Protocol):
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]: ...
    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]: ...
    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None: ...
    def create_worker(self, row: SubcontractorWorker) -> SubcontractorWorker: ...
    def update_worker(self, row: SubcontractorWorker) -> SubcontractorWorker: ...
    def find_worker_by_number(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorker | None: ...
    def list_worker_qualifications(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
    ) -> list[SubcontractorWorkerQualification]: ...
    def get_worker_qualification(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
    ) -> SubcontractorWorkerQualification | None: ...
    def create_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification: ...
    def update_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification: ...
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None: ...
    def list_worker_credentials(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
    ) -> list[SubcontractorWorkerCredential]: ...
    def get_worker_credential(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        credential_id: str,
    ) -> SubcontractorWorkerCredential | None: ...
    def create_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential: ...
    def update_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential: ...
    def find_worker_credential_by_no(
        self,
        tenant_id: str,
        credential_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None: ...
    def find_worker_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None: ...


class SubcontractorWorkforceDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...


class SubcontractorWorkforceService:
    def __init__(
        self,
        repository: SubcontractorWorkforceRepository,
        *,
        document_repository: SubcontractorWorkforceDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_workers(
        self,
        tenant_id: str,
        subcontractor_id: str,
        filters: SubcontractorWorkerFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerListItem]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return [
            SubcontractorWorkerListItem.model_validate(row)
            for row in self.repository.list_workers(tenant_id, subcontractor_id, filters)
        ]

    def list_portal_qualification_types(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[SubcontractorPortalQualificationTypeOptionRead]:
        self._require_portal_subcontractor(context)
        return [
            SubcontractorPortalQualificationTypeOptionRead(
                id=row.id,
                code=row.code,
                label=row.label,
                expiry_required=row.expiry_required,
                default_validity_days=row.default_validity_days,
                proof_required=row.proof_required,
                compliance_relevant=row.compliance_relevant,
            )
            for row in self.repository.list_qualification_types(context.tenant_id)
        ]

    def list_workers_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        filters: SubcontractorWorkerFilter,
    ) -> list[SubcontractorWorkerListItem]:
        self._require_portal_subcontractor(context)
        return [
            SubcontractorWorkerListItem.model_validate(row)
            for row in self.repository.list_workers(context.tenant_id, context.subcontractor_id, filters)
        ]

    def get_worker_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
    ) -> SubcontractorPortalWorkerRead:
        row = self._require_portal_worker(context, worker_id)
        return self._serialize_portal_worker(row)

    def create_worker_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        payload: SubcontractorPortalWorkerCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorPortalWorkerRead:
        self._require_portal_subcontractor(context)
        if self.repository.find_worker_by_number(context.tenant_id, context.subcontractor_id, payload.worker_no) is not None:
            raise ApiException(409, "subcontractors.conflict.worker_no", "errors.subcontractors.worker.duplicate_number")
        row = self.repository.create_worker(
            SubcontractorWorker(
                tenant_id=context.tenant_id,
                subcontractor_id=context.subcontractor_id,
                worker_no=payload.worker_no,
                first_name=payload.first_name,
                last_name=payload.last_name,
                preferred_name=self._normalize_optional(payload.preferred_name),
                birth_date=payload.birth_date,
                email=self._normalize_optional(payload.email),
                phone=self._normalize_optional(payload.phone),
                mobile=self._normalize_optional(payload.mobile),
                notes=None,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker.created",
            entity_type="partner.subcontractor_worker",
            entity_id=row.id,
            tenant_id=context.tenant_id,
            after_json=self._worker_snapshot(row),
            metadata_json={"source": "portal"},
        )
        return self._serialize_portal_worker(row)

    def update_worker_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        payload: SubcontractorPortalWorkerUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorPortalWorkerRead:
        row = self._require_portal_worker(context, worker_id)
        before = self._worker_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "worker")
        next_worker_no = payload.worker_no if payload.worker_no is not None else row.worker_no
        if self.repository.find_worker_by_number(context.tenant_id, context.subcontractor_id, next_worker_no, exclude_id=worker_id) is not None:
            raise ApiException(409, "subcontractors.conflict.worker_no", "errors.subcontractors.worker.duplicate_number")
        row.worker_no = next_worker_no
        row.first_name = self._effective_optional(payload.first_name, row.first_name)
        row.last_name = self._effective_optional(payload.last_name, row.last_name)
        row.preferred_name = self._effective_optional(payload.preferred_name, row.preferred_name)
        row.birth_date = payload.birth_date if "birth_date" in payload.model_fields_set else row.birth_date
        row.email = self._effective_optional(payload.email, row.email)
        row.phone = self._effective_optional(payload.phone, row.phone)
        row.mobile = self._effective_optional(payload.mobile, row.mobile)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_worker(row)
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker.updated",
            entity_type="partner.subcontractor_worker",
            entity_id=worker_id,
            tenant_id=context.tenant_id,
            before_json=before,
            after_json=self._worker_snapshot(updated),
            metadata_json={"source": "portal"},
        )
        return self._serialize_portal_worker(updated)

    def list_worker_qualifications_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
    ) -> list[SubcontractorWorkerQualificationRead]:
        self._require_portal_worker(context, worker_id)
        return [
            self._serialize_qualification(context.tenant_id, row)
            for row in self.repository.list_worker_qualifications(context.tenant_id, context.subcontractor_id, worker_id)
        ]

    def create_worker_qualification_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        payload: SubcontractorPortalWorkerQualificationCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationRead:
        self._require_portal_worker(context, worker_id)
        resolved = self._resolve_qualification_type(context.tenant_id, payload.qualification_type_id, payload.issued_at, payload.valid_until)
        row = self.repository.create_worker_qualification(
            SubcontractorWorkerQualification(
                tenant_id=context.tenant_id,
                worker_id=worker_id,
                qualification_type_id=payload.qualification_type_id,
                certificate_no=self._normalize_optional(payload.certificate_no),
                issued_at=payload.issued_at,
                valid_until=resolved.valid_until,
                issuing_authority=self._normalize_optional(payload.issuing_authority),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker_qualification.created",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=row.id,
            tenant_id=context.tenant_id,
            after_json=self._qualification_snapshot(row),
            metadata_json={"source": "portal", "subcontractor_id": context.subcontractor_id},
        )
        return self._serialize_qualification(context.tenant_id, row)

    def update_worker_qualification_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorPortalWorkerQualificationUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationRead:
        row = self._require_portal_worker_qualification(context, worker_id, qualification_id)
        before = self._qualification_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "worker_qualification")
        issued_at = payload.issued_at if "issued_at" in payload.model_fields_set else row.issued_at
        valid_until = payload.valid_until if "valid_until" in payload.model_fields_set else row.valid_until
        resolved = self._resolve_qualification_type(context.tenant_id, row.qualification_type_id, issued_at, valid_until)
        row.certificate_no = self._effective_optional(payload.certificate_no, row.certificate_no)
        row.issued_at = issued_at
        row.valid_until = resolved.valid_until
        row.issuing_authority = self._effective_optional(payload.issuing_authority, row.issuing_authority)
        row.notes = self._effective_optional(payload.notes, row.notes)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_worker_qualification(row)
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker_qualification.updated",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=context.tenant_id,
            before_json=before,
            after_json=self._qualification_snapshot(updated),
            metadata_json={"source": "portal", "subcontractor_id": context.subcontractor_id},
        )
        return self._serialize_qualification(context.tenant_id, updated)

    def list_worker_qualification_proofs_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        qualification_id: str,
    ) -> list[SubcontractorWorkerQualificationProofRead]:
        self._require_portal_worker_qualification(context, worker_id, qualification_id)
        return self._qualification_proofs(context.tenant_id, qualification_id)

    def upload_worker_qualification_proof_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorWorkerQualificationProofUpload,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationProofRead:
        qualification = self._require_portal_worker_qualification(context, worker_id, qualification_id)
        title = (payload.title or "").strip() or self._default_proof_title(qualification)
        document = self.document_service.create_document(
            context.tenant_id,
            DocumentCreate(
                tenant_id=context.tenant_id,
                title=title,
                source_module="subcontractors",
                source_label="worker_qualification_proof",
                metadata_json={
                    "worker_id": worker_id,
                    "worker_qualification_id": qualification_id,
                    "subcontractor_id": context.subcontractor_id,
                    "source": "portal",
                },
            ),
            actor,
        )
        self.document_service.add_document_version(
            context.tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=payload.file_name,
                content_type=payload.content_type,
                content_base64=payload.content_base64,
                metadata_json={"kind": "worker_qualification_proof"},
            ),
            actor,
        )
        self.document_service.add_document_link(
            context.tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="partner.subcontractor_worker_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=title,
                metadata_json={"worker_id": worker_id, "subcontractor_id": context.subcontractor_id},
            ),
            actor,
        )
        proof = next(item for item in self._qualification_proofs(context.tenant_id, qualification_id) if item.document_id == document.id)
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker_qualification.proof_uploaded",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=context.tenant_id,
            metadata_json={"document_id": proof.document_id, "source": "portal"},
        )
        return proof

    def link_existing_worker_qualification_proof_for_portal(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorWorkerQualificationProofLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationProofRead:
        self._require_portal_worker_qualification(context, worker_id, qualification_id)
        self.document_service.add_document_link(
            context.tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="partner.subcontractor_worker_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=self._normalize_optional(payload.label),
                metadata_json={"worker_id": worker_id, "subcontractor_id": context.subcontractor_id},
            ),
            actor,
        )
        proof = next(item for item in self._qualification_proofs(context.tenant_id, qualification_id) if item.document_id == payload.document_id)
        self._record_event(
            actor,
            event_type="subcontractors.portal.worker_qualification.proof_linked",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=context.tenant_id,
            metadata_json={"document_id": payload.document_id, "source": "portal"},
        )
        return proof

    def get_worker(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerRead:
        row = self._require_worker_for_read(tenant_id, subcontractor_id, worker_id, actor)
        return self._serialize_worker(row)

    def create_worker(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        self._validate_worker_path(tenant_id, subcontractor_id, payload)
        if self.repository.find_worker_by_number(tenant_id, subcontractor_id, payload.worker_no) is not None:
            raise ApiException(409, "subcontractors.conflict.worker_no", "errors.subcontractors.worker.duplicate_number")
        row = self.repository.create_worker(
            SubcontractorWorker(
                tenant_id=tenant_id,
                subcontractor_id=subcontractor_id,
                worker_no=payload.worker_no,
                first_name=payload.first_name,
                last_name=payload.last_name,
                preferred_name=self._normalize_optional(payload.preferred_name),
                birth_date=payload.birth_date,
                email=self._normalize_optional(payload.email),
                phone=self._normalize_optional(payload.phone),
                mobile=self._normalize_optional(payload.mobile),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.worker.created",
            entity_type="partner.subcontractor_worker",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._worker_snapshot(row),
        )
        return self._serialize_worker(row)

    def update_worker(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerRead:
        row = self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        before = self._worker_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "worker")
        next_worker_no = payload.worker_no if payload.worker_no is not None else row.worker_no
        if self.repository.find_worker_by_number(tenant_id, subcontractor_id, next_worker_no, exclude_id=worker_id) is not None:
            raise ApiException(409, "subcontractors.conflict.worker_no", "errors.subcontractors.worker.duplicate_number")
        row.worker_no = next_worker_no
        row.first_name = self._effective_optional(payload.first_name, row.first_name)
        row.last_name = self._effective_optional(payload.last_name, row.last_name)
        row.preferred_name = self._effective_optional(payload.preferred_name, row.preferred_name)
        row.birth_date = payload.birth_date if "birth_date" in payload.model_fields_set else row.birth_date
        row.email = self._effective_optional(payload.email, row.email)
        row.phone = self._effective_optional(payload.phone, row.phone)
        row.mobile = self._effective_optional(payload.mobile, row.mobile)
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_worker(row)
        self._record_event(
            actor,
            event_type="subcontractors.worker.updated",
            entity_type="partner.subcontractor_worker",
            entity_id=worker_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._worker_snapshot(updated),
        )
        return self._serialize_worker(updated)

    def list_worker_qualifications(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerQualificationRead]:
        self._require_worker_for_read(tenant_id, subcontractor_id, worker_id, actor)
        return [
            self._serialize_qualification(tenant_id, row)
            for row in self.repository.list_worker_qualifications(tenant_id, subcontractor_id, worker_id)
        ]

    def create_worker_qualification(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerQualificationCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationRead:
        self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        self._validate_worker_qualification_path(tenant_id, subcontractor_id, worker_id, payload)
        resolved = self._resolve_qualification_type(tenant_id, payload.qualification_type_id, payload.issued_at, payload.valid_until)
        row = self.repository.create_worker_qualification(
            SubcontractorWorkerQualification(
                tenant_id=tenant_id,
                worker_id=worker_id,
                qualification_type_id=payload.qualification_type_id,
                certificate_no=self._normalize_optional(payload.certificate_no),
                issued_at=payload.issued_at,
                valid_until=resolved.valid_until,
                issuing_authority=self._normalize_optional(payload.issuing_authority),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.worker_qualification.created",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._qualification_snapshot(row),
        )
        return self._serialize_qualification(tenant_id, row)

    def update_worker_qualification(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorWorkerQualificationUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationRead:
        self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        row = self._require_worker_qualification(tenant_id, subcontractor_id, worker_id, qualification_id)
        before = self._qualification_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "worker_qualification")
        issued_at = payload.issued_at if "issued_at" in payload.model_fields_set else row.issued_at
        valid_until = payload.valid_until if "valid_until" in payload.model_fields_set else row.valid_until
        resolved = self._resolve_qualification_type(tenant_id, row.qualification_type_id, issued_at, valid_until)
        row.certificate_no = self._effective_optional(payload.certificate_no, row.certificate_no)
        row.issued_at = issued_at
        row.valid_until = resolved.valid_until
        row.issuing_authority = self._effective_optional(payload.issuing_authority, row.issuing_authority)
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_worker_qualification(row)
        self._record_event(
            actor,
            event_type="subcontractors.worker_qualification.updated",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._qualification_snapshot(updated),
        )
        return self._serialize_qualification(tenant_id, updated)

    def list_worker_qualification_proofs(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerQualificationProofRead]:
        self._require_worker_qualification_for_read(tenant_id, subcontractor_id, worker_id, qualification_id, actor)
        return self._qualification_proofs(tenant_id, qualification_id)

    def upload_worker_qualification_proof(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorWorkerQualificationProofUpload,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationProofRead:
        qualification = self._require_worker_qualification_for_write(tenant_id, subcontractor_id, worker_id, qualification_id, actor)
        title = (payload.title or "").strip() or self._default_proof_title(qualification)
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="subcontractors",
                source_label="worker_qualification_proof",
                metadata_json={
                    "worker_id": worker_id,
                    "worker_qualification_id": qualification_id,
                    "subcontractor_id": subcontractor_id,
                },
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=payload.file_name,
                content_type=payload.content_type,
                content_base64=payload.content_base64,
                metadata_json={"kind": "worker_qualification_proof"},
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="partner.subcontractor_worker_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=title,
                metadata_json={"worker_id": worker_id, "subcontractor_id": subcontractor_id},
            ),
            actor,
        )
        proof = next(
            item
            for item in self._qualification_proofs(tenant_id, qualification_id)
            if item.document_id == document.id
        )
        self._record_event(
            actor,
            event_type="subcontractors.worker_qualification.proof_uploaded",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": proof.document_id},
        )
        return proof

    def link_existing_worker_qualification_proof(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        payload: SubcontractorWorkerQualificationProofLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualificationProofRead:
        self._require_worker_qualification_for_write(tenant_id, subcontractor_id, worker_id, qualification_id, actor)
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="partner.subcontractor_worker_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=self._normalize_optional(payload.label),
                metadata_json={"worker_id": worker_id, "subcontractor_id": subcontractor_id},
            ),
            actor,
        )
        proof = next(
            item
            for item in self._qualification_proofs(tenant_id, qualification_id)
            if item.document_id == payload.document_id
        )
        self._record_event(
            actor,
            event_type="subcontractors.worker_qualification.proof_linked",
            entity_type="partner.subcontractor_worker_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": payload.document_id},
        )
        return proof

    def list_worker_credentials(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerCredentialRead]:
        self._require_worker_for_read(tenant_id, subcontractor_id, worker_id, actor)
        return [
            SubcontractorWorkerCredentialRead.model_validate(row)
            for row in self.repository.list_worker_credentials(tenant_id, subcontractor_id, worker_id)
        ]

    def create_worker_credential(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerCredentialCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerCredentialRead:
        self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        self._validate_worker_credential_path(tenant_id, subcontractor_id, worker_id, payload)
        self._validate_credential_shape(payload.credential_type, payload.valid_from, payload.valid_until)
        self._ensure_credential_unique(tenant_id, payload.credential_no, payload.encoded_value)
        row = self.repository.create_worker_credential(
            SubcontractorWorkerCredential(
                tenant_id=tenant_id,
                worker_id=worker_id,
                credential_no=payload.credential_no,
                credential_type=payload.credential_type,
                encoded_value=payload.encoded_value,
                valid_from=payload.valid_from,
                valid_until=payload.valid_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="subcontractors.worker_credential.created",
            entity_type="partner.subcontractor_worker_credential",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._credential_snapshot(row),
        )
        return SubcontractorWorkerCredentialRead.model_validate(row)

    def update_worker_credential(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        credential_id: str,
        payload: SubcontractorWorkerCredentialUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerCredentialRead:
        self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        row = self._require_worker_credential(tenant_id, subcontractor_id, worker_id, credential_id)
        before = self._credential_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "worker_credential")
        next_encoded = payload.encoded_value if payload.encoded_value is not None else row.encoded_value
        next_from = payload.valid_from if payload.valid_from is not None else row.valid_from
        next_until = payload.valid_until if "valid_until" in payload.model_fields_set else row.valid_until
        self._validate_credential_shape(row.credential_type, next_from, next_until)
        self._ensure_credential_unique(tenant_id, row.credential_no, next_encoded, exclude_id=credential_id)
        row.encoded_value = next_encoded
        row.valid_from = next_from
        row.valid_until = next_until
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            if payload.status not in EMPLOYEE_CREDENTIAL_STATUSES:
                raise ApiException(400, "subcontractors.worker_credential.invalid_status", "errors.subcontractors.worker_credential.invalid_status")
            row.status = payload.status
            now = datetime.now(UTC)
            if payload.status == "issued":
                row.issued_at = now
                row.revoked_at = None
            elif payload.status in {"revoked", "expired"}:
                row.revoked_at = now
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        updated = self.repository.update_worker_credential(row)
        self._record_event(
            actor,
            event_type="subcontractors.worker_credential.updated",
            entity_type="partner.subcontractor_worker_credential",
            entity_id=credential_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._credential_snapshot(updated),
        )
        return SubcontractorWorkerCredentialRead.model_validate(updated)

    def _validate_worker_path(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerCreate,
    ) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.worker_tenant_mismatch", "errors.subcontractors.worker.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.validation.worker_company_mismatch",
                "errors.subcontractors.worker.subcontractor_mismatch",
            )

    def _validate_worker_qualification_path(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerQualificationCreate,
    ) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.worker_qualification_tenant_mismatch", "errors.subcontractors.worker_qualification.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.validation.worker_qualification_company_mismatch",
                "errors.subcontractors.worker_qualification.subcontractor_mismatch",
            )
        if payload.worker_id != worker_id:
            raise ApiException(
                400,
                "subcontractors.validation.worker_qualification_worker_mismatch",
                "errors.subcontractors.worker_qualification.worker_mismatch",
            )

    def _validate_worker_credential_path(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerCredentialCreate,
    ) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.worker_credential_tenant_mismatch", "errors.subcontractors.worker_credential.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.validation.worker_credential_company_mismatch",
                "errors.subcontractors.worker_credential.subcontractor_mismatch",
            )
        if payload.worker_id != worker_id:
            raise ApiException(
                400,
                "subcontractors.validation.worker_credential_worker_mismatch",
                "errors.subcontractors.worker_credential.worker_mismatch",
            )

    def _resolve_qualification_type(
        self,
        tenant_id: str,
        qualification_type_id: str,
        issued_at: date | None,
        valid_until: date | None,
    ) -> _ResolvedQualificationType:
        row = self.repository.get_qualification_type(tenant_id, qualification_type_id)
        if row is None or not row.is_active:
            raise ApiException(404, "subcontractors.worker_qualification.qualification_type_not_found", "errors.subcontractors.worker_qualification.qualification_type_not_found")
        if valid_until is not None and issued_at is not None and valid_until < issued_at:
            raise ApiException(400, "subcontractors.worker_qualification.invalid_window", "errors.subcontractors.worker_qualification.invalid_window")
        resolved_valid_until = valid_until
        if resolved_valid_until is None and issued_at is not None and row.default_validity_days is not None:
            resolved_valid_until = issued_at.fromordinal(issued_at.toordinal() + row.default_validity_days)
        if row.expiry_required and resolved_valid_until is None:
            raise ApiException(400, "subcontractors.worker_qualification.expiry_required", "errors.subcontractors.worker_qualification.expiry_required")
        return _ResolvedQualificationType(qualification_type=row, valid_until=resolved_valid_until)

    def _validate_credential_shape(self, credential_type: str, valid_from: date, valid_until: date | None) -> None:
        if credential_type not in EMPLOYEE_CREDENTIAL_TYPES:
            raise ApiException(400, "subcontractors.worker_credential.invalid_type", "errors.subcontractors.worker_credential.invalid_type")
        if valid_until is not None and valid_until < valid_from:
            raise ApiException(400, "subcontractors.worker_credential.invalid_window", "errors.subcontractors.worker_credential.invalid_window")

    def _ensure_credential_unique(
        self,
        tenant_id: str,
        credential_no: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if self.repository.find_worker_credential_by_no(tenant_id, credential_no, exclude_id=exclude_id) is not None:
            raise ApiException(409, "subcontractors.worker_credential.duplicate_no", "errors.subcontractors.worker_credential.duplicate_no")
        if self.repository.find_worker_credential_by_encoded_value(tenant_id, encoded_value, exclude_id=exclude_id) is not None:
            raise ApiException(
                409,
                "subcontractors.worker_credential.duplicate_encoded_value",
                "errors.subcontractors.worker_credential.duplicate_encoded_value",
            )

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

    def _require_portal_subcontractor(self, context: SubcontractorPortalContextRead) -> Subcontractor:
        row = self.repository.get_subcontractor(context.tenant_id, context.subcontractor_id)
        if row is None:
            raise ApiException(404, "subcontractors.subcontractor.not_found", "errors.subcontractors.subcontractor.not_found")
        return row

    def _require_portal_worker(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
    ) -> SubcontractorWorker:
        self._require_portal_subcontractor(context)
        row = self.repository.get_worker(context.tenant_id, context.subcontractor_id, worker_id)
        if row is None:
            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")
        return row

    def _require_portal_worker_qualification(
        self,
        context: SubcontractorPortalContextRead,
        worker_id: str,
        qualification_id: str,
    ) -> SubcontractorWorkerQualification:
        self._require_portal_worker(context, worker_id)
        row = self.repository.get_worker_qualification(context.tenant_id, context.subcontractor_id, worker_id, qualification_id)
        if row is None:
            raise ApiException(
                404,
                "subcontractors.worker_qualification.not_found",
                "errors.subcontractors.worker_qualification.not_found",
            )
        return row

    def _require_worker_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorker:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        row = self.repository.get_worker(tenant_id, subcontractor_id, worker_id)
        if row is None:
            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")
        return row

    def _require_worker_for_write(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorker:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        row = self.repository.get_worker(tenant_id, subcontractor_id, worker_id)
        if row is None:
            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")
        return row

    def _require_worker_qualification(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
    ) -> SubcontractorWorkerQualification:
        row = self.repository.get_worker_qualification(tenant_id, subcontractor_id, worker_id, qualification_id)
        if row is None:
            raise ApiException(
                404,
                "subcontractors.worker_qualification.not_found",
                "errors.subcontractors.worker_qualification.not_found",
            )
        return row

    def _require_worker_qualification_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualification:
        self._require_worker_for_read(tenant_id, subcontractor_id, worker_id, actor)
        return self._require_worker_qualification(tenant_id, subcontractor_id, worker_id, qualification_id)

    def _require_worker_qualification_for_write(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerQualification:
        self._require_worker_for_write(tenant_id, subcontractor_id, worker_id, actor)
        return self._require_worker_qualification(tenant_id, subcontractor_id, worker_id, qualification_id)

    def _require_worker_credential(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        credential_id: str,
    ) -> SubcontractorWorkerCredential:
        row = self.repository.get_worker_credential(tenant_id, subcontractor_id, worker_id, credential_id)
        if row is None:
            raise ApiException(
                404,
                "subcontractors.worker_credential.not_found",
                "errors.subcontractors.worker_credential.not_found",
            )
        return row

    def _serialize_worker(self, row: SubcontractorWorker) -> SubcontractorWorkerRead:
        return SubcontractorWorkerRead.model_validate(row).model_copy(
            update={
                "qualifications": [self._serialize_qualification(row.tenant_id, item) for item in row.qualifications],
                "credentials": [SubcontractorWorkerCredentialRead.model_validate(item) for item in row.credentials],
            }
        )

    def _serialize_portal_worker(self, row: SubcontractorWorker) -> SubcontractorPortalWorkerRead:
        return SubcontractorPortalWorkerRead.model_validate(row).model_copy(
            update={
                "qualifications": [self._serialize_qualification(row.tenant_id, item) for item in row.qualifications],
            }
        )

    def _serialize_qualification(
        self,
        tenant_id: str,
        row: SubcontractorWorkerQualification,
    ) -> SubcontractorWorkerQualificationRead:
        return SubcontractorWorkerQualificationRead.model_validate(row).model_copy(
            update={
                "qualification_type_code": row.qualification_type.code if row.qualification_type is not None else None,
                "qualification_type_label": row.qualification_type.label if row.qualification_type is not None else None,
                "proofs": self._qualification_proofs(tenant_id, row.id),
            }
        )

    def _qualification_proofs(self, tenant_id: str, qualification_id: str) -> list[SubcontractorWorkerQualificationProofRead]:
        proofs: list[SubcontractorWorkerQualificationProofRead] = []
        for document in self.document_repository.list_documents_for_owner(
            tenant_id,
            "partner.subcontractor_worker_qualification",
            qualification_id,
        ):
            current_version = self._current_document_version(document)
            proofs.append(
                SubcontractorWorkerQualificationProofRead(
                    document_id=document.id,
                    title=document.title,
                    document_type_key=document.document_type.key if document.document_type else None,
                    file_name=current_version.file_name if current_version else None,
                    content_type=current_version.content_type if current_version else None,
                    current_version_no=document.current_version_no,
                    relation_type="proof_document",
                )
            )
        return proofs

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
    def _worker_snapshot(row: SubcontractorWorker) -> dict[str, object]:
        return {
            "subcontractor_id": row.subcontractor_id,
            "worker_no": row.worker_no,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "preferred_name": row.preferred_name,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _qualification_snapshot(row: SubcontractorWorkerQualification) -> dict[str, object]:
        return {
            "worker_id": row.worker_id,
            "qualification_type_id": row.qualification_type_id,
            "certificate_no": row.certificate_no,
            "issued_at": row.issued_at.isoformat() if row.issued_at else None,
            "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _credential_snapshot(row: SubcontractorWorkerCredential) -> dict[str, object]:
        return {
            "worker_id": row.worker_id,
            "credential_no": row.credential_no,
            "credential_type": row.credential_type,
            "encoded_value": row.encoded_value,
            "status": row.status,
            "valid_from": row.valid_from.isoformat(),
            "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            "version_no": row.version_no,
        }

    @staticmethod
    def _default_proof_title(row: SubcontractorWorkerQualification) -> str:
        if row.qualification_type is not None:
            return f"Nachweis {row.qualification_type.label}"
        return "Qualifikationsnachweis"

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @classmethod
    def _effective_optional(cls, value: str | None, current_value: str | None) -> str | None:
        if value is None:
            return current_value
        return cls._normalize_optional(value)

    @staticmethod
    def _require_version(current_version: int, next_version: int | None, entity_name: str) -> None:
        if next_version is None or next_version != current_version:
            raise ApiException(
                409,
                f"subcontractors.conflict.{entity_name}.stale_version",
                f"errors.subcontractors.{entity_name}.stale_version",
            )

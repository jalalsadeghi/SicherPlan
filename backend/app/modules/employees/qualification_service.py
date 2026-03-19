"""Service layer for employee function/qualification catalogs and proof documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import (
    EMPLOYEE_QUALIFICATION_RECORD_KINDS,
    Employee,
    EmployeeQualification,
    FunctionType,
    QualificationType,
)
from app.modules.employees.schemas import (
    EmployeeDocumentListItemRead,
    EmployeeQualificationCreate,
    EmployeeQualificationFilter,
    EmployeeQualificationProofLinkCreate,
    EmployeeQualificationProofRead,
    EmployeeQualificationProofUpload,
    EmployeeQualificationRead,
    EmployeeQualificationUpdate,
    FunctionTypeCreate,
    FunctionTypeRead,
    FunctionTypeUpdate,
    QualificationTypeCreate,
    QualificationTypeRead,
    QualificationTypeUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.platform_services.docs_models import Document
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


@dataclass(frozen=True, slots=True)
class QualificationTarget:
    function_type: FunctionType | None
    qualification_type: QualificationType | None


class EmployeeQualificationRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def list_function_types(self, tenant_id: str) -> list[FunctionType]: ...
    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None: ...
    def find_function_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> FunctionType | None: ...
    def create_function_type(self, row: FunctionType) -> FunctionType: ...
    def update_function_type(self, row: FunctionType) -> FunctionType: ...
    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]: ...
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None: ...
    def find_qualification_type_by_code(
        self,
        tenant_id: str,
        code: str,
        *,
        exclude_id: str | None = None,
    ) -> QualificationType | None: ...
    def create_qualification_type(self, row: QualificationType) -> QualificationType: ...
    def update_qualification_type(self, row: QualificationType) -> QualificationType: ...
    def list_employee_qualifications(
        self,
        tenant_id: str,
        filters: EmployeeQualificationFilter | None = None,
    ) -> list[EmployeeQualification]: ...
    def get_employee_qualification(self, tenant_id: str, qualification_id: str) -> EmployeeQualification | None: ...
    def create_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification: ...
    def update_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification: ...


class EmployeeQualificationDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...


class EmployeeQualificationService:
    def __init__(
        self,
        *,
        repository: EmployeeQualificationRepository,
        document_repository: EmployeeQualificationDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_function_types(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
    ) -> list[FunctionTypeRead]:
        self._require_read_scope(tenant_id, context)
        return [FunctionTypeRead.model_validate(row) for row in self.repository.list_function_types(tenant_id)]

    def create_function_type(
        self,
        tenant_id: str,
        payload: FunctionTypeCreate,
        context: RequestAuthorizationContext,
    ) -> FunctionTypeRead:
        self._require_write_scope(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.function_type.tenant_mismatch", "errors.employees.function_type.tenant_mismatch")
        code = payload.code.strip()
        if self.repository.find_function_type_by_code(tenant_id, code) is not None:
            raise ApiException(409, "employees.function_type.duplicate_code", "errors.employees.function_type.duplicate_code")
        row = self.repository.create_function_type(
            FunctionType(
                tenant_id=tenant_id,
                code=code,
                label=payload.label.strip(),
                category=self._normalize_optional(payload.category),
                description=self._normalize_optional(payload.description),
                is_active=payload.is_active,
                planning_relevant=payload.planning_relevant,
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.function_type.created",
            entity_type="hr.function_type",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._function_type_snapshot(row),
        )
        return FunctionTypeRead.model_validate(row)

    def update_function_type(
        self,
        tenant_id: str,
        function_type_id: str,
        payload: FunctionTypeUpdate,
        context: RequestAuthorizationContext,
    ) -> FunctionTypeRead:
        self._require_write_scope(tenant_id, context)
        row = self._require_function_type(tenant_id, function_type_id)
        before = self._function_type_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "function_type")
        next_code = self._effective_text(payload.code, row.code)
        duplicate = self.repository.find_function_type_by_code(tenant_id, next_code, exclude_id=function_type_id)
        if duplicate is not None:
            raise ApiException(409, "employees.function_type.duplicate_code", "errors.employees.function_type.duplicate_code")
        row.code = next_code
        row.label = self._effective_text(payload.label, row.label)
        row.category = self._effective_optional(payload.category, row.category)
        row.description = self._effective_optional(payload.description, row.description)
        if payload.is_active is not None:
            row.is_active = payload.is_active
        if payload.planning_relevant is not None:
            row.planning_relevant = payload.planning_relevant
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_function_type(row)
        self._record_event(
            context,
            event_type="employees.function_type.updated",
            entity_type="hr.function_type",
            entity_id=function_type_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._function_type_snapshot(updated),
        )
        return FunctionTypeRead.model_validate(updated)

    def list_qualification_types(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
    ) -> list[QualificationTypeRead]:
        self._require_read_scope(tenant_id, context)
        return [QualificationTypeRead.model_validate(row) for row in self.repository.list_qualification_types(tenant_id)]

    def create_qualification_type(
        self,
        tenant_id: str,
        payload: QualificationTypeCreate,
        context: RequestAuthorizationContext,
    ) -> QualificationTypeRead:
        self._require_write_scope(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.qualification_type.tenant_mismatch",
                "errors.employees.qualification_type.tenant_mismatch",
            )
        code = payload.code.strip()
        if self.repository.find_qualification_type_by_code(tenant_id, code) is not None:
            raise ApiException(
                409,
                "employees.qualification_type.duplicate_code",
                "errors.employees.qualification_type.duplicate_code",
            )
        self._validate_default_validity(payload.default_validity_days)
        row = self.repository.create_qualification_type(
            QualificationType(
                tenant_id=tenant_id,
                code=code,
                label=payload.label.strip(),
                category=self._normalize_optional(payload.category),
                description=self._normalize_optional(payload.description),
                is_active=payload.is_active,
                planning_relevant=payload.planning_relevant,
                compliance_relevant=payload.compliance_relevant,
                expiry_required=payload.expiry_required,
                default_validity_days=payload.default_validity_days,
                proof_required=payload.proof_required,
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.qualification_type.created",
            entity_type="hr.qualification_type",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._qualification_type_snapshot(row),
        )
        return QualificationTypeRead.model_validate(row)

    def update_qualification_type(
        self,
        tenant_id: str,
        qualification_type_id: str,
        payload: QualificationTypeUpdate,
        context: RequestAuthorizationContext,
    ) -> QualificationTypeRead:
        self._require_write_scope(tenant_id, context)
        row = self._require_qualification_type(tenant_id, qualification_type_id)
        before = self._qualification_type_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "qualification_type")
        next_code = self._effective_text(payload.code, row.code)
        duplicate = self.repository.find_qualification_type_by_code(tenant_id, next_code, exclude_id=qualification_type_id)
        if duplicate is not None:
            raise ApiException(
                409,
                "employees.qualification_type.duplicate_code",
                "errors.employees.qualification_type.duplicate_code",
            )
        next_default_validity = payload.default_validity_days if payload.default_validity_days is not None else row.default_validity_days
        self._validate_default_validity(next_default_validity)
        row.code = next_code
        row.label = self._effective_text(payload.label, row.label)
        row.category = self._effective_optional(payload.category, row.category)
        row.description = self._effective_optional(payload.description, row.description)
        if payload.is_active is not None:
            row.is_active = payload.is_active
        if payload.planning_relevant is not None:
            row.planning_relevant = payload.planning_relevant
        if payload.compliance_relevant is not None:
            row.compliance_relevant = payload.compliance_relevant
        if payload.expiry_required is not None:
            row.expiry_required = payload.expiry_required
        row.default_validity_days = next_default_validity
        if payload.proof_required is not None:
            row.proof_required = payload.proof_required
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_qualification_type(row)
        self._record_event(
            context,
            event_type="employees.qualification_type.updated",
            entity_type="hr.qualification_type",
            entity_id=qualification_type_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._qualification_type_snapshot(updated),
        )
        return QualificationTypeRead.model_validate(updated)

    def list_employee_qualifications(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
        filters: EmployeeQualificationFilter | None = None,
    ) -> list[EmployeeQualificationRead]:
        self._require_read_scope(tenant_id, context)
        if filters is not None and filters.employee_id is not None:
            self._require_employee(tenant_id, filters.employee_id)
        rows = self.repository.list_employee_qualifications(tenant_id, filters or EmployeeQualificationFilter())
        return [EmployeeQualificationRead.model_validate(row) for row in rows]

    def get_employee_qualification(
        self,
        tenant_id: str,
        qualification_id: str,
        context: RequestAuthorizationContext,
    ) -> EmployeeQualificationRead:
        self._require_read_scope(tenant_id, context)
        row = self._require_employee_qualification(tenant_id, qualification_id)
        return EmployeeQualificationRead.model_validate(row)

    def create_employee_qualification(
        self,
        tenant_id: str,
        payload: EmployeeQualificationCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeQualificationRead:
        self._require_write_scope(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.employee_qualification.tenant_mismatch",
                "errors.employees.employee_qualification.tenant_mismatch",
            )
        employee = self._require_employee(tenant_id, payload.employee_id)
        record_kind = payload.record_kind.strip()
        target = self._resolve_target(tenant_id, record_kind, payload.function_type_id, payload.qualification_type_id)
        valid_until = self._resolve_valid_until(
            target.qualification_type,
            issued_at=payload.issued_at,
            valid_until=payload.valid_until,
        )
        row = self.repository.create_employee_qualification(
            EmployeeQualification(
                tenant_id=tenant_id,
                employee_id=employee.id,
                record_kind=record_kind,
                function_type_id=target.function_type.id if target.function_type is not None else None,
                qualification_type_id=target.qualification_type.id if target.qualification_type is not None else None,
                certificate_no=self._normalize_optional(payload.certificate_no),
                issued_at=payload.issued_at,
                valid_until=valid_until,
                issuing_authority=self._normalize_optional(payload.issuing_authority),
                granted_internally=payload.granted_internally,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.employee_qualification.created",
            entity_type="hr.employee_qualification",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._employee_qualification_snapshot(row),
        )
        return EmployeeQualificationRead.model_validate(row)

    def update_employee_qualification(
        self,
        tenant_id: str,
        qualification_id: str,
        payload: EmployeeQualificationUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeQualificationRead:
        self._require_write_scope(tenant_id, context)
        row = self._require_employee_qualification(tenant_id, qualification_id)
        before = self._employee_qualification_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "employee_qualification")
        record_kind = row.record_kind
        function_type_id = payload.function_type_id if payload.function_type_id is not None else row.function_type_id
        qualification_type_id = (
            payload.qualification_type_id if payload.qualification_type_id is not None else row.qualification_type_id
        )
        target = self._resolve_target(tenant_id, record_kind, function_type_id, qualification_type_id)
        issued_at = payload.issued_at if payload.issued_at is not None else row.issued_at
        valid_until = payload.valid_until if payload.valid_until is not None else row.valid_until
        row.function_type_id = target.function_type.id if target.function_type is not None else None
        row.qualification_type_id = target.qualification_type.id if target.qualification_type is not None else None
        row.certificate_no = self._effective_optional(payload.certificate_no, row.certificate_no)
        row.issued_at = issued_at
        row.valid_until = self._resolve_valid_until(target.qualification_type, issued_at=issued_at, valid_until=valid_until)
        row.issuing_authority = self._effective_optional(payload.issuing_authority, row.issuing_authority)
        if payload.granted_internally is not None:
            row.granted_internally = payload.granted_internally
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_employee_qualification(row)
        self._record_event(
            context,
            event_type="employees.employee_qualification.updated",
            entity_type="hr.employee_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._employee_qualification_snapshot(updated),
        )
        return EmployeeQualificationRead.model_validate(updated)

    def list_proofs(
        self,
        tenant_id: str,
        qualification_id: str,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeQualificationProofRead]:
        self._require_read_scope(tenant_id, context)
        self._require_employee_qualification(tenant_id, qualification_id)
        return [
            EmployeeQualificationProofRead(**self._map_document(document).model_dump())
            for document in self.document_repository.list_documents_for_owner(
                tenant_id,
                "hr.employee_qualification",
                qualification_id,
            )
        ]

    def upload_proof(
        self,
        tenant_id: str,
        qualification_id: str,
        payload: EmployeeQualificationProofUpload,
        context: RequestAuthorizationContext,
    ) -> EmployeeQualificationProofRead:
        self._require_write_scope(tenant_id, context)
        qualification = self._require_employee_qualification(tenant_id, qualification_id)
        title = (payload.title or "").strip() or self._default_proof_title(qualification)
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="employees",
                source_label="qualification_proof",
                metadata_json={
                    "employee_id": qualification.employee_id,
                    "employee_qualification_id": qualification_id,
                    "record_kind": qualification.record_kind,
                },
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
                metadata_json={"kind": "qualification_proof"},
            ),
            context,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="hr.employee_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=title,
                metadata_json={"employee_id": qualification.employee_id},
            ),
            context,
        )
        proof_document = next(
            item
            for item in self.document_repository.list_documents_for_owner(tenant_id, "hr.employee_qualification", qualification_id)
            if item.id == document.id
        )
        proof = self._map_document(proof_document)
        self._record_event(
            context,
            event_type="employees.employee_qualification.proof_uploaded",
            entity_type="hr.employee_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": proof.document_id},
        )
        return EmployeeQualificationProofRead(**proof.model_dump())

    def link_existing_proof(
        self,
        tenant_id: str,
        qualification_id: str,
        payload: EmployeeQualificationProofLinkCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeQualificationProofRead:
        self._require_write_scope(tenant_id, context)
        qualification = self._require_employee_qualification(tenant_id, qualification_id)
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="hr.employee_qualification",
                owner_id=qualification_id,
                relation_type="proof_document",
                label=self._normalize_optional(payload.label),
                metadata_json={"employee_id": qualification.employee_id},
            ),
            context,
        )
        linked_document = next(
            document
            for document in self.document_repository.list_documents_for_owner(tenant_id, "hr.employee_qualification", qualification_id)
            if document.id == payload.document_id
        )
        proof = self._map_document(linked_document)
        self._record_event(
            context,
            event_type="employees.employee_qualification.proof_linked",
            entity_type="hr.employee_qualification",
            entity_id=qualification_id,
            tenant_id=tenant_id,
            metadata_json={"document_id": payload.document_id},
        )
        return EmployeeQualificationProofRead(**proof.model_dump())

    def _resolve_target(
        self,
        tenant_id: str,
        record_kind: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
    ) -> QualificationTarget:
        normalized_kind = record_kind.strip()
        if normalized_kind not in EMPLOYEE_QUALIFICATION_RECORD_KINDS:
            raise ApiException(
                400,
                "employees.employee_qualification.invalid_kind",
                "errors.employees.employee_qualification.invalid_kind",
            )
        if normalized_kind == "function":
            if function_type_id is None or qualification_type_id is not None:
                raise ApiException(
                    400,
                    "employees.employee_qualification.target_mismatch",
                    "errors.employees.employee_qualification.target_mismatch",
                )
            return QualificationTarget(function_type=self._require_function_type(tenant_id, function_type_id), qualification_type=None)
        if qualification_type_id is None or function_type_id is not None:
            raise ApiException(
                400,
                "employees.employee_qualification.target_mismatch",
                "errors.employees.employee_qualification.target_mismatch",
            )
        return QualificationTarget(function_type=None, qualification_type=self._require_qualification_type(tenant_id, qualification_type_id))

    def _resolve_valid_until(
        self,
        qualification_type: QualificationType | None,
        *,
        issued_at: date | None,
        valid_until: date | None,
    ) -> date | None:
        resolved = valid_until
        if qualification_type is not None and resolved is None and issued_at is not None and qualification_type.default_validity_days:
            resolved = issued_at + timedelta(days=qualification_type.default_validity_days)
        if resolved is not None and issued_at is not None and resolved < issued_at:
            raise ApiException(
                400,
                "employees.employee_qualification.invalid_window",
                "errors.employees.employee_qualification.invalid_window",
            )
        if qualification_type is not None and qualification_type.expiry_required and resolved is None:
            raise ApiException(
                400,
                "employees.employee_qualification.expiry_required",
                "errors.employees.employee_qualification.expiry_required",
            )
        return resolved

    @staticmethod
    def _validate_default_validity(default_validity_days: int | None) -> None:
        if default_validity_days is None:
            return
        if default_validity_days <= 0:
            raise ApiException(
                400,
                "employees.qualification_type.invalid_validity_days",
                "errors.employees.qualification_type.invalid_validity_days",
            )

    def _require_read_scope(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.read" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.read"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_write_scope(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.write" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "employees.employee.write"},
            )
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        employee = self.repository.get_employee(tenant_id, employee_id)
        if employee is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return employee

    def _require_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType:
        row = self.repository.get_function_type(tenant_id, function_type_id)
        if row is None:
            raise ApiException(
                404,
                "employees.function_type.not_found",
                "errors.employees.function_type.not_found",
            )
        return row

    def _require_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType:
        row = self.repository.get_qualification_type(tenant_id, qualification_type_id)
        if row is None:
            raise ApiException(
                404,
                "employees.qualification_type.not_found",
                "errors.employees.qualification_type.not_found",
            )
        return row

    def _require_employee_qualification(self, tenant_id: str, qualification_id: str) -> EmployeeQualification:
        row = self.repository.get_employee_qualification(tenant_id, qualification_id)
        if row is None:
            raise ApiException(
                404,
                "employees.employee_qualification.not_found",
                "errors.employees.employee_qualification.not_found",
            )
        return row

    @staticmethod
    def _require_version(current: int, incoming: int | None, resource: str) -> None:
        if incoming is None or incoming != current:
            raise ApiException(
                409,
                f"employees.{resource}.stale_version",
                f"errors.employees.{resource}.stale_version",
            )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _effective_text(value: str | None, current: str) -> str:
        if value is None:
            return current
        normalized = value.strip()
        return normalized or current

    @staticmethod
    def _effective_optional(value: str | None, current: str | None) -> str | None:
        if value is None:
            return current
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _default_proof_title(row: EmployeeQualification) -> str:
        if row.record_kind == "function":
            return "Funktionsnachweis"
        return "Qualifikationsnachweis"

    def _record_event(
        self,
        context: RequestAuthorizationContext,
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
                user_id=context.user_id,
                session_id=context.session_id,
                request_id=context.request_id,
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
    def _function_type_snapshot(row: FunctionType) -> dict[str, object]:
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "code": row.code,
            "label": row.label,
            "category": row.category,
            "is_active": row.is_active,
            "planning_relevant": row.planning_relevant,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _qualification_type_snapshot(row: QualificationType) -> dict[str, object]:
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "code": row.code,
            "label": row.label,
            "category": row.category,
            "is_active": row.is_active,
            "planning_relevant": row.planning_relevant,
            "compliance_relevant": row.compliance_relevant,
            "expiry_required": row.expiry_required,
            "default_validity_days": row.default_validity_days,
            "proof_required": row.proof_required,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _employee_qualification_snapshot(row: EmployeeQualification) -> dict[str, object]:
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "employee_id": row.employee_id,
            "record_kind": row.record_kind,
            "function_type_id": row.function_type_id,
            "qualification_type_id": row.qualification_type_id,
            "certificate_no": row.certificate_no,
            "issued_at": row.issued_at.isoformat() if row.issued_at else None,
            "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            "issuing_authority": row.issuing_authority,
            "granted_internally": row.granted_internally,
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _map_document(document: Document) -> EmployeeDocumentListItemRead:
        latest_version = max(document.versions, key=lambda version: version.version_no) if document.versions else None
        links = [link for link in document.links if link.owner_type == "hr.employee_qualification"]
        links.sort(key=lambda link: link.linked_at, reverse=True)
        link = links[0] if links else None
        return EmployeeDocumentListItemRead(
            document_id=document.id,
            relation_type=link.relation_type if link else "proof_document",
            label=link.label if link else None,
            title=document.title,
            document_type_key=document.document_type.key if document.document_type else None,
            file_name=latest_version.file_name if latest_version else None,
            content_type=latest_version.content_type if latest_version else None,
            current_version_no=document.current_version_no if document.current_version_no > 0 else None,
            linked_at=link.linked_at if link else None,
        )

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Branch, Mandate
from app.modules.employees.models import Employee, EmployeeQualification, FunctionType, QualificationType
from app.modules.employees.qualification_service import EmployeeQualificationService
from app.modules.employees.schemas import (
    EmployeeQualificationCreate,
    EmployeeQualificationFilter,
    EmployeeQualificationProofLinkCreate,
    EmployeeQualificationProofUpload,
    EmployeeQualificationUpdate,
    FunctionTypeCreate,
    QualificationTypeCreate,
)
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentVersion
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentRead, DocumentVersionCreate, DocumentVersionRead


def _context(*permissions: str, tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeQualificationRepository:
    tenant_id: str = "tenant-1"
    branch_id: str = "branch-1"
    mandate_id: str = "mandate-1"
    employees: dict[str, Employee] = field(default_factory=dict)
    function_types: dict[str, FunctionType] = field(default_factory=dict)
    qualification_types: dict[str, QualificationType] = field(default_factory=dict)
    employee_qualifications: dict[str, EmployeeQualification] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.branch = Branch(
            id=self.branch_id,
            tenant_id=self.tenant_id,
            code="BER",
            name="Berlin",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.mandate = Mandate(
            id=self.mandate_id,
            tenant_id=self.tenant_id,
            branch_id=self.branch_id,
            code="M-001",
            name="Mandate",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        employee = Employee(
            id="employee-1",
            tenant_id=self.tenant_id,
            personnel_no="EMP-1001",
            first_name="Anna",
            last_name="Wagner",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.employees[employee.id] = employee

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "status", None) is None:
            row.status = "active"
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        if getattr(row, "version_no", None) is None:
            row.version_no = 1

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        row = self.employees.get(employee_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_function_types(self, tenant_id: str) -> list[FunctionType]:
        return sorted(
            [row for row in self.function_types.values() if row.tenant_id == tenant_id],
            key=lambda row: row.code,
        )

    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None:
        row = self.function_types.get(function_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_function_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> FunctionType | None:
        for row in self.function_types.values():
            if row.tenant_id == tenant_id and row.code == code and row.id != exclude_id:
                return row
        return None

    def create_function_type(self, row: FunctionType) -> FunctionType:
        self._stamp(row)
        self.function_types[row.id] = row
        return row

    def update_function_type(self, row: FunctionType) -> FunctionType:
        self._stamp(row)
        self.function_types[row.id] = row
        return row

    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]:
        return sorted(
            [row for row in self.qualification_types.values() if row.tenant_id == tenant_id],
            key=lambda row: row.code,
        )

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        row = self.qualification_types.get(qualification_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_qualification_type_by_code(
        self,
        tenant_id: str,
        code: str,
        *,
        exclude_id: str | None = None,
    ) -> QualificationType | None:
        for row in self.qualification_types.values():
            if row.tenant_id == tenant_id and row.code == code and row.id != exclude_id:
                return row
        return None

    def create_qualification_type(self, row: QualificationType) -> QualificationType:
        self._stamp(row)
        self.qualification_types[row.id] = row
        return row

    def update_qualification_type(self, row: QualificationType) -> QualificationType:
        self._stamp(row)
        self.qualification_types[row.id] = row
        return row

    def list_employee_qualifications(
        self,
        tenant_id: str,
        filters: EmployeeQualificationFilter | None = None,
    ) -> list[EmployeeQualification]:
        rows = [row for row in self.employee_qualifications.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.record_kind is not None:
                rows = [row for row in rows if row.record_kind == filters.record_kind]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
            if not filters.include_expired:
                cutoff = filters.valid_on or date.today()
                rows = [row for row in rows if row.valid_until is None or row.valid_until >= cutoff]
        rows.sort(key=lambda row: (row.valid_until or date.max, row.created_at))
        return rows

    def get_employee_qualification(self, tenant_id: str, qualification_id: str) -> EmployeeQualification | None:
        row = self.employee_qualifications.get(qualification_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification:
        self._stamp(row)
        row.employee = self.get_employee(row.tenant_id, row.employee_id)
        row.function_type = self.get_function_type(row.tenant_id, row.function_type_id) if row.function_type_id else None
        row.qualification_type = (
            self.get_qualification_type(row.tenant_id, row.qualification_type_id) if row.qualification_type_id else None
        )
        self.employee_qualifications[row.id] = row
        return row

    def update_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification:
        self._stamp(row)
        row.employee = self.get_employee(row.tenant_id, row.employee_id)
        row.function_type = self.get_function_type(row.tenant_id, row.function_type_id) if row.function_type_id else None
        row.qualification_type = (
            self.get_qualification_type(row.tenant_id, row.qualification_type_id) if row.qualification_type_id else None
        )
        self.employee_qualifications[row.id] = row
        return row


@dataclass
class FakeDocumentRepo:
    documents: list[Document] = field(default_factory=list)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        return [
            document
            for document in self.documents
            if document.tenant_id == tenant_id
            and any(link.owner_type == owner_type and link.owner_id == owner_id for link in document.links)
        ]


class FakeDocumentService:
    def __init__(self, repository: FakeDocumentRepo) -> None:
        self.repository = repository

    def create_document(self, tenant_id: str, payload: DocumentCreate, actor) -> DocumentRead:  # noqa: ANN001
        now = datetime.now(UTC)
        document = Document(
            id=f"document-{len(self.repository.documents) + 1}",
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
            metadata_json=payload.metadata_json,
            current_version_no=0,
            status="active",
            created_at=now,
            updated_at=now,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            version_no=1,
            versions=[],
            links=[],
        )
        self.repository.documents.append(document)
        return DocumentRead.model_validate(document)

    def add_document_version(
        self,
        tenant_id: str,
        document_id: str,
        payload: DocumentVersionCreate,
        actor,  # noqa: ANN001
    ) -> DocumentVersionRead:
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        version_no = document.current_version_no + 1
        version = DocumentVersion(
            id=f"version-{document_id}-{version_no}",
            tenant_id=tenant_id,
            document_id=document_id,
            version_no=version_no,
            file_name=payload.file_name,
            content_type=payload.content_type,
            object_bucket="bucket",
            object_key=f"{document_id}/{version_no}",
            checksum_sha256="checksum",
            file_size_bytes=10,
            uploaded_by_user_id=actor.user_id,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=False,
            metadata_json=payload.metadata_json,
        )
        document.versions.append(version)
        document.current_version_no = version_no
        document.updated_at = datetime.now(UTC)
        return DocumentVersionRead.model_validate(version)

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        link = DocumentLink(
            id=f"link-{document_id}-{len(document.links) + 1}",
            tenant_id=tenant_id,
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            relation_type=payload.relation_type,
            label=payload.label,
            linked_by_user_id=actor.user_id,
            linked_at=datetime.now(UTC),
            metadata_json=payload.metadata_json,
        )
        document.links.append(link)
        return link


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


class EmployeeQualificationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeQualificationRepository()
        self.document_repository = FakeDocumentRepo()
        self.audit_repository = RecordingAuditRepository()
        self.service = EmployeeQualificationService(
            repository=self.repository,
            document_repository=self.document_repository,
            document_service=FakeDocumentService(self.document_repository),
            audit_service=AuditService(self.audit_repository),
        )

    def test_create_qualification_type_and_assignment_applies_default_validity(self) -> None:
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="FIRST_AID",
                label="Erste Hilfe",
                expiry_required=True,
                default_validity_days=365,
                proof_required=True,
            ),
            _context("employees.employee.write"),
        )

        assignment = self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="qualification",
                qualification_type_id=qualification_type.id,
                issued_at=date(2026, 1, 1),
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(assignment.valid_until, date(2027, 1, 1))
        self.assertEqual(assignment.qualification_type_id, qualification_type.id)
        self.assertIn(
            "employees.employee_qualification.created",
            [event.event_type for event in self.audit_repository.audit_events],
        )

    def test_create_function_assignment_requires_function_target_only(self) -> None:
        function_type = self.service.create_function_type(
            "tenant-1",
            FunctionTypeCreate(
                tenant_id="tenant-1",
                code="SHIFT_LEAD",
                label="Schichtleitung",
            ),
            _context("employees.employee.write"),
        )

        assignment = self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="function",
                function_type_id=function_type.id,
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(assignment.record_kind, "function")
        self.assertEqual(assignment.function_type_id, function_type.id)
        self.assertIsNone(assignment.qualification_type_id)

    def test_reported_g34a_qualification_succeeds_without_valid_until(self) -> None:
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="G34A",
                label="34a certified",
                compliance_relevant=True,
                proof_required=True,
                expiry_required=False,
                default_validity_days=None,
            ),
            _context("employees.employee.write"),
        )

        assignment = self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="qualification",
                qualification_type_id=qualification_type.id,
                certificate_no="G34A-EK-2026-031",
                issued_at=date(2026, 1, 20),
                valid_until=None,
                issuing_authority="IHK Köln",
                granted_internally=False,
                notes="Eligible for standard guard deployment.",
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(assignment.record_kind, "qualification")
        self.assertEqual(assignment.qualification_type_id, qualification_type.id)
        self.assertIsNone(assignment.function_type_id)
        self.assertIsNone(assignment.valid_until)

    def test_create_qualification_rejects_stale_function_target_for_qualification_kind(self) -> None:
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="G34A",
                label="34a certified",
            ),
            _context("employees.employee.write"),
        )
        function_type = self.service.create_function_type(
            "tenant-1",
            FunctionTypeCreate(
                tenant_id="tenant-1",
                code="SHIFT_LEAD",
                label="Schichtleitung",
            ),
            _context("employees.employee.write"),
        )

        with self.assertRaises(ApiException) as raised:
            self.service.create_employee_qualification(
                "tenant-1",
                EmployeeQualificationCreate(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    record_kind="qualification",
                    function_type_id=function_type.id,
                    qualification_type_id=qualification_type.id,
                    certificate_no="G34A-EK-2026-031",
                    issued_at=date(2026, 1, 20),
                    issuing_authority="IHK Köln",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(raised.exception.message_key, "errors.employees.employee_qualification.target_mismatch")

    def test_update_assignment_rejects_missing_expiry_for_required_type(self) -> None:
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="GSSK",
                label="GSSK",
                expiry_required=True,
            ),
            _context("employees.employee.write"),
        )
        assignment = self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="qualification",
                qualification_type_id=qualification_type.id,
                issued_at=date(2026, 1, 1),
                valid_until=date(2027, 1, 1),
            ),
            _context("employees.employee.write"),
        )

        with self.assertRaises(ApiException) as raised:
            self.service.update_employee_qualification(
                "tenant-1",
                assignment.id,
                EmployeeQualificationUpdate(
                    qualification_type_id=qualification_type.id,
                    issued_at=date(2026, 6, 1),
                    valid_until=date(2026, 5, 1),
                    version_no=assignment.version_no,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(raised.exception.message_key, "errors.employees.employee_qualification.invalid_window")

    def test_upload_and_link_proofs_use_docs_owner_type(self) -> None:
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="SACHKUNDE",
                label="Sachkunde",
            ),
            _context("employees.employee.write"),
        )
        assignment = self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="qualification",
                qualification_type_id=qualification_type.id,
            ),
            _context("employees.employee.write"),
        )

        uploaded = self.service.upload_proof(
            "tenant-1",
            assignment.id,
            EmployeeQualificationProofUpload(
                title="Sachkundenachweis",
                file_name="proof.pdf",
                content_type="application/pdf",
                content_base64="YQ==",
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(uploaded.relation_type, "proof_document")
        self.assertEqual(
            self.document_repository.documents[0].links[0].owner_type,
            "hr.employee_qualification",
        )

        linked = self.service.link_existing_proof(
            "tenant-1",
            assignment.id,
            EmployeeQualificationProofLinkCreate(document_id=uploaded.document_id, label="Bereits vorhanden"),
            _context("employees.employee.write"),
        )
        self.assertEqual(linked.document_id, uploaded.document_id)
        self.assertIn(
            "employees.employee_qualification.proof_linked",
            [event.event_type for event in self.audit_repository.audit_events],
        )

    def test_list_filters_hide_expired_rows_by_default_and_can_filter_by_kind(self) -> None:
        function_type = self.service.create_function_type(
            "tenant-1",
            FunctionTypeCreate(
                tenant_id="tenant-1",
                code="DISPATCH",
                label="Disposition",
            ),
            _context("employees.employee.write"),
        )
        qualification_type = self.service.create_qualification_type(
            "tenant-1",
            QualificationTypeCreate(
                tenant_id="tenant-1",
                code="NIGHT",
                label="Nachtbewachung",
            ),
            _context("employees.employee.write"),
        )
        self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="function",
                function_type_id=function_type.id,
            ),
            _context("employees.employee.write"),
        )
        self.service.create_employee_qualification(
            "tenant-1",
            EmployeeQualificationCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                record_kind="qualification",
                qualification_type_id=qualification_type.id,
                issued_at=date(2024, 1, 1),
                valid_until=date(2024, 12, 31),
            ),
            _context("employees.employee.write"),
        )

        default_rows = self.service.list_employee_qualifications(
            "tenant-1",
            _context("employees.employee.read"),
            EmployeeQualificationFilter(employee_id="employee-1"),
        )
        qualification_rows = self.service.list_employee_qualifications(
            "tenant-1",
            _context("employees.employee.read"),
            EmployeeQualificationFilter(
                employee_id="employee-1",
                record_kind="qualification",
                include_expired=True,
            ),
        )

        self.assertEqual(len(default_rows), 1)
        self.assertEqual(default_rows[0].record_kind, "function")
        self.assertEqual(len(qualification_rows), 1)
        self.assertEqual(qualification_rows[0].record_kind, "qualification")

    def test_metadata_exposes_expected_constraints_and_docs_owner_support(self) -> None:
        function_table = Base.metadata.tables["hr.function_type"]
        qualification_table = Base.metadata.tables["hr.qualification_type"]
        employee_qualification_table = Base.metadata.tables["hr.employee_qualification"]

        function_uniques = {
            tuple(constraint.columns.keys())
            for constraint in function_table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        qualification_checks = {
            constraint.name
            for constraint in qualification_table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        qualification_indexes = {
            index.name for index in employee_qualification_table.indexes if isinstance(index, Index)
        }

        self.assertIn(("tenant_id", "code"), function_uniques)
        self.assertIn("ck_qualification_type_qualification_type_default_validity_positive", qualification_checks)
        self.assertIn(
            "ck_employee_qualification_employee_qualification_record_kind_valid",
            {c.name for c in employee_qualification_table.constraints if isinstance(c, CheckConstraint)},
        )
        self.assertIn("ix_hr_employee_qualification_employee_kind_status", qualification_indexes)
        self.assertIn("hr.employee_qualification", SqlAlchemyDocumentRepository.SUPPORTED_OWNER_TYPES)


if __name__ == "__main__":
    unittest.main()

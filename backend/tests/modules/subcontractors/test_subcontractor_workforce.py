from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.employees.models import QualificationType
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentType, DocumentVersion
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.subcontractors.models import (
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.schemas import (
    SubcontractorCreate,
    SubcontractorWorkerCreate,
    SubcontractorWorkerCredentialCreate,
    SubcontractorWorkerCredentialUpdate,
    SubcontractorWorkerFilter,
    SubcontractorWorkerQualificationCreate,
    SubcontractorWorkerQualificationProofLinkCreate,
    SubcontractorWorkerQualificationProofUpload,
    SubcontractorWorkerQualificationUpdate,
    SubcontractorWorkerUpdate,
)
from app.modules.subcontractors.service import SubcontractorService
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService
from tests.modules.subcontractors.test_subcontractor_master import (
    FakeHistoryDocumentRepository,
    FakeSubcontractorRepository,
    RecordingAuditRepository,
    _context,
)
from app.modules.iam.audit_service import AuditService


@dataclass
class FakeSubcontractorWorkforceRepository(FakeSubcontractorRepository):
    workers: dict[str, SubcontractorWorker] = field(default_factory=dict)
    worker_qualifications: dict[str, SubcontractorWorkerQualification] = field(default_factory=dict)
    worker_credentials: dict[str, SubcontractorWorkerCredential] = field(default_factory=dict)
    qualification_types: dict[str, QualificationType] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.qualification_types["qual-expiring"] = QualificationType(
            id="qual-expiring",
            tenant_id=self.tenant_id,
            code="sachkunde34a",
            label="Sachkunde 34a",
            category="security",
            description=None,
            is_active=True,
            planning_relevant=True,
            compliance_relevant=True,
            expiry_required=True,
            default_validity_days=365,
            proof_required=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.qualification_types["qual-open"] = QualificationType(
            id="qual-open",
            tenant_id=self.tenant_id,
            code="ersthelfer",
            label="Ersthelfer",
            category="safety",
            description=None,
            is_active=True,
            planning_relevant=True,
            compliance_relevant=False,
            expiry_required=False,
            default_validity_days=None,
            proof_required=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )

    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]:
        rows = [
            row
            for row in self.workers.values()
            if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id
        ]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.status is not None:
            rows = [row for row in rows if row.status == filters.status]
        if filters.search:
            term = filters.search.lower()
            rows = [
                row
                for row in rows
                if term in row.worker_no.lower()
                or term in row.first_name.lower()
                or term in row.last_name.lower()
                or term in (row.preferred_name or "").lower()
            ]
        rows.sort(key=lambda row: row.worker_no)
        for row in rows:
            self._hydrate_worker(row)
        return rows

    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None:
        row = self.workers.get(worker_id)
        if row is None or row.tenant_id != tenant_id or row.subcontractor_id != subcontractor_id:
            return None
        self._hydrate_worker(row)
        return row

    def create_worker(self, row: SubcontractorWorker) -> SubcontractorWorker:
        self._stamp(row)
        self.workers[row.id] = row
        self._hydrate_worker(row)
        return row

    def update_worker(self, row: SubcontractorWorker) -> SubcontractorWorker:
        row.updated_at = datetime.now(UTC)
        self.workers[row.id] = row
        self._hydrate_worker(row)
        return row

    def find_worker_by_number(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorker | None:
        for row in self.workers.values():
            if (
                row.tenant_id == tenant_id
                and row.subcontractor_id == subcontractor_id
                and row.worker_no.lower() == worker_no.strip().lower()
                and row.id != exclude_id
            ):
                return row
        return None

    def list_worker_qualifications(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> list[SubcontractorWorkerQualification]:
        rows = [
            row
            for row in self.worker_qualifications.values()
            if row.tenant_id == tenant_id and row.worker_id == worker_id and self.workers[row.worker_id].subcontractor_id == subcontractor_id
        ]
        rows.sort(key=lambda row: (row.valid_until or date.max, row.created_at))
        for row in rows:
            row.qualification_type = self.qualification_types.get(row.qualification_type_id)
        return rows

    def get_worker_qualification(self, tenant_id: str, subcontractor_id: str, worker_id: str, qualification_id: str) -> SubcontractorWorkerQualification | None:
        row = self.worker_qualifications.get(qualification_id)
        if row is None or row.tenant_id != tenant_id or row.worker_id != worker_id:
            return None
        worker = self.workers.get(worker_id)
        if worker is None or worker.subcontractor_id != subcontractor_id:
            return None
        row.qualification_type = self.qualification_types.get(row.qualification_type_id)
        return row

    def create_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification:
        self._stamp(row)
        self.worker_qualifications[row.id] = row
        row.qualification_type = self.qualification_types.get(row.qualification_type_id)
        return row

    def update_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification:
        row.updated_at = datetime.now(UTC)
        self.worker_qualifications[row.id] = row
        row.qualification_type = self.qualification_types.get(row.qualification_type_id)
        return row

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        row = self.qualification_types.get(qualification_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]:
        rows = [
            row
            for row in self.qualification_types.values()
            if row.tenant_id == tenant_id and row.is_active and row.status == "active" and row.archived_at is None
        ]
        rows.sort(key=lambda row: (row.label, row.code))
        return rows

    def list_worker_credentials(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> list[SubcontractorWorkerCredential]:
        rows = [
            row
            for row in self.worker_credentials.values()
            if row.tenant_id == tenant_id and row.worker_id == worker_id and self.workers[row.worker_id].subcontractor_id == subcontractor_id
        ]
        rows.sort(key=lambda row: (row.valid_from, row.created_at))
        return rows

    def get_worker_credential(self, tenant_id: str, subcontractor_id: str, worker_id: str, credential_id: str) -> SubcontractorWorkerCredential | None:
        row = self.worker_credentials.get(credential_id)
        if row is None or row.tenant_id != tenant_id or row.worker_id != worker_id:
            return None
        worker = self.workers.get(worker_id)
        if worker is None or worker.subcontractor_id != subcontractor_id:
            return None
        return row

    def create_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential:
        self._stamp(row)
        self.worker_credentials[row.id] = row
        return row

    def update_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential:
        row.updated_at = datetime.now(UTC)
        self.worker_credentials[row.id] = row
        return row

    def find_worker_credential_by_no(self, tenant_id: str, credential_no: str, *, exclude_id: str | None = None) -> SubcontractorWorkerCredential | None:
        for row in self.worker_credentials.values():
            if row.tenant_id == tenant_id and row.credential_no == credential_no and row.id != exclude_id:
                return row
        return None

    def find_worker_credential_by_encoded_value(self, tenant_id: str, encoded_value: str, *, exclude_id: str | None = None) -> SubcontractorWorkerCredential | None:
        for row in self.worker_credentials.values():
            if row.tenant_id == tenant_id and row.encoded_value == encoded_value and row.id != exclude_id:
                return row
        return None

    def _hydrate_worker(self, row: SubcontractorWorker) -> None:
        row.qualifications = self.list_worker_qualifications(row.tenant_id, row.subcontractor_id, row.id)
        row.credentials = self.list_worker_credentials(row.tenant_id, row.subcontractor_id, row.id)


@dataclass
class FakeWorkforceDocumentService:
    document_repository: FakeHistoryDocumentRepository

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document = Document(
            id=str(uuid4()),
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
            current_version_no=0,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
            metadata_json=payload.metadata_json,
        )
        document.document_type = DocumentType(
            id="doc-type-1",
            key="attachment",
            name="Attachment",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
            is_system_type=True,
        )
        document.versions = []
        document.links = []
        self.document_repository.documents_by_owner.setdefault((tenant_id, "__unlinked__", "__unlinked__"), []).append(document)
        return document

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = self._require_document(tenant_id, document_id)
        version_no = len(document.versions) + 1
        version = DocumentVersion(
            id=str(uuid4()),
            tenant_id=tenant_id,
            document_id=document_id,
            version_no=version_no,
            file_name=payload.file_name,
            content_type=payload.content_type,
            object_bucket="local",
            object_key=f"{document_id}/{version_no}",
            checksum_sha256="abc",
            file_size_bytes=len(payload.content_base64),
            uploaded_by_user_id=actor.user_id,
            metadata_json=payload.metadata_json,
            is_revision_safe_pdf=False,
        )
        document.current_version_no = version_no
        document.versions.append(version)
        return version

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = self._require_document(tenant_id, document_id)
        link = DocumentLink(
            id=str(uuid4()),
            tenant_id=tenant_id,
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            relation_type=payload.relation_type,
            label=payload.label,
            linked_by_user_id=actor.user_id,
            metadata_json=payload.metadata_json,
        )
        document.links.append(link)
        key = (tenant_id, payload.owner_type, payload.owner_id)
        self.document_repository.documents_by_owner.setdefault(key, [])
        if not any(existing.id == document.id for existing in self.document_repository.documents_by_owner[key]):
            self.document_repository.documents_by_owner[key].append(document)
        return link

    def _require_document(self, tenant_id: str, document_id: str) -> Document:
        for rows in self.document_repository.documents_by_owner.values():
            for document in rows:
                if document.id == document_id and document.tenant_id == tenant_id:
                    return document
        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            title=f"Dokument {document_id}",
            source_module="subcontractors",
            source_label="worker-proof",
            current_version_no=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        document.document_type = DocumentType(
            id="doc-type-1",
            key="attachment",
            name="Attachment",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
            is_system_type=True,
        )
        document.versions = []
        document.links = []
        self.document_repository.documents_by_owner.setdefault((tenant_id, "__unlinked__", "__unlinked__"), []).append(document)
        return document


class SubcontractorWorkforceServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorWorkforceRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeHistoryDocumentRepository()
        self.master_service = SubcontractorService(
            self.repository,
            audit_service=AuditService(self.audit_repository),
        )
        self.service = SubcontractorWorkforceService(
            self.repository,
            document_repository=self.document_repository,
            document_service=FakeWorkforceDocumentService(self.document_repository),
            audit_service=AuditService(self.audit_repository),
        )
        self.subcontractor = self.master_service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )

    def test_create_and_update_worker_inside_owning_subcontractor(self) -> None:
        worker = self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
                email="erika@example.com",
            ),
            _context("subcontractors.company.write"),
        )
        updated = self.service.update_worker(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            SubcontractorWorkerUpdate(preferred_name="Eri", version_no=worker.version_no),
            _context("subcontractors.company.write"),
        )

        self.assertEqual(updated.preferred_name, "Eri")
        self.assertEqual(updated.worker_no, "W-100")

    def test_duplicate_worker_number_is_rejected_per_subcontractor(self) -> None:
        self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as raised:
            self.service.create_worker(
                "tenant-1",
                self.subcontractor.id,
                SubcontractorWorkerCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=self.subcontractor.id,
                    worker_no="W-100",
                    first_name="Max",
                    last_name="Muster",
                ),
                _context("subcontractors.company.write"),
            )

        self.assertEqual(raised.exception.message_key, "errors.subcontractors.worker.duplicate_number")

    def test_qualification_default_validity_and_expiry_rules_are_enforced(self) -> None:
        worker = self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )
        qualification = self.service.create_worker_qualification(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            SubcontractorWorkerQualificationCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_id=worker.id,
                qualification_type_id="qual-expiring",
                issued_at=date(2026, 1, 1),
            ),
            _context("subcontractors.company.write"),
        )

        self.assertEqual(qualification.valid_until, date(2027, 1, 1))

        with self.assertRaises(ApiException) as invalid_window:
            self.service.update_worker_qualification(
                "tenant-1",
                self.subcontractor.id,
                worker.id,
                qualification.id,
                SubcontractorWorkerQualificationUpdate(
                    issued_at=date(2026, 5, 1),
                    valid_until=date(2026, 4, 1),
                    version_no=qualification.version_no,
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(invalid_window.exception.message_key, "errors.subcontractors.worker_qualification.invalid_window")

    def test_qualification_proofs_use_docs_backbone(self) -> None:
        worker = self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )
        qualification = self.service.create_worker_qualification(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            SubcontractorWorkerQualificationCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_id=worker.id,
                qualification_type_id="qual-open",
                issued_at=date(2026, 1, 1),
            ),
            _context("subcontractors.company.write"),
        )

        uploaded = self.service.upload_worker_qualification_proof(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            qualification.id,
            SubcontractorWorkerQualificationProofUpload(
                title="Nachweis PDF",
                file_name="nachweis.pdf",
                content_type="application/pdf",
                content_base64="cGRm",
            ),
            _context("subcontractors.company.write"),
        )
        linked = self.service.link_existing_worker_qualification_proof(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            qualification.id,
            SubcontractorWorkerQualificationProofLinkCreate(document_id="doc-existing", label="Altbestand"),
            _context("subcontractors.company.write"),
        )

        self.assertEqual(uploaded.relation_type, "proof_document")
        owner_docs = self.document_repository.list_documents_for_owner(
            "tenant-1",
            "partner.subcontractor_worker_qualification",
            qualification.id,
        )
        self.assertEqual(len(owner_docs), 2)
        self.assertEqual(linked.document_id, "doc-existing")

    def test_credentials_enforce_uniqueness_and_validity_rules(self) -> None:
        worker = self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )
        credential = self.service.create_worker_credential(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            SubcontractorWorkerCredentialCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_id=worker.id,
                credential_no="ID-100",
                credential_type="work_badge",
                encoded_value="qr:100",
                valid_from=date(2026, 1, 1),
            ),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as duplicate:
            self.service.create_worker_credential(
                "tenant-1",
                self.subcontractor.id,
                worker.id,
                SubcontractorWorkerCredentialCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=self.subcontractor.id,
                    worker_id=worker.id,
                    credential_no="ID-100",
                    credential_type="work_badge",
                    encoded_value="qr:101",
                    valid_from=date(2026, 1, 1),
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(duplicate.exception.message_key, "errors.subcontractors.worker_credential.duplicate_no")

        updated = self.service.update_worker_credential(
            "tenant-1",
            self.subcontractor.id,
            worker.id,
            credential.id,
            SubcontractorWorkerCredentialUpdate(
                status="issued",
                valid_until=date(2026, 12, 31),
                version_no=credential.version_no,
            ),
            _context("subcontractors.company.write"),
        )
        self.assertEqual(updated.status, "issued")
        self.assertIsNotNone(updated.issued_at)

    def test_cross_subcontractor_worker_access_is_denied(self) -> None:
        worker = self.service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )
        other = self.master_service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1002", legal_name="Andere GmbH"),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as raised:
            self.service.get_worker("tenant-1", other.id, worker.id, _context("subcontractors.company.read"))

        self.assertEqual(raised.exception.message_key, "errors.subcontractors.worker.not_found")

    def test_metadata_and_docs_owner_types_expose_expected_partner_worker_constraints(self) -> None:
        worker_table = Base.metadata.tables["partner.subcontractor_worker"]
        qualification_table = Base.metadata.tables["partner.subcontractor_worker_qualification"]
        credential_table = Base.metadata.tables["partner.subcontractor_worker_credential"]

        worker_uniques = {
            tuple(column.name for column in constraint.columns)
            for constraint in worker_table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        qualification_checks = {constraint.name for constraint in qualification_table.constraints if isinstance(constraint, CheckConstraint)}
        credential_checks = {constraint.name for constraint in credential_table.constraints if isinstance(constraint, CheckConstraint)}

        self.assertIn(("tenant_id", "subcontractor_id", "worker_no"), worker_uniques)
        self.assertIn("ck_subcontractor_worker_qualification_partner_worker_qualification_valid_window", qualification_checks)
        self.assertIn("ck_subcontractor_worker_credential_partner_worker_credential_window_valid", credential_checks)
        self.assertIn("partner.subcontractor_worker", SqlAlchemyDocumentRepository.SUPPORTED_OWNER_TYPES)
        self.assertIn("partner.subcontractor_worker_qualification", SqlAlchemyDocumentRepository.SUPPORTED_OWNER_TYPES)


if __name__ == "__main__":
    unittest.main()

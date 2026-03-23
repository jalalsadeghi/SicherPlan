from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from app.modules.employees.models import QualificationType
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentType
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorScope,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.schemas import SubcontractorWorkerReadinessFilter


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeReadinessRepository:
    subcontractors: list[Subcontractor] = field(default_factory=list)
    workers: list[SubcontractorWorker] = field(default_factory=list)

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        return next((row for row in self.subcontractors if row.tenant_id == tenant_id and row.id == subcontractor_id), None)

    def list_workers(self, tenant_id: str, subcontractor_id: str, filters) -> list[SubcontractorWorker]:  # noqa: ANN001
        rows = [row for row in self.workers if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id]
        if filters.search:
            needle = filters.search.lower()
            rows = [row for row in rows if needle in row.worker_no.lower() or needle in row.first_name.lower() or needle in row.last_name.lower()]
        if filters.status:
            rows = [row for row in rows if row.status == filters.status]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None:
        return next(
            (
                row
                for row in self.workers
                if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id and row.id == worker_id
            ),
            None,
        )


@dataclass
class FakeReadinessDocumentRepository:
    documents_by_owner: dict[tuple[str, str, str], list[Document]] = field(default_factory=dict)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        return list(self.documents_by_owner.get((tenant_id, owner_type, owner_id), []))


def _qualification_type(
    qual_id: str,
    *,
    compliance_relevant: bool,
    proof_required: bool,
    expiry_required: bool,
) -> QualificationType:
    return QualificationType(
        id=qual_id,
        tenant_id="tenant-1",
        code=qual_id.upper(),
        label=f"Type {qual_id}",
        category=None,
        description=None,
        is_active=True,
        planning_relevant=True,
        compliance_relevant=compliance_relevant,
        expiry_required=expiry_required,
        default_validity_days=None,
        proof_required=proof_required,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version_no=1,
    )


def _document(document_id: str) -> Document:
    row = Document(
        id=document_id,
        tenant_id="tenant-1",
        title=f"Document {document_id}",
        source_module="subcontractors",
        source_label="test",
        current_version_no=1,
        metadata_json={},
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version_no=1,
    )
    row.document_type = DocumentType(
        id=f"type-{document_id}",
        key="compliance",
        name="Compliance",
        description=None,
        is_system_type=True,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version_no=1,
    )
    return row


class SubcontractorReadinessServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        subcontractor = Subcontractor(
            id="subcontractor-1",
            tenant_id="tenant-1",
            subcontractor_number="SUB-001",
            legal_name="Partner GmbH",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        subcontractor.scopes = [
            SubcontractorScope(
                id="scope-1",
                tenant_id="tenant-1",
                subcontractor_id="subcontractor-1",
                branch_id="branch-1",
                mandate_id=None,
                valid_from=date.today() - timedelta(days=30),
                valid_to=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        qual_blocking = _qualification_type("qual-blocking", compliance_relevant=True, proof_required=True, expiry_required=True)
        qual_warning = _qualification_type("qual-warning", compliance_relevant=False, proof_required=False, expiry_required=False)
        worker_ready = SubcontractorWorker(
            id="worker-ready",
            tenant_id="tenant-1",
            subcontractor_id="subcontractor-1",
            worker_no="WK-100",
            first_name="Erika",
            last_name="Partner",
            preferred_name=None,
            birth_date=None,
            email=None,
            phone=None,
            mobile=None,
            notes=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        worker_ready.qualifications = [
            SubcontractorWorkerQualification(
                id="qual-row-ready",
                tenant_id="tenant-1",
                worker_id="worker-ready",
                qualification_type_id=qual_blocking.id,
                certificate_no=None,
                issued_at=date.today() - timedelta(days=5),
                valid_until=date.today() + timedelta(days=120),
                issuing_authority=None,
                notes=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        worker_ready.qualifications[0].qualification_type = qual_blocking
        worker_ready.credentials = [
            SubcontractorWorkerCredential(
                id="cred-ready",
                tenant_id="tenant-1",
                worker_id="worker-ready",
                credential_no="C-100",
                credential_type="work_badge",
                encoded_value="encoded-100",
                valid_from=date.today() - timedelta(days=10),
                valid_until=date.today() + timedelta(days=200),
                issued_at=datetime.now(UTC),
                revoked_at=None,
                notes=None,
                status="issued",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]

        worker_blocked = SubcontractorWorker(
            id="worker-blocked",
            tenant_id="tenant-1",
            subcontractor_id="subcontractor-1",
            worker_no="WK-200",
            first_name="Nora",
            last_name="Block",
            preferred_name=None,
            birth_date=None,
            email=None,
            phone=None,
            mobile=None,
            notes=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        worker_blocked.qualifications = [
            SubcontractorWorkerQualification(
                id="qual-row-blocked",
                tenant_id="tenant-1",
                worker_id="worker-blocked",
                qualification_type_id=qual_blocking.id,
                certificate_no=None,
                issued_at=date.today() - timedelta(days=90),
                valid_until=date.today() - timedelta(days=1),
                issuing_authority=None,
                notes=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        worker_blocked.qualifications[0].qualification_type = qual_blocking
        worker_blocked.credentials = []

        worker_warning = SubcontractorWorker(
            id="worker-warning",
            tenant_id="tenant-1",
            subcontractor_id="subcontractor-1",
            worker_no="WK-300",
            first_name="Lina",
            last_name="Warn",
            preferred_name=None,
            birth_date=None,
            email=None,
            phone=None,
            mobile=None,
            notes=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        worker_warning.qualifications = [
            SubcontractorWorkerQualification(
                id="qual-row-warning",
                tenant_id="tenant-1",
                worker_id="worker-warning",
                qualification_type_id=qual_warning.id,
                certificate_no=None,
                issued_at=date.today() - timedelta(days=5),
                valid_until=date.today() + timedelta(days=10),
                issuing_authority=None,
                notes=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        worker_warning.qualifications[0].qualification_type = qual_warning
        worker_warning.credentials = []

        self.repository = FakeReadinessRepository(subcontractors=[subcontractor], workers=[worker_ready, worker_blocked, worker_warning])
        self.documents = FakeReadinessDocumentRepository(
            {
                ("tenant-1", "partner.subcontractor_worker_qualification", "qual-row-ready"): [_document("doc-ready")],
            }
        )
        self.service = SubcontractorReadinessService(self.repository, document_repository=self.documents)
        self.context = _context("subcontractors.company.read")

    def test_worker_with_valid_requirements_is_ready(self) -> None:
        result = self.service.get_worker_readiness("tenant-1", "subcontractor-1", "worker-ready", self.context)

        self.assertEqual(result.readiness_status, "ready")
        self.assertEqual(result.blocking_issue_count, 0)
        self.assertEqual(result.warning_issue_count, 0)

    def test_missing_proof_and_expired_compliance_qualification_block_worker(self) -> None:
        result = self.service.get_worker_readiness("tenant-1", "subcontractor-1", "worker-blocked", self.context)

        self.assertEqual(result.readiness_status, "not_ready")
        self.assertGreaterEqual(result.blocking_issue_count, 2)
        issue_codes = {issue.issue_code for issue in result.issues}
        self.assertIn("qualification_expired", issue_codes)
        self.assertIn("qualification_proof_missing", issue_codes)
        self.assertIn("credential_missing", issue_codes)

    def test_warning_only_worker_stays_ready_with_warnings(self) -> None:
        result = self.service.get_worker_readiness("tenant-1", "subcontractor-1", "worker-warning", self.context)

        self.assertEqual(result.readiness_status, "ready_with_warnings")
        self.assertEqual(result.blocking_issue_count, 0)
        self.assertGreaterEqual(result.warning_issue_count, 1)
        self.assertIn("credential_missing", {issue.issue_code for issue in result.issues})

    def test_summary_and_filters_are_consistent(self) -> None:
        summary = self.service.get_subcontractor_readiness_summary("tenant-1", "subcontractor-1", self.context)
        not_ready = self.service.list_worker_readiness(
            "tenant-1",
            "subcontractor-1",
            SubcontractorWorkerReadinessFilter(readiness_status="not_ready"),
            self.context,
        )
        blocking = self.service.list_worker_readiness(
            "tenant-1",
            "subcontractor-1",
            SubcontractorWorkerReadinessFilter(issue_severity="blocking"),
            self.context,
        )

        self.assertEqual(summary.total_workers, 3)
        self.assertEqual(summary.ready_workers, 1)
        self.assertEqual(summary.warning_only_workers, 1)
        self.assertEqual(summary.not_ready_workers, 1)
        self.assertEqual(len(not_ready), 1)
        self.assertEqual(not_ready[0].worker_id, "worker-blocked")
        self.assertEqual(len(blocking), 1)
        self.assertEqual(blocking[0].worker_id, "worker-blocked")


if __name__ == "__main__":
    unittest.main()

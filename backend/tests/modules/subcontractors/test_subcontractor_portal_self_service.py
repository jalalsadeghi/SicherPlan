from __future__ import annotations

import unittest
from datetime import UTC, date, datetime

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.subcontractors.portal_service import SubcontractorPortalService
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorCreate,
    SubcontractorPortalWorkerCreate,
    SubcontractorPortalWorkerQualificationCreate,
    SubcontractorPortalWorkerQualificationUpdate,
    SubcontractorPortalWorkerUpdate,
    SubcontractorWorkerCreate,
    SubcontractorWorkerQualificationProofLinkCreate,
    SubcontractorWorkerQualificationProofUpload,
)
from app.modules.subcontractors.service import SubcontractorService
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService
from tests.modules.subcontractors.test_subcontractor_master import (
    FakeHistoryDocumentRepository,
    RecordingAuditRepository,
)
from tests.modules.subcontractors.test_subcontractor_workforce import (
    FakeSubcontractorWorkforceRepository,
    FakeWorkforceDocumentService,
)


def _internal_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-admin",
        user_id="user-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"subcontractors.company.read", "subcontractors.company.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-admin",
    )


def _portal_actor(subcontractor_id: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-sub",
        user_id="user-portal",
        tenant_id="tenant-1",
        role_keys=frozenset({"subcontractor_user"}),
        permission_keys=frozenset({"portal.subcontractor.access"}),
        scopes=(
            AuthenticatedRoleScope(
                role_key="subcontractor_user",
                scope_type="subcontractor",
                subcontractor_id=subcontractor_id,
            ),
        ),
        request_id="req-portal",
    )


class TestSubcontractorPortalSelfService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorWorkforceRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeHistoryDocumentRepository()
        self.master_service = SubcontractorService(
            self.repository,
            audit_service=AuditService(self.audit_repository),
        )
        self.portal_service = SubcontractorPortalService(self.repository)
        self.workforce_service = SubcontractorWorkforceService(
            self.repository,
            document_repository=self.document_repository,
            document_service=FakeWorkforceDocumentService(self.document_repository),
            audit_service=AuditService(self.audit_repository),
        )
        self.subcontractor = self.master_service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _internal_actor(),
        )
        self.other_subcontractor = self.master_service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1002", legal_name="Andere GmbH"),
            _internal_actor(),
        )
        self.master_service.create_contact(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                full_name="Pat Portal",
                email="portal@example.invalid",
                user_id="user-portal",
                portal_enabled=True,
                is_primary_contact=True,
            ),
            _internal_actor(),
        )
        self.context = self.portal_service.get_context(_portal_actor(self.subcontractor.id))

    def test_portal_user_can_create_and_update_only_own_workers(self) -> None:
        worker = self.workforce_service.create_worker_for_portal(
            self.context,
            SubcontractorPortalWorkerCreate(
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
                email="erika@example.com",
            ),
            _portal_actor(self.subcontractor.id),
        )

        updated = self.workforce_service.update_worker_for_portal(
            self.context,
            worker.id,
            SubcontractorPortalWorkerUpdate(
                preferred_name="Eri",
                mobile="+491234",
                version_no=worker.version_no,
            ),
            _portal_actor(self.subcontractor.id),
        )

        self.assertEqual(updated.preferred_name, "Eri")
        self.assertEqual(updated.mobile, "+491234")
        self.assertEqual(updated.qualifications, [])

    def test_portal_user_cannot_read_or_update_other_subcontractor_worker(self) -> None:
        other_worker = self.workforce_service.create_worker(
            "tenant-1",
            self.other_subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.other_subcontractor.id,
                worker_no="W-200",
                first_name="Fremd",
                last_name="Partner",
            ),
            _internal_actor(),
        )

        with self.assertRaises(ApiException) as raised:
            self.workforce_service.get_worker_for_portal(self.context, other_worker.id)

        self.assertEqual(raised.exception.message_key, "errors.subcontractors.worker.not_found")

    def test_portal_user_can_maintain_qualifications_and_upload_proofs(self) -> None:
        worker = self.workforce_service.create_worker_for_portal(
            self.context,
            SubcontractorPortalWorkerCreate(
                worker_no="W-100",
                first_name="Erika",
                last_name="Partner",
            ),
            _portal_actor(self.subcontractor.id),
        )
        qualification = self.workforce_service.create_worker_qualification_for_portal(
            self.context,
            worker.id,
            SubcontractorPortalWorkerQualificationCreate(
                qualification_type_id="qual-open",
                issued_at=date(2026, 1, 1),
                certificate_no="CERT-1",
            ),
            _portal_actor(self.subcontractor.id),
        )
        updated = self.workforce_service.update_worker_qualification_for_portal(
            self.context,
            worker.id,
            qualification.id,
            SubcontractorPortalWorkerQualificationUpdate(
                issuing_authority="IHK",
                version_no=qualification.version_no,
            ),
            _portal_actor(self.subcontractor.id),
        )
        proof = self.workforce_service.upload_worker_qualification_proof_for_portal(
            self.context,
            worker.id,
            qualification.id,
            SubcontractorWorkerQualificationProofUpload(
                title="Nachweis PDF",
                file_name="nachweis.pdf",
                content_type="application/pdf",
                content_base64="cGRm",
            ),
            _portal_actor(self.subcontractor.id),
        )
        linked = self.workforce_service.link_existing_worker_qualification_proof_for_portal(
            self.context,
            worker.id,
            qualification.id,
            SubcontractorWorkerQualificationProofLinkCreate(document_id="doc-existing", label="Altbestand"),
            _portal_actor(self.subcontractor.id),
        )

        self.assertEqual(updated.issuing_authority, "IHK")
        self.assertEqual(proof.relation_type, "proof_document")
        self.assertEqual(linked.document_id, "doc-existing")
        proofs = self.workforce_service.list_worker_qualification_proofs_for_portal(self.context, worker.id, qualification.id)
        self.assertEqual(len(proofs), 2)

    def test_portal_self_service_exposes_active_qualification_type_options(self) -> None:
        options = self.workforce_service.list_portal_qualification_types(self.context)

        self.assertEqual([item.id for item in options], ["qual-open", "qual-expiring"])
        self.assertTrue(any(item.proof_required for item in options))


if __name__ == "__main__":
    unittest.main()

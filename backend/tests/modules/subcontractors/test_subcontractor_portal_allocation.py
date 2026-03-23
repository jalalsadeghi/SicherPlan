from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.errors import ApiException
from app.modules.subcontractors.portal_allocation_service import (
    AllocationAdapterPreview,
    AllocationAdapterResult,
    SubcontractorPortalAllocationService,
)
from app.modules.subcontractors.portal_read_service import ReleasedPortalPositionRecord
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.schemas import (
    SubcontractorCreate,
    SubcontractorPortalAllocationRequest,
    SubcontractorPortalContextRead,
    SubcontractorPortalContactRead,
    SubcontractorPortalCompanyRead,
    SubcontractorPortalScopeRead,
    SubcontractorWorkerCreate,
    SubcontractorWorkerCredentialCreate,
    SubcontractorWorkerQualificationCreate,
)
from app.modules.subcontractors.service import SubcontractorService
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService
from app.modules.iam.audit_service import AuditService
from tests.modules.subcontractors.test_subcontractor_master import (
    FakeHistoryDocumentRepository,
    RecordingAuditRepository,
    _context,
)
from tests.modules.subcontractors.test_subcontractor_workforce import (
    FakeSubcontractorWorkforceRepository,
    FakeWorkforceDocumentService,
)


@dataclass(slots=True)
class FakeAllocationAdapter:
    position: ReleasedPortalPositionRecord | None

    def get_released_position(
        self,
        context: SubcontractorPortalContextRead,
        position_id: str,
    ) -> ReleasedPortalPositionRecord | None:
        if self.position is None or self.position.id != position_id:
            return None
        return self.position

    def preview_allocation(
        self,
        context: SubcontractorPortalContextRead,
        position: ReleasedPortalPositionRecord,
        payload: SubcontractorPortalAllocationRequest,
    ) -> AllocationAdapterPreview:
        return AllocationAdapterPreview(
            command_status="ready_for_submit",
            can_submit=True,
            validation_scope="planning_adapter",
            issues=[],
        )

    def apply_allocation(
        self,
        context: SubcontractorPortalContextRead,
        position: ReleasedPortalPositionRecord,
        payload: SubcontractorPortalAllocationRequest,
    ) -> AllocationAdapterResult:
        return AllocationAdapterResult(
            command_status="confirmed",
            message_key="portalSubcontractor.feedback.allocationSubmitted",
            confirmed_at=datetime.now(UTC),
            issues=[],
        )


class SubcontractorPortalAllocationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorWorkforceRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeHistoryDocumentRepository()
        self.master_service = SubcontractorService(
            self.repository,
            audit_service=AuditService(self.audit_repository),
        )
        self.workforce_service = SubcontractorWorkforceService(
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
        self.other_subcontractor = self.master_service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1002", legal_name="Andere GmbH"),
            _context("subcontractors.company.write"),
        )
        self.ready_worker = self.workforce_service.create_worker(
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
        self.workforce_service.create_worker_credential(
            "tenant-1",
            self.subcontractor.id,
            self.ready_worker.id,
            SubcontractorWorkerCredentialCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_id=self.ready_worker.id,
                credential_no="ID-100",
                credential_type="work_badge",
                encoded_value="qr:100",
                valid_from=date(2026, 1, 1),
                status="issued",
            ),
            _context("subcontractors.company.write"),
        )
        self.blocked_worker = self.workforce_service.create_worker(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_no="W-101",
                first_name="Max",
                last_name="Nichtbereit",
            ),
            _context("subcontractors.company.write"),
        )
        self.workforce_service.create_worker_qualification(
            "tenant-1",
            self.subcontractor.id,
            self.blocked_worker.id,
            SubcontractorWorkerQualificationCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                worker_id=self.blocked_worker.id,
                qualification_type_id="qual-expiring",
                issued_at=date(2025, 1, 1),
                valid_until=date(2025, 12, 31),
            ),
            _context("subcontractors.company.write"),
        )
        self.other_worker = self.workforce_service.create_worker(
            "tenant-1",
            self.other_subcontractor.id,
            SubcontractorWorkerCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.other_subcontractor.id,
                worker_no="W-200",
                first_name="Fremd",
                last_name="Partner",
            ),
            _context("subcontractors.company.write"),
        )
        self.context = SubcontractorPortalContextRead(
            tenant_id="tenant-1",
            user_id="portal-user-1",
            subcontractor_id=self.subcontractor.id,
            contact_id="contact-1",
            company=SubcontractorPortalCompanyRead(
                id=self.subcontractor.id,
                tenant_id="tenant-1",
                subcontractor_number=self.subcontractor.subcontractor_number,
                legal_name=self.subcontractor.legal_name,
                display_name=self.subcontractor.display_name,
                status=self.subcontractor.status,
            ),
            contact=SubcontractorPortalContactRead(
                id="contact-1",
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                full_name="Portal Kontakt",
                function_label="Disposition",
                email="portal@example.com",
                phone=None,
                mobile=None,
                portal_enabled=True,
                status="active",
            ),
            scopes=[
                SubcontractorPortalScopeRead(
                    role_key="subcontractor_user",
                    scope_type="subcontractor",
                    subcontractor_id=self.subcontractor.id,
                )
            ],
        )

    def test_list_candidates_returns_only_current_subcontractor_workers(self) -> None:
        service = SubcontractorPortalAllocationService(
            self.repository,
            readiness_service=SubcontractorReadinessService(
                self.repository,
                document_repository=self.document_repository,
            ),
        )

        result = service.list_candidates(self.context)

        self.assertEqual([item.worker_id for item in result.items], [self.ready_worker.id, self.blocked_worker.id])

    def test_preview_denies_cross_subcontractor_worker(self) -> None:
        service = SubcontractorPortalAllocationService(
            self.repository,
            readiness_service=SubcontractorReadinessService(
                self.repository,
                document_repository=self.document_repository,
            ),
        )

        with self.assertRaises(ApiException) as raised:
            service.preview(
                self.context,
                SubcontractorPortalAllocationRequest(
                    position_id="released-pos-1",
                    worker_id=self.other_worker.id,
                    action="assign",
                ),
            )

        self.assertEqual(raised.exception.message_key, "errors.subcontractors.worker.not_found")

    def test_preview_without_planning_adapter_reports_blocking_readiness_issues(self) -> None:
        service = SubcontractorPortalAllocationService(
            self.repository,
            readiness_service=SubcontractorReadinessService(
                self.repository,
                document_repository=self.document_repository,
            ),
        )

        preview = service.preview(
            self.context,
            SubcontractorPortalAllocationRequest(
                position_id="released-pos-1",
                worker_id=self.blocked_worker.id,
                action="assign",
            ),
        )

        self.assertEqual(preview.command_status, "blocked_by_validation")
        self.assertFalse(preview.can_submit)
        self.assertEqual(preview.validation_scope, "local_readiness_only")
        self.assertIn("qualification_expired", {issue.issue_code for issue in preview.issues})
        self.assertIn("planning_contract_unavailable", {issue.issue_code for issue in preview.issues})

    def test_submit_without_planning_adapter_returns_explicit_unavailable_result(self) -> None:
        service = SubcontractorPortalAllocationService(
            self.repository,
            readiness_service=SubcontractorReadinessService(
                self.repository,
                document_repository=self.document_repository,
            ),
        )

        result = service.submit(
            self.context,
            SubcontractorPortalAllocationRequest(
                position_id="released-pos-1",
                worker_id=self.ready_worker.id,
                action="assign",
            ),
        )

        self.assertEqual(result.command_status, "planning_contract_unavailable")
        self.assertEqual(
            result.message_key,
            "errors.subcontractors.portal_allocation.planning_contract_unavailable",
        )

    def test_submit_uses_planning_adapter_when_available(self) -> None:
        service = SubcontractorPortalAllocationService(
            self.repository,
            readiness_service=SubcontractorReadinessService(
                self.repository,
                document_repository=self.document_repository,
            ),
            allocation_adapter=FakeAllocationAdapter(
                ReleasedPortalPositionRecord(
                    id="released-pos-1",
                    subcontractor_id=self.subcontractor.id,
                    reference_no="REL-1",
                    title="Nachtbewachung",
                    branch_label="HQ",
                    mandate_label="Objekt 1",
                    work_start=datetime(2026, 3, 20, 20, 0, tzinfo=UTC),
                    work_end=datetime(2026, 3, 21, 6, 0, tzinfo=UTC),
                    location_label="Werkstor",
                    readiness_status="released",
                    confirmation_status="open",
                )
            ),
        )

        result = service.submit(
            self.context,
            SubcontractorPortalAllocationRequest(
                position_id="released-pos-1",
                worker_id=self.ready_worker.id,
                action="assign",
            ),
        )

        self.assertEqual(result.command_status, "confirmed")
        self.assertEqual(result.message_key, "portalSubcontractor.feedback.allocationSubmitted")
        self.assertEqual(result.acted_by_user_id, self.context.user_id)
        self.assertIsNotNone(result.confirmed_at)


if __name__ == "__main__":
    unittest.main()

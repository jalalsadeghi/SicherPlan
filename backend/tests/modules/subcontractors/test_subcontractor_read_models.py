from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from app.modules.employees.models import QualificationType
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.subcontractors.contracts import SubcontractorDownstreamFilter, SubcontractorWorkerDownstreamFilter
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorFinanceProfile,
    SubcontractorScope,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.read_model_service import SubcontractorReadModelService
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.schemas import SubcontractorFilter, SubcontractorWorkerFilter


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


def _qualification_type() -> QualificationType:
    return QualificationType(
        id="qual-type-1",
        tenant_id="tenant-1",
        code="G34",
        label="Sachkunde",
        category=None,
        description=None,
        is_active=True,
        planning_relevant=True,
        compliance_relevant=True,
        expiry_required=True,
        default_validity_days=None,
        proof_required=True,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version_no=1,
    )


@dataclass
class FakeRepo:
    subcontractors: list[Subcontractor] = field(default_factory=list)
    workers: list[SubcontractorWorker] = field(default_factory=list)
    finance_profiles: dict[tuple[str, str], SubcontractorFinanceProfile] = field(default_factory=dict)

    def list_subcontractors(self, tenant_id: str, filters: SubcontractorFilter) -> list[Subcontractor]:
        rows = [row for row in self.subcontractors if row.tenant_id == tenant_id]
        if filters.search:
            needle = filters.search.lower()
            rows = [row for row in rows if needle in row.subcontractor_number.lower() or needle in row.legal_name.lower()]
        if filters.status:
            rows = [row for row in rows if row.status == filters.status]
        return rows

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        return next((row for row in self.subcontractors if row.tenant_id == tenant_id and row.id == subcontractor_id), None)

    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]:
        rows = [row for row in self.workers if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id]
        if filters.search:
            needle = filters.search.lower()
            rows = [row for row in rows if needle in row.worker_no.lower() or needle in row.first_name.lower() or needle in row.last_name.lower()]
        if filters.status:
            rows = [row for row in rows if row.status == filters.status]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None:
        return self.finance_profiles.get((tenant_id, subcontractor_id))

    def find_worker_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None:
        for worker in self.workers:
            for credential in worker.credentials:
                if credential.tenant_id == tenant_id and credential.encoded_value == encoded_value:
                    if exclude_id is not None and credential.id == exclude_id:
                        continue
                    return credential
        return None

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
class FakeDocumentRepo:
    documents_by_owner: dict[tuple[str, str, str], list[object]] = field(default_factory=dict)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list:  # noqa: ANN001
        return list(self.documents_by_owner.get((tenant_id, owner_type, owner_id), []))


class SubcontractorReadModelServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        qualification_type = _qualification_type()
        self.subcontractor = Subcontractor(
            id="sub-1",
            tenant_id="tenant-1",
            subcontractor_number="SUB-001",
            legal_name="Partner GmbH",
            display_name="Partner",
            managing_director_name="M. Partner",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        self.subcontractor.contacts = [
            SubcontractorContact(
                id="contact-1",
                tenant_id="tenant-1",
                subcontractor_id="sub-1",
                full_name="Lea Kontakt",
                title=None,
                function_label="Disposition",
                email="lea@example.com",
                phone=None,
                mobile=None,
                is_primary_contact=True,
                portal_enabled=True,
                user_id=None,
                notes=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        self.subcontractor.scopes = [
            SubcontractorScope(
                id="scope-1",
                tenant_id="tenant-1",
                subcontractor_id="sub-1",
                branch_id="branch-1",
                mandate_id="mandate-1",
                valid_from=date.today() - timedelta(days=10),
                valid_to=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
            )
        ]
        self.worker = SubcontractorWorker(
            id="worker-1",
            tenant_id="tenant-1",
            subcontractor_id="sub-1",
            worker_no="WK-100",
            first_name="Erika",
            last_name="Partner",
            preferred_name=None,
            birth_date=None,
            email="erika@example.com",
            phone=None,
            mobile=None,
            notes=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        self.worker.subcontractor = self.subcontractor
        qualification = SubcontractorWorkerQualification(
            id="qual-1",
            tenant_id="tenant-1",
            worker_id="worker-1",
            qualification_type_id=qualification_type.id,
            certificate_no="CERT-1",
            issued_at=date.today() - timedelta(days=5),
            valid_until=date.today() + timedelta(days=120),
            issuing_authority=None,
            notes=None,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        qualification.qualification_type = qualification_type
        credential = SubcontractorWorkerCredential(
            id="cred-1",
            tenant_id="tenant-1",
            worker_id="worker-1",
            credential_no="CARD-1",
            credential_type="work_badge",
            encoded_value="scan-1",
            valid_from=date.today() - timedelta(days=30),
            valid_until=date.today() + timedelta(days=30),
            issued_at=datetime.now(UTC),
            revoked_at=None,
            notes=None,
            status="issued",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        credential.worker = self.worker
        self.worker.qualifications = [qualification]
        self.worker.credentials = [credential]
        document_repo = FakeDocumentRepo(
            documents_by_owner={
                ("tenant-1", "partner.subcontractor_worker_qualification", "qual-1"): [object()],
            }
        )
        repo = FakeRepo(
            subcontractors=[self.subcontractor],
            workers=[self.worker],
            finance_profiles={
                ("tenant-1", "sub-1"): SubcontractorFinanceProfile(
                    id="finance-1",
                    tenant_id="tenant-1",
                    subcontractor_id="sub-1",
                    invoice_email="rechnung@example.com",
                    payment_terms_days=14,
                    payment_terms_note="14 Tage netto",
                    tax_number="SECRET-TAX",
                    vat_id="SECRET-VAT",
                    bank_account_holder="SECRET HOLDER",
                    bank_iban="SECRET-IBAN",
                    bank_bic="SECRET-BIC",
                    bank_name="SECRET BANK",
                    invoice_delivery_method_lookup_id=None,
                    invoice_status_mode_lookup_id=None,
                    billing_note="Kontrolliert",
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    version_no=1,
                )
            },
        )
        readiness_service = SubcontractorReadinessService(repo, document_repository=document_repo)
        self.service = SubcontractorReadModelService(repo, readiness_service=readiness_service)

    def test_partner_contracts_include_active_scope_contacts_and_summary(self) -> None:
        contracts = self.service.list_partner_contracts("tenant-1", SubcontractorDownstreamFilter(), _context("subcontractors.company.read"))
        self.assertEqual(len(contracts), 1)
        contract = contracts[0]
        self.assertEqual(contract.subcontractor_number, "SUB-001")
        self.assertEqual(len(contract.portal_contacts), 1)
        self.assertEqual(contract.portal_contacts[0].full_name, "Lea Kontakt")
        self.assertEqual(contract.readiness_summary["ready_workers"], 1)

    def test_worker_contracts_filter_ready_only_and_hide_contact_fields(self) -> None:
        rows = self.service.list_worker_contracts(
            "tenant-1",
            "sub-1",
            SubcontractorWorkerDownstreamFilter(ready_only=True),
            _context("subcontractors.company.read"),
        )
        self.assertEqual(len(rows), 1)
        worker = rows[0]
        self.assertEqual(worker.worker_no, "WK-100")
        self.assertEqual(len(worker.qualifications), 1)
        self.assertEqual(len(worker.credentials), 1)
        self.assertFalse(hasattr(worker, "email"))

    def test_finance_summary_omits_bank_and_tax_fields(self) -> None:
        summary = self.service.get_commercial_summary("tenant-1", "sub-1", _context("subcontractors.finance.read"))
        payload = summary.model_dump()
        self.assertEqual(payload["invoice_email"], "rechnung@example.com")
        self.assertNotIn("tax_number", payload)
        self.assertNotIn("bank_iban", payload)
        self.assertEqual(payload["readiness_summary"]["ready_workers"], 1)

    def test_field_credential_resolution_returns_worker_identity_and_readiness(self) -> None:
        resolution = self.service.resolve_field_credential("tenant-1", "scan-1", _context("subcontractors.company.read"))
        assert resolution is not None
        self.assertEqual(resolution.worker_no, "WK-100")
        self.assertEqual(resolution.credential_no, "CARD-1")
        self.assertEqual(resolution.readiness.readiness_status, "ready")

    def test_missing_credential_resolution_is_empty_state(self) -> None:
        resolution = self.service.resolve_field_credential("tenant-1", "does-not-exist", _context("subcontractors.company.read"))
        self.assertIsNone(resolution)


if __name__ == "__main__":
    unittest.main()

"""Read-only subcontractor contracts for downstream modules."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext, enforce_permission
from app.modules.subcontractors.contracts import (
    SubcontractorCommercialSummaryRead,
    SubcontractorCredentialResolutionRead,
    SubcontractorDownstreamFilter,
    SubcontractorPartnerContractRead,
    SubcontractorPortalContactContractRead,
    SubcontractorReadinessIssueContractRead,
    SubcontractorReadinessSummaryContractRead,
    SubcontractorScopeContractRead,
    SubcontractorWorkerContractRead,
    SubcontractorWorkerCredentialContractRead,
    SubcontractorWorkerDownstreamFilter,
    SubcontractorWorkerQualificationContractRead,
)
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorFinanceProfile,
    SubcontractorScope,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.policy import (
    can_read_subcontractor_internal,
    enforce_subcontractor_internal_read_access,
)
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.schemas import SubcontractorFilter, SubcontractorWorkerFilter, SubcontractorWorkerReadinessFilter


class SubcontractorReadModelRepository(Protocol):
    def list_subcontractors(self, tenant_id: str, filters: SubcontractorFilter) -> list[Subcontractor]: ...
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]: ...
    def get_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None: ...
    def find_worker_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None: ...


class SubcontractorReadModelService:
    def __init__(
        self,
        repository: SubcontractorReadModelRepository,
        *,
        readiness_service: SubcontractorReadinessService,
    ) -> None:
        self.repository = repository
        self.readiness_service = readiness_service

    def list_partner_contracts(
        self,
        tenant_id: str,
        filters: SubcontractorDownstreamFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorPartnerContractRead]:
        enforce_permission(actor, "subcontractors.company.read")
        rows = self.repository.list_subcontractors(
            tenant_id,
            SubcontractorFilter(
                search=filters.search,
                branch_id=filters.branch_id,
                mandate_id=filters.mandate_id,
                include_archived=False,
                status="active",
            ),
        )
        contracts: list[SubcontractorPartnerContractRead] = []
        for row in rows:
            if not self._is_active_subcontractor(row):
                continue
            if not can_read_subcontractor_internal(actor, tenant_id=tenant_id, subcontractor=row):
                continue
            summary = self.readiness_service.get_subcontractor_readiness_summary(tenant_id, row.id, actor)
            contracts.append(
                SubcontractorPartnerContractRead(
                    subcontractor_id=row.id,
                    subcontractor_number=row.subcontractor_number,
                    legal_name=row.legal_name,
                    display_name=row.display_name,
                    managing_director_name=row.managing_director_name,
                    status=row.status,
                    scopes=[self._scope_contract(scope) for scope in row.scopes if self._is_active_scope(scope)],
                    portal_contacts=[
                        self._portal_contact_contract(contact)
                        for contact in row.contacts
                        if self._is_active_portal_contact(contact)
                    ],
                    readiness_summary=self._summary_dict(summary),
                )
            )
        return contracts

    def list_worker_contracts(
        self,
        tenant_id: str,
        subcontractor_id: str,
        filters: SubcontractorWorkerDownstreamFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerContractRead]:
        subcontractor = self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        readiness_rows = self.readiness_service.list_worker_readiness(
            tenant_id,
            subcontractor.id,
            SubcontractorWorkerReadinessFilter(
                search=filters.search,
                include_archived=False,
                status="active",
            ),
            actor,
        )
        readiness_by_worker = {row.worker_id: row for row in readiness_rows}
        workers = self.repository.list_workers(
            tenant_id,
            subcontractor.id,
            SubcontractorWorkerFilter(
                search=filters.search,
                include_archived=False,
                status="active",
            ),
        )
        contracts: list[SubcontractorWorkerContractRead] = []
        for worker in workers:
            if not self._is_active_worker(worker):
                continue
            readiness = readiness_by_worker.get(worker.id)
            if readiness is None:
                continue
            if filters.ready_only and readiness.readiness_status != "ready":
                continue
            qualifications = [
                self._qualification_contract(row)
                for row in worker.qualifications
                if self._is_valid_qualification(row)
                and (filters.qualification_type_id is None or row.qualification_type_id == filters.qualification_type_id)
            ]
            credentials = [
                self._credential_contract(row)
                for row in worker.credentials
                if self._is_active_credential(row)
                and (filters.credential_type is None or row.credential_type == filters.credential_type)
            ]
            contracts.append(
                SubcontractorWorkerContractRead(
                    worker_id=worker.id,
                    subcontractor_id=worker.subcontractor_id,
                    worker_no=worker.worker_no,
                    first_name=worker.first_name,
                    last_name=worker.last_name,
                    preferred_name=worker.preferred_name,
                    status=worker.status,
                    qualifications=qualifications,
                    credentials=credentials,
                    readiness=self._readiness_contract(readiness),
                )
            )
        return contracts

    def get_commercial_summary(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorCommercialSummaryRead:
        enforce_permission(actor, "subcontractors.finance.read")
        subcontractor = self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        finance = self.repository.get_finance_profile(tenant_id, subcontractor_id)
        summary = self.readiness_service.get_subcontractor_readiness_summary(tenant_id, subcontractor.id, actor)
        primary_contact = next(
            (row for row in subcontractor.contacts if row.is_primary_contact and self._is_active_contact(row)),
            None,
        )
        return SubcontractorCommercialSummaryRead(
            subcontractor_id=subcontractor.id,
            subcontractor_number=subcontractor.subcontractor_number,
            legal_name=subcontractor.legal_name,
            display_name=subcontractor.display_name,
            invoice_email=finance.invoice_email if finance else None,
            payment_terms_days=finance.payment_terms_days if finance else None,
            payment_terms_note=finance.payment_terms_note if finance else None,
            invoice_delivery_method_lookup_id=finance.invoice_delivery_method_lookup_id if finance else None,
            invoice_delivery_method_code=finance.invoice_delivery_method_lookup.code if finance and finance.invoice_delivery_method_lookup else None,
            invoice_delivery_method_label=finance.invoice_delivery_method_lookup.name if finance and finance.invoice_delivery_method_lookup else None,
            invoice_status_mode_lookup_id=finance.invoice_status_mode_lookup_id if finance else None,
            invoice_status_mode_code=finance.invoice_status_mode_lookup.code if finance and finance.invoice_status_mode_lookup else None,
            invoice_status_mode_label=finance.invoice_status_mode_lookup.name if finance and finance.invoice_status_mode_lookup else None,
            billing_note=finance.billing_note if finance else None,
            primary_contact_name=primary_contact.full_name if primary_contact else None,
            primary_contact_email=primary_contact.email if primary_contact else None,
            readiness_summary=self._summary_dict(summary),
        )

    def resolve_field_credential(
        self,
        tenant_id: str,
        encoded_value: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorCredentialResolutionRead | None:
        enforce_permission(actor, "subcontractors.company.read")
        credential = self.repository.find_worker_credential_by_encoded_value(tenant_id, encoded_value)
        if credential is None:
            return None
        worker = credential.worker
        if worker is None or not self._is_active_worker(worker):
            return None
        subcontractor = worker.subcontractor
        if subcontractor is None or not self._is_active_subcontractor(subcontractor):
            return None
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=subcontractor)
        if not self._is_active_credential(credential):
            return None
        readiness = self.readiness_service.get_worker_readiness(tenant_id, subcontractor.id, worker.id, actor)
        return SubcontractorCredentialResolutionRead(
            subcontractor_id=subcontractor.id,
            subcontractor_number=subcontractor.subcontractor_number,
            legal_name=subcontractor.legal_name,
            worker_id=worker.id,
            worker_no=worker.worker_no,
            first_name=worker.first_name,
            last_name=worker.last_name,
            preferred_name=worker.preferred_name,
            credential_id=credential.id,
            credential_no=credential.credential_no,
            credential_type=credential.credential_type,
            credential_status=credential.status,
            valid_from=credential.valid_from.isoformat(),
            valid_until=credential.valid_until.isoformat() if credential.valid_until else None,
            readiness=self._readiness_contract(readiness),
        )

    def _require_subcontractor_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise ApiException(404, "subcontractors.not_found", "errors.subcontractors.subcontractor.not_found")
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=row)
        return row

    @staticmethod
    def _is_active_subcontractor(row: Subcontractor) -> bool:
        return row.archived_at is None and row.status == "active"

    @staticmethod
    def _is_active_contact(row: SubcontractorContact) -> bool:
        return row.archived_at is None and row.status == "active"

    @classmethod
    def _is_active_portal_contact(cls, row: SubcontractorContact) -> bool:
        return cls._is_active_contact(row) and row.portal_enabled

    @staticmethod
    def _is_active_scope(row: SubcontractorScope, today: date | None = None) -> bool:
        effective_today = today or date.today()
        if row.archived_at is not None or row.status != "active":
            return False
        if row.valid_from > effective_today:
            return False
        if row.valid_to is not None and row.valid_to < effective_today:
            return False
        return True

    @staticmethod
    def _is_active_worker(row: SubcontractorWorker) -> bool:
        return row.archived_at is None and row.status == "active"

    @staticmethod
    def _is_valid_qualification(row: SubcontractorWorkerQualification, today: date | None = None) -> bool:
        effective_today = today or date.today()
        if row.archived_at is not None or row.status != "active":
            return False
        if row.valid_until is not None and row.valid_until < effective_today:
            return False
        return True

    @staticmethod
    def _is_active_credential(row: SubcontractorWorkerCredential, today: date | None = None) -> bool:
        effective_today = today or date.today()
        if row.archived_at is not None:
            return False
        if row.status not in {"active", "issued"}:
            return False
        if row.revoked_at is not None:
            return False
        if row.valid_from > effective_today:
            return False
        if row.valid_until is not None and row.valid_until < effective_today:
            return False
        return True

    @staticmethod
    def _scope_contract(row: SubcontractorScope) -> SubcontractorScopeContractRead:
        return SubcontractorScopeContractRead(
            branch_id=row.branch_id,
            mandate_id=row.mandate_id,
            valid_from=row.valid_from.isoformat(),
            valid_to=row.valid_to.isoformat() if row.valid_to else None,
        )

    @staticmethod
    def _portal_contact_contract(row: SubcontractorContact) -> SubcontractorPortalContactContractRead:
        return SubcontractorPortalContactContractRead(
            contact_id=row.id,
            full_name=row.full_name,
            function_label=row.function_label,
            email=row.email,
            is_primary_contact=row.is_primary_contact,
            portal_enabled=row.portal_enabled,
        )

    @staticmethod
    def _qualification_contract(row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualificationContractRead:
        qualification_type = row.qualification_type
        return SubcontractorWorkerQualificationContractRead(
            qualification_id=row.id,
            qualification_type_id=row.qualification_type_id,
            qualification_type_code=qualification_type.code if qualification_type else None,
            qualification_type_label=qualification_type.label if qualification_type else None,
            valid_until=row.valid_until.isoformat() if row.valid_until else None,
            compliance_relevant=bool(qualification_type.compliance_relevant) if qualification_type else False,
            proof_required=bool(qualification_type.proof_required) if qualification_type else False,
        )

    @staticmethod
    def _credential_contract(row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredentialContractRead:
        return SubcontractorWorkerCredentialContractRead(
            credential_id=row.id,
            credential_no=row.credential_no,
            credential_type=row.credential_type,
            valid_from=row.valid_from.isoformat(),
            valid_until=row.valid_until.isoformat() if row.valid_until else None,
            status=row.status,
        )

    @staticmethod
    def _readiness_contract(row) -> SubcontractorReadinessSummaryContractRead:  # noqa: ANN001
        return SubcontractorReadinessSummaryContractRead(
            readiness_status=row.readiness_status,
            is_ready=row.is_ready,
            blocking_issue_count=row.blocking_issue_count,
            warning_issue_count=row.warning_issue_count,
            missing_proof_count=row.missing_proof_count,
            expired_qualification_count=row.expired_qualification_count,
            expiring_qualification_count=row.expiring_qualification_count,
            missing_credential_count=row.missing_credential_count,
            issues=[
                SubcontractorReadinessIssueContractRead(
                    issue_code=issue.issue_code,
                    message_key=issue.message_key,
                    severity=issue.severity,
                    category=issue.category,
                    reference_type=issue.reference_type,
                    reference_id=issue.reference_id,
                    due_on=issue.due_on,
                )
                for issue in row.issues
            ],
        )

    @staticmethod
    def _summary_dict(summary) -> dict[str, int | str]:  # noqa: ANN001
        return {
            "total_workers": summary.total_workers,
            "ready_workers": summary.ready_workers,
            "warning_only_workers": summary.warning_only_workers,
            "not_ready_workers": summary.not_ready_workers,
            "missing_proof_workers": summary.missing_proof_workers,
            "expired_qualification_workers": summary.expired_qualification_workers,
            "expiring_qualification_workers": summary.expiring_qualification_workers,
            "missing_credential_workers": summary.missing_credential_workers,
            "checked_at": summary.checked_at.isoformat() if hasattr(summary.checked_at, "isoformat") else str(summary.checked_at),
        }

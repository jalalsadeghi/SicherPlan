"""Derived compliance readiness views for subcontractor workers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.platform_services.docs_models import Document
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.policy import enforce_subcontractor_internal_read_access
from app.modules.subcontractors.schemas import (
    SubcontractorWorkforceReadinessSummaryRead,
    SubcontractorWorkerFilter,
    SubcontractorWorkerReadinessFilter,
    SubcontractorWorkerReadinessIssueRead,
    SubcontractorWorkerReadinessListItem,
    SubcontractorWorkerReadinessRead,
)


WARNING_WINDOW_DAYS = 30


class SubcontractorReadinessRepository(Protocol):
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]: ...
    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None: ...


class SubcontractorReadinessDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...


@dataclass(slots=True)
class _DerivedWorkerReadiness:
    worker: SubcontractorWorker
    issues: list[SubcontractorWorkerReadinessIssueRead]
    checked_at: datetime

    @property
    def blocking_issue_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "blocking")

    @property
    def warning_issue_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def readiness_status(self) -> str:
        if self.blocking_issue_count:
            return "not_ready"
        if self.warning_issue_count:
            return "ready_with_warnings"
        return "ready"

    @property
    def missing_proof_count(self) -> int:
        return sum(1 for issue in self.issues if issue.issue_code == "qualification_proof_missing")

    @property
    def expired_qualification_count(self) -> int:
        return sum(1 for issue in self.issues if issue.issue_code == "qualification_expired")

    @property
    def expiring_qualification_count(self) -> int:
        return sum(1 for issue in self.issues if issue.issue_code == "qualification_expiring")

    @property
    def missing_credential_count(self) -> int:
        return sum(1 for issue in self.issues if issue.issue_code == "credential_missing")

    @property
    def qualification_count(self) -> int:
        return sum(1 for row in self.worker.qualifications if row.archived_at is None and row.status != "archived")

    @property
    def credential_count(self) -> int:
        return sum(1 for row in self.worker.credentials if row.archived_at is None and row.status != "archived")

    def to_list_item(self) -> SubcontractorWorkerReadinessListItem:
        return SubcontractorWorkerReadinessListItem(
            worker_id=self.worker.id,
            tenant_id=self.worker.tenant_id,
            subcontractor_id=self.worker.subcontractor_id,
            worker_no=self.worker.worker_no,
            first_name=self.worker.first_name,
            last_name=self.worker.last_name,
            preferred_name=self.worker.preferred_name,
            status=self.worker.status,
            archived_at=self.worker.archived_at,
            readiness_status=self.readiness_status,
            is_ready=self.blocking_issue_count == 0,
            blocking_issue_count=self.blocking_issue_count,
            warning_issue_count=self.warning_issue_count,
            missing_proof_count=self.missing_proof_count,
            expired_qualification_count=self.expired_qualification_count,
            expiring_qualification_count=self.expiring_qualification_count,
            missing_credential_count=self.missing_credential_count,
            issues=self.issues,
        )

    def to_read(self) -> SubcontractorWorkerReadinessRead:
        return SubcontractorWorkerReadinessRead(
            **self.to_list_item().model_dump(),
            qualification_count=self.qualification_count,
            credential_count=self.credential_count,
            checked_at=self.checked_at,
        )


class SubcontractorReadinessService:
    def __init__(
        self,
        repository: SubcontractorReadinessRepository,
        *,
        document_repository: SubcontractorReadinessDocumentRepository,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository

    def list_worker_readiness(
        self,
        tenant_id: str,
        subcontractor_id: str,
        filters: SubcontractorWorkerReadinessFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorWorkerReadinessListItem]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        workers = self.repository.list_workers(
            tenant_id,
            subcontractor_id,
            SubcontractorWorkerFilter(
                search=filters.search,
                status=filters.status,
                include_archived=filters.include_archived,
            ),
        )
        items = [self._evaluate_worker(worker).to_list_item() for worker in workers]
        return self._apply_readiness_filters(items, filters)

    def get_worker_readiness(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerReadinessRead:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        worker = self.repository.get_worker(tenant_id, subcontractor_id, worker_id)
        if worker is None:
            from app.errors import ApiException

            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")
        return self._evaluate_worker(worker).to_read()

    def evaluate_worker_record(self, worker: SubcontractorWorker) -> SubcontractorWorkerReadinessRead:
        return self._evaluate_worker(worker).to_read()

    def get_subcontractor_readiness_summary(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkforceReadinessSummaryRead:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        checked_at = datetime.now(UTC)
        items = [
          self._evaluate_worker(worker).to_list_item()
          for worker in self.repository.list_workers(
              tenant_id,
              subcontractor_id,
              SubcontractorWorkerFilter(include_archived=False),
          )
        ]
        return SubcontractorWorkforceReadinessSummaryRead(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            total_workers=len(items),
            ready_workers=sum(1 for row in items if row.readiness_status == "ready"),
            warning_only_workers=sum(1 for row in items if row.readiness_status == "ready_with_warnings"),
            not_ready_workers=sum(1 for row in items if row.readiness_status == "not_ready"),
            missing_proof_workers=sum(1 for row in items if row.missing_proof_count > 0),
            expired_qualification_workers=sum(1 for row in items if row.expired_qualification_count > 0),
            expiring_qualification_workers=sum(1 for row in items if row.expiring_qualification_count > 0),
            missing_credential_workers=sum(1 for row in items if row.missing_credential_count > 0),
            checked_at=checked_at,
        )

    def _evaluate_worker(self, worker: SubcontractorWorker) -> _DerivedWorkerReadiness:
        checked_at = datetime.now(UTC)
        today = checked_at.date()
        warning_threshold = today + timedelta(days=WARNING_WINDOW_DAYS)
        issues: list[SubcontractorWorkerReadinessIssueRead] = []

        if worker.archived_at is not None or worker.status != "active":
            issues.append(
                SubcontractorWorkerReadinessIssueRead(
                    issue_code="worker_inactive",
                    message_key="sicherplan.subcontractors.workforce.readiness.issue.workerInactive",
                    severity="blocking",
                    category="worker",
                    reference_type="worker",
                    reference_id=worker.id,
                    title=f"{worker.worker_no} ist nicht aktiv",
                )
            )

        active_credentials = [row for row in worker.credentials if row.archived_at is None and row.status != "archived"]
        if not active_credentials:
            issues.append(
                SubcontractorWorkerReadinessIssueRead(
                    issue_code="credential_missing",
                    message_key="sicherplan.subcontractors.workforce.readiness.issue.credentialMissing",
                    severity="warning",
                    category="credential",
                    reference_type="worker",
                    reference_id=worker.id,
                    title="Kein aktiver Ausweis vorhanden",
                )
            )
        else:
            issues.extend(self._credential_issues(active_credentials, today))

        for qualification in worker.qualifications:
            if qualification.archived_at is not None or qualification.status == "archived":
                continue
            qualification_type = qualification.qualification_type
            label = qualification_type.label if qualification_type is not None else qualification.qualification_type_id
            severity_for_validity = "blocking" if qualification_type is not None and qualification_type.compliance_relevant else "warning"
            if qualification.valid_until is not None and qualification.valid_until < today:
                issues.append(
                    SubcontractorWorkerReadinessIssueRead(
                        issue_code="qualification_expired",
                        message_key="sicherplan.subcontractors.workforce.readiness.issue.qualificationExpired",
                        severity=severity_for_validity,
                        category="qualification",
                        reference_type="qualification",
                        reference_id=qualification.id,
                        title=f"{label} ist abgelaufen",
                        due_on=qualification.valid_until,
                    )
                )
            elif qualification.valid_until is not None and qualification.valid_until <= warning_threshold:
                issues.append(
                    SubcontractorWorkerReadinessIssueRead(
                        issue_code="qualification_expiring",
                        message_key="sicherplan.subcontractors.workforce.readiness.issue.qualificationExpiring",
                        severity="warning",
                        category="qualification",
                        reference_type="qualification",
                        reference_id=qualification.id,
                        title=f"{label} laeuft bald ab",
                        due_on=qualification.valid_until,
                    )
                )
            proof_count = len(
                self.document_repository.list_documents_for_owner(
                    worker.tenant_id,
                    "partner.subcontractor_worker_qualification",
                    qualification.id,
                )
            )
            if qualification_type is not None and qualification_type.proof_required and proof_count == 0:
                issues.append(
                    SubcontractorWorkerReadinessIssueRead(
                        issue_code="qualification_proof_missing",
                        message_key="sicherplan.subcontractors.workforce.readiness.issue.qualificationProofMissing",
                        severity="blocking" if qualification_type.compliance_relevant else "warning",
                        category="proof",
                        reference_type="qualification",
                        reference_id=qualification.id,
                        title=f"{label} hat keinen Nachweis",
                        metadata_json={"qualification_type_id": qualification.qualification_type_id},
                    )
                )

        return _DerivedWorkerReadiness(worker=worker, issues=issues, checked_at=checked_at)

    @staticmethod
    def _credential_issues(
        credentials: list[SubcontractorWorkerCredential],
        today: date,
    ) -> list[SubcontractorWorkerReadinessIssueRead]:
        issues: list[SubcontractorWorkerReadinessIssueRead] = []
        has_issued = any(row.status == "issued" and (row.valid_until is None or row.valid_until >= today) for row in credentials)
        if not has_issued:
            issues.append(
                SubcontractorWorkerReadinessIssueRead(
                    issue_code="credential_missing",
                    message_key="sicherplan.subcontractors.workforce.readiness.issue.credentialMissing",
                    severity="warning",
                    category="credential",
                    reference_type="credential",
                    title="Kein gueltiger ausgegebener Ausweis vorhanden",
                )
            )
        for credential in credentials:
            if credential.valid_until is not None and credential.valid_until < today:
                issues.append(
                    SubcontractorWorkerReadinessIssueRead(
                        issue_code="credential_expired",
                        message_key="sicherplan.subcontractors.workforce.readiness.issue.credentialExpired",
                        severity="warning",
                        category="credential",
                        reference_type="credential",
                        reference_id=credential.id,
                        title=f"Ausweis {credential.credential_no} ist abgelaufen",
                        due_on=credential.valid_until,
                    )
                )
            elif credential.status in {"revoked", "expired"}:
                issues.append(
                    SubcontractorWorkerReadinessIssueRead(
                        issue_code="credential_inactive",
                        message_key="sicherplan.subcontractors.workforce.readiness.issue.credentialInactive",
                        severity="warning",
                        category="credential",
                        reference_type="credential",
                        reference_id=credential.id,
                        title=f"Ausweis {credential.credential_no} ist nicht aktiv",
                    )
                )
        return issues

    @staticmethod
    def _apply_readiness_filters(
        items: list[SubcontractorWorkerReadinessListItem],
        filters: SubcontractorWorkerReadinessFilter,
    ) -> list[SubcontractorWorkerReadinessListItem]:
        rows = items
        if filters.readiness_status:
            rows = [row for row in rows if row.readiness_status == filters.readiness_status]
        if filters.issue_severity:
            rows = [row for row in rows if any(issue.severity == filters.issue_severity for issue in row.issues)]
        return rows

    def _require_subcontractor_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            from app.errors import ApiException

            raise ApiException(404, "subcontractors.subcontractor.not_found", "errors.subcontractors.subcontractor.not_found")
        enforce_scope(actor, scope="tenant", tenant_id=tenant_id)
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=row)
        return row

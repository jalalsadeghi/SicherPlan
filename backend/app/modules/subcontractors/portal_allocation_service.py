"""Portal allocation seam for subcontractor self-allocation against released work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.subcontractors.portal_read_service import ReleasedPortalPositionRecord
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.schemas import (
    SubcontractorPortalAllocationCandidateCollectionRead,
    SubcontractorPortalAllocationCandidateRead,
    SubcontractorPortalAllocationPreviewRead,
    SubcontractorPortalAllocationRequest,
    SubcontractorPortalAllocationResultRead,
    SubcontractorPortalContextRead,
    SubcontractorWorkerFilter,
    SubcontractorWorkerReadinessIssueRead,
)


class SubcontractorPortalAllocationRepository(Protocol):
    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter): ...  # noqa: ANN001
    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str): ...  # noqa: ANN001


@dataclass(frozen=True, slots=True)
class AllocationAdapterPreview:
    command_status: str
    can_submit: bool
    validation_scope: str
    issues: list[SubcontractorWorkerReadinessIssueRead]


@dataclass(frozen=True, slots=True)
class AllocationAdapterResult:
    command_status: str
    message_key: str
    confirmed_at: datetime | None
    issues: list[SubcontractorWorkerReadinessIssueRead]


class PortalAllocationAdapter(Protocol):
    def get_released_position(
        self,
        context: SubcontractorPortalContextRead,
        position_id: str,
    ) -> ReleasedPortalPositionRecord | None: ...

    def preview_allocation(
        self,
        context: SubcontractorPortalContextRead,
        position: ReleasedPortalPositionRecord,
        payload: SubcontractorPortalAllocationRequest,
    ) -> AllocationAdapterPreview: ...

    def apply_allocation(
        self,
        context: SubcontractorPortalContextRead,
        position: ReleasedPortalPositionRecord,
        payload: SubcontractorPortalAllocationRequest,
    ) -> AllocationAdapterResult: ...


class SubcontractorPortalAllocationService:
    def __init__(
        self,
        repository: SubcontractorPortalAllocationRepository,
        *,
        readiness_service: SubcontractorReadinessService,
        allocation_adapter: PortalAllocationAdapter | None = None,
    ) -> None:
        self.repository = repository
        self.readiness_service = readiness_service
        self.allocation_adapter = allocation_adapter

    def list_candidates(
        self,
        context: SubcontractorPortalContextRead,
    ) -> SubcontractorPortalAllocationCandidateCollectionRead:
        workers = self.repository.list_workers(
            context.tenant_id,
            context.subcontractor_id,
            SubcontractorWorkerFilter(include_archived=False, status="active"),
        )
        items = []
        for worker in workers:
            readiness = self.readiness_service.evaluate_worker_record(worker)
            items.append(
                SubcontractorPortalAllocationCandidateRead(
                    worker_id=worker.id,
                    worker_no=worker.worker_no,
                    display_name=" ".join(part for part in [worker.preferred_name, worker.first_name, worker.last_name] if part),
                    readiness_status=readiness.readiness_status,
                    is_ready=readiness.is_ready,
                    blocking_issue_count=readiness.blocking_issue_count,
                    warning_issue_count=readiness.warning_issue_count,
                    issues=readiness.issues,
                )
            )
        return SubcontractorPortalAllocationCandidateCollectionRead(
            subcontractor_id=context.subcontractor_id,
            items=items,
        )

    def preview(
        self,
        context: SubcontractorPortalContextRead,
        payload: SubcontractorPortalAllocationRequest,
    ) -> SubcontractorPortalAllocationPreviewRead:
        worker = self.repository.get_worker(context.tenant_id, context.subcontractor_id, payload.worker_id)
        if worker is None:
            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")

        readiness = self.readiness_service.evaluate_worker_record(worker)
        issues = list(readiness.issues)

        if self.allocation_adapter is None:
            issues.append(self._planning_unavailable_issue(payload.position_id))
            command_status = "blocked_by_validation" if readiness.blocking_issue_count else "planning_contract_unavailable"
            return SubcontractorPortalAllocationPreviewRead(
                subcontractor_id=context.subcontractor_id,
                position_id=payload.position_id,
                worker_id=payload.worker_id,
                action=payload.action,
                command_status=command_status,
                validation_scope="local_readiness_only",
                can_submit=False,
                issues=issues,
            )

        position = self.allocation_adapter.get_released_position(context, payload.position_id)
        if position is None or position.subcontractor_id != context.subcontractor_id:
            raise ApiException(
                404,
                "subcontractors.portal_allocation.position_not_found",
                "errors.subcontractors.portal_allocation.position_not_found",
            )

        adapter_preview = self.allocation_adapter.preview_allocation(context, position, payload)
        all_issues = [*issues, *adapter_preview.issues]
        can_submit = adapter_preview.can_submit and readiness.blocking_issue_count == 0
        command_status = adapter_preview.command_status if can_submit else "blocked_by_validation"
        return SubcontractorPortalAllocationPreviewRead(
            subcontractor_id=context.subcontractor_id,
            position_id=payload.position_id,
            worker_id=payload.worker_id,
            action=payload.action,
            command_status=command_status,
            validation_scope=adapter_preview.validation_scope,
            can_submit=can_submit,
            issues=all_issues,
        )

    def submit(
        self,
        context: SubcontractorPortalContextRead,
        payload: SubcontractorPortalAllocationRequest,
    ) -> SubcontractorPortalAllocationResultRead:
        preview = self.preview(context, payload)
        if self.allocation_adapter is None and preview.command_status == "blocked_by_validation":
            return SubcontractorPortalAllocationResultRead(
                subcontractor_id=context.subcontractor_id,
                position_id=payload.position_id,
                worker_id=payload.worker_id,
                action=payload.action,
                command_status="blocked_by_validation",
                message_key="errors.subcontractors.portal_allocation.blocked_by_validation",
                acted_by_user_id=context.user_id,
                issues=preview.issues,
            )
        if self.allocation_adapter is None:
            return SubcontractorPortalAllocationResultRead(
                subcontractor_id=context.subcontractor_id,
                position_id=payload.position_id,
                worker_id=payload.worker_id,
                action=payload.action,
                command_status="planning_contract_unavailable",
                message_key="errors.subcontractors.portal_allocation.planning_contract_unavailable",
                acted_by_user_id=context.user_id,
                issues=preview.issues,
            )
        if not preview.can_submit:
            return SubcontractorPortalAllocationResultRead(
                subcontractor_id=context.subcontractor_id,
                position_id=payload.position_id,
                worker_id=payload.worker_id,
                action=payload.action,
                command_status="blocked_by_validation",
                message_key="errors.subcontractors.portal_allocation.blocked_by_validation",
                acted_by_user_id=context.user_id,
                issues=preview.issues,
            )

        position = self.allocation_adapter.get_released_position(context, payload.position_id)
        if position is None:
            raise ApiException(
                404,
                "subcontractors.portal_allocation.position_not_found",
                "errors.subcontractors.portal_allocation.position_not_found",
            )
        result = self.allocation_adapter.apply_allocation(context, position, payload)
        return SubcontractorPortalAllocationResultRead(
            subcontractor_id=context.subcontractor_id,
            position_id=payload.position_id,
            worker_id=payload.worker_id,
            action=payload.action,
            command_status=result.command_status,
            message_key=result.message_key,
            acted_by_user_id=context.user_id,
            confirmed_at=result.confirmed_at,
            issues=result.issues,
        )

    @staticmethod
    def _planning_unavailable_issue(position_id: str) -> SubcontractorWorkerReadinessIssueRead:
        return SubcontractorWorkerReadinessIssueRead(
            issue_code="planning_contract_unavailable",
            message_key="errors.subcontractors.portal_allocation.planning_contract_unavailable",
            severity="blocking",
            category="planning",
            reference_type="position",
            reference_id=position_id,
            title="Planungsfreigabe fuer Selbstdisposition ist noch nicht angebunden",
        )

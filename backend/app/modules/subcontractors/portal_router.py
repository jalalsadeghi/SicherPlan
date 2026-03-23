"""Subcontractor-portal API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.finance.subcontractor_check_repository import SqlAlchemySubcontractorInvoiceCheckRepository
from app.modules.finance.subcontractor_check_schemas import SubcontractorPortalInvoiceCheckDetailRead
from app.modules.finance.subcontractor_check_service import SubcontractorInvoiceCheckService
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context
from app.modules.field_execution.repository import SqlAlchemyWatchbookRepository
from app.modules.field_execution.schemas import WatchbookEntryCreate, WatchbookEntryRead
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.repository import SqlAlchemyPlanningRepository
from app.modules.subcontractors.portal_allocation_service import SubcontractorPortalAllocationService
from app.modules.subcontractors.portal_read_service import ReleasedPortalInvoiceCheckRecord, SubcontractorPortalReadService
from app.modules.subcontractors.portal_service import SubcontractorPortalService
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.repository import SqlAlchemySubcontractorRepository
from app.modules.subcontractors.schemas import (
    SubcontractorPortalAllocationCandidateCollectionRead,
    SubcontractorPortalAllocationPreviewRead,
    SubcontractorPortalAllocationRequest,
    SubcontractorPortalAllocationResultRead,
    SubcontractorPortalActualSummaryCollectionRead,
    SubcontractorPortalAttendanceCollectionRead,
    SubcontractorPortalCollectionSourceRead,
    SubcontractorPortalContextRead,
    SubcontractorPortalInvoiceCheckCollectionRead,
    SubcontractorPortalPositionCollectionRead,
    SubcontractorPortalQualificationTypeOptionRead,
    SubcontractorPortalScheduleCollectionRead,
    SubcontractorPortalWatchbookCollectionRead,
    SubcontractorPortalWorkerCreate,
    SubcontractorPortalWorkerQualificationCreate,
    SubcontractorPortalWorkerQualificationUpdate,
    SubcontractorPortalWorkerRead,
    SubcontractorPortalWorkerUpdate,
    SubcontractorWorkerFilter,
    SubcontractorWorkerListItem,
    SubcontractorWorkerQualificationProofLinkCreate,
    SubcontractorWorkerQualificationProofRead,
    SubcontractorWorkerQualificationProofUpload,
    SubcontractorWorkerQualificationRead,
)
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.config import settings


router = APIRouter(prefix="/api/portal/subcontractor", tags=["subcontractor_portal"])


def get_subcontractor_portal_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorPortalService:
    return SubcontractorPortalService(SqlAlchemySubcontractorRepository(session))


def get_subcontractor_portal_read_service(
    invoice_check_service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_portal_invoice_check_service)],
) -> SubcontractorPortalReadService:
    return SubcontractorPortalReadService(invoice_check_adapter=_PortalInvoiceCheckAdapter(invoice_check_service))


def get_subcontractor_portal_invoice_check_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorInvoiceCheckService:
    return SubcontractorInvoiceCheckService(SqlAlchemySubcontractorInvoiceCheckRepository(session))


class _PortalInvoiceCheckAdapter:
    def __init__(self, service: SubcontractorInvoiceCheckService) -> None:
        self.service = service

    def list_invoice_checks(self, context: SubcontractorPortalContextRead) -> list[ReleasedPortalInvoiceCheckRecord]:
        return [
            ReleasedPortalInvoiceCheckRecord(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                period_label=row.period_label,
                status=row.status,
                submitted_invoice_ref=row.submitted_invoice_ref,
                approved_minutes=row.approved_minutes,
                approved_amount=row.approved_amount,
                submitted_invoice_amount=row.submitted_invoice_amount,
                last_checked_at=row.last_checked_at,
                variance_amount=row.variance_amount,
            )
            for row in self.service.list_portal_invoice_checks(context.tenant_id, context.subcontractor_id)
        ]


def get_subcontractor_released_schedule_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReleasedScheduleService:
    return ReleasedScheduleService(SqlAlchemyPlanningRepository(session))


def get_subcontractor_portal_allocation_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorPortalAllocationService:
    repository = SqlAlchemySubcontractorRepository(session)
    return SubcontractorPortalAllocationService(
        repository,
        readiness_service=SubcontractorReadinessService(
            repository,
            document_repository=SqlAlchemyDocumentRepository(session),
        ),
    )


def get_subcontractor_portal_workforce_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorWorkforceService:
    repository = SqlAlchemySubcontractorRepository(session)
    return SubcontractorWorkforceService(
        repository,
        document_repository=SqlAlchemyDocumentRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_subcontractor_watchbook_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> WatchbookService:
    return WatchbookService(
        repository=SqlAlchemyWatchbookRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("/context", response_model=SubcontractorPortalContextRead)
def get_subcontractor_portal_context(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
) -> SubcontractorPortalContextRead:
    return service.get_context(actor)


@router.get("/positions", response_model=SubcontractorPortalPositionCollectionRead)
def list_subcontractor_portal_positions(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    read_service: Annotated[SubcontractorPortalReadService, Depends(get_subcontractor_portal_read_service)],
) -> SubcontractorPortalPositionCollectionRead:
    return read_service.list_positions(context_service.get_context(actor))


@router.get("/schedules", response_model=SubcontractorPortalScheduleCollectionRead)
def list_subcontractor_portal_schedules(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    released_schedule_service: Annotated[ReleasedScheduleService, Depends(get_subcontractor_released_schedule_service)],
) -> SubcontractorPortalScheduleCollectionRead:
    return released_schedule_service.list_subcontractor_schedules(context_service.get_context(actor))


@router.get("/watchbooks", response_model=SubcontractorPortalWatchbookCollectionRead)
def list_subcontractor_portal_watchbooks(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    watchbook_service: Annotated[WatchbookService, Depends(get_subcontractor_watchbook_service)],
) -> SubcontractorPortalWatchbookCollectionRead:
    context = context_service.get_context(actor)
    items = [
        {
            "id": row.id,
            "subcontractor_id": row.subcontractor_id,
            "log_date": row.log_date,
            "occurred_at": row.entries[-1].occurred_at if row.entries else row.reviewed_at,
            "entry_type_code": row.entries[-1].entry_type_code if row.entries else "remark",
            "summary": row.entries[-1].summary if row.entries else (row.summary or row.headline or row.context_type),
            "status": row.closure_state_code,
            "pdf_document_id": row.pdf_document.document_id if row.pdf_document is not None else None,
        }
        for row in watchbook_service.list_subcontractor_released_watchbooks(context)
    ]
    return SubcontractorPortalWatchbookCollectionRead(
        subcontractor_id=context.subcontractor_id,
        source=SubcontractorPortalCollectionSourceRead(
            domain_key="watchbooks",
            source_module_key="field_execution",
            availability_status="ready",
            released_only=True,
            subcontractor_scoped=True,
            docs_backed_outputs=True,
            message_key="portalSubcontractor.datasets.watchbooks.pending",
        ),
        items=items,
    )


@router.post("/watchbooks/{watchbook_id}/entries", response_model=WatchbookEntryRead)
def create_subcontractor_portal_watchbook_entry(
    watchbook_id: str,
    payload: WatchbookEntryCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    watchbook_service: Annotated[WatchbookService, Depends(get_subcontractor_watchbook_service)],
) -> WatchbookEntryRead:
    return watchbook_service.add_subcontractor_portal_entry(context_service.get_context(actor), watchbook_id, payload, actor)


@router.get("/actuals", response_model=SubcontractorPortalActualSummaryCollectionRead)
def list_subcontractor_portal_actuals(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    read_service: Annotated[SubcontractorPortalReadService, Depends(get_subcontractor_portal_read_service)],
) -> SubcontractorPortalActualSummaryCollectionRead:
    return read_service.list_actual_summaries(context_service.get_context(actor))


@router.get("/attendance", response_model=SubcontractorPortalAttendanceCollectionRead)
def list_subcontractor_portal_attendance(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    read_service: Annotated[SubcontractorPortalReadService, Depends(get_subcontractor_portal_read_service)],
) -> SubcontractorPortalAttendanceCollectionRead:
    return read_service.list_attendance_visibility(context_service.get_context(actor))


@router.get("/invoice-checks", response_model=SubcontractorPortalInvoiceCheckCollectionRead)
def list_subcontractor_portal_invoice_checks(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    read_service: Annotated[SubcontractorPortalReadService, Depends(get_subcontractor_portal_read_service)],
) -> SubcontractorPortalInvoiceCheckCollectionRead:
    return read_service.list_invoice_checks(context_service.get_context(actor))


@router.get("/invoice-checks/{invoice_check_id}", response_model=SubcontractorPortalInvoiceCheckDetailRead)
def get_subcontractor_portal_invoice_check_detail(
    invoice_check_id: str,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_portal_invoice_check_service)],
) -> SubcontractorPortalInvoiceCheckDetailRead:
    context = context_service.get_context(actor)
    return service.get_portal_invoice_check_detail(context.tenant_id, context.subcontractor_id, invoice_check_id)


@router.get("/allocation/candidates", response_model=SubcontractorPortalAllocationCandidateCollectionRead)
def list_subcontractor_portal_allocation_candidates(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    allocation_service: Annotated[
        SubcontractorPortalAllocationService,
        Depends(get_subcontractor_portal_allocation_service),
    ],
) -> SubcontractorPortalAllocationCandidateCollectionRead:
    return allocation_service.list_candidates(context_service.get_context(actor))


@router.post("/allocation/preview", response_model=SubcontractorPortalAllocationPreviewRead)
def preview_subcontractor_portal_allocation(
    payload: SubcontractorPortalAllocationRequest,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    allocation_service: Annotated[
        SubcontractorPortalAllocationService,
        Depends(get_subcontractor_portal_allocation_service),
    ],
) -> SubcontractorPortalAllocationPreviewRead:
    return allocation_service.preview(context_service.get_context(actor), payload)


@router.post("/allocation/submit", response_model=SubcontractorPortalAllocationResultRead)
def submit_subcontractor_portal_allocation(
    payload: SubcontractorPortalAllocationRequest,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    allocation_service: Annotated[
        SubcontractorPortalAllocationService,
        Depends(get_subcontractor_portal_allocation_service),
    ],
) -> SubcontractorPortalAllocationResultRead:
    return allocation_service.submit(context_service.get_context(actor), payload)


@router.get("/worker-qualification-types", response_model=list[SubcontractorPortalQualificationTypeOptionRead])
def list_subcontractor_portal_worker_qualification_types(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> list[SubcontractorPortalQualificationTypeOptionRead]:
    return workforce_service.list_portal_qualification_types(context_service.get_context(actor))


@router.get("/workers", response_model=list[SubcontractorWorkerListItem])
def list_subcontractor_portal_workers(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> list[SubcontractorWorkerListItem]:
    return workforce_service.list_workers_for_portal(
        context_service.get_context(actor),
        SubcontractorWorkerFilter(include_archived=False),
    )


@router.post("/workers", response_model=SubcontractorPortalWorkerRead)
def create_subcontractor_portal_worker(
    payload: SubcontractorPortalWorkerCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorPortalWorkerRead:
    return workforce_service.create_worker_for_portal(context_service.get_context(actor), payload, actor)


@router.get("/workers/{worker_id}", response_model=SubcontractorPortalWorkerRead)
def get_subcontractor_portal_worker(
    worker_id: str,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorPortalWorkerRead:
    return workforce_service.get_worker_for_portal(context_service.get_context(actor), worker_id)


@router.patch("/workers/{worker_id}", response_model=SubcontractorPortalWorkerRead)
def update_subcontractor_portal_worker(
    worker_id: str,
    payload: SubcontractorPortalWorkerUpdate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorPortalWorkerRead:
    return workforce_service.update_worker_for_portal(context_service.get_context(actor), worker_id, payload, actor)


@router.get("/workers/{worker_id}/qualifications", response_model=list[SubcontractorWorkerQualificationRead])
def list_subcontractor_portal_worker_qualifications(
    worker_id: str,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> list[SubcontractorWorkerQualificationRead]:
    return workforce_service.list_worker_qualifications_for_portal(context_service.get_context(actor), worker_id)


@router.post("/workers/{worker_id}/qualifications", response_model=SubcontractorWorkerQualificationRead)
def create_subcontractor_portal_worker_qualification(
    worker_id: str,
    payload: SubcontractorPortalWorkerQualificationCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorWorkerQualificationRead:
    return workforce_service.create_worker_qualification_for_portal(
        context_service.get_context(actor),
        worker_id,
        payload,
        actor,
    )


@router.patch("/workers/{worker_id}/qualifications/{qualification_id}", response_model=SubcontractorWorkerQualificationRead)
def update_subcontractor_portal_worker_qualification(
    worker_id: str,
    qualification_id: str,
    payload: SubcontractorPortalWorkerQualificationUpdate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorWorkerQualificationRead:
    return workforce_service.update_worker_qualification_for_portal(
        context_service.get_context(actor),
        worker_id,
        qualification_id,
        payload,
        actor,
    )


@router.get(
    "/workers/{worker_id}/qualifications/{qualification_id}/proofs",
    response_model=list[SubcontractorWorkerQualificationProofRead],
)
def list_subcontractor_portal_worker_qualification_proofs(
    worker_id: str,
    qualification_id: str,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> list[SubcontractorWorkerQualificationProofRead]:
    return workforce_service.list_worker_qualification_proofs_for_portal(
        context_service.get_context(actor),
        worker_id,
        qualification_id,
    )


@router.post(
    "/workers/{worker_id}/qualifications/{qualification_id}/proofs/upload",
    response_model=SubcontractorWorkerQualificationProofRead,
)
def upload_subcontractor_portal_worker_qualification_proof(
    worker_id: str,
    qualification_id: str,
    payload: SubcontractorWorkerQualificationProofUpload,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorWorkerQualificationProofRead:
    return workforce_service.upload_worker_qualification_proof_for_portal(
        context_service.get_context(actor),
        worker_id,
        qualification_id,
        payload,
        actor,
    )


@router.post(
    "/workers/{worker_id}/qualifications/{qualification_id}/proofs/link",
    response_model=SubcontractorWorkerQualificationProofRead,
)
def link_subcontractor_portal_worker_qualification_proof(
    worker_id: str,
    qualification_id: str,
    payload: SubcontractorWorkerQualificationProofLinkCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[SubcontractorPortalService, Depends(get_subcontractor_portal_service)],
    workforce_service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_portal_workforce_service)],
) -> SubcontractorWorkerQualificationProofRead:
    return workforce_service.link_existing_worker_qualification_proof_for_portal(
        context_service.get_context(actor),
        worker_id,
        qualification_id,
        payload,
        actor,
    )

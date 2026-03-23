"""Customer-portal API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.config import settings
from app.modules.finance.billing_repository import SqlAlchemyFinanceBillingRepository
from app.modules.finance.billing_service import FinanceBillingService
from app.modules.customers.collaboration_service import CustomerCollaborationService
from app.modules.customers.portal_read_service import CustomerPortalReadService
from app.modules.customers.portal_service import CustomerPortalService
from app.modules.customers.repository import SqlAlchemyCustomerRepository
from app.modules.customers.schemas import (
    CustomerPortalCollectionSourceRead,
    CustomerPortalContextRead,
    CustomerPortalHistoryCollectionRead,
    CustomerPortalInvoiceCollectionRead,
    CustomerPortalOrderCollectionRead,
    CustomerPortalReportPackageCollectionRead,
    CustomerPortalScheduleCollectionRead,
    CustomerPortalTimesheetCollectionRead,
    CustomerPortalWatchbookCollectionRead,
)
from app.modules.field_execution.repository import SqlAlchemyWatchbookRepository
from app.modules.field_execution.schemas import WatchbookEntryCreate, WatchbookEntryRead
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.repository import SqlAlchemyPlanningRepository
from app.rate_limit import DOCUMENT_DOWNLOAD_RULE, rate_limiter


router = APIRouter(prefix="/api/portal/customer", tags=["customer_portal"])


def get_customer_portal_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerPortalService:
    return CustomerPortalService(SqlAlchemyCustomerRepository(session))


def get_customer_portal_read_service() -> CustomerPortalReadService:
    return CustomerPortalReadService()


def get_customer_finance_billing_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> FinanceBillingService:
    return FinanceBillingService(
        repository=SqlAlchemyFinanceBillingRepository(session),
        integration_repository=SqlAlchemyIntegrationRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_released_schedule_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReleasedScheduleService:
    return ReleasedScheduleService(SqlAlchemyPlanningRepository(session))


def get_customer_collaboration_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerCollaborationService:
    return CustomerCollaborationService(
        SqlAlchemyCustomerRepository(session),
        login_audit_repository=SqlAlchemyAuditRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_watchbook_service(
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


@router.get("/context", response_model=CustomerPortalContextRead)
def get_customer_portal_context(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
) -> CustomerPortalContextRead:
    return service.get_context(actor)


@router.get("/orders", response_model=CustomerPortalOrderCollectionRead)
def list_customer_portal_orders(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    read_service: Annotated[CustomerPortalReadService, Depends(get_customer_portal_read_service)],
) -> CustomerPortalOrderCollectionRead:
    return read_service.list_orders(context_service.get_context(actor))


@router.get("/schedules", response_model=CustomerPortalScheduleCollectionRead)
def list_customer_portal_schedules(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    released_schedule_service: Annotated[ReleasedScheduleService, Depends(get_customer_released_schedule_service)],
) -> CustomerPortalScheduleCollectionRead:
    return released_schedule_service.list_customer_schedules(context_service.get_context(actor))


@router.get("/watchbooks", response_model=CustomerPortalWatchbookCollectionRead)
def list_customer_portal_watchbooks(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    watchbook_service: Annotated[WatchbookService, Depends(get_customer_watchbook_service)],
) -> CustomerPortalWatchbookCollectionRead:
    context = context_service.get_context(actor)
    items = [
        {
            "id": row.id,
            "customer_id": row.customer_id,
            "log_date": row.log_date,
            "occurred_at": row.entries[-1].occurred_at if row.entries else row.updated_at,
            "entry_type_code": row.entries[-1].entry_type_code if row.entries else None,
            "summary": row.entries[-1].summary if row.entries else (row.summary or row.headline or row.context_type),
            "status": row.closure_state_code,
            "personal_names_released": False,
            "pdf_document_id": row.pdf_document.document_id if row.pdf_document is not None else None,
        }
        for row in watchbook_service.list_customer_released_watchbooks(context)
    ]
    return CustomerPortalWatchbookCollectionRead(
        customer_id=context.customer_id,
        source=CustomerPortalCollectionSourceRead(
            domain_key="watchbooks",
            source_module_key="field_execution",
            availability_status="ready",
            released_only=True,
            customer_scoped=True,
            docs_backed_outputs=True,
            message_key="portalCustomer.datasets.watchbooks.pending",
        ),
        items=items,
    )


@router.post("/watchbooks/{watchbook_id}/entries", response_model=WatchbookEntryRead)
def create_customer_portal_watchbook_entry(
    watchbook_id: str,
    payload: WatchbookEntryCreate,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    watchbook_service: Annotated[WatchbookService, Depends(get_customer_watchbook_service)],
) -> WatchbookEntryRead:
    return watchbook_service.add_customer_portal_entry(context_service.get_context(actor), watchbook_id, payload, actor)


@router.get("/timesheets", response_model=CustomerPortalTimesheetCollectionRead)
def list_customer_portal_timesheets(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    billing_service: Annotated[FinanceBillingService, Depends(get_customer_finance_billing_service)],
) -> CustomerPortalTimesheetCollectionRead:
    return billing_service.list_customer_portal_timesheets(context_service.get_context(actor))


@router.get("/timesheets/{timesheet_id}/documents/{document_id}/versions/{version_no}/download")
def download_customer_portal_timesheet_document(
    timesheet_id: str,
    document_id: str,
    version_no: int,
    request: Request,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    billing_service: Annotated[FinanceBillingService, Depends(get_customer_finance_billing_service)],
) -> Response:
    rate_limiter.assert_allowed(
        DOCUMENT_DOWNLOAD_RULE,
        principal=f"{actor.tenant_id}:{actor.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    download = billing_service.download_customer_portal_timesheet_document(context_service.get_context(actor), timesheet_id, document_id, version_no)
    return Response(
        content=download.content,
        media_type=download.content_type,
        headers={"Content-Disposition": f'attachment; filename="{download.file_name}"'},
    )


@router.get("/invoices", response_model=CustomerPortalInvoiceCollectionRead)
def list_customer_portal_invoices(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    billing_service: Annotated[FinanceBillingService, Depends(get_customer_finance_billing_service)],
) -> CustomerPortalInvoiceCollectionRead:
    return billing_service.list_customer_portal_invoices(context_service.get_context(actor))


@router.get("/invoices/{invoice_id}/documents/{document_id}/versions/{version_no}/download")
def download_customer_portal_invoice_document(
    invoice_id: str,
    document_id: str,
    version_no: int,
    request: Request,
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    billing_service: Annotated[FinanceBillingService, Depends(get_customer_finance_billing_service)],
) -> Response:
    rate_limiter.assert_allowed(
        DOCUMENT_DOWNLOAD_RULE,
        principal=f"{actor.tenant_id}:{actor.user_id or (request.client.host if request.client else 'anonymous')}",
    )
    download = billing_service.download_customer_portal_invoice_document(context_service.get_context(actor), invoice_id, document_id, version_no)
    return Response(
        content=download.content,
        media_type=download.content_type,
        headers={"Content-Disposition": f'attachment; filename="{download.file_name}"'},
    )


@router.get("/reports", response_model=CustomerPortalReportPackageCollectionRead)
def list_customer_portal_reports(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    read_service: Annotated[CustomerPortalReadService, Depends(get_customer_portal_read_service)],
) -> CustomerPortalReportPackageCollectionRead:
    return read_service.list_report_packages(context_service.get_context(actor))


@router.get("/history", response_model=CustomerPortalHistoryCollectionRead)
def list_customer_portal_history(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    collaboration_service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerPortalHistoryCollectionRead:
    return collaboration_service.list_portal_history(context_service.get_context(actor))

"""Customer-portal API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.config import settings
from app.modules.customers.collaboration_service import CustomerCollaborationService
from app.modules.customers.portal_read_service import CustomerPortalReadService
from app.modules.customers.portal_service import CustomerPortalService
from app.modules.customers.repository import SqlAlchemyCustomerRepository
from app.modules.customers.schemas import (
    CustomerPortalContextRead,
    CustomerPortalHistoryCollectionRead,
    CustomerPortalOrderCollectionRead,
    CustomerPortalReportPackageCollectionRead,
    CustomerPortalScheduleCollectionRead,
    CustomerPortalTimesheetCollectionRead,
    CustomerPortalWatchbookCollectionRead,
)
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/portal/customer", tags=["customer_portal"])


def get_customer_portal_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerPortalService:
    return CustomerPortalService(SqlAlchemyCustomerRepository(session))


def get_customer_portal_read_service() -> CustomerPortalReadService:
    return CustomerPortalReadService()


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
    read_service: Annotated[CustomerPortalReadService, Depends(get_customer_portal_read_service)],
) -> CustomerPortalScheduleCollectionRead:
    return read_service.list_schedules(context_service.get_context(actor))


@router.get("/watchbooks", response_model=CustomerPortalWatchbookCollectionRead)
def list_customer_portal_watchbooks(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    read_service: Annotated[CustomerPortalReadService, Depends(get_customer_portal_read_service)],
) -> CustomerPortalWatchbookCollectionRead:
    return read_service.list_watchbook_entries(context_service.get_context(actor))


@router.get("/timesheets", response_model=CustomerPortalTimesheetCollectionRead)
def list_customer_portal_timesheets(
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    context_service: Annotated[CustomerPortalService, Depends(get_customer_portal_service)],
    read_service: Annotated[CustomerPortalReadService, Depends(get_customer_portal_read_service)],
) -> CustomerPortalTimesheetCollectionRead:
    return read_service.list_timesheets(context_service.get_context(actor))


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

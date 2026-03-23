"""HTTP API for finance customer timesheets and invoices."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.finance.billing_repository import SqlAlchemyFinanceBillingRepository
from app.modules.finance.billing_schemas import (
    CustomerInvoiceListItem,
    CustomerInvoiceRead,
    InvoiceDispatchRequest,
    InvoiceGenerateRequest,
    InvoiceIssueRequest,
    InvoiceListFilter,
    InvoiceReleaseRequest,
    TimesheetGenerateRequest,
    TimesheetListFilter,
    TimesheetListItem,
    TimesheetRead,
    TimesheetReleaseRequest,
)
from app.modules.finance.billing_service import FinanceBillingService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository
from app.modules.platform_services.storage import build_object_storage_adapter


router = APIRouter(prefix="/api/finance/tenants/{tenant_id}/billing", tags=["finance-billing"])


def get_finance_billing_service(
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


@router.get("/timesheets", response_model=list[TimesheetListItem])
def list_timesheets(
    tenant_id: UUID,
    filters: Annotated[TimesheetListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.read", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> list[TimesheetListItem]:
    return service.list_timesheets(str(tenant_id), filters, actor)


@router.get("/timesheets/{timesheet_id}", response_model=TimesheetRead)
def get_timesheet(
    tenant_id: UUID,
    timesheet_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.read", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> TimesheetRead:
    return service.get_timesheet(str(tenant_id), str(timesheet_id), actor)


@router.post("/timesheets", response_model=TimesheetRead, status_code=status.HTTP_201_CREATED)
def generate_timesheet(
    tenant_id: UUID,
    payload: TimesheetGenerateRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.write", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> TimesheetRead:
    return service.generate_timesheet(str(tenant_id), payload, actor)


@router.post("/timesheets/{timesheet_id}/release", response_model=TimesheetRead)
def release_timesheet(
    tenant_id: UUID,
    timesheet_id: UUID,
    payload: TimesheetReleaseRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.write", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> TimesheetRead:
    return service.release_timesheet(str(tenant_id), str(timesheet_id), payload, actor)


@router.get("/invoices", response_model=list[CustomerInvoiceListItem])
def list_invoices(
    tenant_id: UUID,
    filters: Annotated[InvoiceListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.read", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> list[CustomerInvoiceListItem]:
    return service.list_invoices(str(tenant_id), filters, actor)


@router.get("/invoices/{invoice_id}", response_model=CustomerInvoiceRead)
def get_invoice(
    tenant_id: UUID,
    invoice_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.read", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> CustomerInvoiceRead:
    return service.get_invoice(str(tenant_id), str(invoice_id), actor)


@router.post("/invoices", response_model=CustomerInvoiceRead, status_code=status.HTTP_201_CREATED)
def generate_invoice(
    tenant_id: UUID,
    payload: InvoiceGenerateRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.write", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> CustomerInvoiceRead:
    return service.generate_invoice(str(tenant_id), payload, actor)


@router.post("/invoices/{invoice_id}/issue", response_model=CustomerInvoiceRead)
def issue_invoice(
    tenant_id: UUID,
    invoice_id: UUID,
    payload: InvoiceIssueRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.write", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> CustomerInvoiceRead:
    return service.issue_invoice(str(tenant_id), str(invoice_id), payload, actor)


@router.post("/invoices/{invoice_id}/release", response_model=CustomerInvoiceRead)
def release_invoice(
    tenant_id: UUID,
    invoice_id: UUID,
    payload: InvoiceReleaseRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.write", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> CustomerInvoiceRead:
    return service.release_invoice(str(tenant_id), str(invoice_id), payload, actor)


@router.post("/invoices/{invoice_id}/queue-dispatch", response_model=CustomerInvoiceRead)
def queue_invoice_dispatch(
    tenant_id: UUID,
    invoice_id: UUID,
    payload: InvoiceDispatchRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.billing.delivery", scope="tenant")),
    ],
    service: Annotated[FinanceBillingService, Depends(get_finance_billing_service)],
) -> CustomerInvoiceRead:
    return service.queue_invoice_dispatch(str(tenant_id), str(invoice_id), payload, actor)

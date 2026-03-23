from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.finance.subcontractor_check_repository import SqlAlchemySubcontractorInvoiceCheckRepository
from app.modules.finance.subcontractor_check_schemas import (
    SubcontractorInvoiceCheckGenerateRequest,
    SubcontractorInvoiceCheckListFilter,
    SubcontractorInvoiceCheckListItem,
    SubcontractorInvoiceCheckNoteCreate,
    SubcontractorInvoiceCheckRead,
    SubcontractorInvoiceCheckStatusRequest,
    SubcontractorInvoiceSubmissionUpdateRequest,
)
from app.modules.finance.subcontractor_check_service import SubcontractorInvoiceCheckService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


router = APIRouter(prefix="/api/finance/tenants/{tenant_id}/subcontractor-invoice-checks", tags=["finance-subcontractor-invoice-checks"])


def get_subcontractor_invoice_check_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorInvoiceCheckService:
    return SubcontractorInvoiceCheckService(
        repository=SqlAlchemySubcontractorInvoiceCheckRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[SubcontractorInvoiceCheckListItem])
def list_subcontractor_invoice_checks(
    tenant_id: UUID,
    filters: Annotated[SubcontractorInvoiceCheckListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.read", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> list[SubcontractorInvoiceCheckListItem]:
    return service.list_invoice_checks(str(tenant_id), filters, actor)


@router.get("/{invoice_check_id}", response_model=SubcontractorInvoiceCheckRead)
def get_subcontractor_invoice_check(
    tenant_id: UUID,
    invoice_check_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.read", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> SubcontractorInvoiceCheckRead:
    return service.get_invoice_check(str(tenant_id), str(invoice_check_id), actor)


@router.get("/{invoice_check_id}/audit-history", response_model=list[AuditEventRead])
def get_subcontractor_invoice_check_audit_history(
    tenant_id: UUID,
    invoice_check_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.read", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> list[AuditEventRead]:
    return service.get_audit_history(str(tenant_id), str(invoice_check_id), actor)


@router.post("/generate", response_model=SubcontractorInvoiceCheckRead, status_code=status.HTTP_201_CREATED)
def generate_subcontractor_invoice_check(
    tenant_id: UUID,
    payload: SubcontractorInvoiceCheckGenerateRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> SubcontractorInvoiceCheckRead:
    return service.generate_invoice_check(str(tenant_id), payload, actor)


@router.post("/{invoice_check_id}/submitted-invoice", response_model=SubcontractorInvoiceCheckRead)
def update_submitted_invoice(
    tenant_id: UUID,
    invoice_check_id: UUID,
    payload: SubcontractorInvoiceSubmissionUpdateRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> SubcontractorInvoiceCheckRead:
    return service.update_submitted_invoice(str(tenant_id), str(invoice_check_id), payload, actor)


@router.post("/{invoice_check_id}/notes", response_model=SubcontractorInvoiceCheckRead, status_code=status.HTTP_201_CREATED)
def add_subcontractor_invoice_check_note(
    tenant_id: UUID,
    invoice_check_id: UUID,
    payload: SubcontractorInvoiceCheckNoteCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> SubcontractorInvoiceCheckRead:
    return service.add_note(str(tenant_id), str(invoice_check_id), payload, actor)


@router.post("/{invoice_check_id}/status", response_model=SubcontractorInvoiceCheckRead)
def change_subcontractor_invoice_check_status(
    tenant_id: UUID,
    invoice_check_id: UUID,
    payload: SubcontractorInvoiceCheckStatusRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.subcontractor_control.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorInvoiceCheckService, Depends(get_subcontractor_invoice_check_service)],
) -> SubcontractorInvoiceCheckRead:
    return service.change_status(str(tenant_id), str(invoice_check_id), payload, actor)

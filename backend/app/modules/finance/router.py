"""HTTP API for finance actual bridge derivation, approvals, and reconciliation."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.rls import rls_session_context
from app.db.session import get_db_session
from app.modules.finance.repository import SqlAlchemyFinanceRepository
from app.modules.finance.schemas import (
    ActualAllowanceCreate,
    ActualApprovalActionRequest,
    ActualCommentCreate,
    ActualExpenseCreate,
    ActualRecordListFilter,
    ActualRecordListItem,
    ActualRecordRead,
    ActualReconciliationCreate,
)
from app.modules.finance.service import FinanceActualService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import (
    RequestAuthorizationContext,
    get_request_authorization_context,
    require_authorization,
)


router = APIRouter(prefix="/api/finance/tenants/{tenant_id}/actual-records", tags=["finance-actuals"])


def get_finance_actual_service(
    session: Annotated[Session, Depends(get_db_session)],
    actor: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
) -> FinanceActualService:
    with rls_session_context(session, tenant_id=actor.tenant_id, bypass=actor.is_platform_admin):
        yield FinanceActualService(
            repository=SqlAlchemyFinanceRepository(session),
            audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        )


@router.get("", response_model=list[ActualRecordListItem])
def list_actual_records(
    tenant_id: UUID,
    filters: Annotated[ActualRecordListFilter, Depends()],
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.read", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> list[ActualRecordListItem]:
    return service.list_actual_records(str(tenant_id), filters, actor)


@router.get("/{actual_record_id}", response_model=ActualRecordRead)
def get_actual_record(
    tenant_id: UUID,
    actual_record_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.read", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.get_actual_record(str(tenant_id), str(actual_record_id), actor)


@router.get("/{actual_record_id}/audit-history", response_model=list[AuditEventRead])
def get_actual_audit_history(
    tenant_id: UUID,
    actual_record_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.read", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> list[AuditEventRead]:
    return service.get_audit_history(str(tenant_id), str(actual_record_id), actor)


@router.post("/derive/assignments/{assignment_id}", response_model=ActualRecordRead, status_code=status.HTTP_201_CREATED)
def derive_actual_for_assignment(
    tenant_id: UUID,
    assignment_id: UUID,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.derive_for_assignment(str(tenant_id), str(assignment_id), actor)


@router.post("/{actual_record_id}/preliminary-submit", response_model=ActualRecordRead)
def submit_preliminary_actual(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualApprovalActionRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.approval.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.submit_preliminary_actual(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/operational-confirm", response_model=ActualRecordRead)
def confirm_operational_actual(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualApprovalActionRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.approval.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.confirm_operational_actual(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/finance-signoff", response_model=ActualRecordRead)
def finance_signoff_actual(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualApprovalActionRequest,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.approval.signoff", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.finance_signoff_actual(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/reconciliations", response_model=ActualRecordRead, status_code=status.HTTP_201_CREATED)
def create_reconciliation(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualReconciliationCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.add_reconciliation(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/allowances", response_model=ActualRecordRead, status_code=status.HTTP_201_CREATED)
def create_allowance(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualAllowanceCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.add_allowance(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/expenses", response_model=ActualRecordRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualExpenseCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.write", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.add_expense(str(tenant_id), str(actual_record_id), payload, actor)


@router.post("/{actual_record_id}/comments", response_model=ActualRecordRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    tenant_id: UUID,
    actual_record_id: UUID,
    payload: ActualCommentCreate,
    actor: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("finance.actual.read", scope="tenant")),
    ],
    service: Annotated[FinanceActualService, Depends(get_finance_actual_service)],
) -> ActualRecordRead:
    return service.add_comment(str(tenant_id), str(actual_record_id), payload, actor)

"""HTTP API for tenant-scoped customer portal access management."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.customers.portal_access_repository import SqlAlchemyCustomerPortalAccessRepository
from app.modules.customers.portal_access_service import CustomerPortalAccessService
from app.modules.customers.schemas import (
    CustomerPortalAccessCreate,
    CustomerPortalAccessListItemRead,
    CustomerPortalAccessPasswordResetRequest,
    CustomerPortalAccessPasswordResetResponse,
    CustomerPortalAccessStatusUpdate,
    CustomerPortalAccessUnlinkResponse,
)
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


router = APIRouter(
    prefix="/api/customers/tenants/{tenant_id}/customers/{customer_id}/portal-access",
    tags=["customer-portal-access"],
)


def get_customer_portal_access_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerPortalAccessService:
    return CustomerPortalAccessService(
        SqlAlchemyCustomerPortalAccessRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[CustomerPortalAccessListItemRead])
def list_customer_portal_access(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.portal_access.read", scope="tenant")),
    ],
    service: Annotated[CustomerPortalAccessService, Depends(get_customer_portal_access_service)],
) -> list[CustomerPortalAccessListItemRead]:
    return service.list_portal_access(str(tenant_id), str(customer_id), context)


@router.post("", response_model=CustomerPortalAccessPasswordResetResponse, status_code=status.HTTP_201_CREATED)
def create_customer_portal_access(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerPortalAccessCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.portal_access.write", scope="tenant")),
    ],
    service: Annotated[CustomerPortalAccessService, Depends(get_customer_portal_access_service)],
) -> CustomerPortalAccessPasswordResetResponse:
    return service.create_portal_access(str(tenant_id), str(customer_id), payload, context)


@router.post("/{user_id}/password-reset", response_model=CustomerPortalAccessPasswordResetResponse)
def reset_customer_portal_access_password(
    tenant_id: UUID,
    customer_id: UUID,
    user_id: UUID,
    payload: CustomerPortalAccessPasswordResetRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.portal_access.write", scope="tenant")),
    ],
    service: Annotated[CustomerPortalAccessService, Depends(get_customer_portal_access_service)],
) -> CustomerPortalAccessPasswordResetResponse:
    return service.reset_portal_access_password(
        str(tenant_id),
        str(customer_id),
        str(user_id),
        payload,
        context,
    )


@router.post("/{user_id}/status", response_model=CustomerPortalAccessListItemRead)
def update_customer_portal_access_status(
    tenant_id: UUID,
    customer_id: UUID,
    user_id: UUID,
    payload: CustomerPortalAccessStatusUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.portal_access.write", scope="tenant")),
    ],
    service: Annotated[CustomerPortalAccessService, Depends(get_customer_portal_access_service)],
) -> CustomerPortalAccessListItemRead:
    return service.update_portal_access_status(str(tenant_id), str(customer_id), str(user_id), payload, context)


@router.delete("/{user_id}", response_model=CustomerPortalAccessUnlinkResponse)
def unlink_customer_portal_access(
    tenant_id: UUID,
    customer_id: UUID,
    user_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.portal_access.write", scope="tenant")),
    ],
    service: Annotated[CustomerPortalAccessService, Depends(get_customer_portal_access_service)],
) -> CustomerPortalAccessUnlinkResponse:
    return service.unlink_portal_access(str(tenant_id), str(customer_id), str(user_id), context)

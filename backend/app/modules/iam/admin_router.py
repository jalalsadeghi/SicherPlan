"""HTTP router for platform-managed tenant admin user flows."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.iam.admin_repository import SqlAlchemyIamAdminRepository
from app.modules.iam.admin_service import IamAdminActorContext, IamAdminService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.iam.schemas import (
    TenantAdminPasswordResetRequest,
    TenantAdminPasswordResetResponse,
    TenantAdminUserCreate,
    TenantAdminUserListItem,
    TenantAdminUserStatusUpdate,
)

router = APIRouter(prefix="/api/iam/admin", tags=["iam-admin"])


def get_iam_admin_actor_context(context: RequestAuthorizationContext) -> IamAdminActorContext:
    return IamAdminActorContext(
        actor_role="platform_admin" if context.is_platform_admin else next(iter(context.role_keys), "user"),
        tenant_id=context.tenant_id,
        actor_user_id=context.user_id,
        actor_session_id=context.session_id,
        request_id=context.request_id,
    )


def get_iam_admin_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> IamAdminService:
    return IamAdminService(
        SqlAlchemyIamAdminRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("/tenants/{tenant_id}/tenant-users", response_model=list[TenantAdminUserListItem])
def list_tenant_admin_users(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.read", scope="platform")),
    ],
    service: Annotated[IamAdminService, Depends(get_iam_admin_service)],
) -> list[TenantAdminUserListItem]:
    actor = get_iam_admin_actor_context(context)
    return service.list_tenant_admin_users(str(tenant_id), actor)


@router.post(
    "/tenants/{tenant_id}/tenant-users",
    response_model=TenantAdminPasswordResetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_admin_user(
    tenant_id: UUID,
    payload: TenantAdminUserCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.create", scope="platform")),
    ],
    service: Annotated[IamAdminService, Depends(get_iam_admin_service)],
) -> TenantAdminPasswordResetResponse:
    actor = get_iam_admin_actor_context(context)
    payload_data = payload.model_dump()
    payload_data["tenant_id"] = str(tenant_id)
    return service.create_tenant_admin_user(
        TenantAdminUserCreate(**payload_data),
        actor,
    )


@router.post("/tenants/{tenant_id}/tenant-users/{user_id}/status", response_model=TenantAdminUserListItem)
def update_tenant_admin_user_status(
    tenant_id: UUID,
    user_id: UUID,
    payload: TenantAdminUserStatusUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.write", scope="platform")),
    ],
    service: Annotated[IamAdminService, Depends(get_iam_admin_service)],
) -> TenantAdminUserListItem:
    actor = get_iam_admin_actor_context(context)
    return service.update_tenant_admin_user_status(str(tenant_id), str(user_id), payload, actor)


@router.post(
    "/tenants/{tenant_id}/tenant-users/{user_id}/password-reset",
    response_model=TenantAdminPasswordResetResponse,
)
def reset_tenant_admin_user_password(
    tenant_id: UUID,
    user_id: UUID,
    payload: TenantAdminPasswordResetRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.write", scope="platform")),
    ],
    service: Annotated[IamAdminService, Depends(get_iam_admin_service)],
) -> TenantAdminPasswordResetResponse:
    actor = get_iam_admin_actor_context(context)
    return service.reset_tenant_admin_password(str(tenant_id), str(user_id), payload, actor)

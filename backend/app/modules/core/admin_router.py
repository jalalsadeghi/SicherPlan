"""Core admin HTTP API for tenant onboarding and settings management."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.core.admin_repository import SqlAlchemyCoreAdminRepository
from app.modules.core.admin_service import AdminActorContext, CoreAdminService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.core.schemas import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    MandateCreate,
    MandateRead,
    MandateUpdate,
    TenantListItem,
    TenantOnboardingCreate,
    TenantOnboardingRead,
    TenantRead,
    TenantSettingCreate,
    TenantSettingRead,
    TenantSettingUpdate,
    TenantStatusUpdate,
    TenantUpdate,
)

router = APIRouter(prefix="/api/core/admin", tags=["core-admin"])


def get_admin_actor_context(
    context: RequestAuthorizationContext,
) -> AdminActorContext:
    if context.is_platform_admin:
        actor_role = "platform_admin"
    elif "tenant_admin" in context.role_keys:
        actor_role = "tenant_admin"
    else:
        actor_role = next(iter(context.role_keys), "user")
    return AdminActorContext(
        actor_role=actor_role,
        tenant_id=context.tenant_id,
        actor_user_id=context.user_id,
        actor_session_id=context.session_id,
        request_id=context.request_id,
        permission_keys=context.permission_keys,
        branch_ids=frozenset(scope.branch_id for scope in context.scopes if scope.branch_id is not None),
        mandate_ids=frozenset(scope.mandate_id for scope in context.scopes if scope.mandate_id is not None),
    )


def get_core_admin_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CoreAdminService:
    return CoreAdminService(
        SqlAlchemyCoreAdminRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.post("/tenants/onboard", response_model=TenantOnboardingRead, status_code=status.HTTP_201_CREATED)
def onboard_tenant(
    payload: TenantOnboardingCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.create", scope="platform")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantOnboardingRead:
    actor = get_admin_actor_context(context)
    return service.onboard_tenant(payload, actor)


@router.get("/tenants", response_model=list[TenantListItem])
def list_tenants(
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.read", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> list[TenantListItem]:
    actor = get_admin_actor_context(context)
    return service.list_tenants(actor)


@router.get("/tenants/{tenant_id}", response_model=TenantRead)
def get_tenant(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.read", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantRead:
    actor = get_admin_actor_context(context)
    return service.get_tenant(str(tenant_id), actor)


@router.patch("/tenants/{tenant_id}", response_model=TenantRead)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantRead:
    actor = get_admin_actor_context(context)
    return service.update_tenant(str(tenant_id), payload, actor)


@router.post("/tenants/{tenant_id}/lifecycle", response_model=TenantRead)
def transition_tenant_status(
    tenant_id: UUID,
    payload: TenantStatusUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.tenant.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantRead:
    actor = get_admin_actor_context(context)
    return service.transition_tenant_status(str(tenant_id), payload, actor)


@router.get("/tenants/{tenant_id}/branches", response_model=list[BranchRead])
def list_branches(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.branch.read", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> list[BranchRead]:
    actor = get_admin_actor_context(context)
    return service.list_branches(str(tenant_id), actor)


@router.post("/tenants/{tenant_id}/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(
    tenant_id: UUID,
    payload: BranchCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.branch.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> BranchRead:
    actor = get_admin_actor_context(context)
    return service.create_branch(str(tenant_id), payload, actor)


@router.patch("/tenants/{tenant_id}/branches/{branch_id}", response_model=BranchRead)
def update_branch(
    tenant_id: UUID,
    branch_id: UUID,
    payload: BranchUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.branch.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> BranchRead:
    actor = get_admin_actor_context(context)
    return service.update_branch(str(tenant_id), str(branch_id), payload, actor)


@router.get("/tenants/{tenant_id}/mandates", response_model=list[MandateRead])
def list_mandates(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.mandate.read", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> list[MandateRead]:
    actor = get_admin_actor_context(context)
    return service.list_mandates(str(tenant_id), actor)


@router.post("/tenants/{tenant_id}/mandates", response_model=MandateRead, status_code=status.HTTP_201_CREATED)
def create_mandate(
    tenant_id: UUID,
    payload: MandateCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.mandate.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> MandateRead:
    actor = get_admin_actor_context(context)
    return service.create_mandate(str(tenant_id), payload, actor)


@router.patch("/tenants/{tenant_id}/mandates/{mandate_id}", response_model=MandateRead)
def update_mandate(
    tenant_id: UUID,
    mandate_id: UUID,
    payload: MandateUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.mandate.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> MandateRead:
    actor = get_admin_actor_context(context)
    return service.update_mandate(str(tenant_id), str(mandate_id), payload, actor)


@router.get("/tenants/{tenant_id}/settings", response_model=list[TenantSettingRead])
def list_settings(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.setting.read", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> list[TenantSettingRead]:
    actor = get_admin_actor_context(context)
    return service.list_settings(str(tenant_id), actor)


@router.post("/tenants/{tenant_id}/settings", response_model=TenantSettingRead, status_code=status.HTTP_201_CREATED)
def create_setting(
    tenant_id: UUID,
    payload: TenantSettingCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.setting.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantSettingRead:
    actor = get_admin_actor_context(context)
    return service.create_setting(str(tenant_id), payload, actor)


@router.put("/tenants/{tenant_id}/settings/{setting_id}", response_model=TenantSettingRead)
def update_setting(
    tenant_id: UUID,
    setting_id: UUID,
    payload: TenantSettingUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("core.admin.setting.write", scope="tenant")),
    ],
    service: Annotated[CoreAdminService, Depends(get_core_admin_service)],
) -> TenantSettingRead:
    actor = get_admin_actor_context(context)
    return service.update_setting(str(tenant_id), str(setting_id), payload, actor)

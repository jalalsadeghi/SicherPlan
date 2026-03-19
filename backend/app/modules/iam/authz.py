"""Reusable RBAC and scope enforcement helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Request

from app.errors import ApiException
from app.modules.iam.auth_router import get_current_auth_context
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.auth_service import AuthenticatedSessionContext


AuthorizationScope = Literal["platform", "tenant", "branch", "mandate", "customer"]


@dataclass(frozen=True, slots=True)
class RequestAuthorizationContext:
    session_id: str
    user_id: str
    tenant_id: str
    role_keys: frozenset[str]
    permission_keys: frozenset[str]
    scopes: tuple[AuthenticatedRoleScope, ...]
    request_id: str | None = None

    @property
    def is_platform_admin(self) -> bool:
        return "platform_admin" in self.role_keys

    @property
    def is_tenant_admin(self) -> bool:
        return "tenant_admin" in self.role_keys

    def has_permission(self, permission_key: str) -> bool:
        return permission_key in self.permission_keys

    def allows_tenant(self, tenant_id: str) -> bool:
        if self.is_platform_admin:
            return True
        return self.tenant_id == tenant_id and any(scope.scope_type == "tenant" for scope in self.scopes)

    def allows_branch(self, tenant_id: str, branch_id: str) -> bool:
        if self.is_platform_admin:
            return True
        if self.tenant_id != tenant_id:
            return False
        if any(scope.scope_type == "tenant" for scope in self.scopes):
            return True
        return any(scope.scope_type == "branch" and scope.branch_id == branch_id for scope in self.scopes)

    def allows_mandate(self, tenant_id: str, mandate_id: str) -> bool:
        if self.is_platform_admin:
            return True
        if self.tenant_id != tenant_id:
            return False
        if any(scope.scope_type == "tenant" for scope in self.scopes):
            return True
        return any(scope.scope_type == "mandate" and scope.mandate_id == mandate_id for scope in self.scopes)

    def allows_customer(self, tenant_id: str, customer_id: str) -> bool:
        if self.is_platform_admin:
            return True
        if self.tenant_id != tenant_id:
            return False
        if any(scope.scope_type == "tenant" for scope in self.scopes):
            return True
        return any(scope.scope_type == "customer" and scope.customer_id == customer_id for scope in self.scopes)

    @classmethod
    def from_authenticated_context(cls, context: AuthenticatedSessionContext) -> "RequestAuthorizationContext":
        return cls(
            session_id=context.session.id,
            user_id=context.user.id,
            tenant_id=context.user.tenant_id,
            request_id=context.request_id,
            role_keys=frozenset(role.role_key for role in context.roles),
            permission_keys=context.permission_keys,
            scopes=tuple(context.roles),
        )


def get_request_authorization_context(
    request: Request,
    context: Annotated[AuthenticatedSessionContext, Depends(get_current_auth_context)],
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id=context.session.id,
        user_id=context.user.id,
        tenant_id=context.user.tenant_id,
        request_id=getattr(request.state, "request_id", None),
        role_keys=frozenset(role.role_key for role in context.roles),
        permission_keys=context.permission_keys,
        scopes=tuple(context.roles),
    )


def enforce_permission(context: RequestAuthorizationContext, permission_key: str) -> None:
    if not context.has_permission(permission_key):
        raise ApiException(
            403,
            "iam.authorization.permission_denied",
            "errors.iam.authorization.permission_denied",
            {"permission_key": permission_key},
        )


def enforce_scope(
    context: RequestAuthorizationContext,
    *,
    scope: AuthorizationScope,
    tenant_id: str | None = None,
    branch_id: str | None = None,
    mandate_id: str | None = None,
    request_customer_id: str | None = None,
) -> None:
    if scope == "platform":
        if not context.is_platform_admin:
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": scope},
            )
        return

    if scope == "tenant":
        effective_tenant_id = tenant_id or context.tenant_id
        if not context.allows_tenant(effective_tenant_id):
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": scope, "tenant_id": effective_tenant_id},
            )
        return

    if scope == "branch":
        if tenant_id is None or branch_id is None or not context.allows_branch(tenant_id, branch_id):
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": scope, "tenant_id": tenant_id, "branch_id": branch_id},
            )
        return

    if scope == "mandate":
        if tenant_id is None or mandate_id is None or not context.allows_mandate(tenant_id, mandate_id):
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": scope, "tenant_id": tenant_id, "mandate_id": mandate_id},
            )
        return

    if scope == "customer":
        if tenant_id is None or request_customer_id is None or not context.allows_customer(tenant_id, request_customer_id):
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": scope, "tenant_id": tenant_id, "customer_id": request_customer_id},
            )
        return


def require_authorization(
    permission_key: str,
    *,
    scope: AuthorizationScope = "tenant",
    tenant_param: str = "tenant_id",
    branch_param: str = "branch_id",
    mandate_param: str = "mandate_id",
    customer_param: str = "customer_id",
):
    def dependency(
        request: Request,
        context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    ) -> RequestAuthorizationContext:
        enforce_permission(context, permission_key)
        enforce_scope(
            context,
            scope=scope,
            tenant_id=request.path_params.get(tenant_param),
            branch_id=request.path_params.get(branch_param),
            mandate_id=request.path_params.get(mandate_param),
            request_customer_id=request.path_params.get(customer_param),
        )
        return context

    return dependency

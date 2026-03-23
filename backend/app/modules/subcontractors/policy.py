"""Subcontractor-module visibility and privacy policy rules."""

from __future__ import annotations

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.subcontractors.models import Subcontractor


PORTAL_ROLE_KEYS = frozenset({"customer_user", "subcontractor_user", "employee_user"})

SUBCONTRACTOR_PORTAL_BOUNDARY = (
    "Portal-facing subcontractor users must not consume the internal partner master-data APIs directly. "
    "Portal access must stay constrained to dedicated subcontractor-scoped read/write surfaces."
)


def enforce_subcontractor_internal_write_access(
    actor: RequestAuthorizationContext,
    *,
    tenant_id: str,
) -> None:
    if actor.is_platform_admin:
        return
    if actor.tenant_id != tenant_id:
        raise ApiException(
            403,
            "iam.authorization.scope_denied",
            "errors.iam.authorization.scope_denied",
            {"tenant_id": tenant_id},
        )
    if actor.role_keys & PORTAL_ROLE_KEYS:
        raise ApiException(
            403,
            "subcontractors.authorization.portal_forbidden",
            "errors.subcontractors.authorization.portal_forbidden",
            {"privacy_boundary": SUBCONTRACTOR_PORTAL_BOUNDARY},
        )
    if not any(scope.scope_type == "tenant" for scope in actor.scopes):
        raise ApiException(
            403,
            "subcontractors.authorization.internal_scope_required",
            "errors.subcontractors.authorization.internal_scope_required",
            {"tenant_id": tenant_id},
        )


def can_read_subcontractor_internal(
    actor: RequestAuthorizationContext,
    *,
    tenant_id: str,
    subcontractor: Subcontractor,
) -> bool:
    if actor.is_platform_admin:
        return True
    if actor.tenant_id != tenant_id:
        return False
    if actor.role_keys & PORTAL_ROLE_KEYS:
        return False
    if any(scope.scope_type == "tenant" for scope in actor.scopes):
        return True
    if any(scope.scope_type == "subcontractor" and scope.subcontractor_id == subcontractor.id for scope in actor.scopes):
        return True

    active_branch_ids = {scope.branch_id for scope in subcontractor.scopes if scope.archived_at is None and scope.branch_id}
    active_mandate_ids = {scope.mandate_id for scope in subcontractor.scopes if scope.archived_at is None and scope.mandate_id}

    for scope in actor.scopes:
        if scope.scope_type == "branch" and scope.branch_id in active_branch_ids:
            return True
        if scope.scope_type == "mandate" and scope.mandate_id in active_mandate_ids:
            return True
    return False


def enforce_subcontractor_internal_read_access(
    actor: RequestAuthorizationContext,
    *,
    tenant_id: str,
    subcontractor: Subcontractor,
) -> None:
    if not actor.is_platform_admin and actor.tenant_id != tenant_id:
        raise ApiException(
            403,
            "iam.authorization.scope_denied",
            "errors.iam.authorization.scope_denied",
            {"tenant_id": tenant_id},
        )
    if not can_read_subcontractor_internal(actor, tenant_id=tenant_id, subcontractor=subcontractor):
        if actor.role_keys & PORTAL_ROLE_KEYS:
            raise ApiException(
                403,
                "subcontractors.authorization.portal_forbidden",
                "errors.subcontractors.authorization.portal_forbidden",
                {"privacy_boundary": SUBCONTRACTOR_PORTAL_BOUNDARY},
            )
        raise ApiException(
            403,
            "subcontractors.authorization.internal_scope_required",
            "errors.subcontractors.authorization.internal_scope_required",
            {"tenant_id": tenant_id, "subcontractor_id": subcontractor.id},
        )

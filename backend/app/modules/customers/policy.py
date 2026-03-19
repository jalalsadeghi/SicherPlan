"""Customer-module visibility and privacy policy rules."""

from __future__ import annotations

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext


PORTAL_ROLE_KEYS = frozenset({"customer_user", "subcontractor_user", "employee_user"})

# Internal CRM APIs remain tenant-internal. Future customer-portal work must use
# dedicated read models with explicit customer-scoped associations and privacy rules.
CUSTOMER_PORTAL_PRIVACY_BOUNDARY = (
    "Customer-scoped portal users must not consume internal CRM master-data APIs directly. "
    "Portal-facing views must be released through dedicated read models and hide personal names by default "
    "unless the tenant explicitly approves their disclosure."
)


def enforce_customer_module_access(
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
            "customers.authorization.portal_forbidden",
            "errors.customers.authorization.portal_forbidden",
            {"privacy_boundary": CUSTOMER_PORTAL_PRIVACY_BOUNDARY},
        )
    if not any(scope.scope_type == "tenant" for scope in actor.scopes):
        raise ApiException(
            403,
            "customers.authorization.internal_scope_required",
            "errors.customers.authorization.internal_scope_required",
            {"tenant_id": tenant_id},
        )

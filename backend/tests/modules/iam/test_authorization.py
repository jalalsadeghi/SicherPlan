from __future__ import annotations

import unittest

from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import (
    RequestAuthorizationContext,
    enforce_permission,
    enforce_scope,
)


def _context(
    *,
    tenant_id: str = "tenant-1",
    role_keys: tuple[str, ...],
    permission_keys: tuple[str, ...],
    scopes: tuple[AuthenticatedRoleScope, ...],
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permission_keys),
        scopes=scopes,
    )


class TestAuthorizationHelpers(unittest.TestCase):
    def test_permission_denies_by_default(self) -> None:
        context = _context(
            role_keys=("tenant_admin",),
            permission_keys=(),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )

        with self.assertRaises(ApiException) as raised:
            enforce_permission(context, "core.admin.tenant.read")

        self.assertEqual(raised.exception.code, "iam.authorization.permission_denied")

    def test_tenant_scope_blocks_cross_tenant_access(self) -> None:
        context = _context(
            role_keys=("tenant_admin",),
            permission_keys=("core.admin.tenant.read",),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )

        with self.assertRaises(ApiException) as raised:
            enforce_scope(context, scope="tenant", tenant_id="tenant-2")

        self.assertEqual(raised.exception.code, "iam.authorization.scope_denied")

    def test_platform_scope_requires_platform_admin_role(self) -> None:
        tenant_context = _context(
            role_keys=("tenant_admin",),
            permission_keys=("core.admin.tenant.create",),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )
        platform_context = _context(
            role_keys=("platform_admin",),
            permission_keys=("core.admin.tenant.create",),
            scopes=(AuthenticatedRoleScope(role_key="platform_admin", scope_type="tenant"),),
        )

        with self.assertRaises(ApiException):
            enforce_scope(tenant_context, scope="platform")

        enforce_scope(platform_context, scope="platform")

    def test_branch_scope_allows_only_matching_branch(self) -> None:
        context = _context(
            role_keys=("dispatcher",),
            permission_keys=("planning.shift.read",),
            scopes=(AuthenticatedRoleScope(role_key="dispatcher", scope_type="branch", branch_id="branch-1"),),
        )

        enforce_scope(context, scope="branch", tenant_id="tenant-1", branch_id="branch-1")

        with self.assertRaises(ApiException):
            enforce_scope(context, scope="branch", tenant_id="tenant-1", branch_id="branch-2")

    def test_mandate_scope_allows_only_matching_mandate(self) -> None:
        context = _context(
            role_keys=("dispatcher",),
            permission_keys=("planning.shift.read",),
            scopes=(AuthenticatedRoleScope(role_key="dispatcher", scope_type="mandate", mandate_id="mandate-1"),),
        )

        enforce_scope(context, scope="mandate", tenant_id="tenant-1", mandate_id="mandate-1")

        with self.assertRaises(ApiException):
            enforce_scope(context, scope="mandate", tenant_id="tenant-1", mandate_id="mandate-2")

    def test_tenant_scope_extends_to_branch_and_mandate_routes(self) -> None:
        context = _context(
            role_keys=("tenant_admin",),
            permission_keys=("core.admin.branch.read", "core.admin.mandate.read"),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )

        enforce_scope(context, scope="branch", tenant_id="tenant-1", branch_id="branch-1")
        enforce_scope(context, scope="mandate", tenant_id="tenant-1", mandate_id="mandate-1")

    def test_customer_scope_allows_only_matching_customer(self) -> None:
        context = _context(
            role_keys=("customer_user",),
            permission_keys=("portal.customer.access",),
            scopes=(AuthenticatedRoleScope(role_key="customer_user", scope_type="customer", customer_id="customer-1"),),
        )

        enforce_scope(context, scope="customer", tenant_id="tenant-1", request_customer_id="customer-1")

        with self.assertRaises(ApiException):
            enforce_scope(context, scope="customer", tenant_id="tenant-1", request_customer_id="customer-2")

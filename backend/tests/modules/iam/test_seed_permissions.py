from __future__ import annotations

import unittest

from app.modules.iam.models import Permission, Role, RolePermission
from app.modules.iam.seed_permissions import PERMISSIONS, ROLES, seed_iam_catalog


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN201
        return self.value


class _FakeSession:
    def __init__(self) -> None:
        self.permissions: list[Permission] = []
        self.roles: list[Role] = []
        self.role_permissions: list[RolePermission] = []

    def add(self, row) -> None:  # noqa: ANN001
        if isinstance(row, Permission):
            if row.id is None:
                row.id = f"permission-{len(self.permissions) + 1}"
            self.permissions.append(row)
            return
        if isinstance(row, Role):
            if row.id is None:
                row.id = f"role-{len(self.roles) + 1}"
            self.roles.append(row)
            return
        if isinstance(row, RolePermission):
            self.role_permissions.append(row)
            return
        raise AssertionError(f"Unexpected row type: {type(row)!r}")

    def flush(self) -> None:
        return None

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        params = compiled.params
        if len(params) == 1:
            key = next(iter(params.values()))
            for row in [*self.permissions, *self.roles]:
                if getattr(row, "key", None) == key:
                    return _FakeScalarResult(row)
            return _FakeScalarResult(None)
        raise AssertionError(f"Unexpected query shape: {params}")

    def get(self, model, identity):  # noqa: ANN001
        if model is not RolePermission:
            raise AssertionError(f"Unexpected model lookup: {model!r}")
        for row in self.role_permissions:
            if row.role_id == identity["role_id"] and row.permission_id == identity["permission_id"]:
                return row
        return None


class TestSeedIamCatalog(unittest.TestCase):
    def test_seed_iam_catalog_is_idempotent(self) -> None:
        session = _FakeSession()

        first = seed_iam_catalog(session)
        second = seed_iam_catalog(session)

        self.assertEqual(first["permissions_inserted"], len(PERMISSIONS))
        self.assertEqual(first["roles_inserted"], len(ROLES))
        self.assertGreater(first["role_permissions_inserted"], 0)
        self.assertEqual(second["permissions_inserted"], 0)
        self.assertEqual(second["roles_inserted"], 0)
        self.assertEqual(second["role_permissions_inserted"], 0)

    def test_seed_builds_stable_permission_keys_by_module_and_action(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        permission_keys = {permission.key: (permission.module, permission.action) for permission in session.permissions}
        self.assertEqual(permission_keys["core.admin.tenant.write"], ("core_admin", "tenant_write"))
        self.assertEqual(permission_keys["core.admin.branch.read"], ("core_admin", "branch_read"))
        self.assertEqual(permission_keys["customers.billing.read"], ("customers", "billing_read"))
        self.assertEqual(permission_keys["customers.portal_access.read"], ("customers", "portal_access_read"))
        self.assertEqual(permission_keys["employees.private.write"], ("employees", "private_write"))
        self.assertEqual(permission_keys["portal.customer.access"], ("portal_customer", "access"))
        self.assertEqual(permission_keys["assistant.chat.access"], ("assistant", "chat_access"))
        self.assertEqual(permission_keys["assistant.diagnostics.read"], ("assistant", "diagnostics_read"))
        self.assertEqual(permission_keys["assistant.feedback.write"], ("assistant", "feedback_write"))
        self.assertEqual(permission_keys["assistant.knowledge.read"], ("assistant", "knowledge_read"))
        self.assertEqual(permission_keys["assistant.knowledge.reindex"], ("assistant", "knowledge_reindex"))
        self.assertEqual(permission_keys["assistant.admin"], ("assistant", "admin"))

    def test_seed_includes_all_assistant_permissions(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        permission_keys = {permission.key for permission in session.permissions}
        self.assertTrue(
            {
                "assistant.chat.access",
                "assistant.diagnostics.read",
                "assistant.feedback.write",
                "assistant.knowledge.read",
                "assistant.knowledge.reindex",
                "assistant.admin",
            }.issubset(permission_keys)
        )

    def test_role_catalog_includes_internal_and_portal_roles(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        self.assertFalse(roles["tenant_admin"].is_portal_role)
        self.assertTrue(roles["customer_user"].is_portal_role)
        self.assertIn("employee_user", roles)

    def test_tenant_admin_seed_includes_employee_write_permission(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        permissions = {permission.key: permission for permission in session.permissions}
        tenant_admin = roles["tenant_admin"]
        employee_write = permissions["employees.employee.write"]

        self.assertTrue(
            any(
                row.role_id == tenant_admin.id and row.permission_id == employee_write.id
                for row in session.role_permissions
            )
        )

    def test_tenant_admin_seed_includes_customer_portal_access_permissions(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        permissions = {permission.key: permission for permission in session.permissions}
        tenant_admin = roles["tenant_admin"]
        portal_access_read = permissions["customers.portal_access.read"]
        portal_access_write = permissions["customers.portal_access.write"]

        self.assertTrue(
            any(
                row.role_id == tenant_admin.id and row.permission_id == portal_access_read.id
                for row in session.role_permissions
            )
        )
        self.assertTrue(
            any(
                row.role_id == tenant_admin.id and row.permission_id == portal_access_write.id
                for row in session.role_permissions
            )
        )

    def test_assistant_chat_access_is_granted_to_internal_and_portal_roles(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        permissions = {permission.key: permission for permission in session.permissions}
        assistant_chat = permissions["assistant.chat.access"]

        for role_key in (
            "platform_admin",
            "tenant_admin",
            "dispatcher",
            "accounting",
            "controller_qm",
            "customer_user",
            "subcontractor_user",
            "employee_user",
        ):
            role = roles[role_key]
            self.assertTrue(
                any(
                    row.role_id == role.id and row.permission_id == assistant_chat.id
                    for row in session.role_permissions
                ),
                role_key,
            )

    def test_assistant_diagnostics_read_is_not_granted_to_portal_roles(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        permissions = {permission.key: permission for permission in session.permissions}
        diagnostics_read = permissions["assistant.diagnostics.read"]

        for role_key in ("customer_user", "subcontractor_user", "employee_user"):
            role = roles[role_key]
            self.assertFalse(
                any(
                    row.role_id == role.id and row.permission_id == diagnostics_read.id
                    for row in session.role_permissions
                ),
                role_key,
            )

    def test_assistant_reindex_and_admin_are_restricted_to_platform_admin(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        permissions = {permission.key: permission for permission in session.permissions}
        reindex = permissions["assistant.knowledge.reindex"]
        assistant_admin = permissions["assistant.admin"]

        platform_admin = roles["platform_admin"]
        self.assertTrue(
            any(
                row.role_id == platform_admin.id and row.permission_id == reindex.id
                for row in session.role_permissions
            )
        )
        self.assertTrue(
            any(
                row.role_id == platform_admin.id and row.permission_id == assistant_admin.id
                for row in session.role_permissions
            )
        )

        for role_key in (
            "tenant_admin",
            "dispatcher",
            "accounting",
            "controller_qm",
            "customer_user",
            "subcontractor_user",
            "employee_user",
        ):
            role = roles[role_key]
            self.assertFalse(
                any(
                    row.role_id == role.id and row.permission_id == reindex.id
                    for row in session.role_permissions
                ),
                f"{role_key}:reindex",
            )
            self.assertFalse(
                any(
                    row.role_id == role.id and row.permission_id == assistant_admin.id
                    for row in session.role_permissions
                ),
                f"{role_key}:admin",
            )


if __name__ == "__main__":
    unittest.main()

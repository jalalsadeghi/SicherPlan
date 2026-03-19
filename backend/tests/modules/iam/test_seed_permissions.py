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
        self.assertEqual(permission_keys["portal.customer.access"], ("portal_customer", "access"))

    def test_role_catalog_includes_internal_and_portal_roles(self) -> None:
        session = _FakeSession()
        seed_iam_catalog(session)

        roles = {role.key: role for role in session.roles}
        self.assertFalse(roles["tenant_admin"].is_portal_role)
        self.assertTrue(roles["customer_user"].is_portal_role)
        self.assertIn("employee_user", roles)


if __name__ == "__main__":
    unittest.main()

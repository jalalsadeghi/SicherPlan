from __future__ import annotations

import unittest
from dataclasses import dataclass
from uuid import uuid4

from app.modules.iam.bootstrap_admin import (
    SystemAdminBootstrapConfig,
    SystemAdminBootstrapper,
)


@dataclass
class FakeTenant:
    id: str
    code: str
    name: str
    legal_name: str | None = None
    default_locale: str = "de"
    timezone: str = "Europe/Berlin"


@dataclass
class FakeRole:
    id: str
    key: str


@dataclass
class FakeUser:
    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    password_hash: str
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    is_platform_user: bool = False
    is_password_login_enabled: bool = True
    status: str = "active"
    archived_at: str | None = None
    version_no: int = 1


@dataclass
class FakeAssignment:
    id: str
    tenant_id: str
    user_account_id: str
    role_id: str
    scope_type: str
    status: str = "active"
    archived_at: str | None = None
    version_no: int = 1


class FakeBootstrapRepository:
    def __init__(self) -> None:
        self.tenants: dict[str, FakeTenant] = {}
        self.role = FakeRole(id=str(uuid4()), key="platform_admin")
        self.users: dict[str, FakeUser] = {}
        self.assignments: dict[tuple[str, str, str], FakeAssignment] = {}

    def get_tenant_by_code(self, code: str):
        return self.tenants.get(code)

    def create_tenant(self, tenant):
        fake = FakeTenant(
            id=str(uuid4()),
            code=tenant.code,
            name=tenant.name,
            legal_name=tenant.legal_name,
            default_locale=tenant.default_locale,
            timezone=tenant.timezone,
        )
        self.tenants[fake.code] = fake
        return fake

    def get_role_by_key(self, key: str):
        if key == self.role.key:
            return self.role
        return None

    def find_user_for_tenant(self, tenant_id: str, *, username: str, email: str):
        for user in self.users.values():
            if user.tenant_id == tenant_id and (user.username == username or user.email == email):
                return user
        return None

    def save_user(self, user):
        fake = user
        if not getattr(fake, "id", None):
            fake.id = str(uuid4())
        self.users[fake.id] = fake
        return fake

    def get_role_assignment(self, user_id: str, role_id: str, tenant_id: str):
        return self.assignments.get((user_id, role_id, tenant_id))

    def save_role_assignment(self, assignment):
        fake = assignment
        if not getattr(fake, "id", None):
            fake.id = str(uuid4())
        self.assignments[(fake.user_account_id, fake.role_id, fake.tenant_id)] = fake
        return fake


class TestBootstrapSystemAdmin(unittest.TestCase):
    def test_bootstrap_creates_tenant_user_and_assignment(self) -> None:
        repository = FakeBootstrapRepository()
        summary = SystemAdminBootstrapper(repository).bootstrap()

        self.assertTrue(summary.tenant_created)
        self.assertTrue(summary.user_created)
        self.assertTrue(summary.role_assignment_created)
        self.assertEqual(summary.tenant_code, "system")
        self.assertEqual(summary.username, "sysadmin")

    def test_bootstrap_is_idempotent_and_reactivates_existing_user(self) -> None:
        repository = FakeBootstrapRepository()
        config = SystemAdminBootstrapConfig(password="Secret123!")
        first = SystemAdminBootstrapper(repository).bootstrap(config)
        self.assertTrue(first.user_created)

        tenant = repository.get_tenant_by_code(config.tenant_code)
        assert tenant is not None
        user = repository.find_user_for_tenant(tenant.id, username=config.username, email=config.email)
        assert user is not None
        user.status = "inactive"
        user.archived_at = "2025-01-01T00:00:00Z"
        user.is_platform_user = False
        user.version_no = 3

        second = SystemAdminBootstrapper(repository).bootstrap(config)
        self.assertFalse(second.tenant_created)
        self.assertFalse(second.user_created)
        self.assertTrue(second.user_updated)
        self.assertEqual(user.status, "active")
        self.assertIsNone(user.archived_at)
        self.assertTrue(user.is_platform_user)


if __name__ == "__main__":
    unittest.main()

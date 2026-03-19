"""Bootstrap a local system administrator for development environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.core.models import Tenant
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.iam.security import hash_password


@dataclass(frozen=True, slots=True)
class SystemAdminBootstrapConfig:
    tenant_code: str = "system"
    tenant_name: str = "SicherPlan System"
    username: str = "sysadmin"
    email: str = "sysadmin@local.sicherplan.invalid"
    full_name: str = "System Administrator"
    password: str = "SicherPlanAdmin!123"
    locale: str = "de"
    timezone: str = "Europe/Berlin"


@dataclass(frozen=True, slots=True)
class SystemAdminBootstrapSummary:
    tenant_created: bool
    user_created: bool
    user_updated: bool
    role_assignment_created: bool
    tenant_code: str
    username: str
    email: str
    password: str


class SystemAdminBootstrapRepository(Protocol):
    def get_tenant_by_code(self, code: str) -> Tenant | None: ...
    def create_tenant(self, tenant: Tenant) -> Tenant: ...
    def get_role_by_key(self, key: str) -> Role | None: ...
    def find_user_for_tenant(self, tenant_id: str, *, username: str, email: str) -> UserAccount | None: ...
    def save_user(self, user: UserAccount) -> UserAccount: ...
    def get_role_assignment(self, user_id: str, role_id: str, tenant_id: str) -> UserRoleAssignment | None: ...
    def save_role_assignment(self, assignment: UserRoleAssignment) -> UserRoleAssignment: ...


class SystemAdminBootstrapper:
    def __init__(self, repository: SystemAdminBootstrapRepository) -> None:
        self.repository = repository

    def bootstrap(
        self,
        config: SystemAdminBootstrapConfig = SystemAdminBootstrapConfig(),
    ) -> SystemAdminBootstrapSummary:
        tenant = self.repository.get_tenant_by_code(config.tenant_code)
        tenant_created = tenant is None
        if tenant is None:
            tenant = self.repository.create_tenant(
                Tenant(
                    code=config.tenant_code,
                    name=config.tenant_name,
                    legal_name=config.tenant_name,
                    default_locale=config.locale,
                    timezone=config.timezone,
                )
            )

        role = self.repository.get_role_by_key("platform_admin")
        if role is None:
            raise RuntimeError("platform_admin role is missing. Run IAM catalog seeding first.")

        user = self.repository.find_user_for_tenant(
            tenant.id,
            username=config.username,
            email=config.email,
        )
        user_created = user is None
        user_updated = False
        password_hash = hash_password(config.password)
        if user is None:
            user = self.repository.save_user(
                UserAccount(
                    tenant_id=tenant.id,
                    username=config.username,
                    email=config.email,
                    full_name=config.full_name,
                    password_hash=password_hash,
                    locale=config.locale,
                    timezone=config.timezone,
                    is_platform_user=True,
                    is_password_login_enabled=True,
                )
            )
        else:
            changed = False
            for field_name, value in (
                ("username", config.username),
                ("email", config.email),
                ("full_name", config.full_name),
                ("password_hash", password_hash),
                ("locale", config.locale),
                ("timezone", config.timezone),
                ("is_platform_user", True),
                ("is_password_login_enabled", True),
                ("status", "active"),
                ("archived_at", None),
            ):
                if getattr(user, field_name) != value:
                    setattr(user, field_name, value)
                    changed = True
            if changed:
                user.version_no += 1
                user = self.repository.save_user(user)
                user_updated = True

        assignment = self.repository.get_role_assignment(user.id, role.id, tenant.id)
        role_assignment_created = assignment is None
        if assignment is None:
            self.repository.save_role_assignment(
                UserRoleAssignment(
                    tenant_id=tenant.id,
                    user_account_id=user.id,
                    role_id=role.id,
                    scope_type="tenant",
                )
            )
        elif assignment.status != "active" or assignment.archived_at is not None:
            assignment.status = "active"
            assignment.archived_at = None
            assignment.version_no = (assignment.version_no or 0) + 1
            self.repository.save_role_assignment(assignment)

        return SystemAdminBootstrapSummary(
            tenant_created=tenant_created,
            user_created=user_created,
            user_updated=user_updated,
            role_assignment_created=role_assignment_created,
            tenant_code=config.tenant_code,
            username=config.username,
            email=config.email,
            password=config.password,
        )

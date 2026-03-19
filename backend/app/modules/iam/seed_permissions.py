"""Bootstrap the baseline IAM role and permission catalog."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.iam.models import Permission, Role, RolePermission


@dataclass(frozen=True, slots=True)
class PermissionSeed:
    key: str
    module: str
    action: str
    description: str


@dataclass(frozen=True, slots=True)
class RoleSeed:
    key: str
    name: str
    description: str
    is_portal_role: bool
    permission_keys: tuple[str, ...]


PERMISSIONS: tuple[PermissionSeed, ...] = (
    PermissionSeed("core.admin.access", "core_admin", "access", "Access the core administration workspace."),
    PermissionSeed("core.admin.tenant.read", "core_admin", "tenant_read", "Read tenant records."),
    PermissionSeed("core.admin.tenant.write", "core_admin", "tenant_write", "Update tenant records."),
    PermissionSeed("core.admin.tenant.create", "core_admin", "tenant_create", "Create tenants."),
    PermissionSeed("core.admin.branch.read", "core_admin", "branch_read", "Read branch records."),
    PermissionSeed("core.admin.branch.write", "core_admin", "branch_write", "Create and update branch records."),
    PermissionSeed("core.admin.mandate.read", "core_admin", "mandate_read", "Read mandate records."),
    PermissionSeed("core.admin.mandate.write", "core_admin", "mandate_write", "Create and update mandate records."),
    PermissionSeed("core.admin.setting.read", "core_admin", "setting_read", "Read tenant settings."),
    PermissionSeed("core.admin.setting.write", "core_admin", "setting_write", "Create and update tenant settings."),
    PermissionSeed("platform.docs.read", "platform_docs", "read", "Read tenant-scoped documents and versions."),
    PermissionSeed("platform.docs.write", "platform_docs", "write", "Create tenant-scoped documents and links."),
    PermissionSeed("platform.comm.read", "platform_comm", "read", "Read tenant-scoped communication records."),
    PermissionSeed("platform.comm.write", "platform_comm", "write", "Manage templates and queue outbound messages."),
    PermissionSeed("platform.info.read", "platform_info", "read", "Read tenant-scoped notices and acknowledgements."),
    PermissionSeed("platform.info.write", "platform_info", "write", "Author and publish tenant-scoped notices."),
    PermissionSeed("platform.integration.read", "platform_integration", "read", "Read integration endpoints, jobs, and outbox state."),
    PermissionSeed("platform.integration.write", "platform_integration", "write", "Manage integration endpoints, jobs, and outbox publication."),
    PermissionSeed("platform.admin.access", "platform", "admin_access", "Access platform-level administration."),
    PermissionSeed("portal.customer.access", "portal_customer", "access", "Access customer portal surfaces."),
    PermissionSeed(
        "portal.subcontractor.access",
        "portal_subcontractor",
        "access",
        "Access subcontractor portal surfaces.",
    ),
    PermissionSeed("portal.employee.access", "portal_employee", "access", "Access employee mobile or portal surfaces."),
)


ROLES: tuple[RoleSeed, ...] = (
    RoleSeed(
        "platform_admin",
        "Platform Administrator",
        "Platform-wide administrator with tenant backbone and platform setup access.",
        False,
        (
            "platform.admin.access",
            "core.admin.access",
            "core.admin.tenant.read",
            "core.admin.tenant.write",
            "core.admin.tenant.create",
            "core.admin.branch.read",
            "core.admin.branch.write",
            "core.admin.mandate.read",
            "core.admin.mandate.write",
            "core.admin.setting.read",
            "core.admin.setting.write",
            "platform.docs.read",
            "platform.docs.write",
            "platform.comm.read",
            "platform.comm.write",
            "platform.info.read",
            "platform.info.write",
            "platform.integration.read",
            "platform.integration.write",
        ),
    ),
    RoleSeed(
        "tenant_admin",
        "Tenant Administrator",
        "Tenant-scoped administrator for core backbone maintenance.",
        False,
        (
            "core.admin.access",
            "core.admin.tenant.read",
            "core.admin.tenant.write",
            "core.admin.branch.read",
            "core.admin.branch.write",
            "core.admin.mandate.read",
            "core.admin.mandate.write",
            "core.admin.setting.read",
            "core.admin.setting.write",
            "platform.docs.read",
            "platform.docs.write",
            "platform.comm.read",
            "platform.comm.write",
            "platform.info.read",
            "platform.info.write",
            "platform.integration.read",
            "platform.integration.write",
        ),
    ),
    RoleSeed(
        "dispatcher",
        "Dispatcher",
        "Operational planning role with later planning and field access.",
        False,
        ("platform.info.read", "platform.integration.read"),
    ),
    RoleSeed(
        "accounting",
        "Accounting",
        "Finance-oriented role with later finance module access.",
        False,
        ("platform.info.read", "platform.integration.read"),
    ),
    RoleSeed(
        "controller_qm",
        "Controlling / QA",
        "Controlling and quality role with later reporting and compliance access.",
        False,
        ("platform.info.read", "platform.info.write", "platform.integration.read"),
    ),
    RoleSeed(
        "customer_user",
        "Customer Portal User",
        "Tenant-scoped external customer actor.",
        True,
        ("portal.customer.access", "platform.info.read"),
    ),
    RoleSeed(
        "subcontractor_user",
        "Subcontractor Portal User",
        "Tenant-scoped external subcontractor actor.",
        True,
        ("portal.subcontractor.access", "platform.info.read"),
    ),
    RoleSeed(
        "employee_user",
        "Employee User",
        "Tenant-scoped employee actor for mobile and portal surfaces.",
        True,
        ("portal.employee.access", "platform.info.read"),
    ),
)


def seed_iam_catalog(session: Session, actor_user_id: str | None = None) -> dict[str, int]:
    permission_map: dict[str, Permission] = {}
    role_map: dict[str, Role] = {}
    stats = {
        "permissions_inserted": 0,
        "permissions_updated": 0,
        "roles_inserted": 0,
        "roles_updated": 0,
        "role_permissions_inserted": 0,
    }

    for seed in PERMISSIONS:
        permission = session.scalars(select(Permission).where(Permission.key == seed.key)).one_or_none()
        if permission is None:
            permission = Permission(
                key=seed.key,
                module=seed.module,
                action=seed.action,
                description=seed.description,
            )
            session.add(permission)
            stats["permissions_inserted"] += 1
        else:
            changed = False
            if permission.module != seed.module:
                permission.module = seed.module
                changed = True
            if permission.action != seed.action:
                permission.action = seed.action
                changed = True
            if permission.description != seed.description:
                permission.description = seed.description
                changed = True
            if changed:
                stats["permissions_updated"] += 1
        permission_map[seed.key] = permission

    session.flush()

    for seed in ROLES:
        role = session.scalars(select(Role).where(Role.key == seed.key)).one_or_none()
        if role is None:
            role = Role(
                key=seed.key,
                name=seed.name,
                description=seed.description,
                is_portal_role=seed.is_portal_role,
                is_system_role=True,
                created_by_user_id=actor_user_id,
                updated_by_user_id=actor_user_id,
            )
            session.add(role)
            stats["roles_inserted"] += 1
        else:
            changed = False
            if role.name != seed.name:
                role.name = seed.name
                changed = True
            if role.description != seed.description:
                role.description = seed.description
                changed = True
            if role.is_portal_role != seed.is_portal_role:
                role.is_portal_role = seed.is_portal_role
                changed = True
            if changed:
                role.updated_by_user_id = actor_user_id
                role.version_no += 1
                stats["roles_updated"] += 1
        role_map[seed.key] = role

    session.flush()

    for seed in ROLES:
        role = role_map[seed.key]
        for permission_key in seed.permission_keys:
            permission = permission_map[permission_key]
            existing = session.get(
                RolePermission,
                {"role_id": role.id, "permission_id": permission.id},
            )
            if existing is None:
                session.add(RolePermission(role_id=role.id, permission_id=permission.id))
                stats["role_permissions_inserted"] += 1

    return stats

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
    PermissionSeed("customers.customer.read", "customers", "customer_read", "Read tenant-scoped customer master records."),
    PermissionSeed("customers.customer.write", "customers", "customer_write", "Create and update tenant-scoped customer master records."),
    PermissionSeed("customers.billing.read", "customers", "billing_read", "Read customer commercial and billing settings."),
    PermissionSeed("customers.billing.write", "customers", "billing_write", "Create and update customer commercial and billing settings."),
    PermissionSeed("recruiting.applicant.read", "recruiting", "applicant_read", "Read tenant-scoped applicant records and workflow state."),
    PermissionSeed("recruiting.applicant.write", "recruiting", "applicant_write", "Transition applicants and add recruiting workflow activity."),
    PermissionSeed("employees.employee.read", "employees", "employee_read", "Read operational employee master records."),
    PermissionSeed("employees.employee.write", "employees", "employee_write", "Create and update operational employee master records."),
    PermissionSeed("employees.private.read", "employees", "private_read", "Read HR-private employee profile and address data."),
    PermissionSeed("employees.private.write", "employees", "private_write", "Create and update HR-private employee profile and address data."),
    PermissionSeed("planning.ops.read", "planning", "ops_read", "Read operational planning master records."),
    PermissionSeed("planning.ops.write", "planning", "ops_write", "Create and update operational planning master records."),
    PermissionSeed("planning.order.read", "planning", "order_read", "Read planning customer orders and attachments."),
    PermissionSeed("planning.order.write", "planning", "order_write", "Create and update planning customer orders and attachments."),
    PermissionSeed("planning.record.read", "planning", "record_read", "Read planning records and release context."),
    PermissionSeed("planning.record.write", "planning", "record_write", "Create and update planning records and release context."),
    PermissionSeed("planning.shift.read", "planning", "shift_read", "Read shift plans, templates, series, and concrete shifts."),
    PermissionSeed("planning.shift.write", "planning", "shift_write", "Create and update shift plans, templates, series, and concrete shifts."),
    PermissionSeed("planning.staffing.read", "planning", "staffing_read", "Read planning staffing, releases, and coverage."),
    PermissionSeed("planning.staffing.write", "planning", "staffing_write", "Create and update planning staffing, releases, and coverage."),
    PermissionSeed("planning.staffing.override", "planning", "staffing_override", "Record append-only validation overrides for planning staffing."),
    PermissionSeed("field.watchbook.read", "field_execution", "watchbook_read", "Read watchbooks, entries, and generated outputs."),
    PermissionSeed("field.watchbook.write", "field_execution", "watchbook_write", "Create watchbooks and append watchbook entries."),
    PermissionSeed("field.watchbook.review", "field_execution", "watchbook_review", "Review, close, release, and generate outputs for watchbooks."),
    PermissionSeed("field.attendance.read", "field_execution", "attendance_read", "Read derived attendance summaries and discrepancy context."),
    PermissionSeed("field.attendance.write", "field_execution", "attendance_write", "Derive and refresh attendance summaries from raw time evidence."),
    PermissionSeed("field.time_capture.read", "field_execution", "time_capture_read", "Read time-capture devices, policies, and raw time events."),
    PermissionSeed("field.time_capture.write", "field_execution", "time_capture_write", "Manage time-capture devices, policies, and raw ingest configuration."),
    PermissionSeed("field.patrol.read", "field_execution", "patrol_read", "Read patrol routes, rounds, evaluations, and evidence."),
    PermissionSeed("field.patrol.write", "field_execution", "patrol_write", "Start, capture, complete, abort, and sync patrol rounds."),
    PermissionSeed("finance.actual.read", "finance", "actual_read", "Read finance-owned actual bridge records and discrepancy context."),
    PermissionSeed("finance.actual.write", "finance", "actual_write", "Derive and refresh finance-owned actual bridge records."),
    PermissionSeed("finance.approval.write", "finance", "approval_write", "Submit and operationally confirm staged actual approvals."),
    PermissionSeed("finance.approval.signoff", "finance", "approval_signoff", "Record final finance signoff for staged actual approvals."),
    PermissionSeed("finance.billing.read", "finance", "billing_read", "Read customer timesheets, invoices, and billing release context."),
    PermissionSeed("finance.billing.write", "finance", "billing_write", "Generate and release customer timesheets and invoices."),
    PermissionSeed("finance.billing.delivery", "finance", "billing_delivery", "Queue invoice delivery and update billing dispatch context."),
    PermissionSeed("finance.subcontractor_control.read", "finance", "subcontractor_control_read", "Read subcontractor invoice checks, approved basis, and control variance context."),
    PermissionSeed("finance.subcontractor_control.write", "finance", "subcontractor_control_write", "Generate, review, note, approve, and release subcontractor invoice checks."),
    PermissionSeed("finance.payroll.read", "finance", "payroll_read", "Read payroll tariffs, pay profiles, export batches, archives, and reconciliation outputs."),
    PermissionSeed("finance.payroll.write", "finance", "payroll_write", "Maintain payroll tariffs, pay profiles, and payslip archive records."),
    PermissionSeed("finance.payroll.export", "finance", "payroll_export", "Generate payroll export batches and queue outbound payroll delivery."),
    PermissionSeed("reporting.read", "reporting", "read", "Read tenant-scoped reporting views and reporting APIs."),
    PermissionSeed("reporting.export", "reporting", "export", "Download tenant-scoped reporting exports."),
    PermissionSeed("subcontractors.company.read", "subcontractors", "company_read", "Read tenant-scoped subcontractor company master records."),
    PermissionSeed("subcontractors.company.write", "subcontractors", "company_write", "Create and update tenant-scoped subcontractor company master records."),
    PermissionSeed("subcontractors.finance.read", "subcontractors", "finance_read", "Read subcontractor commercial and finance settings."),
    PermissionSeed("subcontractors.finance.write", "subcontractors", "finance_write", "Create and update subcontractor commercial and finance settings."),
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
            "customers.customer.read",
            "customers.customer.write",
            "customers.billing.read",
            "customers.billing.write",
            "recruiting.applicant.read",
            "recruiting.applicant.write",
            "employees.employee.read",
            "employees.employee.write",
            "employees.private.read",
            "employees.private.write",
            "planning.ops.read",
            "planning.ops.write",
            "planning.order.read",
            "planning.order.write",
            "planning.record.read",
            "planning.record.write",
            "planning.shift.read",
            "planning.shift.write",
            "planning.staffing.read",
            "planning.staffing.write",
            "planning.staffing.override",
            "field.watchbook.read",
            "field.watchbook.write",
            "field.watchbook.review",
            "field.attendance.read",
            "field.attendance.write",
            "field.time_capture.read",
            "field.time_capture.write",
            "field.patrol.read",
            "field.patrol.write",
            "finance.actual.read",
            "finance.actual.write",
            "finance.approval.write",
            "finance.approval.signoff",
            "finance.billing.read",
            "finance.billing.write",
            "finance.billing.delivery",
            "finance.subcontractor_control.read",
            "finance.subcontractor_control.write",
            "finance.payroll.read",
            "finance.payroll.write",
            "finance.payroll.export",
            "reporting.read",
            "reporting.export",
            "subcontractors.company.read",
            "subcontractors.company.write",
            "subcontractors.finance.read",
            "subcontractors.finance.write",
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
            "customers.customer.read",
            "customers.customer.write",
            "customers.billing.read",
            "customers.billing.write",
            "recruiting.applicant.read",
            "recruiting.applicant.write",
            "employees.employee.read",
            "employees.employee.write",
            "employees.private.read",
            "employees.private.write",
            "planning.ops.read",
            "planning.ops.write",
            "planning.order.read",
            "planning.order.write",
            "planning.record.read",
            "planning.record.write",
            "planning.shift.read",
            "planning.shift.write",
            "planning.staffing.read",
            "planning.staffing.write",
            "planning.staffing.override",
            "field.watchbook.read",
            "field.watchbook.write",
            "field.watchbook.review",
            "field.attendance.read",
            "field.attendance.write",
            "field.time_capture.read",
            "field.time_capture.write",
            "field.patrol.read",
            "field.patrol.write",
            "finance.actual.read",
            "finance.actual.write",
            "finance.approval.write",
            "finance.approval.signoff",
            "finance.billing.read",
            "finance.billing.write",
            "finance.billing.delivery",
            "finance.subcontractor_control.read",
            "finance.subcontractor_control.write",
            "finance.payroll.read",
            "finance.payroll.write",
            "finance.payroll.export",
            "reporting.read",
            "reporting.export",
            "subcontractors.company.read",
            "subcontractors.company.write",
            "subcontractors.finance.read",
            "subcontractors.finance.write",
        ),
    ),
    RoleSeed(
        "dispatcher",
        "Dispatcher",
        "Operational planning role with later planning and field access.",
        False,
        (
            "platform.info.read",
            "platform.integration.read",
            "customers.customer.read",
            "employees.employee.read",
            "planning.ops.read",
            "planning.ops.write",
            "planning.order.read",
            "planning.order.write",
            "planning.record.read",
            "planning.record.write",
            "planning.shift.read",
            "planning.shift.write",
            "planning.staffing.read",
            "planning.staffing.write",
            "planning.staffing.override",
            "field.watchbook.read",
            "field.watchbook.write",
            "field.watchbook.review",
            "field.attendance.read",
            "field.attendance.write",
            "field.time_capture.read",
            "field.time_capture.write",
            "field.patrol.read",
            "field.patrol.write",
            "finance.actual.read",
            "finance.actual.write",
            "finance.approval.write",
            "finance.billing.read",
            "finance.billing.write",
            "finance.subcontractor_control.read",
            "finance.subcontractor_control.write",
            "reporting.read",
            "subcontractors.company.read",
        ),
    ),
    RoleSeed(
        "accounting",
        "Accounting",
        "Finance-oriented role with later finance module access.",
        False,
        (
            "platform.info.read",
            "platform.integration.read",
            "customers.customer.read",
            "customers.billing.read",
            "field.attendance.read",
            "finance.actual.read",
            "finance.actual.write",
            "finance.approval.write",
            "finance.approval.signoff",
            "finance.billing.read",
            "finance.billing.write",
            "finance.billing.delivery",
            "finance.subcontractor_control.read",
            "finance.subcontractor_control.write",
            "finance.payroll.read",
            "finance.payroll.write",
            "finance.payroll.export",
            "reporting.read",
            "reporting.export",
            "subcontractors.company.read",
            "subcontractors.finance.read",
        ),
    ),
    RoleSeed(
        "controller_qm",
        "Controlling / QA",
        "Controlling and quality role with later reporting and compliance access.",
        False,
        (
            "platform.info.read",
            "platform.info.write",
            "platform.integration.read",
            "customers.customer.read",
            "employees.employee.read",
            "field.watchbook.read",
            "field.watchbook.review",
            "field.attendance.read",
            "finance.actual.read",
            "finance.subcontractor_control.read",
            "reporting.read",
            "reporting.export",
            "subcontractors.company.read",
        ),
    ),
    RoleSeed(
        "customer_user",
        "Customer Portal User",
        "Tenant-scoped external customer actor.",
        True,
        ("portal.customer.access", "platform.info.read", "field.watchbook.read"),
    ),
    RoleSeed(
        "subcontractor_user",
        "Subcontractor Portal User",
        "Tenant-scoped external subcontractor actor.",
        True,
        ("portal.subcontractor.access", "platform.info.read", "field.watchbook.read"),
    ),
    RoleSeed(
        "employee_user",
        "Employee User",
        "Tenant-scoped employee actor for mobile and portal surfaces.",
        True,
        ("portal.employee.access", "platform.info.read", "field.watchbook.read", "field.watchbook.write", "field.patrol.read", "field.patrol.write"),
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

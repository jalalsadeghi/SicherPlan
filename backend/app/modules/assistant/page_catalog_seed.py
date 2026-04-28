"""Assistant page route catalog seed data."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assistant.models import AssistantPageRouteCatalog


@dataclass(frozen=True, slots=True)
class AssistantPageRouteSeed:
    page_id: str
    label: str
    route_name: str | None
    path_template: str
    module_key: str
    api_families: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    allowed_role_keys: tuple[str, ...] = ()
    scope_kind: str | None = None
    supports_entity_deep_link: bool = False
    entity_param_map: dict[str, str] | None = None
    active: bool = True


ASSISTANT_PAGE_ROUTE_SEEDS: tuple[AssistantPageRouteSeed, ...] = (
    AssistantPageRouteSeed(
        page_id="F-02",
        label="Dashboard",
        route_name="SicherPlanDashboard",
        path_template="/admin/dashboard",
        module_key="dashboard",
        api_families=("dashboard",),
        allowed_role_keys=("platform_admin", "tenant_admin", "dispatcher", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="F-03",
        label="Current Session / Sessions / Access Codes",
        route_name="SicherPlanTenantUsers",
        path_template="/admin/iam/users",
        module_key="iam",
        api_families=("iam",),
        allowed_role_keys=("platform_admin",),
        scope_kind="platform",
    ),
    AssistantPageRouteSeed(
        page_id="A-02",
        label="Tenants & Core System",
        route_name="SicherPlanCoreAdmin",
        path_template="/admin/core",
        module_key="core",
        api_families=("core",),
        required_permissions=("core.admin.access",),
        allowed_role_keys=("platform_admin", "tenant_admin"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="A-03",
        label="Branch & Mandate Management",
        route_name="SicherPlanCoreAdmin",
        path_template="/admin/core",
        module_key="core",
        api_families=("core",),
        required_permissions=("core.admin.branch.read", "core.admin.mandate.read"),
        allowed_role_keys=("platform_admin", "tenant_admin"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="A-04",
        label="Tenant Settings",
        route_name="SicherPlanCoreAdmin",
        path_template="/admin/core",
        module_key="core",
        api_families=("core",),
        required_permissions=("core.admin.setting.read",),
        allowed_role_keys=("platform_admin", "tenant_admin"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="A-05",
        label="Tenant Users & IAM",
        route_name="SicherPlanTenantUsers",
        path_template="/admin/iam/users",
        module_key="iam",
        api_families=("iam",),
        allowed_role_keys=("platform_admin",),
        scope_kind="platform",
    ),
    AssistantPageRouteSeed(
        page_id="A-06",
        label="Health & Diagnostics",
        route_name="SicherPlanHealthDiagnostics",
        path_template="/admin/health",
        module_key="platform_services",
        api_families=("health", "platform_services"),
        allowed_role_keys=("platform_admin",),
        scope_kind="platform",
    ),
    AssistantPageRouteSeed(
        page_id="PS-01",
        label="Platform Services Workspace",
        route_name="SicherPlanPlatformServices",
        path_template="/admin/platform-services",
        module_key="platform_services",
        api_families=("platform_services",),
        allowed_role_keys=("platform_admin", "tenant_admin", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="C-01",
        label="Customers Workspace",
        route_name="SicherPlanCustomers",
        path_template="/admin/customers",
        module_key="customers",
        api_families=("customers",),
        required_permissions=("customers.customer.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "accounting", "controller_qm"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"customer_id": "customer_id", "tab": "tab"},
    ),
    AssistantPageRouteSeed(
        page_id="C-02",
        label="Customer Order Workspace",
        route_name="SicherPlanCustomerOrderWorkspace",
        path_template="/admin/customers/order-workspace",
        module_key="customers",
        api_families=("customers", "planningOrders", "planningShifts", "platformDocuments"),
        allowed_role_keys=("tenant_admin",),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={
            "customer_id": "customer_id",
            "order_id": "order_id",
            "planning_record_id": "planning_record_id",
            "shift_plan_id": "shift_plan_id",
        },
    ),
    AssistantPageRouteSeed(
        page_id="E-01",
        label="Employees Workspace",
        route_name="SicherPlanEmployees",
        path_template="/admin/employees",
        module_key="employees",
        api_families=("employees",),
        required_permissions=("employees.employee.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"employee_id": "employee_id"},
    ),
    AssistantPageRouteSeed(
        page_id="R-01",
        label="Recruiting Workspace",
        route_name="SicherPlanRecruiting",
        path_template="/admin/recruiting",
        module_key="recruiting",
        api_families=("recruiting",),
        required_permissions=("recruiting.applicant.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="R-02",
        label="Applicant Public Form",
        route_name="SicherPlanApplicantForm",
        path_template="/public/apply/:tenantCode",
        module_key="recruiting",
        api_families=("recruiting",),
        scope_kind="public",
    ),
    AssistantPageRouteSeed(
        page_id="S-01",
        label="Subcontractors Workspace",
        route_name="SicherPlanSubcontractors",
        path_template="/admin/subcontractors",
        module_key="subcontractors",
        api_families=("subcontractors",),
        required_permissions=("subcontractors.company.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"subcontractor_id": "subcontractor_id"},
    ),
    AssistantPageRouteSeed(
        page_id="P-01",
        label="Planning Setup",
        route_name="SicherPlanPlanning",
        path_template="/admin/planning",
        module_key="planning",
        api_families=("planning",),
        required_permissions=("planning.ops.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="P-02",
        label="Orders & Planning Records",
        route_name="SicherPlanPlanningOrders",
        path_template="/admin/planning-orders",
        module_key="planning",
        api_families=("planning",),
        required_permissions=("planning.order.read", "planning.record.read"),
        allowed_role_keys=("tenant_admin", "dispatcher", "accounting", "controller_qm"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"planning_record_id": "planning_record_id", "customer_id": "customer_id", "date": "date"},
    ),
    AssistantPageRouteSeed(
        page_id="P-03",
        label="Shift Planning",
        route_name="SicherPlanPlanningShifts",
        path_template="/admin/planning-shifts",
        module_key="planning",
        api_families=("planning",),
        required_permissions=("planning.shift.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"shift_id": "shift_id", "planning_record_id": "planning_record_id", "date": "date"},
    ),
    AssistantPageRouteSeed(
        page_id="P-04",
        label="Staffing Board & Coverage",
        route_name="SicherPlanPlanningStaffing",
        path_template="/admin/planning-staffing",
        module_key="planning",
        api_families=("planning",),
        required_permissions=("planning.staffing.read",),
        allowed_role_keys=("tenant_admin", "dispatcher"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={
            "shift_id": "shift_id",
            "assignment_id": "assignment_id",
            "planning_record_id": "planning_record_id",
            "date": "date",
        },
    ),
    AssistantPageRouteSeed(
        page_id="P-05",
        label="Dispatch, Outputs & Subcontractor Releases",
        route_name="SicherPlanPlanningStaffing",
        path_template="/admin/planning-staffing",
        module_key="planning",
        api_families=("planning",),
        required_permissions=("planning.staffing.read",),
        allowed_role_keys=("tenant_admin", "dispatcher"),
        scope_kind="tenant",
        supports_entity_deep_link=True,
        entity_param_map={"subcontractor_id": "subcontractor_id", "planning_record_id": "planning_record_id", "date": "date"},
    ),
    AssistantPageRouteSeed(
        page_id="FD-01",
        label="Field Operations Workspace",
        route_name="SicherPlanPlanning",
        path_template="/admin/planning",
        module_key="field_execution",
        api_families=("field_execution",),
        required_permissions=("planning.ops.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="FI-01",
        label="Actuals / Actual-Freigaben Workspace",
        route_name="SicherPlanFinanceActuals",
        path_template="/admin/finance-actuals",
        module_key="finance",
        api_families=("finance",),
        required_permissions=("finance.actual.read",),
        allowed_role_keys=("tenant_admin", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="FI-02",
        label="Billing Workspace",
        route_name="SicherPlanFinanceBilling",
        path_template="/admin/finance-billing",
        module_key="finance",
        api_families=("finance",),
        required_permissions=("finance.billing.read",),
        allowed_role_keys=("tenant_admin", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="FI-03",
        label="Payroll Workspace",
        route_name="SicherPlanFinancePayroll",
        path_template="/admin/finance-payroll",
        module_key="finance",
        api_families=("finance",),
        required_permissions=("finance.payroll.read",),
        allowed_role_keys=("tenant_admin", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="FI-04",
        label="Subcontractor Invoice Checks",
        route_name="SicherPlanFinanceSubcontractorChecks",
        path_template="/admin/finance-subcontractor-checks",
        module_key="finance",
        api_families=("finance",),
        required_permissions=("finance.subcontractor_control.read",),
        allowed_role_keys=("tenant_admin", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="REP-01",
        label="Reporting Hub",
        route_name="SicherPlanReporting",
        path_template="/admin/reporting",
        module_key="reporting",
        api_families=("reporting",),
        required_permissions=("reporting.read",),
        allowed_role_keys=("tenant_admin", "accounting", "controller_qm"),
        scope_kind="tenant",
    ),
    AssistantPageRouteSeed(
        page_id="ES-01",
        label="Employee Self-Service Portal",
        route_name="SicherPlanEmployees",
        path_template="/admin/employees",
        module_key="employee_self_service",
        api_families=("employees", "employee_self_service"),
        required_permissions=("employees.employee.read",),
        allowed_role_keys=("tenant_admin", "dispatcher", "controller_qm"),
        scope_kind="employee_self_service",
        supports_entity_deep_link=True,
        entity_param_map={"employee_id": "employee_id"},
    ),
    AssistantPageRouteSeed(
        page_id="CP-01",
        label="Customer Portal",
        route_name="SicherPlanCustomerPortalOverview",
        path_template="/portal/customer/overview",
        module_key="customer_portal",
        api_families=("portal_customer",),
        required_permissions=("portal.customer.access",),
        allowed_role_keys=("customer_user",),
        scope_kind="customer",
    ),
    AssistantPageRouteSeed(
        page_id="SP-01",
        label="Subcontractor Portal",
        route_name="SicherPlanSubcontractorPortal",
        path_template="/portal/subcontractor",
        module_key="subcontractor_portal",
        api_families=("portal_subcontractor",),
        required_permissions=("portal.subcontractor.access",),
        allowed_role_keys=("subcontractor_user",),
        scope_kind="subcontractor",
    ),
)


def seed_assistant_page_route_catalog(session: Session) -> dict[str, int]:
    inserted = 0
    updated = 0
    for seed in ASSISTANT_PAGE_ROUTE_SEEDS:
        existing = session.scalars(
            select(AssistantPageRouteCatalog).where(
                AssistantPageRouteCatalog.page_id == seed.page_id,
                AssistantPageRouteCatalog.path_template == seed.path_template,
            )
        ).one_or_none()
        if existing is None:
            session.add(
                AssistantPageRouteCatalog(
                    page_id=seed.page_id,
                    label=seed.label,
                    route_name=seed.route_name,
                    path_template=seed.path_template,
                    module_key=seed.module_key,
                    api_families=list(seed.api_families) or None,
                    required_permissions=list(seed.required_permissions) or None,
                    allowed_role_keys=list(seed.allowed_role_keys) or None,
                    scope_kind=seed.scope_kind,
                    supports_entity_deep_link=seed.supports_entity_deep_link,
                    entity_param_map=seed.entity_param_map,
                    active=seed.active,
                )
            )
            inserted += 1
            continue
        changed = False
        changed |= _assign(existing, "label", seed.label)
        changed |= _assign(existing, "route_name", seed.route_name)
        changed |= _assign(existing, "module_key", seed.module_key)
        changed |= _assign(existing, "api_families", list(seed.api_families) or None)
        changed |= _assign(existing, "required_permissions", list(seed.required_permissions) or None)
        changed |= _assign(existing, "allowed_role_keys", list(seed.allowed_role_keys) or None)
        changed |= _assign(existing, "scope_kind", seed.scope_kind)
        changed |= _assign(existing, "supports_entity_deep_link", seed.supports_entity_deep_link)
        changed |= _assign(existing, "entity_param_map", seed.entity_param_map)
        changed |= _assign(existing, "active", seed.active)
        if changed:
            updated += 1
    return {"inserted": inserted, "updated": updated}


def _assign(row: AssistantPageRouteCatalog, field_name: str, value: object) -> bool:
    if getattr(row, field_name) == value:
        return False
    setattr(row, field_name, value)
    return True

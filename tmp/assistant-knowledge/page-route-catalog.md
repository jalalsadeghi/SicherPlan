# Assistant Page Route Catalog

## F-02 Dashboard

- route_name: SicherPlanDashboard
- path_template: /admin/dashboard
- module_key: dashboard
- api_families: dashboard
- required_permissions: none
- allowed_role_keys: platform_admin, tenant_admin, dispatcher, accounting, controller_qm
- scope_kind: tenant

## F-03 Current Session / Sessions / Access Codes

- route_name: SicherPlanTenantUsers
- path_template: /admin/iam/users
- module_key: iam
- api_families: iam
- required_permissions: none
- allowed_role_keys: platform_admin
- scope_kind: platform

## A-02 Tenants & Core System

- route_name: SicherPlanCoreAdmin
- path_template: /admin/core
- module_key: core
- api_families: core
- required_permissions: core.admin.access
- allowed_role_keys: platform_admin, tenant_admin
- scope_kind: tenant

## A-03 Branch & Mandate Management

- route_name: SicherPlanCoreAdmin
- path_template: /admin/core
- module_key: core
- api_families: core
- required_permissions: core.admin.branch.read, core.admin.mandate.read
- allowed_role_keys: platform_admin, tenant_admin
- scope_kind: tenant

## A-04 Tenant Settings

- route_name: SicherPlanCoreAdmin
- path_template: /admin/core
- module_key: core
- api_families: core
- required_permissions: core.admin.setting.read
- allowed_role_keys: platform_admin, tenant_admin
- scope_kind: tenant

## A-05 Tenant Users & IAM

- route_name: SicherPlanTenantUsers
- path_template: /admin/iam/users
- module_key: iam
- api_families: iam
- required_permissions: none
- allowed_role_keys: platform_admin
- scope_kind: platform

## A-06 Health & Diagnostics

- route_name: SicherPlanHealthDiagnostics
- path_template: /admin/health
- module_key: platform_services
- api_families: health, platform_services
- required_permissions: none
- allowed_role_keys: platform_admin
- scope_kind: platform

## PS-01 Platform Services Workspace

- route_name: SicherPlanPlatformServices
- path_template: /admin/platform-services
- module_key: platform_services
- api_families: platform_services
- required_permissions: none
- allowed_role_keys: platform_admin, tenant_admin, controller_qm
- scope_kind: tenant

## C-01 Customers Workspace

- route_name: SicherPlanCustomers
- path_template: /admin/customers
- module_key: customers
- api_families: customers
- required_permissions: customers.customer.read
- allowed_role_keys: tenant_admin, dispatcher, accounting, controller_qm
- scope_kind: tenant

## C-02 Customer Order Workspace

- route_name: SicherPlanCustomerOrderWorkspace
- path_template: /admin/customers/order-workspace
- module_key: customers
- api_families: customers, planningOrders, planningShifts, platformDocuments
- required_permissions: none
- allowed_role_keys: tenant_admin
- scope_kind: tenant

## E-01 Employees Workspace

- route_name: SicherPlanEmployees
- path_template: /admin/employees
- module_key: employees
- api_families: employees
- required_permissions: employees.employee.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## R-01 Recruiting Workspace

- route_name: SicherPlanRecruiting
- path_template: /admin/recruiting
- module_key: recruiting
- api_families: recruiting
- required_permissions: recruiting.applicant.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## R-02 Applicant Public Form

- route_name: SicherPlanApplicantForm
- path_template: /public/apply/:tenantCode
- module_key: recruiting
- api_families: recruiting
- required_permissions: none
- allowed_role_keys: none
- scope_kind: public

## S-01 Subcontractors Workspace

- route_name: SicherPlanSubcontractors
- path_template: /admin/subcontractors
- module_key: subcontractors
- api_families: subcontractors
- required_permissions: subcontractors.company.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## P-01 Planning Setup

- route_name: SicherPlanPlanning
- path_template: /admin/planning
- module_key: planning
- api_families: planning
- required_permissions: planning.ops.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## P-02 Orders & Planning Records

- route_name: SicherPlanPlanningOrders
- path_template: /admin/planning-orders
- module_key: planning
- api_families: planning
- required_permissions: planning.order.read, planning.record.read
- allowed_role_keys: tenant_admin, dispatcher, accounting, controller_qm
- scope_kind: tenant

## P-03 Shift Planning

- route_name: SicherPlanPlanningShifts
- path_template: /admin/planning-shifts
- module_key: planning
- api_families: planning
- required_permissions: planning.shift.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## P-04 Staffing Board & Coverage

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- api_families: planning
- required_permissions: planning.staffing.read
- allowed_role_keys: tenant_admin, dispatcher
- scope_kind: tenant

## P-05 Dispatch, Outputs & Subcontractor Releases

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- api_families: planning
- required_permissions: planning.staffing.read
- allowed_role_keys: tenant_admin, dispatcher
- scope_kind: tenant

## FD-01 Field Operations Workspace

- route_name: SicherPlanPlanning
- path_template: /admin/planning
- module_key: field_execution
- api_families: field_execution
- required_permissions: planning.ops.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: tenant

## FI-01 Actuals / Actual-Freigaben Workspace

- route_name: SicherPlanFinanceActuals
- path_template: /admin/finance-actuals
- module_key: finance
- api_families: finance
- required_permissions: finance.actual.read
- allowed_role_keys: tenant_admin, accounting, controller_qm
- scope_kind: tenant

## FI-02 Billing Workspace

- route_name: SicherPlanFinanceBilling
- path_template: /admin/finance-billing
- module_key: finance
- api_families: finance
- required_permissions: finance.billing.read
- allowed_role_keys: tenant_admin, accounting, controller_qm
- scope_kind: tenant

## FI-03 Payroll Workspace

- route_name: SicherPlanFinancePayroll
- path_template: /admin/finance-payroll
- module_key: finance
- api_families: finance
- required_permissions: finance.payroll.read
- allowed_role_keys: tenant_admin, accounting, controller_qm
- scope_kind: tenant

## FI-04 Subcontractor Invoice Checks

- route_name: SicherPlanFinanceSubcontractorChecks
- path_template: /admin/finance-subcontractor-checks
- module_key: finance
- api_families: finance
- required_permissions: finance.subcontractor_control.read
- allowed_role_keys: tenant_admin, accounting, controller_qm
- scope_kind: tenant

## REP-01 Reporting Hub

- route_name: SicherPlanReporting
- path_template: /admin/reporting
- module_key: reporting
- api_families: reporting
- required_permissions: reporting.read
- allowed_role_keys: tenant_admin, accounting, controller_qm
- scope_kind: tenant

## ES-01 Employee Self-Service Portal

- route_name: SicherPlanEmployees
- path_template: /admin/employees
- module_key: employee_self_service
- api_families: employees, employee_self_service
- required_permissions: employees.employee.read
- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- scope_kind: employee_self_service

## CP-01 Customer Portal

- route_name: SicherPlanCustomerPortalOverview
- path_template: /portal/customer/overview
- module_key: customer_portal
- api_families: portal_customer
- required_permissions: portal.customer.access
- allowed_role_keys: customer_user
- scope_kind: customer

## SP-01 Subcontractor Portal

- route_name: SicherPlanSubcontractorPortal
- path_template: /portal/subcontractor
- module_key: subcontractor_portal
- api_families: portal_subcontractor
- required_permissions: portal.subcontractor.access
- allowed_role_keys: subcontractor_user
- scope_kind: subcontractor

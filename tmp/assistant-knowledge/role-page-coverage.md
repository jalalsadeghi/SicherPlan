# Role-Based Page Coverage Map

This generated source summarizes which roles and permissions can reach verified assistant page IDs.

## F-02 — Dashboard

- allowed_role_keys: platform_admin, tenant_admin, dispatcher, accounting, controller_qm
- required_permissions: none
- scope_kind: tenant

## F-03 — Current Session / Sessions / Access Codes

- allowed_role_keys: platform_admin
- required_permissions: none
- scope_kind: platform

## A-02 — Tenants & Core System

- allowed_role_keys: platform_admin, tenant_admin
- required_permissions: core.admin.access
- scope_kind: tenant

## A-03 — Branch & Mandate Management

- allowed_role_keys: platform_admin, tenant_admin
- required_permissions: core.admin.branch.read, core.admin.mandate.read
- scope_kind: tenant

## A-04 — Tenant Settings

- allowed_role_keys: platform_admin, tenant_admin
- required_permissions: core.admin.setting.read
- scope_kind: tenant

## A-05 — Tenant Users & IAM

- allowed_role_keys: platform_admin
- required_permissions: none
- scope_kind: platform

## A-06 — Health & Diagnostics

- allowed_role_keys: platform_admin
- required_permissions: none
- scope_kind: platform

## PS-01 — Platform Services Workspace

- allowed_role_keys: platform_admin, tenant_admin, controller_qm
- required_permissions: none
- scope_kind: tenant

## C-01 — Customers Workspace

- allowed_role_keys: tenant_admin, dispatcher, accounting, controller_qm
- required_permissions: customers.customer.read
- scope_kind: tenant

## C-02 — Customer Order Workspace

- allowed_role_keys: tenant_admin
- required_permissions: none
- scope_kind: tenant

## E-01 — Employees Workspace

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: employees.employee.read
- scope_kind: tenant

## R-01 — Recruiting Workspace

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: recruiting.applicant.read
- scope_kind: tenant

## R-02 — Applicant Public Form

- allowed_role_keys: none
- required_permissions: none
- scope_kind: public

## S-01 — Subcontractors Workspace

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: subcontractors.company.read
- scope_kind: tenant

## P-01 — Planning Setup

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: planning.ops.read
- scope_kind: tenant

## P-02 — Orders & Planning Records

- allowed_role_keys: tenant_admin, dispatcher, accounting, controller_qm
- required_permissions: planning.order.read, planning.record.read
- scope_kind: tenant

## P-03 — Shift Planning

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: planning.shift.read
- scope_kind: tenant

## P-04 — Staffing Board & Coverage

- allowed_role_keys: tenant_admin, dispatcher
- required_permissions: planning.staffing.read
- scope_kind: tenant

## P-05 — Dispatch, Outputs & Subcontractor Releases

- allowed_role_keys: tenant_admin, dispatcher
- required_permissions: planning.staffing.read
- scope_kind: tenant

## FD-01 — Field Operations Workspace

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: planning.ops.read
- scope_kind: tenant

## FI-01 — Actuals / Actual-Freigaben Workspace

- allowed_role_keys: tenant_admin, accounting, controller_qm
- required_permissions: finance.actual.read
- scope_kind: tenant

## FI-02 — Billing Workspace

- allowed_role_keys: tenant_admin, accounting, controller_qm
- required_permissions: finance.billing.read
- scope_kind: tenant

## FI-03 — Payroll Workspace

- allowed_role_keys: tenant_admin, accounting, controller_qm
- required_permissions: finance.payroll.read
- scope_kind: tenant

## FI-04 — Subcontractor Invoice Checks

- allowed_role_keys: tenant_admin, accounting, controller_qm
- required_permissions: finance.subcontractor_control.read
- scope_kind: tenant

## REP-01 — Reporting Hub

- allowed_role_keys: tenant_admin, accounting, controller_qm
- required_permissions: reporting.read
- scope_kind: tenant

## ES-01 — Employee Self-Service Portal

- allowed_role_keys: tenant_admin, dispatcher, controller_qm
- required_permissions: employees.employee.read
- scope_kind: employee_self_service

## CP-01 — Customer Portal

- allowed_role_keys: customer_user
- required_permissions: portal.customer.access
- scope_kind: customer

## SP-01 — Subcontractor Portal

- allowed_role_keys: subcontractor_user
- required_permissions: portal.subcontractor.access
- scope_kind: subcontractor

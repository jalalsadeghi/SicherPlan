# Assistant API Endpoint Map

This generated source maps workspace pages to backend API families verified in the route catalog.

## F-02 — Dashboard

- module_key: dashboard
- api_families: dashboard
- route_name: SicherPlanDashboard
- path_template: /admin/dashboard

## F-03 — Current Session / Sessions / Access Codes

- module_key: iam
- api_families: iam
- route_name: SicherPlanTenantUsers
- path_template: /admin/iam/users

## A-02 — Tenants & Core System

- module_key: core
- api_families: core
- route_name: SicherPlanCoreAdmin
- path_template: /admin/core

## A-03 — Branch & Mandate Management

- module_key: core
- api_families: core
- route_name: SicherPlanCoreAdmin
- path_template: /admin/core

## A-04 — Tenant Settings

- module_key: core
- api_families: core
- route_name: SicherPlanCoreAdmin
- path_template: /admin/core

## A-05 — Tenant Users & IAM

- module_key: iam
- api_families: iam
- route_name: SicherPlanTenantUsers
- path_template: /admin/iam/users

## A-06 — Health & Diagnostics

- module_key: platform_services
- api_families: health, platform_services
- route_name: SicherPlanHealthDiagnostics
- path_template: /admin/health

## PS-01 — Platform Services Workspace

- module_key: platform_services
- api_families: platform_services
- route_name: SicherPlanPlatformServices
- path_template: /admin/platform-services

## C-01 — Customers Workspace

- module_key: customers
- api_families: customers
- route_name: SicherPlanCustomers
- path_template: /admin/customers

## E-01 — Employees Workspace

- module_key: employees
- api_families: employees
- route_name: SicherPlanEmployees
- path_template: /admin/employees

## R-01 — Recruiting Workspace

- module_key: recruiting
- api_families: recruiting
- route_name: SicherPlanRecruiting
- path_template: /admin/recruiting

## R-02 — Applicant Public Form

- module_key: recruiting
- api_families: recruiting
- route_name: SicherPlanApplicantForm
- path_template: /public/apply/:tenantCode

## S-01 — Subcontractors Workspace

- module_key: subcontractors
- api_families: subcontractors
- route_name: SicherPlanSubcontractors
- path_template: /admin/subcontractors

## P-01 — Planning Setup

- module_key: planning
- api_families: planning
- route_name: SicherPlanPlanning
- path_template: /admin/planning

## P-02 — Orders & Planning Records

- module_key: planning
- api_families: planning
- route_name: SicherPlanPlanningOrders
- path_template: /admin/planning-orders

## P-03 — Shift Planning

- module_key: planning
- api_families: planning
- route_name: SicherPlanPlanningShifts
- path_template: /admin/planning-shifts

## P-04 — Staffing Board & Coverage

- module_key: planning
- api_families: planning
- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing

## P-05 — Dispatch, Outputs & Subcontractor Releases

- module_key: planning
- api_families: planning
- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing

## FD-01 — Field Operations Workspace

- module_key: field_execution
- api_families: field_execution
- route_name: SicherPlanPlanning
- path_template: /admin/planning

## FI-01 — Actuals / Actual-Freigaben Workspace

- module_key: finance
- api_families: finance
- route_name: SicherPlanFinanceActuals
- path_template: /admin/finance-actuals

## FI-02 — Billing Workspace

- module_key: finance
- api_families: finance
- route_name: SicherPlanFinanceBilling
- path_template: /admin/finance-billing

## FI-03 — Payroll Workspace

- module_key: finance
- api_families: finance
- route_name: SicherPlanFinancePayroll
- path_template: /admin/finance-payroll

## FI-04 — Subcontractor Invoice Checks

- module_key: finance
- api_families: finance
- route_name: SicherPlanFinanceSubcontractorChecks
- path_template: /admin/finance-subcontractor-checks

## REP-01 — Reporting Hub

- module_key: reporting
- api_families: reporting
- route_name: SicherPlanReporting
- path_template: /admin/reporting

## ES-01 — Employee Self-Service Portal

- module_key: employee_self_service
- api_families: employees, employee_self_service
- route_name: SicherPlanEmployees
- path_template: /admin/employees

## CP-01 — Customer Portal

- module_key: customer_portal
- api_families: portal_customer
- route_name: SicherPlanCustomerPortalOverview
- path_template: /portal/customer/overview

## SP-01 — Subcontractor Portal

- module_key: subcontractor_portal
- api_families: portal_subcontractor
- route_name: SicherPlanSubcontractorPortal
- path_template: /portal/subcontractor

# Tenant Administrator Page Authorization Review

## Source note

The prompt references `SicherPlan_Role_Based_Page_Coverage_Map.pdf` and `SicherPlan API.pdf`, but neither PDF exists anywhere in this workspace. This review therefore uses:

- the canonical Tenant Administrator page list embedded in `docs/prompts/fix.md`
- the current repository routes, views, sidebar structure, and API families

## 1. Tenant Administrator — Allowed Page Inventory

| Page ID | Page name | Summary | Scope | Source API family | Sidebar visibility | Suggested route | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | Authentication & Password Reset | Shared internal authentication flow | login, refresh, logout, password reset request and confirm | `auth` | No | `/auth/login`, `/auth/forget-password` | OK |
| F-02 | Dashboard | Shared landing page after login | role-aware shortcuts and entry points | shared shell plus `auth` session bootstrap | Yes | `/admin/dashboard` | OK |
| F-03 | Current Session / Sessions / Access Codes | Shared security/self-service area | current session, sessions, access codes | `auth` | No | `/profile` plus `/api/auth/me`, `/api/auth/sessions`, `/api/auth/codes` | Partial |
| A-02 | Tenants & Core System | Tenant-scoped company backbone workspace | tenant detail, lifecycle, tenant-scoped core administration entry | `core-admin` | Yes | `/admin/core` | OK |
| A-03 | Branch & Mandate Management | Organizational structure maintenance | branch and mandate list/create/update inside tenant scope | `core-admin` | Yes, inside Core | `/admin/core` | Partial |
| A-04 | Tenant Settings | Tenant configuration workspace | tenant settings list/create/update | `core-admin` | Yes, inside Core | `/admin/core` | Partial |
| A-05 | Tenant Users & IAM | Tenant-local user and role administration | list/create/status/password reset for tenant admin accounts | expected `iam-admin` | Yes | `/admin/iam/users` | Missing |
| PS-01 | Platform Services Workspace | Shared tenant-scoped platform services | documents, communication, notices, integrations | `platform-docs`, `platform-communication`, `platform-notices`, `platform-integration` | Yes | `/admin/platform-services` | Partial |
| C-01 | Customers Workspace | Customer master and commercial workspace | customer admin, commercial settings, billing profile, contacts, portal/privacy-related controls | `customers` | Yes | `/admin/customers` | Partial |
| E-01 | Employees Workspace | Employee lifecycle and readiness workspace | employee lifecycle, HR-private/operational split, credentials, qualifications, attach/detach login access, import/export | `employees` | Yes | `/admin/employees` | Partial |
| R-01 | Recruiting Workspace | Applicant workflow workspace | applicants, stage transitions, activities, conversion | `recruiting` | Yes | `/admin/recruiting` | Partial |
| S-01 | Subcontractors Workspace | Partner administration workspace | subcontractor lifecycle, finance profile, workers, readiness, credentials, import/export | `subcontractors` | Yes | `/admin/subcontractors` | Partial |
| P-01 | Planning Setup | Planning master setup workspace | requirement types, equipment, sites, venues, trade fairs, patrol routes, checkpoints | `planning` | Yes | `/admin/planning` | Partial |
| P-02 | Orders & Planning Records | Planning record and order workspace | orders, requirement lines, attachments, planning records, release state | `planning` | Yes | `/admin/planning-orders` | Partial |
| P-03 | Shift Planning | Shift planning workspace | templates, plans, series, exceptions, shifts, validations, release state | `planning` | Yes | `/admin/planning-shifts` | Partial |
| P-04 | Staffing Board & Coverage | Staffing and coverage workspace | demand groups, teams, assignments, overrides, coverage views | `planning` | Yes | `/admin/planning-staffing` | Partial |
| P-05 | Dispatch, Outputs & Subcontractor Releases | Dispatch and outbound operations workspace | outputs, dispatch preview/messages, subcontractor releases, ops import execute/dry-run | expected planning/field/dispatch support | Yes | no dedicated route today | Missing |
| FI-01 | Actuals / Actual-Freigaben Workspace | Actual approval and reconciliation workspace | derive, preliminary submit, operational confirm, finance signoff, reconciliation, comments | `finance` | Yes | `/admin/finance-actuals` | Partial |
| FI-02 | Billing Workspace | Billing output workspace | timesheets, invoices, release, issue, dispatch queue | `finance` | Yes | `/admin/finance-billing` | Partial |
| FI-03 | Payroll Workspace | Payroll calculation/export workspace | tariffs, rates, pay profiles, export batches, archives, reconciliation | `finance` | Yes | `/admin/finance-payroll` | Partial |
| FI-04 | Subcontractor Invoice Checks | Subcontractor control workspace | list/detail, audit history, generation, notes, status changes | `finance` | Yes | `/admin/finance-subcontractor-checks` | Partial |
| REP-01 | Reporting Hub | Tenant reporting workspace | exports, delivery jobs, KPI/report areas | `reporting` | Yes | `/admin/reporting` | Partial |

## 2. Sidebar Navigation for Tenant Administrator

- Dashboard
  - Dashboard — `/admin/dashboard`
- Administration
  - Tenants & Core System — `/admin/core`
  - Tenant Users & IAM — missing, target `/admin/iam/users`
  - Platform Services — `/admin/platform-services`
- Customers
  - Customers — `/admin/customers`
- Workforce & HR
  - Employees — `/admin/employees`
  - Recruiting — `/admin/recruiting`
- Subcontractors
  - Subcontractors — `/admin/subcontractors`
- Operations & Planning
  - Planning Setup — `/admin/planning`
  - Orders & Planning Records — `/admin/planning-orders`
  - Shift Planning — `/admin/planning-shifts`
  - Staffing Board & Coverage — `/admin/planning-staffing`
  - Dispatch, Outputs & Subcontractor Releases — missing dedicated route
- Finance
  - Actuals / Actual-Freigaben — `/admin/finance-actuals`
  - Billing — `/admin/finance-billing`
  - Payroll — `/admin/finance-payroll`
  - Subcontractor Invoice Checks — `/admin/finance-subcontractor-checks`
- Reporting
  - Reporting Hub — `/admin/reporting`

Notes:

- Branch & Mandate Management and Tenant Settings are currently nested inside `/admin/core`, which is acceptable per the prompt.
- `A-01 Tenant Onboarding` and `A-06 Health & Diagnostics` are intentionally not part of the Tenant Administrator sidebar.

## 3. Allowed but non-sidebar pages

- Login — `/auth/login`
  - Shared authentication entry, not a post-login navigation item.
- Password reset — `/auth/forget-password`
  - Shared recovery flow, not a sidebar item.
- Profile / Security area — `/profile`
  - Better kept under user/profile rather than the main sidebar.
- Current session API — `/api/auth/me`
  - Support endpoint, not a page.
- Session list API — `/api/auth/sessions`
  - Support endpoint, not a page.
- Access codes API — `/api/auth/codes`
  - Support endpoint, not a page.

## 4. Pages currently visible but not allowed for this role

- Health & Diagnostics — `/admin/health`
  - Platform-only. Correctly hidden from `tenant_admin` in current route authority.
- Tenant Onboarding as a standalone page
  - Platform-only. There is no standalone sidebar entry, which is correct.
- Customer Portal — `/portal/customer`
  - Runtime portal, not a normal internal Tenant Administrator sidebar page.
- Subcontractor Portal — `/portal/subcontractor`
  - Runtime portal, not a normal internal Tenant Administrator sidebar page.
- Public Applicant Form — `/public/apply/:tenantCode`
  - Public page, not an internal sidebar page.

Current exposure status:

- these platform/public/portal pages are not in the tenant-admin route authority set in [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts)
- the prior tenant-admin dead links from core/platform-services quick links were corrected by filtering quick links by role in [admin-module-view.vue](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/views/sicherplan/admin-module-view.vue) and [module-registry.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/views/sicherplan/module-registry.ts)

## 5. Gaps and recommendations

Missing pages:

- `A-05 Tenant Users & IAM`
  - frontend route exists only for `platform_admin`
  - backend `iam-admin` endpoints in [admin_router.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/admin_router.py) require platform scope, not tenant scope
  - result: canonical Tenant Administrator IAM coverage is missing
- `P-05 Dispatch, Outputs & Subcontractor Releases`
  - no dedicated tenant-admin route exists today

Partial pages:

- `/admin/core` covers `A-02`, `A-03`, and `A-04`, but those scopes are still merged into one workspace
- `/admin/platform-services` is partial on the frontend because the current workspace remains notice-centric even though the backend supports docs, communication, notices, and integrations
- customers, employees, recruiting, subcontractors, planning, finance, and reporting routes exist, but several remain legacy or incomplete relative to the full scope listed in the prompt

Navigation cleanup completed:

- Tenant Administrator keeps the tenant-operational sidebar groups: customers, workforce, subcontractors, operations, finance, and reporting
- Health & Diagnostics remains hidden from Tenant Administrator
- Platform-only quick links were removed from tenant-admin-visible module views

Permission and guard corrections still needed:

1. Implement a tenant-scoped `Tenant Users & IAM` page and backend API path for `tenant_admin`.
2. Add a dedicated `Dispatch, Outputs & Subcontractor Releases` route if that workflow is intended as a separate page rather than being absorbed into planning/staffing.
3. Consider splitting `/admin/core` into clearer sub-routes if page-level authorization becomes important.
4. Align backend IAM role seeds and frontend route authorities so `tenant_admin` coverage is complete without inheriting platform-only scope.

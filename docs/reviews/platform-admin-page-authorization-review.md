# Platform Administrator / System Administrator Page Authorization Review

## Source note

The prompt names `SicherPlan API.pdf` and `SicherPlan_Role_Based_Page_Coverage_Map.pdf` as the primary source of truth, but those PDF files are not present anywhere in this workspace. This review therefore uses:

- the canonical Platform Administrator page list embedded in `docs/prompts/fix.md`
- the current repository routes, sidebar structure, views, and API families

## Short role definition

Platform Administrator / System Administrator is the cross-tenant platform owner responsible for:

- tenant setup
- tenant admin IAM and access control
- platform services
- platform diagnostics

This role is not the default operator for tenant business modules such as customers, recruiting, employees, planning, finance, or reporting.

## 1. Platform Administrator / System Administrator — Allowed Page Inventory

| Page ID | Page name | Summary | Scope | Source API family | Sidebar visibility | Suggested route | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | Authentication & Password Reset | Shared login and password recovery entry flow | login, refresh, logout, reset request, reset confirm | `auth` | No | `/auth/login`, `/auth/forget-password` | OK |
| F-02 | Dashboard | Role-aware landing page for Platform Administrator | shortcuts, queues, high-level entry points | `auth` plus route shell | Yes | `/admin/dashboard` | OK |
| F-03 | Current Session / Sessions / Access Codes | Shared security and session hygiene area | current session, active sessions, access codes | `auth` | No | `/profile` plus `/api/auth/me`, `/api/auth/sessions`, `/api/auth/codes` | Partial |
| A-01 | Tenant Onboarding | Cross-tenant onboarding flow | create tenant and baseline records | `core-admin` | Yes, as part of core workspace | `/admin/core` | Partial |
| A-02 | Tenants & Core System | Tenant registry and lifecycle workspace | list, detail, lifecycle, tenant metadata | `core-admin` | Yes | `/admin/core` | OK |
| A-03 | Branch & Mandate Management | Tenant organization maintenance | create, list, update branches and mandates | `core-admin` | Yes, as part of core workspace | `/admin/core` | Partial |
| A-04 | Tenant Settings | Tenant configuration workspace | list, create, update tenant settings | `core-admin` | Yes, as part of core workspace | `/admin/core` | Partial |
| A-05 | Tenant Users & IAM | Cross-tenant tenant-admin account management | list, create, status, password reset | `iam-admin` and `core-admin` | Yes | `/admin/iam/users` | OK |
| PS-01 | Platform Services Workspace | Shared platform services administration | documents, communication, notices, integrations | `platform-docs`, `platform-communication`, `platform-notices`, `platform-integration` | Yes | `/admin/platform-services` | Partial |
| A-06 | Health & Diagnostics | Platform operational diagnostics | live, ready, version, support checks | `health` | Yes | `/admin/health` | OK |

Notes:

- `A-01`, `A-03`, and `A-04` are implemented inside the combined Core workspace, not as distinct pages.
- `PS-01` still uses a notice-centric legacy workspace on the frontend, so page scope is only partial compared with the full backend API family.
- `F-03` backend support is complete, but the frontend still relies on the generic profile page rather than a dedicated security workspace.

## 2. Sidebar Navigation for Platform Administrator / System Administrator

- Dashboard
  - Dashboard — `/admin/dashboard`
- Administration
  - Tenants & Core System — `/admin/core`
  - Tenant Users & IAM — `/admin/iam/users`
  - Platform Services — `/admin/platform-services`
  - Health & Diagnostics — `/admin/health`

Implementation note:

- Branch & Mandate Management and Tenant Settings are currently kept under `/admin/core`. That matches the prompt’s allowance to nest them under Tenants & Core System while their scope remains covered.
- Tenant Onboarding is also currently part of `/admin/core`.

## 3. Allowed but non-sidebar pages

- Authentication / Login — `/auth/login`
  - Shared entry flow, not a sidebar destination after login.
- Password reset — `/auth/forget-password`
  - Shared recovery flow, not a post-login navigation item.
- Profile / Security area — `/profile`
  - Best kept outside the main sidebar because it is a shared account/security page for authenticated users.
- Current session API — `/api/auth/me`
  - Backend support endpoint, not a navigation page.
- Session list API — `/api/auth/sessions`
  - Backend support endpoint, not a navigation page.
- Access codes API — `/api/auth/codes`
  - Backend support endpoint, not a navigation page.

## 4. Pages currently visible but not allowed for this role

These pages should not be part of the Platform Administrator sidebar/navigation baseline:

- Customers — `/admin/customers`
- Recruiting — `/admin/recruiting`
- Employees — `/admin/employees`
- Subcontractors — `/admin/subcontractors`
- Planning — `/admin/planning`
- Orders & Planning — `/admin/planning-orders`
- Shift Planning — `/admin/planning-shifts`
- Staffing & Coverage — `/admin/planning-staffing`
- Actual approvals — `/admin/finance-actuals`
- Payroll & export — `/admin/finance-payroll`
- Billing & invoices — `/admin/finance-billing`
- Subcontractor invoice checks — `/admin/finance-subcontractor-checks`
- Reporting — `/admin/reporting`
- Customer portal — `/portal/customer`
- Subcontractor portal — `/portal/subcontractor`
- Public applicant form — `/public/apply/:tenantCode`

Current status after the fix:

- these pages remain in the application for the roles that need them
- they are no longer part of the Platform Administrator route authority set in [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts)

## 5. Gaps and recommendations

Missing or partial pages:

- `F-03 Current Session / Sessions / Access Codes` is still only partial on the frontend. The backend is there, but the UI remains a generic profile page rather than a dedicated SysAdmin security workspace.
- `A-01 Tenant Onboarding`, `A-03 Branch & Mandate Management`, and `A-04 Tenant Settings` are still bundled into `/admin/core` rather than separated into explicit routes.
- `PS-01 Platform Services Workspace` still needs a fuller native frontend workspace for documents, communication, notices, and integrations.

Navigation cleanup completed:

- Platform Administrator sidebar scope is now minimal and administration-focused.
- A dedicated Health & Diagnostics page now exists at `/admin/health`.
- The dashboard and header quick links were made role-aware so Platform Administrator no longer gets default shortcuts into tenant-operational workspaces.
- Platform Administrator default home path now resolves to `/admin/dashboard` instead of `/admin/core`.

Permission and guard corrections completed:

- Removed `ignoreAccess` from protected SicherPlan routes in [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts).
- Added `meta.authority` role lists so frontend access control now reflects role intent.
- Restricted `Tenant Users & IAM` and `Health & Diagnostics` to `platform_admin`.
- Removed Platform Administrator from tenant-operational route authorities such as customers, workforce, operations, finance, and reporting.

Further recommendations:

1. Add a dedicated security/session page for Platform Administrator instead of relying on the generic `/profile` route.
2. Split `/admin/core` into sub-routes if page-level authorization and clearer navigation become more important than a combined workspace.
3. Narrow backend `platform_admin` seed permissions in IAM to match the new frontend navigation model more closely.

# Platform Admin IAM Surface Review

## Scope

Review whether SicherPlan already contains an existing or partial web/admin surface for:

- role management
- permission scope management
- delegated administrative access beyond tenant-admin account handling
- audit review or audit administration

without introducing a new IAM architecture.

## Result

The current implementation contains:

- IAM data models for roles, permissions, user-role assignments, sessions, and audit events
- seed/bootstrap logic for the role and permission catalog
- authorization helpers and scoped backend enforcement
- append-only audit writers used by auth and business-sensitive modules
- one platform-admin web page for tenant-admin account management at `/admin/iam/users`

The current implementation does **not** contain:

- an existing routed web page for role catalog management
- an existing routed web page for permission assignment or permission-scope administration
- an existing routed web page for audit-event review
- a hidden frontend route or menu entry for those capabilities
- a backend router exposing role/permission CRUD or audit-event review APIs for the web shell

## Evidence

Frontend:

- [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts) exposes only `/admin/core`, `/admin/platform-services`, `/admin/iam/users`, and `/admin/health` for Platform Administrator.
- [tenant-users/index.vue](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/views/sicherplan/tenant-users/index.vue) is strictly tenant-admin account management.
- `find web/apps/web-antd/src/views -maxdepth 3 -type f | rg 'iam|audit|health|role|permission'` returns only the health page under the native SicherPlan views.

Backend:

- [admin_router.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/admin_router.py) exposes only tenant-admin user list/create/status/password-reset endpoints.
- [schemas.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/schemas.py) defines role, permission, and user-role-assignment schemas, but no router exposes them.
- [audit_repository.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/audit_repository.py) can list audit events, but there is no corresponding router/page exposing that capability to the web app.

## Minimal change applied

No new IAM module, route tree, or backend CRUD surface was added.

I only made the limitation explicit inside the existing `/admin/iam/users` page so Platform Administrator can see that:

- the current page is limited to tenant-admin account administration
- richer role/permission/audit administration does not currently exist as a hidden web surface in this repo

## Architecture confirmation

- No new parallel IAM architecture was introduced.
- Current project structure was preserved.
- `/admin/iam/users` continues to function as the tenant-admin account-management page.

# Authorization And Scope Rules

## Baseline conventions

- Authentication resolves the current session and user identity first.
- Authorization is explicit and default-deny.
- Routes declare a stable permission key and a scope expectation.
- Service code receives a normalized actor/request context instead of ad hoc headers.

## Current request context

`RequestAuthorizationContext` carries:

- `user_id`
- `tenant_id`
- `session_id`
- effective `role_keys`
- effective `permission_keys`
- resolved scope assignments

This context is derived from the authenticated session plus active role assignments and role-permission links.

## Route guard pattern

Use `require_authorization(permission_key, scope=...)` on protected routes.

Current supported scopes:

- `platform`
- `tenant`
- `branch`
- `mandate`

The dependency enforces both:

1. the required permission key
2. the requested path scope

## Scope behavior

- Platform admins can pass platform, tenant, branch, and mandate scope checks only when the required permission is also present.
- Tenant-scoped assignments can access only their own tenant and can satisfy narrower branch/mandate checks inside that tenant.
- Branch-scoped assignments are limited to the explicitly assigned branch IDs.
- Mandate-scoped assignments are limited to the explicitly assigned mandate IDs.
- Customer and subcontractor scope fields remain part of the same abstraction but are not yet wired to Sprint 2 business routes.

## Current protected Sprint 2 routes

`/api/core/admin/*` now uses explicit permissions:

- `core.admin.tenant.create`
- `core.admin.tenant.read`
- `core.admin.tenant.write`
- `core.admin.branch.read`
- `core.admin.branch.write`
- `core.admin.mandate.read`
- `core.admin.mandate.write`
- `core.admin.setting.read`
- `core.admin.setting.write`

## Follow-up expectation

Later modules should reuse the same permission-key and scope-dependency pattern instead of inventing module-local authorization checks or falling back to role-name conditionals inside handlers.

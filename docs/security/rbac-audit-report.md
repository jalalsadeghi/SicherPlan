# SicherPlan RBAC Audit Report

## Summary

This audit compares the documented access model against the current repository state across IAM seed data, backend authorization, session claims, and frontend route behavior.

Current conclusion:

- The backend has a credible scoped-RBAC foundation with explicit permission keys, scoped role assignments, session-backed auth, and audit/login events.
- The implemented role catalog is narrower than the documented business role model.
- The biggest practical mismatch is frontend route enforcement in the Vben shell: current SicherPlan admin routes are all configured with `ignoreAccess: true`, so role-based route blocking is not happening in the new shell.
- The broadest authorization drift is that `platform_admin` and `tenant_admin` currently carry very large operational and finance permission sets.

## Severity Findings

### P1

1. Frontend admin route guard bypass in the Vben shell.
   Evidence:
   - [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts)
   - [guard.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/guard.ts)
   - The current route module contains `28` occurrences of `ignoreAccess: true`, matching the approximate route count.
   Impact:
   - Protected admin pages remain directly reachable by URL from the frontend shell perspective.
   - Backend APIs still enforce access in many cases, so this is not a total server-side bypass, but it is still a broken route-guard contract and weakens user-journey correctness.
   Status:
   - Identified and documented. Not broadly patched in this audit because the current Vben route metadata contract needs a coordinated role/permission rewrite instead of a blind mass edit.

### P2

1. Documented role model is richer than the implemented IAM seed.
   Evidence:
   - [fix.md](/home/jey/Projects/SicherPlan/docs/prompts/fix.md)
   - [US-35-T2.md](/home/jey/Projects/SicherPlan/docs/prompts/US-35-T2.md)
   - [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py)
   Details:
   - Implemented role keys: `platform_admin`, `tenant_admin`, `dispatcher`, `accounting`, `controller_qm`, `customer_user`, `subcontractor_user`, `employee_user`
   - Missing distinct role keys for:
     - subcontractor administrator versus planner/operator split
     - field supervisor / object or event lead

2. `platform_admin` and `tenant_admin` are over-broad relative to documented least privilege.
   Evidence:
   - [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py)
   Details:
   - `platform_admin` currently has `67` permissions.
   - `tenant_admin` currently has `65` permissions.
   - Both include broad planning, field, finance, payroll, and reporting powers.

3. Frontend home-path mapping is incomplete for portal actors.
   Evidence:
   - [auth.mappers.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/core/auth.mappers.ts)
   Details:
   - Before this audit, `subcontractor_user` was still sent to `/admin/core` after login.
   - Fixed in this audit.

4. Legacy route definitions and Vben route definitions are inconsistent.
   Evidence:
   - [routes.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/sicherplan-legacy/router/routes.ts)
   - [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts)
   Details:
   - Legacy routes carry role and permission metadata.
   - New Vben routes currently do not.

### P3

1. Documentation drift around customer/subcontractor scope wiring.
   Evidence:
   - [authorization-and-scope-rules.md](/home/jey/Projects/SicherPlan/docs/engineering/authorization-and-scope-rules.md)
   - [authz.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/authz.py)
   Details:
   - Engineering notes still describe customer/subcontractor scopes as not yet wired in the Sprint 2 baseline.
   - Current authz code and portal services now do use customer/subcontractor scope semantics.

## Reference Role Matrix From Documentation

See [rbac-matrix.md](/home/jey/Projects/SicherPlan/docs/security/rbac-matrix.md) and [rbac-matrix.json](/home/jey/Projects/SicherPlan/docs/security/rbac-matrix.json).

## Current Implemented Matrix

Seed source:

- [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py)

Current counts:

- roles: `8`
- permissions: `70`

Role totals:

- `platform_admin`: `67`
- `tenant_admin`: `65`
- `dispatcher`: `33`
- `accounting`: `21`
- `controller_qm`: `13`
- `customer_user`: `3`
- `subcontractor_user`: `3`
- `employee_user`: `6`

## Backend Audit Notes

Reviewed:

- [models.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/models.py)
- [schemas.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/schemas.py)
- [authz.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/authz.py)
- [auth_service.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/auth_service.py)
- [auth_router.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/auth_router.py)
- [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py)
- [core/admin_router.py](/home/jey/Projects/SicherPlan/backend/app/modules/core/admin_router.py)
- [customers/portal_service.py](/home/jey/Projects/SicherPlan/backend/app/modules/customers/portal_service.py)
- [subcontractors/portal_service.py](/home/jey/Projects/SicherPlan/backend/app/modules/subcontractors/portal_service.py)
- [finance/service.py](/home/jey/Projects/SicherPlan/backend/app/modules/finance/service.py)
- [field_execution/watchbook_service.py](/home/jey/Projects/SicherPlan/backend/app/modules/field_execution/watchbook_service.py)

Findings:

1. The auth/session foundation is consistent.
   - Login, refresh, logout, password reset, session revocation, and audit/login events are wired coherently.
   - Inactive and archived users are blocked at auth time.

2. Route-level backend protection is generally explicit on internal APIs.
   - `require_authorization(...)` is heavily used across admin, finance, planning, field, and reporting routers.

3. Portal routers often use service-level enforcement instead of route-level `require_authorization(...)`.
   - Customer and subcontractor portal routers depend on `get_request_authorization_context`, then call context-resolution services that enforce the portal permission and scope.
   - This is acceptable but less uniform than the preferred route-guard pattern.

4. Service-level checks sometimes rely on role names, not only permission keys.
   - Example: finance and watchbook services use direct role checks such as `dispatcher`, `controller_qm`, or `employee_user`.
   - This is practical but creates drift risk if role taxonomy changes.

## Frontend Audit Notes

Reviewed:

- [guard.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/guard.ts)
- [access.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/access.ts)
- [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts)
- [routes.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/sicherplan-legacy/router/routes.ts)
- [auth.mappers.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/core/auth.mappers.ts)

Findings:

1. The legacy shell has route role metadata; the new Vben shell does not.
2. The new Vben SicherPlan route tree currently uses `ignoreAccess: true` everywhere, which defeats route-level protection in the shell.
3. Frontend access generation is role-based from the Vben user object, but the current route tree does not expose matching role metadata.
4. The new shell still lacks route-level permission-key parity with backend endpoints.

## Scope Enforcement Audit

Observed behavior:

1. IAM persistence supports `tenant`, `branch`, `mandate`, `customer`, and `subcontractor` scopes.
2. Generic authz helpers can enforce `platform`, `tenant`, `branch`, `mandate`, `customer`, and `subcontractor`.
3. Portal services resolve customer/subcontractor scope through both IAM scope assignments and linked contact membership.
4. Employee self-scope is enforced in service logic for employee-oriented flows, not as a distinct generic scope type in `authz.py`.

Assessment:

- Tenant isolation is structurally strong on the backend.
- Customer/subcontractor/employee self-scope is implemented, but not yet expressed as one fully uniform cross-module policy layer.

## Authentication / Authorization Consistency

Current state:

1. User creation -> role assignment -> login -> role claims works.
2. Access tokens carry role keys, not full permission keys.
3. Backend recalculates effective permissions from live role assignments on authenticated requests.
4. Frontend route behavior is driven by mapped role keys only.

Implication:

- Backend correctness is stronger than frontend access presentation.
- Route/menu correctness in the new shell still needs a proper role/permission metadata pass.

## Corrections Applied In This Audit

1. Added the canonical audit artifacts:
   - [rbac-audit-report.md](/home/jey/Projects/SicherPlan/docs/security/rbac-audit-report.md)
   - [rbac-matrix.md](/home/jey/Projects/SicherPlan/docs/security/rbac-matrix.md)
   - [rbac-matrix.json](/home/jey/Projects/SicherPlan/docs/security/rbac-matrix.json)
2. Fixed subcontractor login home-path mapping:
   - [auth.mappers.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/core/auth.mappers.ts)
   - [auth.mappers.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/core/auth.mappers.test.ts)

## Recommended Next Actions

1. Replace `ignoreAccess: true` on protected Vben admin routes with real role/permission metadata and verify the access generator contract.
2. Split documented-but-missing role families:
   - subcontractor administrator versus planner/operator
   - field supervisor / object or event lead
3. Narrow `tenant_admin` and `platform_admin` permission sets, especially around finance and payroll.
4. Standardize portal routers on explicit route-level permission dependencies where practical, even when service-level context resolution remains necessary.
5. Add dedicated regression tests for:
   - frontend route gating
   - customer/subcontractor scope denial cases
   - employee self-scope denial cases
   - finance versus ops separation
   - role-change audit evidence once role-management flows exist

## Unresolved Ambiguities

1. The proposal/docs mention richer subcontractor and field-supervisor role distinctions than the current seed implements, but they do not yet define the final stable IAM keys.
2. The new Vben route metadata contract for role/permission gating is not documented in-repo as clearly as the legacy route model, so a broad access rewrite should be done deliberately, not by guesswork.

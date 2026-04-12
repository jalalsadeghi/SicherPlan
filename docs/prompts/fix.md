You are working in the SicherPlan repository.

Goal:
Fix the post-auth regression in the legacy admin workspaces so `/admin/customers` and
`/admin/employees` work from the authenticated tenant session after bootstrap, idle
recovery, and hard refresh, without requiring manual bearer-token input or manual tenant
selection for normal tenant-scoped internal users.

This is a focused follow-up to the previous auth/session-lifecycle change. Do not do
unrelated refactors.

Before coding:
1. Read `AGENTS.md`.
2. Keep tenant isolation, RBAC, auditability, and session security intact.
3. Verify the current regression first in the live repo code before changing anything.

Files to inspect first:
Frontend views:
- `web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue`

Frontend API/auth/session:
- `web/apps/web-antd/src/sicherplan-legacy/api/customers.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/sessionRequest.ts`
- `web/apps/web-antd/src/sicherplan-legacy/stores/auth.ts`
- `web/apps/web-antd/src/store/auth.ts`
- `web/apps/web-antd/src/store/auth-session.ts`
- `web/apps/web-antd/src/store/auth-session-lifecycle.ts`
- `web/apps/web-antd/src/api/request.ts`
- `web/apps/web-antd/src/router/guard.ts`
- `web/apps/web-antd/src/bootstrap.ts`

Backend/auth only if truly needed:
- `backend/app/modules/iam/auth_router.py`
- `backend/app/modules/iam/auth_service.py`
- `backend/app/config.py`

What you must verify first:
1. `CustomerAdminView.vue` still asks for both tenant scope and bearer token manually.
2. `EmployeeAdminView.vue` still asks for tenant scope manually.
3. `customers.ts` still depends on explicitly passed `accessToken`.
4. `employeeAdmin.ts` still duplicates its own token/refresh flow instead of relying on the shared session path.
5. `legacySessionRequest` and the legacy auth store already provide enough shared session primitives to remove these UI-level auth prompts.

Business behavior to preserve:
- Customers and Employees are authenticated tenant-scoped internal workspaces.
- A normal tenant-scoped internal user should not manually type a bearer token anywhere in the UI.
- A normal tenant-scoped internal user should not have to manually choose a tenant every time to use Customers or Employees.
- Platform-wide support/admin flows may still need explicit tenant switching, but that must be deliberate and role-scoped, not the default path for normal tenant users.
- Hard refresh should not throw the user out when a valid refresh session still exists.
- Do not weaken logout, revocation, password-reset invalidation, or audit behavior.

Required implementation outcome:
A. Remove manual bearer-token entry from `/admin/customers`.
B. Remove manual tenant-selection gating from `/admin/customers` and `/admin/employees` for normal tenant-scoped internal users.
C. Derive effective tenant scope from authenticated session / role scope / legacy auth store.
D. Use a single shared authenticated request path for these legacy pages instead of bespoke raw bearer-token plumbing.
E. Reuse `legacySessionRequest` or an equivalent single central path so both pages follow the same session lifecycle as the rest of the app.
F. On mount/bootstrap/hard refresh, both pages must:
   - sync from the primary auth session
   - ensure session readiness
   - resolve effective tenant scope
   - load data without asking the user for a token
G. Keep an explicit tenant selector only where truly justified by role (for example platform-admin/support mode), and make that behavior intentional and clearly scoped.
H. Do not leave parallel token refresh logic in `employeeAdmin.ts` if it can be cleanly replaced by the shared session-aware request layer.
I. Keep the change set focused on Customers and Employees regression only.

Implementation details to target:
1. `CustomerAdminView.vue`
- Remove the manual access-token input UI and any “remember token” UI/state.
- Stop blocking the page on `!accessToken`.
- Use session-backed auth from the shared store/helper.
- Resolve tenant scope from session for tenant users.
- If platform-admin needs tenant selection, keep only that tenant-selection behavior and make it role-aware.

2. `EmployeeAdminView.vue`
- Remove the normal-user dependency on manual tenant selection.
- Resolve tenant scope from session/bootstrap state.
- Preserve an explicit selector only for justified cross-tenant/admin scenarios.

3. `customers.ts`
- Refactor away from low-level request functions that require caller-supplied accessToken.
- Route requests through `legacySessionRequest` or a single shared session-aware helper.
- Keep tenantId in path params where the backend requires it, but derive it from the effective tenant context in the page/store layer instead of asking the user to type it.

4. `employeeAdmin.ts`
- Remove duplicated bespoke refresh/token logic if shared session-aware request plumbing can replace it safely.
- Use the same authenticated request strategy as Customers.
- Keep behavior narrow and do not rewrite the whole module unnecessarily.

5. Legacy auth/session glue
- Use the existing legacy auth store capabilities such as:
  - syncing from primary session
  - effective tenant scope
  - effective access token
  - ensureSessionReady
- Make sure these pages recover correctly after:
  - idle period
  - tab focus regain
  - hard refresh
  - direct deep-link load

Tests and validation:
Add or update tests for:
1. `/admin/customers` no longer showing a manual bearer-token requirement for normal tenant users.
2. `/admin/employees` no longer requiring manual tenant selection for normal tenant users.
3. Hard refresh on both pages when refresh session is valid.
4. Session bootstrap and sync from primary auth store.
5. Customer creation flow can open/load after refresh-backed restore.
6. Employee creation flow can open/load after refresh-backed restore.
7. Any platform-admin/support tenant-switch behavior you keep remains explicit and does not leak into normal tenant-user flow.
8. No duplicate refresh races or conflicting auth paths remain between these legacy pages and the main auth store.

Run before finishing:
- relevant frontend tests
- lint/typecheck for touched files
- any backend auth tests only if backend changes were required

Important self-check:
Before finalizing, challenge your own solution and verify that:
- `/admin/customers` does NOT still contain a manual bearer-token gate for normal tenant users
- `/admin/employees` does NOT still contain a manual tenant-scope gate for normal tenant users
- you did not just hide the error message while leaving the broken dependency in place
- you did not leave two competing refresh/session mechanisms in these legacy modules
- you did not break platform-admin/support tenant-switch use cases
- you did not weaken auth security to make the problem disappear

Final response format:
1. Short diagnosis
2. Exact files changed
3. What manual gates were removed
4. How tenant scope is now resolved
5. How Customers and Employees now use shared session-aware requests
6. Tests/validation run and results
7. Remaining assumptions or edge cases
8. Self-validation summary

Extra instruction:
Do not trust your first patch. After implementing, explicitly verify the two user-reported regressions end-to-end:
- customer create path after being on the page for a while and after hard refresh
- employee create path after hard refresh
If either page still depends on typed token/scope input, the fix is incomplete.
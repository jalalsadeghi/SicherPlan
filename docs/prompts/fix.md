You are working in the SicherPlan repository.

Goal:
Fix the authenticated web session lifecycle so internal users can keep pages like
`/admin/planning-shifts` and `/admin/employees` open for hours and continue working
without being unexpectedly redirected to login after short inactivity. Also support the
business expectation that a user who chose “remember me” should usually still be signed
in on the next workday, unless the refresh session has truly expired or was revoked.

Before coding:
1. Read `AGENTS.md`.
2. Respect tenant isolation, role scoping, auditability, and safe auth handling.
3. Keep the change set focused on auth/session lifecycle. Do not do unrelated refactors.

Inspect these areas first:
Frontend:
- `web/apps/web-antd/src/api/request.ts`
- `web/apps/web-antd/src/api/core/auth.ts`
- `web/apps/web-antd/src/store/auth.ts`
- `web/apps/web-antd/src/store/auth-session.ts`
- `web/apps/web-antd/src/router/guard.ts`
- `web/apps/web-antd/src/sicherplan-legacy/stores/auth.ts`
- any legacy API utilities used by `admin/planning-shifts` and `admin/employees`
- any app bootstrap/auth persistence code used by this web app

Backend:
- `backend/app/config.py`
- `backend/app/modules/iam/auth_router.py`
- `backend/app/modules/iam/auth_service.py`
- `backend/app/modules/iam/auth_schemas.py`
- related auth/session tests

What you must verify first:
- whether the current backend access token TTL is too short for real admin usage
- whether refresh-token/session handling is already sufficient in theory but not correctly used by the frontend
- whether `accessTokenExpiresAt` and `refreshTokenExpiresAt` are returned by the API but ignored or underused by the frontend
- whether `remember_me` currently affects real session persistence or is mostly a login-form convenience
- whether legacy pages are bypassing or weakening the main refresh/session flow

Required outcome:
A. Keep strong security and tenant safety intact.
B. Do NOT solve this only by making access tokens very long-lived.
C. Make normal inactivity on open internal admin pages survivable when the refresh session is still valid.
D. Support safe session restoration on app bootstrap when a valid refresh token exists.
E. Refresh proactively before access-token expiry and also on window focus / visibility regain.
F. Use a single-flight refresh strategy so parallel API calls do not trigger refresh races.
G. Only redirect to login when refresh truly fails, the session is revoked, or the refresh session is expired.
H. Make “remember me” behave like a real remembered session policy, not just remembered login fields.

Implementation expectations:

1. Frontend session lifecycle
- Persist enough auth-session metadata to know access-token expiry and refresh-token/session expiry.
- Add a focused session manager / composable / service for:
  - proactive refresh shortly before access-token expiry
  - refresh on `visibilitychange` / focus
  - bootstrap restore of session
  - single-flight refresh protection
  - graceful cleanup only after true refresh failure
- Ensure route guards do not send the user to login just because the access token expired while refresh is still valid.
- Ensure legacy pages such as `admin/planning-shifts` and `admin/employees` rely on the same central auth/session flow and do not bypass it.

2. Backend session policy
- Review the default TTL policy for internal web usage.
- Keep access tokens short-lived if possible.
- If needed, improve refresh-session policy so remembered sessions can survive a normal workday boundary.
- If `remember_me` currently has no effective TTL impact, implement a deliberate policy for it.
- Preserve logout, revocation, password-reset invalidation, and audit behavior.

3. UX / behavior
- Users with a valid refresh session should remain signed in after normal inactivity.
- A remembered session should usually survive until the next workday if security policy allows it.
- When the session is really invalid, show one clear re-login path instead of confusing repeated redirects.

Tests and validation:
- Add or update frontend tests for:
  - session restoration on bootstrap
  - proactive refresh before access-token expiry
  - refresh on focus / visibility regain
  - single-flight refresh behavior
  - redirect to login only after true refresh failure
- Add or update backend tests for:
  - login and refresh TTL behavior
  - remember-me policy
  - refresh rotation and revocation
  - password-reset invalidating active sessions
- Test specifically against:
  - `/admin/planning-shifts`
  - `/admin/employees`
- Simulate these scenarios:
  1. idle longer than the access-token TTL while refresh is still valid
  2. browser refresh / tab restore
  3. next-day remembered session
  4. expired refresh token
  5. revoked session
- Run relevant lint, typecheck, and tests before finishing.

Important self-check:
Before finalizing, verify that:
- you did not only increase token TTLs and ignore session-lifecycle gaps
- you did not leave “remember me” as login-form-only convenience
- you did not leave legacy pages outside the central refresh/session flow
- you did not weaken logout, revocation, password-reset security, or auditability
- you did not introduce duplicate refresh races, refresh loops, or hidden auth state inconsistencies

Final response format:
1. Short diagnosis
2. Exact files changed
3. Chosen session policy and why
4. Frontend changes
5. Backend changes
6. Test and validation results
7. Remaining assumptions or security tradeoffs
8. Self-validation summary

Extra instruction:
Do not trust your first fix. After implementing, challenge your own solution and explicitly verify that the user-reported problem is resolved on the two reported pages. If your first idea was “just increase TTL”, reject that as insufficient unless you can prove the session lifecycle is otherwise correct.
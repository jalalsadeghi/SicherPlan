You are working inside the SicherPlan codebase.

Task:
Fix the “Remember Me” behavior on http://localhost:5173/auth/login.

Current problem:
When the user checks “Remember Me” and logs in successfully, they still get logged out after some idle time or after closing and reopening the browser tab/window. The expected behavior is:
- If “Remember Me” is checked, the user should stay signed in across browser close/reopen and normal short inactivity, until they explicitly click Logout or the backend invalidates the session.
- If “Remember Me” is not checked, the session may remain session-scoped as it does now.
- Explicit Logout must always clear the remembered session.

Important constraints:
1. Do NOT weaken security.
2. Do NOT fake persistence by making access tokens unrealistically long-lived.
3. Use the correct auth/session/refresh flow already intended by the app and backend.
4. Preserve existing login form fields and visible UX unless a very small adjustment is necessary.
5. Do NOT break non-remembered sessions.

What to inspect first:
- login page / auth form implementation
- auth store/session store
- token persistence layer (localStorage / sessionStorage / cookies / storage abstraction)
- app bootstrap / app hydration / startup auth restore
- API client interceptors
- refresh token handling
- logout flow
- router guards / session restore logic

Likely root cause to verify:
The app is probably storing only short-lived access state or is not properly rehydrating and refreshing the session on app startup when “Remember Me” is enabled. Another possibility is that refresh-token persistence exists only partially or is not wired into the startup flow.

Required behavior:
1. On login with “Remember Me” checked:
   - persist the correct auth session data in durable storage
   - on app reload/reopen, restore the session
   - if access token is expired but refresh token/session is still valid, silently refresh and keep the user logged in
2. On login without “Remember Me”:
   - keep current session-scoped behavior unless broken
3. On explicit Logout:
   - clear all persisted auth/session data
   - prevent automatic re-login from stale storage
4. On backend-invalidated/expired refresh session:
   - fail safely
   - clear stored auth data
   - redirect to login cleanly

Implementation guidance:
- Do not just persist a boolean flag.
- Persist the minimum required secure session/auth state for remembered login.
- Prefer the existing auth architecture already present in the app.
- If the codebase already has a refresh-token flow, wire it correctly instead of inventing a parallel mechanism.
- Ensure startup logic rehydrates remembered auth before router guards force logout.
- Ensure API interceptors can refresh once when appropriate and then retry safely.
- Avoid refresh loops.
- Avoid inconsistent storage split bugs.
- Keep “Remember Me” semantics explicit and deterministic.

Security expectations:
- Do not store sensitive data unnecessarily.
- Do not leave stale remembered sessions after logout.
- Do not bypass backend expiry rules.
- Respect backend token/session invalidation.

Testing expectations:
Please add or update focused tests for:
1. remembered login persists across reload
2. remembered login restores after browser reopen simulation / fresh app bootstrap
3. expired access token + valid remembered refresh/session => silent recovery
4. logout clears remembered session
5. non-remembered login does not persist after session end
6. invalid refresh/session leads to clean redirect to login

Deliverables:
1. Implement the fix in the proper auth/session layers.
2. Keep the diff focused.
3. At the end, summarize:
   - which files changed
   - what the root cause was
   - how “Remember Me” now works
   - what tests were added/updated
   - confirmation that explicit Logout still clears everything
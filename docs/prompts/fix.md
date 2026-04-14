You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth. Do NOT revert unrelated changes or perform broad refactors. Apply only a focused fix for the initial-load problem on `/admin/dashboard`.

Task:
Fix the SicherPlan admin dashboard so that data loads correctly when the user lands directly on `/admin/dashboard` immediately after login.

Observed bug:
When the user logs in and is redirected directly to `/admin/dashboard`, the dashboard initially shows no data.
If the user navigates to another admin page such as Customers and then comes back to Dashboard, the data appears.
This means the dashboard is mounting before session/auth context is fully ready and is not retrying or reacting when session state becomes available.

What I want:
The dashboard must load its data correctly on the first direct entry after login, without requiring the user to visit another page first.

Current code facts to inspect first:
1. Route `/admin/dashboard` is wired to the SicherPlan dashboard view.
2. The dashboard view currently loads data on `onMounted`.
3. `loadDashboard()` currently depends on access token / tenant scope.
4. The legacy auth store already exposes session helpers such as:
   - `syncFromPrimarySession()`
   - `ensureSessionReady()`
5. Other planning/admin views already use a more resilient session-ready pattern with:
   - initial sync
   - ensure-session logic
   - refresh on visibility/focus
   - session/reactivity watchers

Before coding, verify these facts in the live working tree and use them as the basis for the fix.

Recommended fix direction:
Adopt the same session-ready pattern already used in the more robust SicherPlan admin views, but keep the change minimal and dashboard-specific.

Implementation requirements:
1. In the dashboard view, do not rely on a single raw `onMounted(loadDashboard)` call.
2. First synchronize/resolve session state before attempting the first dashboard load.
3. Re-run dashboard loading once auth/session context becomes available.
4. Ensure the dashboard reacts when:
   - access token becomes available
   - tenant scope becomes available
   - session user / role context becomes available
5. Avoid duplicate uncontrolled reload loops.
6. Preserve current dashboard UI and data shape; this is a loading-timing fix, not a redesign.

Suggested approach:
1. Inspect the dashboard view and identify:
   - current access token source
   - current tenant scope source
   - current `onMounted` logic
2. Reuse the legacy auth store helpers already present in the repo.
3. Implement a resilient initialization flow, for example:
   - sync from primary session
   - ensure session ready
   - only then load dashboard
4. Add a guarded watcher for the auth/session values that matter so the dashboard can load once they become available after redirect.
5. Optionally mirror the existing focus/visibility refresh pattern used elsewhere if that fits the current dashboard architecture cleanly.
6. Keep the solution minimal, readable, and consistent with current admin views.

Important constraints:
- Do NOT change dashboard business content, cards, or routing structure unless necessary for the fix.
- Do NOT introduce a broad shared abstraction unless clearly needed.
- Do NOT break platform-admin vs tenant-admin behavior.
- Do NOT create repeated API floods from uncontrolled watchers.
- Keep loading state sane even if one or more data calls fail.
- Preserve current Promise.allSettled behavior unless there is a strong reason to change it.

What to validate functionally:
1. Direct login -> redirect to `/admin/dashboard` -> dashboard data appears on first load
2. Hard refresh on `/admin/dashboard` with a valid persisted session -> dashboard data appears
3. Platform admin dashboard still works
4. Tenant-scoped dashboard still works
5. No need to visit `/admin/customers` or another page as a workaround anymore

Testing requirements:
Add or update tests for the dashboard view.
At minimum cover:
1. Dashboard does not remain empty when auth/session is resolved after mount
2. Dashboard triggers loading once session becomes ready
3. Dashboard does not require a second route navigation to populate
4. No uncontrolled duplicate loads
5. Existing quick actions / cards still render once data is loaded

If there is no existing dashboard test file, add a focused smoke or behavior test near the dashboard view.
Prefer behavior tests over brittle implementation-detail tests.

A good test scenario:
- mount dashboard with auth/session initially incomplete
- then simulate session becoming available through the same store pattern used in the app
- assert dashboard load runs and content appears

Acceptance criteria:
- The dashboard loads on first direct entry after login
- The workaround “go to Customers and come back” is no longer needed
- The fix is localized and consistent with existing SicherPlan session-handling patterns
- Tests cover the regression

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Which files were changed
3. What initialization/session-loading logic was added or changed
4. How duplicate loads were prevented
5. Which tests were added or updated
6. Any remaining assumptions or follow-up risks

Before coding, explicitly compare the dashboard’s current session-loading behavior with one of the working admin views that already uses `syncFromPrimarySession()` / `ensureSessionReady()` and state clearly what was missing in the dashboard.
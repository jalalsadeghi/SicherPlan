You are working in the SicherPlan repository.

Task title:
Remove the visible Tenant scope / Bearer token control box from the planning-shifts page UI

Goal:
In `/admin/planning-shifts`, remove the whole visible control box that currently contains:
- Tenant scope
- Bearer token
- helper text about real shift-planning endpoints
- Remember scope and token
- Refresh

This box should no longer be shown to the user in the page UI.

Reason:
- It is not needed for the end user
- It is confusing
- It adds unnecessary visual clutter
- The page should behave like a normal admin workspace, not like a developer/debug screen

Important constraints:
1. Remove this box from the visible page layout only.
2. Do NOT break the existing page logic.
3. Do NOT remove backend/API functionality.
4. Do NOT change route structure.
5. Do NOT remove the top shell-level "Module control" intro.
6. Do NOT reintroduce any duplicate inner header/card.
7. Keep the rest of the planning-shifts page intact.

Preferred behavior:
- The page should silently use the existing auth/session/store state.
- If scope/token are already available from the auth store, the page should continue working normally.
- If missing scope/token creates a real runtime problem, handle it with the existing empty/error state logic instead of showing the old manual control box.

Implementation guidance:
A. In:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue`

remove the visible workspace section/card that renders the controls for:
- `tenantScopeInput`
- `accessTokenInput`
- rememberScopeAndToken()
- refreshAll()

B. Keep internal logic only if still needed:
- `tenantScopeId`
- `accessToken`
- `canRead`
- existing feedback/error states
- any store-based session usage

C. Refactor so the page derives scope/token from the auth/session store automatically.
Use the existing auth store values as the source of truth instead of exposing manual inputs.

D. If the component still needs initialization from remembered values:
- do that internally
- do not show any visible form for it

E. If `rememberScopeAndToken()` becomes unused after this change:
- remove it
- remove related reactive inputs
- remove dead code cleanly

F. If `refreshAll()` should still remain available:
- keep it callable internally
- or expose refresh only in a more normal page action pattern if already used elsewhere
- but do NOT keep the removed control box just to host Refresh

G. Ensure there is no empty gap left behind after removing the box.

Acceptance criteria:
1. The planning-shifts page no longer shows a box/card containing Tenant scope and Bearer token.
2. The page looks cleaner and less confusing.
3. Existing page behavior is preserved as much as possible.
4. No backend/API changes are made.
5. No dead code for the removed visible controls remains.
6. The top shell-level page intro stays visible.

Files expected to change:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue`

Before coding:
Briefly explain:
- which visible box you are removing
- whether you will keep any hidden/internal auth state handling

After coding:
Provide:
1. files changed
2. what UI block was removed
3. whether any internal auth/scope logic was retained
4. confirmation that no backend/API behavior was changed
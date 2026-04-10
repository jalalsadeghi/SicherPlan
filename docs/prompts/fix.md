You are working in the SicherPlan repository.

Task goal:
Align `/admin/planning-staffing` with the documented `P-04 — Staffing Board & Coverage` workspace so it becomes a real session-aware, role-scoped staffing board, not just a partial coverage monitor.

Before coding:
1. Read `AGENTS.md`.
2. Find the relevant story/task ID in `docs/sprint/*.md` or `docs/prompts/*.md`.
3. If no official task ID exists for this page, state that explicitly in your summary and do not invent a fake backlog ID.
4. Use source-of-truth order exactly as defined in `AGENTS.md`.

Files to inspect first:
- `web/apps/web-antd/src/router/routes/modules/sicherplan.ts`
- `web/apps/web-antd/src/views/sicherplan/module-registry.ts`
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.helpers.js`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- any related planning schemas/models/tests needed for safe alignment

Business/documentation intent you must preserve:
- `P-04 Staffing Board & Coverage` is not just a report page.
- It must cover board shifts, demand groups, teams, team members, assignments, assignment validations/overrides, staffing-board assign/unassign/substitute actions, and staffing coverage views.
- Coverage is a release gate, not just a color indicator.
- Planning must stay role-scoped and tenant-scoped.
- Do not expose HR-private data.
- Do not bypass `finance.actual_record` or alter downstream finance truth.
- Keep DE-first / EN-secondary i18n parity for any new UI strings.

Current issues you must verify and fix:
1. The current page hardcodes `role = "dispatcher"` instead of using the real authenticated user role/claims.
2. The current page requires manual tenant scope and access token input and stores them in localStorage instead of using the app session/tenant context.
3. Route authority, helper permission matrix, and documented role scope are inconsistent, especially around `controller_qm` and the documented field-operations role.
4. The current front-end staffing page is only partial relative to the documented P-04 scope.
5. The module-registry import path for `PlanningStaffingCoverageView.vue` must resolve correctly inside the actual repo tree.

Required implementation outcome:
A. Remove manual tenant/access-token entry from `/admin/planning-staffing`.
B. Use the existing authenticated app session and tenant scope from the main web app.
C. Remove any hardcoded role assumptions and derive permissions from the real session/auth state.
D. Make route/module/helper permission behavior consistent.
E. At minimum, support these P-04 behaviors directly in the workspace:
   - shift coverage list
   - demand-group level coverage breakdown
   - assignment detail + validations
   - override creation with audited reason
   - staffing assign / unassign / substitute actions using existing backend endpoints
   - reload/refresh behavior after staffing actions
F. If team/team-member or subcontractor-release management is not handled elsewhere in the current UX, either:
   - expose them in this workspace, or
   - add explicit, clear handoff links/actions to the correct adjacent workspace
   Do not leave the user without an actionable path.
G. Preserve privacy and role-scoped visibility.
H. Keep the change set narrow and do not do unrelated refactors.

Role-access requirement:
- Validate the intended access against the project docs before changing role guards.
- If `controller_qm` should NOT use P-04 according to the docs, remove that access consistently from route/module/helper behavior.
- If you find a valid reason to keep `controller_qm`, implement a deliberate read-only oversight mode with no staffing write, override, dispatch, or release actions, and explain that choice in your final summary.
- If a field-operations role exists in the current auth model, align access with the documented P-04 role scope.

Technical expectations:
- Fix import/path consistency for the planning staffing view.
- Extend `planningStaffing.ts` with the missing typed API wrappers needed by the UI.
- Refactor `PlanningStaffingCoverageView.vue` into maintainable pieces if needed, but stay narrow in scope.
- Render demand-group shortages and coverage state at a level that makes staffing decisions actionable.
- Do not regress existing outputs/dispatch/validation behavior unless a correction is required.

Tests and validation:
- Add or update tests for:
  - permission gating by role
  - session-based tenant/auth context usage
  - read-only vs write action visibility
  - assign/unassign/substitute flows refreshing board/coverage data
  - import-path/module-resolution sanity where applicable
- Run the relevant build/typecheck/lint/tests before finishing.
- Verify that `/admin/planning-staffing` renders without manual token entry.
- Verify tenant scoping and role scoping.
- Verify the final result is consistent with the documented P-04 workspace intent.

Important self-check:
Before finalizing, challenge your own solution and verify that:
- you did not silently keep the hardcoded-role bug
- you did not leave manual token/scope entry in place
- you did not keep route/helper/docs role mismatches unresolved
- you did not claim P-04 completeness while still omitting core staffing-board actions
- you did not introduce HR/privacy leakage
- you did not overreach into unrelated modules

Final response format:
1. Short implementation summary
2. Exact files changed
3. Which inconsistencies you confirmed
4. What you changed and why
5. What tests/validation you ran and their results
6. Remaining assumptions or blockers
7. A brief self-validation section explaining why the result now matches the documented P-04 behavior
You are working in the SicherPlan repository.

First read:
1. `AGENTS.md`
2. the relevant sprint doc under `docs/sprint/`
3. any existing prompt/task doc under `docs/prompts/` related to planning / staffing

Traceability requirement:
- Find the correct story/task ID for this fix.
- If no official task ID exists, state that explicitly in the final summary instead of inventing one.

Task goal:
Fix the `/admin/planning-staffing` experience around shifts that appear in "Shift coverage" but have no demand groups, so the page behavior matches the documented P-04 Staffing Board & Coverage intent and the backend planning model.

Known observed runtime behavior:
- A shift appears in "Shift coverage".
- In "Shift detail", the same shift shows:
  - `Min: 0`
  - `Target: 0`
  - `Assigned: 0`
  - `Confirmed: 0`
  - `Partner release: 0`
  - no demand groups
  - staffing actions fieldset disabled
  - buttons Assign / Substitute / Remove disabled
  - blocked-state message explaining that staffing actions require at least one demand group
- This means the shift is visible in coverage, but cannot be staffed.

Important repo/state discrepancy to verify:
- The current `main` branch may still contain an older `PlanningStaffingCoverageView.vue` that requires manual tenant scope and access token input.
- The current `main` branch `planningStaffing.ts` may not yet expose demand-group/team/staffing-board command wrappers even though the backend/API supports them.
- Verify whether the running UI is ahead of `main`, or whether `main` is the source of truth to bring up to parity.

Files to inspect first:
- `AGENTS.md`
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.helpers.js`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- planning schemas/types related to:
  - `CoverageShiftItem`
  - `StaffingBoardShiftItem`
  - `DemandGroup*`
  - `StaffingAssignCommand`
  - `StaffingSubstituteCommand`
  - `StaffingUnassignCommand`

Business/documentation rules you must preserve:
- P-04 is a real staffing board, not just a passive report.
- P-04 should cover board shifts, demand groups, teams, team members, assignments, validations, overrides, staffing-board actions, and coverage views.
- Demand groups are required staffing slots on a shift.
- Assignments must stay tied to a concrete employee or subcontractor worker, with team remaining contextual unless the backend intentionally supports something broader.
- Coverage is a release gate, not just a dashboard color.
- Do not expose HR-private data.
- Preserve tenant scope and role scope.
- Preserve DE-first / EN-secondary i18n.

What to verify technically:
1. Why shifts with zero demand groups still appear in "Shift coverage".
2. Whether the current backend coverage logic returns `yellow` for `min_qty = 0`, `target_qty = 0`, `assigned = 0`, `released = 0`.
3. Whether that behavior is intentional or misleading for the documented product meaning.
4. Whether the current front-end gives the user any real path to create or manage demand groups from P-04.
5. Whether the checked-in front-end is behind the running HTML behavior.

Required implementation outcome:
A. Do NOT enable staffing actions for shifts that have no demand groups.
B. Do NOT silently classify no-demand-group shifts as normal actionable staffing warnings without explanation.
C. Implement one of these clearly justified solutions:
   - preferred: introduce an explicit UI state such as `setup_required` / `no_demand_groups`
   - acceptable: keep the shift visible but render a clear reason badge/message and exclude it from normal staffing-action expectations
   - acceptable only if justified: move such shifts into a separate "needs setup" bucket
D. Add a clear user path when a shift has no demand groups:
   - inline demand-group create/edit in P-04, OR
   - a strong explicit CTA/link/handoff to the correct place where demand groups are maintained
   Do not leave the user stranded with only disabled controls.
E. If P-04 is supposed to support demand-group management according to the project docs, wire the front-end to the existing demand-group endpoints.
F. If staffing-board assign/substitute/unassign commands are not yet wired in the checked-in front-end, add the missing typed API wrappers and connect them safely.
G. Keep team selection contextual; assignment must still target a concrete employee or subcontractor worker unless backend semantics prove otherwise.
H. Reconcile the checked-in page with the actual intended auth/session model:
   - if manual tenant/token input is obsolete, remove it and use real app session context
   - if it is still intentionally required on `main`, explain why in the final summary

Specific behavioral expectations after the fix:
- A shift with no demand groups should not look like a normal staffable item with ordinary yellow coverage.
- The detail panel should clearly explain what is missing.
- The user should be able to reach the correct demand-group creation/edit action.
- Assign/Substitute/Remove should only become actionable when:
  - a selected shift exists
  - demand groups exist
  - the relevant actor/member prerequisites are satisfied
  - role/permission checks pass

Tests and validation:
Add or update tests for:
1. shift with no demand groups => setup-required / blocked state rendered clearly
2. no-demand-group shift does not expose misleading actionable staffing controls
3. coverage-state handling for zero-demand shifts is consistent with the chosen product rule
4. demand-group create/edit CTA or inline action is visible and functional
5. assign flow remains impossible without `demand_group_id`
6. assign flow works once a valid demand group and valid actor are selected
7. substitute/remove remain gated by valid existing assignment state
8. session/tenant/role scoping remains correct
9. build, lint, typecheck, and relevant tests pass

Important self-check before finishing:
- Confirm you did not allow assignment without a demand group.
- Confirm you did not mark no-demand-group shifts as fully covered green unless that is explicitly justified by product docs (it probably is not).
- Confirm the user is no longer trapped by a disabled form with no next step.
- Confirm the change matches the documented P-04 page scope.
- Confirm you did not regress tenant scoping, role scoping, or privacy.
- Confirm whether `main` was behind the running UI and state that explicitly.

Final response format:
1. Short implementation summary
2. Exact task/story ID used (or explicit note that none existed)
3. Exact files changed
4. What you confirmed about the root cause
5. What you changed and why
6. Tests and validation results
7. Any remaining assumptions or branch/runtime mismatch
8. Self-validation against docs, backend model, and UI behavior
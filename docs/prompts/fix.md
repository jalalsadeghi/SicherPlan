Add regression tests for the Customer New Plan wizard Shift Plan row-selection bug.

Target:
Clicking an existing Shift Plan row must select it locally without route refresh/reload and without losing selection. Next must then commit shift_plan_id and advance to series-exceptions.

Test files to inspect/update:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- add a focused test file if needed.

Required test 1 — row click is local and non-routing:
1. Mount new-plan at step=shift-plan with:
   - customer_id
   - order_id
   - planning_record_id
   - planning_entity_id
   - planning_entity_type=site
   - planning_mode_code=site
   - no shift_plan_id
2. Mock listShiftPlans to return one existing plan:
   - id: shift-plan-1
   - name: "Objektschutz RheinForum Köln – Nordtor Juli 2026 / Shift plan"
   - planning_from: "2026-07-01"
   - planning_to: "2026-07-31"
3. Mock getShiftPlan for shift-plan-1.
4. Click customer-new-plan-existing-shift-plan-row.
5. Assert:
   - getShiftPlan was called
   - form fields are populated
   - selected row has selected class or selected summary is visible
   - route query still does NOT contain shift_plan_id immediately after click
   - router.replace was not called solely because of row selection
   - wizard current_step remains shift-plan
   - no "Unsaved draft restored" appears from a blank/stale draft.

Required test 2 — Next commits selected existing ShiftPlan:
1. Continue from test 1 after selecting the row.
2. Click customer-new-plan-next.
3. Assert:
   - createShiftPlan was NOT called
   - updateShiftPlan was NOT called if the form is unchanged
   - saved-context commits shift_plan_id
   - final route contains shift_plan_id=shift-plan-1
   - final route contains step=series-exceptions
   - wizard content data-step-id is series-exceptions.

Required test 3 — stale blank draft does not override selected plan:
1. Seed sessionStorage with a shift-plan draft that has:
   - selected_shift_plan_id: ""
   - draft: empty/default values
2. Mount step=shift-plan with existing shift plan row.
3. Click the row.
4. Assert:
   - selected row remains selected
   - saved plan fields remain visible
   - blank draft is not applied
   - "Unsaved draft restored" is not shown.

Required test 4 — stale generic draft is not applied when wizardState.shift_plan_id exists:
1. Mount route with shift_plan_id=shift-plan-1.
2. Seed sessionStorage with selected_shift_plan_id="" and unrelated draft values.
3. Mock getShiftPlan returns shift-plan-1.
4. Assert:
   - getShiftPlan result is the source of truth
   - generic draft does not overwrite fields
   - selected summary is visible
   - row is highlighted.

Required test 5 — contentful draft for same selected ShiftPlan is restored:
1. Mount route with shift_plan_id=shift-plan-1.
2. Seed sessionStorage with:
   - selected_shift_plan_id: "shift-plan-1"
   - draft with changed remarks or name
3. Mock getShiftPlan returns shift-plan-1.
4. Assert:
   - saved plan loads first
   - matching contentful draft applies
   - "Unsaved draft restored" appears
   - row remains selected.

Required test 6 — auto-select exactly one existing plan without route mutation:
1. Mount shift-plan with no shift_plan_id.
2. listShiftPlans returns exactly one existing plan.
3. No contentful draft exists.
4. Assert:
   - the plan is selected locally
   - route does not immediately get shift_plan_id
   - Next commits it and advances.

Required test 7 — multiple plans are not auto-selected:
1. listShiftPlans returns two plans.
2. Assert neither is selected automatically.
3. Click one row.
4. Assert that row is selected locally and route remains unchanged until Next.

Required test 8 — clicking create new does not wipe planning context:
1. Start with an existing selected shift plan.
2. Click create-new-shift-plan.
3. Assert:
   - selectedShiftPlan is cleared locally
   - draft resets to default from selectedPlanningRecord
   - planning_record_id remains intact
   - no unrelated order/planning context is cleared
   - route update, if any, does not cause step fallback.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- confirmed/corrected root cause
- files changed
- tests added
- commands run
- proof that row selection no longer triggers route refresh
- proof that Next still advances to series-exceptions
- proof that blank/stale drafts do not override saved Shift Plans.
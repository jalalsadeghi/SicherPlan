Add regression tests for the Customer New Plan wizard Shift Plan step.

Target behavior:
After a successful ShiftPlan create/update/select, the wizard must advance to "series-exceptions" and the URL/state must contain shift_plan_id.

Test files to inspect/update:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic*.smoke.test.ts
- add a dedicated test if needed for route synchronization.

Required test 1 — composable context
1. Initialize wizard with:
   - customer_id
   - order_id
   - planning_record_id
   - current_step = shift-plan
2. Call setSavedContext({ shift_plan_id: 'shift-plan-1' }).
3. Assert state.shift_plan_id === 'shift-plan-1'.
4. Assert canEnterStep('series-exceptions') is true.
5. Assert moveNext() from shift-plan moves to series-exceptions.
6. Assert series_id is cleared when shift_plan_id changes.

Required test 2 — no intermediate route rollback
1. Mount new-plan.vue at:
   step=shift-plan
   with customer_id, order_id, planning_record_id, planning_entity_id, planning_entity_type, planning_mode_code.
2. Mock submitCurrentStep / createShiftPlan so it emits saved-context with shift_plan_id.
3. Simulate the exact order:
   - saved-context updates wizardState.shift_plan_id while current_step is still shift-plan
   - route sync watcher would normally want to write step=shift-plan
   - goToNextStep then calls moveNext()
4. Assert no final route contains step=shift-plan after successful submit.
5. Assert final route contains:
   - step=series-exceptions
   - shift_plan_id=<saved id>
6. Assert wizard content data-step-id is "series-exceptions".

Required test 3 — create ShiftPlan advances
1. Mount the full wizard at shift-plan with planning_record_id.
2. Mock:
   - getPlanningRecord
   - listShiftPlans
   - listShiftTemplates
   - listShiftTypeOptions
   - createShiftPlan
3. Fill:
   - name
   - workforce_scope_code
   - planning_from
   - planning_to
   - remarks
4. Click customer-new-plan-next.
5. Assert createShiftPlan was called once with:
   - tenant_id
   - planning_record_id
   - name
   - workforce_scope_code
   - planning_from
   - planning_to
6. Assert the step advances to series-exceptions.
7. Assert route query has shift_plan_id.
8. Assert "Shift plan" is not restored as current step.

Required test 4 — update selected ShiftPlan advances
1. Mount shift-plan with existing shift_plan_id in route/wizard state.
2. Mock getShiftPlan to return a saved plan.
3. Edit name or remarks.
4. Click Next.
5. Assert updateShiftPlan was called, not createShiftPlan.
6. Assert final step is series-exceptions.

Required test 5 — selecting existing ShiftPlan marks context
1. Mount shift-plan with planning_record_id but no shift_plan_id.
2. Mock listShiftPlans to return at least one existing plan.
3. Click the existing plan row.
4. Assert:
   - form is populated
   - selected row is highlighted
   - emitted saved-context stores shift_plan_id
   - step-completion for shift-plan is true
5. Click Next.
6. Assert no duplicate createShiftPlan call happens.
7. Assert step is series-exceptions.

Required test 6 — auto-select exactly one existing plan
1. Mount shift-plan with planning_record_id and no shift_plan_id.
2. Mock listShiftPlans to return exactly one plan.
3. No real unsaved draft exists.
4. Assert that the wizard auto-selects it and route/state get shift_plan_id.
5. Assert clicking Next goes to series-exceptions without creating a duplicate plan.

Required test 7 — multiple existing plans are not auto-selected
1. Mock listShiftPlans to return two plans.
2. Assert both are displayed.
3. Assert no auto-selection occurs.
4. Assert user must select one or explicitly create/edit before continuing.

Required test 8 — date window validation
1. Mock selectedPlanningRecord with planning_from=2026-07-01 and planning_to=2026-07-31.
2. Try shift plan planning_from=2026-06-30 or planning_to=2026-08-01.
3. Assert submit is blocked and createShiftPlan is not called.
4. Assert valid dates inside the window submit successfully.

Required test 9 — real draft behavior
1. Seed a real shift-plan draft in sessionStorage.
2. Mount shift-plan.
3. Assert the draft is restored.
4. Save successfully.
5. Assert the draft is cleared and final step is series-exceptions.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- root cause confirmed or corrected
- files changed
- tests added
- commands run
- proof that successful ShiftPlan save advances to series-exceptions
- proof that route sync no longer rolls the wizard back to shift-plan
- proof that selecting an existing ShiftPlan does not create duplicates
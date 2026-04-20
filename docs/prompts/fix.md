Add regression tests for the Customer New Plan wizard Shift Plan Next behavior.

Target:
When an existing ShiftPlan is selected and the user clicks Next, the wizard must advance to Series & exceptions. It must not remain on or return to Shift plan.

Test files to inspect/update:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- add a focused test if needed.

Required test 1 — submit result commits shift_plan_id before moveNext:
1. Mount new-plan at step=shift-plan with:
   - customer_id
   - order_id
   - planning_record_id
   - planning_entity_id
   - planning_entity_type=site
   - planning_mode_code=site
   - no shift_plan_id
2. Mock listShiftPlans to return:
   - id: shift-plan-1
   - name: "Objektschutz RheinForum Köln – Nordtor Juli 2026 / Shift plan"
   - planning_from: "2026-07-01"
   - planning_to: "2026-07-31"
3. Mock getShiftPlan for shift-plan-1.
4. Click the existing shift plan row.
5. Assert selection is visible locally.
6. Click Next.
7. Assert immediately before moveNext or after normalized submit:
   - wizardState.shift_plan_id === "shift-plan-1"
8. Assert current step becomes series-exceptions.
9. Assert final route query includes:
   - step=series-exceptions
   - shift_plan_id=shift-plan-1

Required test 2 — unchanged selected ShiftPlan does not create/update:
1. Select existing shift-plan-1.
2. Do not edit fields.
3. Click Next.
4. Assert:
   - createShiftPlan was not called
   - updateShiftPlan was not called
   - step is series-exceptions
   - shift_plan_id is committed.

Required test 3 — edited selected ShiftPlan updates and advances:
1. Select existing shift-plan-1.
2. Edit remarks or name.
3. Click Next.
4. Assert:
   - updateShiftPlan was called with version_no
   - returned id is committed
   - step is series-exceptions
   - route has shift_plan_id.

Required test 4 — no route rollback after successful submit:
1. Simulate an old route watcher callback or old route state:
   - route.query.step = shift-plan
   - no shift_plan_id or stale shift_plan_id
2. During goToNextStep, ensure routeSyncSuspended is true.
3. After final route sync, assert:
   - route is not shift-plan
   - route is series-exceptions
   - wizardState.current_step is series-exceptions.

Required test 5 — moveNext blocked diagnostic:
1. Mock submitShiftPlanStep to return success true but no shift_plan_id.
2. Assert parent does not silently remain on shift-plan.
3. Assert it sets a diagnostic/error state or throws in test/dev mode.
4. Assert this prevents hidden regressions.

Required test 6 — stale draft does not override saved selected plan:
1. Seed sessionStorage with a generic shift-plan draft:
   - selected_shift_plan_id: ""
   - default or unrelated values
2. Mount with existing ShiftPlan.
3. Select it and click Next.
4. Assert:
   - selected plan remains source of truth
   - stale draft is ignored
   - step advances.

Required test 7 — contentful matching draft still works:
1. Seed sessionStorage with:
   - selected_shift_plan_id: "shift-plan-1"
   - draft with changed remarks
2. Mount with shift_plan_id=shift-plan-1.
3. Assert draft applies.
4. Click Next.
5. Assert updateShiftPlan is called and step advances.

Required test 8 — create new ShiftPlan still advances:
1. Click create new shift plan.
2. Fill valid fields.
3. Mock createShiftPlan returns id shift-plan-new.
4. Click Next.
5. Assert:
   - createShiftPlan called once
   - shift_plan_id=shift-plan-new committed
   - step=series-exceptions.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- root cause confirmed or corrected
- files changed
- tests added
- commands run
- proof that parent receives/sets shift_plan_id before moveNext
- proof that current_step becomes series-exceptions
- proof that route does not roll back to shift-plan
- proof that unchanged selected ShiftPlan does not create duplicates.
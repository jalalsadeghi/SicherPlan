Add regression tests for atomic context restoration in the Customer New Plan wizard.

The real browser still fails, so tests must target the likely missing production invariant: setSavedContext must preserve downstream ids when they are provided in the same patch, and syncWizardFromRoute must not clear existing context merely because a query key is absent.

Files:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- add focused tests if useful.

Required test 1 — setSavedContext preserves shift_plan_id with planning_record_id:
1. Initialize wizard with customer_id and order_id.
2. Call setSavedContext({
   planning_record_id: 'planning-record-1',
   shift_plan_id: 'shift-plan-1'
})
3. Assert:
   - state.planning_record_id === 'planning-record-1'
   - state.shift_plan_id === 'shift-plan-1'
   - canEnterStep('series-exceptions') is true.

This test must fail on an implementation where planningRecordChanged blindly clears shift_plan_id.

Required test 2 — setSavedContext preserves shift_plan_id in full route restore:
1. Initialize wizard with customer_id only.
2. Call setSavedContext({
   order_id: 'order-1',
   planning_entity_id: 'site-1',
   planning_entity_type: 'site',
   planning_mode_code: 'site',
   planning_record_id: 'planning-record-1',
   shift_plan_id: 'shift-plan-1'
})
3. Assert all ids are preserved.
4. Assert canEnterStep('series-exceptions') is true.
5. Assert applyRequestedStep('series-exceptions') resolves to series-exceptions.

Required test 3 — setSavedContext preserves series_id with shift_plan_id:
1. Initialize wizard with customer_id, order_id, planning_record_id.
2. Call setSavedContext({
   shift_plan_id: 'shift-plan-1',
   series_id: 'series-1'
})
3. Assert:
   - state.shift_plan_id === 'shift-plan-1'
   - state.series_id === 'series-1'
4. Then applyRequestedStep('series-exceptions') remains valid.

Required test 4 — context change without downstream ids still clears correctly:
1. Start with:
   planning_record_id='planning-record-1'
   shift_plan_id='shift-plan-1'
   series_id='series-1'
2. Call setSavedContext({ planning_record_id: 'planning-record-2' }) without shift_plan_id.
3. Assert:
   - planning_record_id is 'planning-record-2'
   - shift_plan_id is cleared
   - series_id is cleared.
4. This proves preservation only happens when downstream ids are explicitly provided.

Required test 5 — route sync absent shift_plan_id must not clear current state after bootstrap:
1. Mount new-plan with valid state:
   current_step=series-exceptions
   shift_plan_id='shift-plan-1'
   planning_record_id='planning-record-1'
   order_id='order-1'
   customer_id='customer-1'
2. Simulate route watcher with route query missing shift_plan_id but otherwise same upstream context.
3. Assert:
   - shift_plan_id remains 'shift-plan-1'
   - current_step remains series-exceptions
   - route is repaired or ignored, but state is not cleared.

Required test 6 — direct valid Step 8 URL works:
1. Mount direct URL:
   step=series-exceptions
   customer_id=customer-1
   order_id=order-1
   planning_record_id=planning-record-1
   shift_plan_id=shift-plan-1
2. Assert:
   - wizardState.shift_plan_id === 'shift-plan-1'
   - rendered step is series-exceptions
   - listShiftSeries is called.

Required test 7 — direct invalid Step 8 URL still falls back:
1. Mount direct URL:
   step=series-exceptions
   customer_id=customer-1
   order_id=order-1
   planning_record_id=planning-record-1
   no shift_plan_id
2. Assert:
   - rendered step is not series-exceptions
   - fallback is shift-plan or furthest valid step.

Required test 8 — real browser-equivalent flow:
1. Mount at step=shift-plan with planning_record_id and no shift_plan_id.
2. Select existing ShiftPlan.
3. Click Next.
4. Assert after all loaders and watcher flushes:
   - wizardState.shift_plan_id is still set
   - current_step is series-exceptions
   - route step is series-exceptions
   - route shift_plan_id is set
   - rendered panel is series-exceptions.

Required test 9 — syncWizardFromRoute should not pass empty strings for absent keys:
1. Spy on setSavedContext from new-plan.vue or expose a test seam.
2. Trigger route watcher with a route missing shift_plan_id.
3. Assert the patch either omits shift_plan_id or explicitly marks preserve; it must not pass shift_plan_id: '' unless this was an intentional clear action.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- production files changed
- tests added
- which tests would fail on the old implementation
- proof that setSavedContext preserves shift_plan_id atomically
- proof that route missing shift_plan_id does not clear committed state after bootstrap
- proof that direct valid and invalid Step 8 URLs behave correctly.
Add regression tests that reproduce the real remaining Shift Plan rollback bug.

The previous tests passed but the real browser still fails. The new tests must simulate this exact evidence:
- Next from shift-plan reaches or begins loading series-exceptions.
- GET /shift-plans/{id}/series equivalent occurs.
- Then a stale route watcher tries to apply step=shift-plan or missing shift_plan_id.
- The wizard must ignore/repair that stale route and remain on series-exceptions.

Test files:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- create a focused route-race test if needed.

Required test 1 — entered series then stale route tries rollback:
1. Mount new-plan at:
   step=shift-plan
   customer_id=84bad50d-209c-491e-b86b-13c7788c7620
   order_id=7eb5cee5-92ab-442b-8433-b9d8b94949e2
   planning_record_id=1606e67d-dc16-4724-8640-843c02e4f16d
   planning_entity_id=cf297d3f-e149-4448-86b6-f6cb70f6da58
   planning_entity_type=site
   planning_mode_code=site
2. Mock existing ShiftPlan:
   id=8ced3d43-8c8b-42eb-b713-518204ffe0ad
3. Select the ShiftPlan row.
4. Click Next.
5. Assert:
   - current_step becomes series-exceptions
   - listShiftSeries or GET /shift-plans/{id}/series mock is called.
6. Then simulate a stale route watcher callback with:
   step=shift-plan
   no shift_plan_id
   same customer_id/order_id/planning_record_id.
7. Assert:
   - current_step remains series-exceptions
   - wizardState.shift_plan_id remains 8ced3d43-8c8b-42eb-b713-518204ffe0ad
   - final route is repaired back to step=series-exceptions with shift_plan_id.
8. Assert no visual rollback to shift-plan.

Required test 2 — stale router.replace completion after final transition:
1. Mock router.replace to allow controlled promises:
   - old replace A: step=shift-plan without shift_plan_id
   - final replace B: step=series-exceptions with shift_plan_id
2. Let B resolve first and A resolve after.
3. Assert A cannot rollback the wizard state or route.
4. Assert route watcher ignores A as stale.

Required test 3 — route-to-state may not clear shift_plan_id after internal transition:
1. Put wizardState into:
   current_step=series-exceptions
   shift_plan_id=shift-plan-1
   planning_record_id=planning-record-1
   order_id=order-1
   customer_id=customer-1
2. Call or simulate syncWizardFromRoute with routeState:
   step=shift-plan
   shift_plan_id=""
   same customer/order/planning_record.
3. Assert:
   - shift_plan_id remains shift-plan-1
   - current_step remains series-exceptions
   - stale route is ignored or repaired.

Required test 4 — real external navigation to earlier step still works:
1. From series-exceptions with shift_plan_id present, simulate explicit user stepper click Previous or click shift-plan step button.
2. Assert moving back to shift-plan works.
3. The stale route guard must not prevent deliberate earlier-step navigation.
4. Context shift_plan_id may remain available so the saved plan can be reloaded.

Required test 5 — direct URL without shift_plan_id still falls back correctly:
1. Load URL with step=series-exceptions but no shift_plan_id.
2. Assert wizard falls back to shift-plan.
3. This proves the guard only protects internal stale routes, not invalid external routes.

Required test 6 — no duplicate create/update for unchanged selected plan:
1. Select existing ShiftPlan.
2. Click Next.
3. Assert createShiftPlan and updateShiftPlan are not called.
4. Assert listShiftSeries is called.
5. Assert current step remains series-exceptions after all route watcher flushes.

Required test 7 — after Next, wait for all async loaders:
1. Click Next.
2. Await all mocked promises:
   - getPlanningRecord
   - listPlanningRecordAttachments
   - listShiftPlans
   - getShiftPlan
   - listShiftTemplates
   - listShiftTypeOptions
   - listShiftSeries
3. Assert final UI is still series-exceptions.
4. This test must fail on the old implementation if stale route/state rollback exists.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- the reproduced route-race/rollback sequence
- tests added
- files changed
- commands run
- proof that /series loading no longer results in visual rollback
- proof that invalid direct URL still falls back correctly
- proof that explicit user navigation back to shift-plan still works.
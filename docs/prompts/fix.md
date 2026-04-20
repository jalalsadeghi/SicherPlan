Add regression tests for the Customer New Plan wizard Planning record step.

Target behavior:
A PlanningRecord created or already existing for an Order must be visible and usable inside the wizard, and Next must advance to planning-record-documents after a successful save.

Inspect/update tests under:
- web/apps/web-antd/src/views/sicherplan/customers/
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic*.smoke.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- add a dedicated composable test for use-customer-new-plan-wizard.ts if missing

Required test 1 — setSavedContext atomic planning record save:
1. Initialize wizard state with:
   - customer_id
   - order_id
   - current_step = planning-record-overview
2. Call setSavedContext({
   planning_entity_id: 'site-1',
   planning_entity_type: 'site',
   planning_mode_code: 'site',
   planning_record_id: 'planning-record-1'
})
3. Assert state.planning_record_id === 'planning-record-1'.
4. Assert canEnterStep('planning-record-documents') is true.
5. Assert moveNext() from planning-record-overview goes to planning-record-documents.

Required test 2 — context-only change still clears planning_record_id:
1. Start with an existing planning_record_id.
2. Call setSavedContext({
   planning_entity_id: 'different-site',
   planning_entity_type: 'site',
   planning_mode_code: 'site'
})
without planning_record_id.
3. Assert planning_record_id is cleared and downstream shift/series ids are cleared.

Required test 3 — existing PlanningRecords are listed in wizard:
1. Mount new-plan route with:
   - customer_id
   - order_id
   - planning_entity_id
   - planning_entity_type=site
   - planning_mode_code=site
   - step=planning-record-overview
2. Mock listPlanningRecords to return a saved record for the order/mode/context:
   - name: "Objektschutz RheinForum Köln – Nordtor Juli 2026"
   - planning_from: "2026-07-01"
   - planning_to: "2026-07-31"
   - release_state: "draft"
3. Assert the wizard renders this record in an existing PlanningRecords list.
4. Assert clicking the row loads the form fields.

Required test 4 — context-only draft must not override saved backend record:
1. Seed sessionStorage with a planning-record-overview draft that contains only planning_context and no real form values.
2. Mock listPlanningRecords/getPlanningRecord to return the saved record.
3. Mount the wizard at planning-record-overview.
4. Assert:
   - no misleading “Unsaved draft restored” appears for the context-only draft
   - the saved PlanningRecord is visible
   - the form can be populated from the saved record
   - the empty draft does not clear name/from/to fields.

Required test 5 — real unsaved draft is preserved:
1. Seed sessionStorage with a real planning-record-overview draft:
   - name
   - planning_from
   - planning_to
   - notes
2. Also mock an existing backend PlanningRecord.
3. Mount the wizard.
4. Assert the user draft is not overwritten automatically.
5. Assert the existing backend PlanningRecord list is still visible so the user can intentionally select it.

Required test 6 — successful create advances:
1. Mount the wizard at planning-record-overview with order_id and planning context.
2. Fill:
   - planning record name
   - planning_from
   - planning_to
   - site watchbook note or notes
3. Mock createPlanningRecord to return a saved PlanningRecord with id.
4. Click Next.
5. Assert:
   - createPlanningRecord was called once with correct order_id, tenant_id, planning_mode_code, and site_detail.site_id
   - saved-context preserves planning_record_id
   - route query contains planning_record_id
   - current step becomes planning-record-documents
   - the wizard does not bounce back to planning-record-overview
   - listPlanningRecords is refreshed and includes the saved record.

Required test 7 — multiple matching records:
1. Mock two PlanningRecords for the same order/mode/context.
2. Assert both are displayed.
3. Assert no automatic selection happens unless route/wizardState specifies planning_record_id.

Required test 8 — admin page parity:
1. Compare the listPlanningRecords filters used in the wizard with PlanningOrdersAdminView.vue.
2. Assert wizard uses order_id and planning_mode_code at minimum.
3. If backend now supports planning_entity_type/planning_entity_id filters, assert those are also used.

Commands to run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

If backend/API schemas are changed:
- run the relevant backend pytest suite for planning records
- run backend type/lint checks used by this repository
- update frontend API types accordingly

Final output must include:
- root cause confirmed or corrected
- files changed
- tests added
- commands run
- proof that Next advances after save
- proof that existing PlanningRecords for the order/mode/context appear in the wizard
- any manual QA steps still required.
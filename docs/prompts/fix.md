You are working in the SicherPlan repository.

This task follows the patch adding existing-order selection to the Customer New Plan Wizard.

Source document:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Do a focused QA/hardening pass for the Order Details step after adding Use Existing Order / Create New Order behavior.

Do not add unrelated features.
Do not change backend APIs.
Do not change other wizard steps unless fixing a direct regression from this patch.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Validation checklist:

1. Existing order loading
- listCustomerOrders is called with the selected customer_id.
- Archived orders are not shown unless the branch convention says otherwise.
- Empty state is clear when no order exists.
- Orders show order_no, title, service dates, and release state.

2. Existing order selection
- Selecting an existing order calls getCustomerOrder.
- The form hydrates correctly.
- selectedOrder is set.
- order_id is stored in wizard state.
- order_id is reflected in route query.
- Refresh keeps the selected order.

3. Existing order editing
- Editing a selected order and clicking Next calls updateCustomerOrder.
- It does not call createCustomerOrder.
- It does not create duplicate orders.
- version_no is handled correctly.

4. Create new mode
- Switching to Create new order clears selected order safely.
- Next calls createCustomerOrder.
- New order_id is persisted into state/route.
- Existing order list remains available if user switches back.

5. Draft persistence
- Unsaved create-new draft does not overwrite selected existing order.
- Existing-order edit draft does not leak into create-new mode.
- Customer switch clears or isolates drafts.
- Browser refresh restores correct selected order/draft behavior.

6. Downstream steps
- Equipment Lines loads lines for selected existing order.
- Requirement Lines loads lines for selected existing order.
- Order Documents loads documents for selected existing order.
- Existing Save/Update-vs-Next behavior remains intact.

7. Non-regression
- Planning step still works.
- Step 1 -> Step 2 route context still works.
- Canonical /admin/planning-orders is unchanged.
- Final handoff is unaffected.

Tests:
Run and update as needed:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any focused new test for existing order selection

Required final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA checklist result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches the existing-order selection proposal.
Avoid unrelated refactors.
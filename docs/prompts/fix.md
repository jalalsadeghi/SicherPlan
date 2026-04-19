You are working in the SicherPlan repository.

This task follows the patch that scopes existing orders in the Customer New Plan Wizard by selected planning entity.

Source document:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Do a focused QA/hardening pass to ensure the Order Details existing-order list only shows orders related to the selected planning entry.

Do not add unrelated features.
Do not change backend APIs beyond the scoped filter already added.
Do not change unrelated wizard steps.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- backend/app/modules/planning/router.py
- backend/app/modules/planning/schemas.py
- backend/app/modules/planning/repository.py
- backend/app/modules/planning/order_service.py
- backend/tests/modules/planning/
- related frontend tests under web/apps/web-antd/src/views/sicherplan/customers/

Validation checklist:

1. Backend filter contract
Confirm:
- /api/planning/tenants/{tenant_id}/ops/orders accepts planning_entity_type and planning_entity_id.
- Existing calls without those filters still work.
- Invalid or incomplete planning entity filters are handled consistently.
- Tenant isolation is preserved.

2. Site filtering
Confirm:
- order is included only if it has a PlanningRecord with SitePlanDetail.site_id matching planning_entity_id.
- unrelated orders for the same customer are excluded.
- duplicate orders are not returned when multiple matching planning records exist.

3. Event venue filtering
Confirm:
- event_venue uses EventPlanDetail.event_venue_id.

4. Trade fair filtering
Confirm:
- trade_fair uses TradeFairPlanDetail.trade_fair_id.

5. Patrol route filtering
Confirm:
- patrol_route uses PatrolPlanDetail.patrol_route_id.

6. Existing filters still compose
Confirm the planning entity filter still works with:
- customer_id
- search
- release_state
- lifecycle_status
- service_from/service_to
- include_archived

7. Frontend wizard
Confirm:
- loadCustomerOrderRows passes planning_entity_type/planning_entity_id when available.
- UI shows only scoped orders.
- Empty state is clear when no related orders exist.
- "Create new order" remains available.
- Selecting scoped order hydrates the form.
- selected order writes order_id to route/state.
- Next updates selected order instead of creating duplicates.

8. Non-regression
Confirm:
- Step 1 Planning still works.
- Order Details create-new mode still works.
- Equipment/Requirement lines still load from selected order.
- Optional document steps still work.
- Planning Record step still works.
- canonical /admin/planning-orders still lists all customer orders as before.

Tests:
Run and update as needed:
- backend planning/order tests
- frontend new-plan tests
- new-plan-epic3.smoke.test.ts
- new-plan-wizard.test.ts

Add missing tests if needed:
- scoped order list excludes unrelated same-customer order
- frontend passes filters
- order selection still works after filtering

Manual QA checklist:
- Select planning entry RheinForum Köln – Objekt Nord.
- Order Details shows only A-4002.
- It does not show OBJECT_GUARD May 2026.
- Select A-4002 and verify editable fields.
- Click Next and verify Equipment Lines load for A-4002.
- Browser refresh and verify selected order remains scoped/loaded.
- Switch to another planning entry and verify different order list.
- Create new order still works.

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches the planning-scoped order proposal.
Avoid unrelated refactors.
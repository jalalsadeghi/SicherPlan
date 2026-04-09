You are working in the SicherPlan monorepo.

Goal:
Align Planning Setup scoping with the documented product design.

Authoritative business rule from project docs:
- `Requirement types` and `Equipment catalog` are reusable tenant-level catalogs.
- `Sites`, `Event venues`, `Trade fairs`, and `Patrol routes` are customer-linked operational master data.
- `Trade fair zones` belong to a trade fair.
- `Patrol checkpoints` belong to a patrol route.

Current implementation drift to fix:
- The current repo requires `customer_id` for `ops.requirement_type` and `ops.equipment_item`.
- P-01 (`admin/planning`) shows customer selection for these two entities.
- P-02 (`admin/planning-orders`) filters requirement types and equipment by selected customer.
- Order-service currently enforces requirement-type/customer matching.
- This behavior is not aligned with the uploaded design documents.

Target behavior:
1. Tenant-level, define once and reuse everywhere in tenant:
   - Requirement types
   - Equipment catalog
2. Customer-linked:
   - Sites
   - Event venues
   - Trade fairs
   - Patrol routes
3. Child entities remain unchanged:
   - Trade fair zones under trade fairs
   - Patrol checkpoints under patrol routes

Required changes

A) Backend/domain alignment
Inspect and update the relevant planning backend files, especially:
- `backend/app/modules/planning/models.py`
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/service.py`
- `backend/app/modules/planning/ops_service.py`
- `backend/app/modules/planning/order_service.py`
- any related repository layer files
- add a new Alembic migration

Implement this rule:
- `ops.requirement_type` and `ops.equipment_item` must behave as tenant-scoped catalogs, not customer-scoped records.
- Remove customer-scoping behavior from those two entities.
- Keep customer-scoping for `site`, `event_venue`, `trade_fair`, and `patrol_route`.

Migration strategy:
- Add a safe migration that removes the requirement that `customer_id` must be set for `requirement_type` and `equipment_item`.
- Prefer backward-compatible migration behavior.
- If dropping the column completely is too invasive for this iteration, make it nullable and stop using it in business logic and UI.
- Preserve existing data.
- Because code uniqueness is already tenant-level, do not introduce duplicate-code regressions.

Business logic changes:
- Remove requirement-type/customer mismatch validation from order creation/update logic.
- Ensure equipment items are treated as tenant-wide catalog items.
- Keep customer-bound validation for site/event venue/trade fair/patrol route.

B) P-01 Planning Setup UI
Inspect and update:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`
- any related helper/i18n/test files

Implement:
- Requirement types and equipment items must no longer require customer selection in the form.
- Sites, event venues, trade fairs, and patrol routes must still require customer selection.
- Replace generic “all non-child entities use customer” logic with an explicit scoping model, for example:
  - tenant-scoped entities
  - customer-scoped entities
  - child entities

Also update:
- import template / CSV expectations if they currently require customer_id for requirement_type or equipment_item
- validation messages if needed
- relevant tests

C) P-02 Orders & Planning Records UI
Inspect and update:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningOrders.helpers.js`
- related tests / i18n files

Implement:
- Requirement type selector must show all tenant-level requirement types, regardless of selected customer.
- Equipment item selector must show all tenant-level equipment items, regardless of selected customer.
- Keep customer filtering for:
  - event venues
  - sites
  - trade fairs
  - patrol routes
- Do not change the current customer filtering for customer-linked operational entities.

D) Tests
Update or add tests for:
- tenant-scoped requirement types in P-01
- tenant-scoped equipment catalog in P-01
- P-02 requirement type selector no longer filtered by customer
- P-02 equipment selector no longer filtered by customer
- customer-linked entities still filtered by customer
- order-service no longer rejects tenant-level requirement types because of customer mismatch

Acceptance criteria
1. I can create one requirement type once in the tenant and reuse it for multiple customers’ orders.
2. I can create one equipment item once in the tenant and reuse it for multiple customers’ orders.
3. Sites, event venues, trade fairs, and patrol routes remain customer-linked.
4. Trade fair zones and patrol checkpoints remain child entities.
5. P-01 no longer asks for customer on requirement type / equipment item.
6. P-02 still filters location-like entities by customer, but not requirement types or equipment items.
7. No regression in planning order creation, equipment lines, requirement lines, or planning-record creation.
8. Alembic migration is included and application/tests pass.

Implementation notes
- Keep changes domain-driven and minimal.
- Do not redesign unrelated screens.
- Do not loosen authorization rules.
- Keep naming and style consistent with existing SicherPlan patterns.

Deliverables
- code changes
- migration
- updated tests
- short summary of what changed
- any remaining compatibility notes
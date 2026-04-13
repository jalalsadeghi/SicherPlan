You are working in the SicherPlan monorepo on the latest main branch.

Task:
Validate and improve the `Service category` field in Planning -> admin/planning-orders -> Order details.

Problem statement:
The current `Service category` field is rendered as a plain text input, but the project model uses the name `service_category_code`, which suggests a controlled code field rather than arbitrary free text.

What you must determine first:
1. Should `Service category` remain a textbox, or should it become a select/searchable select?
2. If it should become a select, should its options come from:
   - a seeded lookup/catalog, or
   - a tenant-managed catalog that users must maintain first?
3. Validate this against the project’s existing architecture and docs instead of assuming.

Key facts already observed:
- `ops.customer_order` stores `service_category_code` as a code field.
- `CustomerOrderCreate` / `CustomerOrderUpdate` also use `service_category_code`.
- The current UI still renders it as a free text input in `PlanningOrdersAdminView.vue`.
- The docs separate `service category` on the order from `planning mode` on the planning record.
- The project architecture prefers stable business dictionaries in `core.lookup_value`.
- Current lookup seeds include domains like `legal_form`, `invoice_layout`, `invoice_delivery_method`, `dunning_policy`, `unit_of_measure`, etc.
- There is currently no confirmed existing lookup domain for `service_category`.
- Core admin currently exposes tenant management for `unit_of_measure`, not for `service_category`.

Files to inspect first:
Frontend
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts`
- any planning-order helper/i18n files

Backend
- `backend/app/modules/planning/models.py`
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/service.py`
- `backend/app/modules/planning/repository.py`

Lookup / seed / admin
- `backend/app/modules/core/lookup_seed.py`
- `backend/app/modules/core/admin_service.py`
- `backend/app/modules/core/admin_repository.py`
- `web/apps/web-antd/src/sicherplan-legacy/views/CoreAdminView.vue`
- any core admin API/schema files related to lookup values

Supporting docs to align with
- `docs/engineering/lookup-seeding.md`
- `docs/configuration/go-live-seed-baseline.md`
- any migration/template docs referencing `service_category_code`

Validation rules you must apply:
A. Do not automatically equate `service_category_code` with `planning_mode_code`.
   They are related but not proven to be identical.
B. If the field is truly a code field, prefer a controlled selector over free text.
C. If no existing catalog exists yet, design the smallest correct catalog path instead of leaving the field as raw free text.
D. Preserve backward compatibility for already-saved free-text values.

Preferred target direction unless validation disproves it:
- Convert `Service category` from textbox to select/searchable select.
- Back it with a lookup-driven option source.
- Add a proper initial seed/catalog for service categories.
- Make the management path explicit if tenant-managed behavior is the right architectural choice.

Important design decision you must make and justify:
Choose one of these and explain why:
1. `service_category` should be a platform-managed lookup domain with system seed values.
2. `service_category` should be a tenant-extensible lookup domain with tenant-owned values.
3. `service_category` should remain free text.
You must justify the choice using the current docs, data model, and lookup governance.

My default recommendation for you to validate:
- This should be a select, not a textbox.
- It should not depend on the order form user typing arbitrary codes.
- It should start from a seeded catalog.
- Only if the business semantics clearly require tenant-specific customization should it become tenant-extensible.

If you conclude it should be a select, implement:
1. a lookup/catalog source for service categories
2. a selector UI in Order details
3. proper placeholder text
4. safe handling for legacy stored values not present in the option set
5. any needed seed additions
6. any needed admin path additions, but only if your ownership decision requires them

Backward compatibility requirements:
- Existing records with legacy free-text `service_category_code` values must still open in Edit mode.
- If a stored value is not in the current option set, it must remain visible/selectable so records are not broken.
- Do not silently destroy or remap existing values without explicit migration logic.

Do NOT do these:
- Do not hardcode a random static list in the component without proper ownership reasoning.
- Do not force `service_category_code` to equal `planning_mode_code` without proof.
- Do not change unrelated planning fields.
- Do not break existing orders.

Acceptance criteria:
1. Codex explicitly states whether textbox or select is correct.
2. Codex explicitly states whether the option source should be seeded lookup or tenant-maintained catalog.
3. If select is correct, the UI uses a proper selector instead of raw text.
4. Legacy stored values still open safely in Edit mode.
5. The chosen solution fits the existing lookup governance.
6. Tests are added/updated appropriately.

Tests to add/update:
- backend tests for service_category_code create/get/update behavior under the chosen model
- lookup seed / admin tests if a new domain is introduced
- frontend test for Order details field behavior
- compatibility test for legacy stored values not in the current option list

Required output:
1. Validation result: textbox vs select
2. Validation result: seeded lookup vs tenant-managed catalog
3. Why that decision is correct
4. Files changed
5. Compatibility handling
6. Tests added/updated
7. Final self-check confirming you validated the recommendation instead of assuming it
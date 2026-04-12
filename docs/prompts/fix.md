You are working in the SicherPlan monorepo on the latest main branch.

Task:
Refine the recently introduced `Unit of measure` select for Planning -> admin/planning -> Planning Setup -> Equipment catalog / Equipment item editor.

Current user feedback:
1. The helper sentence below the field says:
   "Uses a tenant-extensible unit catalog instead of free text."
   This sentence should NOT be shown in the form.
2. The field has no placeholder, which makes the UI confusing.
3. A Tenant Admin currently has no clear way to add or maintain these options. We need a proper admin path.

What you must do:
1. Remove the unnecessary helper sentence from the Equipment item editor UI.
2. Add a clear placeholder to the `Unit of measure` field.
3. Validate and implement the correct management path for Tenant Admins to maintain unit-of-measure options.
4. Validate your solution against the current architecture instead of assuming the right place.

Expected behavior:
- In the Equipment item editor, the field should be clean and simple.
- The user should immediately understand that they must select a value.
- Tenant admins should have a discoverable and role-appropriate place to manage available units.

Validation questions you must answer before finalizing:
A. Is there already an existing admin UI or backend path for tenant-extensible lookup/business-list maintenance that can be reused?
B. If yes, wire this feature to that existing path and make the UX discoverable.
C. If no, add the smallest correct management path consistent with SicherPlan architecture.

Preferred architectural rule:
- Do NOT make users manage unit options inside the Equipment item form itself unless there is no better existing admin surface.
- Prefer a tenant-admin management path aligned with Administration / tenant-scoped business-list management.
- If the project already uses lookup-backed business catalogs, reuse that mechanism instead of inventing a parallel one.

Files to inspect first:
Frontend
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningAdmin.helpers.js`
- relevant i18n/messages files
- any admin/tenant-settings/lookup-related views if present

Backend
- `backend/app/modules/planning/models.py`
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/service.py`
- `backend/app/modules/planning/repository.py`
- `backend/app/modules/planning/router.py`
- any core/lookup-related services, schemas, repositories, or routers
- any tenant settings or business-list management APIs already available

Required UX improvements:
1. Remove the helper text under the `Unit of measure` field.
2. Add a placeholder such as:
   - English: `Select unit of measure`
   - German: `Maßeinheit auswählen`
   Use the project’s i18n/message conventions.
3. If the field is searchable, ensure the placeholder appears correctly in the empty state.
4. Keep legacy stored values safe:
   - If a record contains an older value not in the current catalog, it must still open in Edit mode.
   - The legacy value must remain visible/selectable until normalized.

Required admin-manageability improvement:
You must determine the correct answer to:
“How can a Tenant Admin add more unit options, and where?”
Then implement one of these, based on what the current architecture supports best:

Option A — Reuse existing admin lookup/list management
- If such a page/API already exists, connect the unit catalog to it.
- Make the path discoverable in the UI.
- Prefer a small affordance like a subtle admin-only action, link, or route hint outside the main field chrome, not a noisy helper sentence.

Option B — Add the minimal correct management path
- If no reusable admin surface exists, create the smallest tenant-admin-safe management path consistent with current architecture.
- Prefer an admin/business-list management surface, not inline free-form editing in the Equipment item form.
- Keep permissions tenant-scoped and admin-only.

Important constraint:
- Do not reintroduce free text for regular users just because admin management is missing.
- Solve the management path properly.

What not to do:
- Do not leave the helper sentence in place.
- Do not keep the field without placeholder text.
- Do not hardcode a hidden magic list without a maintenance path.
- Do not put unrelated explanatory text into the form just to compensate for missing UX.
- Do not break existing records or legacy values.

Acceptance criteria:
1. The helper sentence under `Unit of measure` is removed.
2. The field has a proper localized placeholder.
3. A Tenant Admin has a clear, validated place to manage available unit options.
4. Existing records with legacy values still open safely in Edit mode.
5. The implementation follows the existing tenant-scoped architecture.
6. Tests cover the refined behavior.

Tests to add/update:
- frontend test for placeholder rendering and absence of helper text
- frontend/admin-path discoverability test if applicable
- backend test for management path if new backend support is added
- compatibility test for legacy stored values not present in the current option set

Required output from you:
1. Validation result: where Tenant Admin should manage unit options
2. Why that location is correct
3. Files changed
4. UX changes made
5. Compatibility handling
6. Tests added/updated
7. Final self-check confirming you validated the proposal against the current architecture
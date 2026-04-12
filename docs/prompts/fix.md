You are working in the SicherPlan repository.

Goal:
Add the missing UI management for employee `function types` and `qualification types`
inside the Employees workspace, so the frontend matches the documented scope and the
already-existing backend API.

Important:
This is a UI coverage gap fix, not a backend invention task.
The backend endpoints for these catalogs already exist.
Do not move this responsibility into Planning or other modules.

Before coding:
1. Read `AGENTS.md`.
2. Keep the change set focused on the Employees workspace and its related API wiring.
3. Do not do unrelated refactors.
4. Verify the current repo state first and describe exactly what is missing.

Files to inspect first:
Frontend:
- `web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.helpers.js`
- `web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts`
- any employee workspace tests

Routing / workspace registration:
- `web/apps/web-antd/src/views/sicherplan/module-registry.ts`
- any relevant route/module config for `/admin/employees`

Backend contracts already expected to exist:
- `backend/app/modules/employees/router.py`
- related employees schemas/services if needed only for contract confirmation

Source-of-truth constraints you must respect:
- Employees workspace is documented to include:
  - employee list/detail/lifecycle
  - availability/absences/etc.
  - credentials and badge output
  - function/qualification catalogs
  - employee qualifications and proofs
- Data model defines:
  - `hr.function_type`
  - `hr.qualification_type`
- Planning reads these catalogs later; it does not own them.
- OpenAPI already includes:
  - GET/POST/PATCH `/api/employees/tenants/{tenant_id}/employees/catalog/function-types`
  - GET/POST/PATCH `/api/employees/tenants/{tenant_id}/employees/catalog/qualification-types`

What you must verify first:
1. The current Employees UI uses function/qualification options in qualification forms but does not expose a real catalog-management UI.
2. There is no discoverable create/update flow for these catalogs in the current workspace.
3. The missing UI is the real reason the user cannot create these records.
4. The backend contracts are already sufficient for a first UI implementation.

Required implementation outcome:
A. Add a clear, discoverable catalog-management area inside `/admin/employees`.
B. Support at minimum:
   - list function types
   - create function type
   - edit/update function type
   - list qualification types
   - create qualification type
   - edit/update qualification type
C. Keep this inside the Employees workspace, not Planning.
D. Make the catalogs usable immediately by the existing qualifications editor in the same workspace.
E. Preserve tenant scope, auth/session behavior, and role checks.
F. Keep HR-private data boundaries intact; these catalogs are tenant-scoped master data, not private employee fields.
G. Do not rely on the dev/test bootstrap endpoint as the primary UX.
H. If helpful, add a dedicated tab or subpanel called something like `Catalogs`, with two sections:
   - Function types
   - Qualification types

Preferred UX:
1. Add an Employees detail/workspace sub-area for catalogs that is easy to find.
2. Each catalog section should show:
   - existing records
   - status / active flag if applicable
   - create/edit form
3. Recommended fields:
   Function type:
   - code
   - label
   - category_code
   - is_active
   Qualification type:
   - code
   - label
   - qualification_class
   - requires_valid_until
   - default_validity_months
   - is_active (if supported by contract)
4. After create/update, refresh the options used by the employee qualifications editor so the new catalog entries can be selected immediately.
5. If the current workspace has no selected employee, the catalog area should still be usable, because catalogs are tenant-scoped master data, not employee-specific records.

Validation / behavior expectations:
- clear empty states
- required-field validation
- duplicate-code handling based on backend truth
- explicit save/cancel flows
- no hidden dependency on selecting an employee first, unless the existing architecture truly forces it (avoid that if possible)

Tests to add or update:
1. Employees workspace renders catalog-management UI.
2. Function types can be listed, created, and updated.
3. Qualification types can be listed, created, and updated.
4. Newly created catalog entries appear in the qualification editor options.
5. Catalog UI works without selecting a specific employee record first.
6. Tenant-scoped auth/session behavior still works.
7. No regression to existing employee file editing and qualification proof flows.

What not to do:
- Do not invent new backend endpoints if the existing ones are sufficient.
- Do not move catalog management into Planning.
- Do not hide catalog management behind dev/test bootstrap-only behavior.
- Do not make catalog editing depend on having an employee selected unless unavoidable.
- Do not refactor the whole Employees workspace.

Final response format:
1. Short diagnosis
2. Exact repo state found
3. Exact files changed
4. What catalog-management UI was added
5. How it connects to the existing qualification editor
6. Tests/validation run and results
7. Remaining assumptions
8. Self-validation summary

Extra instruction:
Challenge your own solution before finalizing.
Specifically verify:
- a user can create a function type from `/admin/employees`
- a user can create a qualification type from `/admin/employees`
- the newly created entries are selectable in the qualifications editor
If any of those fail, the fix is incomplete.
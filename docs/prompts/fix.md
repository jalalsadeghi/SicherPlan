You are working in the SicherPlan repository.

Task title:
Fix empty Function ID / Qualification ID dropdowns in Customer Rate Lines by adding HR catalog bootstrap data and proper empty-state UX.

Problem:
In Customer Admin > Commercial > Pricing rules > Rate lines, the dropdowns for:
- Function ID
- Qualification ID
are empty and only show:
- "No active entries are available in the HR function catalog yet."
- "No active entries are available in the HR qualification catalog yet."

Context:
- Real HR catalogs already exist in backend:
  - hr.function_type
  - hr.qualification_type
- Employees API already exposes endpoints for them:
  - GET /api/employees/tenants/{tenant_id}/employees/catalog/function-types
  - POST /api/employees/tenants/{tenant_id}/employees/catalog/function-types
  - GET /api/employees/tenants/{tenant_id}/employees/catalog/qualification-types
  - POST /api/employees/tenants/{tenant_id}/employees/catalog/qualification-types
- Customer pricing now depends on these catalogs for rate line references.
- Current issue is not missing backend structure; it is missing usable catalog entries for the current tenant and poor UX when the catalogs are empty.

Business decision:
This project is still in test/development phase.
There is no need to preserve an empty-demo experience.
We want these dropdowns to show usable options immediately in dev/test environments.

Goal:
1. Ensure Function ID and Qualification ID dropdowns can show real options for the current tenant.
2. Add development/test bootstrap seed data for HR function and qualification catalogs.
3. Improve the empty-state UX so users understand what to do when catalogs are empty.
4. Keep HR catalog as the single source of truth. Do not create a CRM shadow catalog.

Scope:
Implement a robust fix that covers both:
- backend sample/demo seed/bootstrap
- frontend empty-state behavior

Likely files to inspect/change:
Backend:
- backend/app/modules/employees/models.py
- backend/app/modules/employees/schemas.py
- backend/app/modules/employees/router.py
- backend/app/modules/employees/qualification_service.py
- backend/app/modules/employees/repository.py
- backend/app/modules/customers/schemas.py
- backend/app/modules/customers/commercial_service.py
- backend/app/modules/customers/router.py
- backend/app/modules/customers/repository.py
- backend/app/message_catalog.py
- backend/alembic/versions/*.py
- any existing seed/bootstrap/dev fixture locations
- tests under backend/tests/modules/employees/ and backend/tests/modules/customers/

Frontend:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/customers.ts
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerCommercial.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts
- relevant frontend tests

Implementation requirements

A) Diagnose current loading path
1. Verify how the customer rate-line form currently receives function and qualification options.
2. Confirm whether it reads them from:
   - customer reference-data,
   - a dedicated customer commercial catalog bridge,
   - or direct employee catalog calls.
3. Keep the architecture clean. Prefer customer-facing read-only consumption if already implemented.

B) Add dev/test bootstrap data
4. Add a development/test bootstrap mechanism that creates sample entries for HR catalogs when they are empty for a tenant.
5. Do NOT auto-create duplicates if entries already exist.
6. Seed at least these sample function types:
   - SEC_GUARD / Security agent
   - SHIFT_SUP / Shift supervisor
   - DISPATCH / Dispatch support
   - FIRE_WATCH / Fire watch
7. Seed at least these sample qualification types:
   - G34A / 34a certified
   - FIRST_AID / First aid
   - FIRE_SAFETY / Fire safety
   - CROWD_CONTROL / Crowd control
8. Seeded rows must be:
   - active
   - not archived
   - planning-relevant where appropriate
9. Use real UUID rows from hr.function_type and hr.qualification_type, not frontend-only constants.

C) Make the fix safe
10. The bootstrap must be clearly limited to development/demo/test flows.
11. Do NOT silently inject sample production data into real tenants in production mode.
12. If the repo already has a fixture/seed/bootstrap mechanism, integrate there instead of inventing a parallel path.
13. If no such mechanism exists, create a minimal, well-contained one and document it.

D) Improve frontend empty-state UX
14. In the Rate lines form:
   - keep Function ID and Qualification ID as real select controls
   - if options exist, show them as:
     CODE · Label
   - selected value must remain the UUID id
15. If no options exist:
   - show a clearer empty-state help text
   - add a visible action for the user, such as:
     - "Create sample HR catalog data" (dev/test only), or
     - "Open HR catalogs" / "Go to HR catalog management"
16. If implementing a direct creation CTA in UI is too invasive, at minimum:
   - show a precise hint saying that the HR catalog must be populated first
   - provide a navigation link or button to the catalog management area if routing exists

E) Keep module ownership clean
17. Do not create any duplicate function or qualification catalog inside CRM/customers.
18. HR remains the single source of truth.
19. Customer pricing only consumes the catalog.

F) Optional but recommended improvement
20. If there is no current customer-facing catalog bridge and the customer page is still depending on fragile wiring, add a stable read-only reference-data path so CustomerAdmin can reliably load:
   - function_types
   - qualification_types
for the current tenant.

G) Testing
21. Add/update backend tests to cover:
   - sample HR catalog bootstrap creates rows when missing
   - bootstrap does not duplicate existing rows
   - seeded rows are visible to the customer rate-line option loader
22. Add/update frontend tests to cover:
   - Function ID dropdown shows real seeded options
   - Qualification ID dropdown shows real seeded options
   - empty-state message is shown only when catalogs are truly empty
   - option labels render as code + label
   - selected value submitted remains UUID

H) Acceptance criteria
23. In a fresh dev/test environment, the Function ID and Qualification ID dropdowns are not empty.
24. The options come from real HR catalog rows, not frontend mock data.
25. No CRM shadow catalog is introduced.
26. In environments where the catalogs are genuinely empty, the UI explains the reason and provides a next step.
27. Existing customer rate-line create/edit flows continue to work.

Before coding:
Provide a short plan with:
- which files you will change
- where bootstrap data will live
- how you will keep it dev/test-only

After coding:
Provide:
1. files changed
2. bootstrap strategy summary
3. frontend UX changes
4. test evidence
5. any follow-up items
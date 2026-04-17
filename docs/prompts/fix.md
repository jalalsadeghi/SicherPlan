You are working in the SicherPlan repository.

Task:
Fix the Legal form field in the admin/subcontractors Overview form so it is no longer a textbox and instead uses a proper select control backed by the same underlying legal-form lookup source of truth used conceptually by the Customers module.

Important architectural requirement:
Do NOT simply hardcode values and do NOT make the Subcontractors UI call the Customers reference-data endpoint directly unless repository analysis proves that this is already the intended shared contract and permission-safe.
Preferred solution:
- keep a shared domain/source-of-truth for legal forms
- expose it through a subcontractor-owned reference-data endpoint or subcontractor-safe read-model surface
- bind the Subcontractors Overview form to that option source

Why this change is needed:
- In backend/app/modules/subcontractors/schemas.py, the field is `legal_form_lookup_id`, so it is a lookup-backed field, not free text.
- In backend/app/modules/subcontractors/service.py, `legal_form_lookup_id` is validated against lookup domain `legal_form`.
- In backend/app/modules/customers/schemas.py, Customers also use `legal_form_lookup_id`.
- In backend/app/modules/customers/router.py, Customers already expose a `reference-data` endpoint that includes `legal_forms`.
- However, Subcontractors currently do not expose an equivalent reference-data endpoint in their router, and directly depending on the Customers endpoint may create the wrong module coupling and permission dependency.

Repository-grounded objective:
1. Confirm whether the Subcontractors Overview Legal form field is currently rendered as textbox.
2. Change it to a select/searchable-select.
3. Source its options from a subcontractor-safe option API or read-model.
4. Reuse the same underlying legal-form lookup domain/source as Customers.
5. Do not introduce duplicated legal-form constants in the frontend.

Implementation expectations:
- Inspect the real subcontractor admin form implementation first.
- Inspect how the Customers UI currently loads and renders legal form.
- If a shared frontend lookup helper already exists, reuse it.
- If no subcontractor-safe option endpoint exists, add the smallest clean backend endpoint for subcontractor reference data, at least for:
  - legal_forms
- If while implementing you find that subcontractors would clearly benefit from a broader reference-data contract, you may include:
  - subcontractor_statuses
  - invoice_delivery_methods
  - invoice_status_modes
  but keep the change minimal and focused.

Hard constraints:
- Do not leave `legal_form_lookup_id` as textbox.
- Do not hardcode legal-form lists in the frontend.
- Do not make Subcontractors depend on Customers permissions just to load legal forms unless that is truly the existing intended architecture and you can justify it.
- Keep tenant-safety and role-safety intact.
- Keep the fix scoped and avoid unrelated refactors.

Files to inspect first:
- backend/app/modules/subcontractors/schemas.py
- backend/app/modules/subcontractors/service.py
- backend/app/modules/subcontractors/router.py
- backend/app/modules/customers/schemas.py
- backend/app/modules/customers/router.py
- web/apps/web-antd/src/sicherplan-legacy/api/subcontractors.ts
- the actual subcontractor admin form/view/component in the web app
- the customer admin form/view/component for Legal form
- any shared lookup/select helpers already used in the repo

Deliverables:
- UI change for Subcontractors Overview Legal form
- any minimal API/helper change needed to provide options safely
- updated frontend API wrapper(s)
- brief explanation of whether the Customers option-loading approach was reused directly or only the underlying data source/domain was reused

Before coding:
Write a short validation summary answering:
1. Is my proposal correct that Legal form in Subcontractors should be a select?
2. Should it use the exact same option source as Customers directly, or the same underlying lookup domain via a subcontractor-owned endpoint?
3. What existing repo pieces can be reused?
4. What new code, if any, is actually required?

After implementation:
Run a self-check and explicitly verify:
- the field now uses a controlled select input
- options come from a trustworthy lookup source
- the chosen solution is permission-safe
- no hardcoded legal-form values were introduced

At the end, include:
1. files changed
2. key decisions
3. validation summary against my proposal
4. remaining gaps
5. commands/tests run

Final sanity-check request:
“Please verify whether using the same underlying legal_form lookup source as Customers, but through a Subcontractors-safe contract, is the most correct design for the current SicherPlan repository. If not, explain exactly why.”
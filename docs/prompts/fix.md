You are working in the SicherPlan repository.

This task is part of:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Read the sprint document first.
This is the final readiness pass before real data entry begins.

Goal:
Validate the final Generate Series handoff, permissions, i18n, route behavior, and non-regression of the Customer New Plan Wizard.

Primary files to inspect:
- web/apps/web-antd/src/router/routes/modules/sicherplan.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerPlansTab.vue
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue
- relevant i18n files for sicherplan.customerPlansWizard and customerAdmin.plans

Before coding:
Validate the current implementation and explicitly state whether the wizard is ready for real data entry.
Do not change code unless you find a real issue.

A. Route and permission validation
Confirm:
- /admin/customers/new-plan exists
- it is hidden from menu/sidebar
- it is restricted to tenant_admin for V1
- Customer > Plans launches it with customer_id
- missing customer_id shows a controlled invalid state
- unauthorized access shows controlled fallback

Fix any issue found.

B. Generate Series handoff validation
Confirm:
- final CTA label is Generate Series & Continue
- series is saved before generateShiftSeries
- generateShiftSeries uses canonical API
- on success, user is redirected to the canonical /admin/planning-staffing page
- Staffing Coverage receives supported query params only

Inspect PlanningStaffingCoverageView.vue and confirm which query params are actually consumed.
Use only supported or safely ignored params.

Preferred handoff params:
- planning_record_id
- date_from
- date_to
- shift_id if supported/useful
- planning_mode_code only if supported or safely ignored

Do not invent unsupported staffing filters.
Do not create a customer-only staffing page.
Do not embed staffing coverage inside the wizard.

C. i18n validation
Confirm all new visible UI text is i18n-driven:
- step labels
- button labels
- dialog titles
- field labels
- error messages
- success messages
- invalid states
- handoff messages

Use German first and English fallback, following existing project conventions.
Fix any hard-coded user-facing strings.

D. Styling final check
Confirm the fixes from the styling pass apply to:
- normal step forms
- modal forms
- list rows
- file inputs
- checkboxes
- buttons
- responsive layout
- dark mode if supported

E. Non-regression validation
Confirm:
- Customer Plans tab still works
- New Plan button still works
- canonical Planning Setup still works
- canonical Orders & Planning still works
- canonical Shift Planning still works
- canonical Staffing Coverage still works
- Operations & Planning menu structure is unchanged

F. Tests
Add or update tests for:
- tenant_admin can open the wizard
- non-tenant-admin cannot access the wizard
- missing customer_id invalid state
- final Generate Series redirect
- supported staffing query params
- i18n labels present
- Customer Plans tab non-regression
- Planning pages non-regression smoke tests where practical

G. Manual QA checklist
Include a manual QA checklist in the final output:
- Customer > Plans > New Plan entry
- Planning step Use Existing
- Planning step Create Site
- Planning step Create Event Venue
- Planning step Create Trade Fair
- Planning step Create Patrol Route
- Order Details
- Equipment Lines + New Equipment
- Requirement Lines + New Requirement
- Order Documents
- Planning Record
- Planning Documents
- Shift Plan
- Series & Exceptions + New Template
- Generate Series & Continue
- landing in Staffing Coverage with narrowed context
- Previous/edit behavior
- browser refresh behavior
- narrow-width layout
- dark mode if supported

Final output:
1. Readiness validation summary
2. Issues found
3. Fixes implemented
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA checklist
8. Clear statement:
   - Ready for real data entry
   - Not ready, with exact blockers

Before finalizing, explicitly state whether my proposal was correct or had to be adjusted.
Avoid unrelated refactors.
Do not broaden V1 scope.
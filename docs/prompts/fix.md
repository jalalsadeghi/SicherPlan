You are working in the SicherPlan repository.

Context:
The Customer New Plan Wizard was implemented from the sprint brief:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

The current visible problem:
On /admin/customers/new-plan?customer_id=..., the wizard shell and steps render, but the form elements inside the step content look unstyled/raw.
The screenshot shows native inputs/selects/textareas without the standard SicherPlan/Vben admin form styling.

Important:
This is primarily a UI/styling and component-polish fix.
Do NOT rewrite the wizard business flow.
Do NOT change backend APIs.
Do NOT remove or redesign the canonical Operations & Planning pages.
Do NOT change the route contract unless you discover a real bug.
Do NOT broaden the feature beyond Tenant Administrator.

Files to inspect first:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.steps.ts
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue
- nearby shared SicherPlan/Vben layout components and form patterns

First validate my diagnosis before coding:
1. Confirm whether new-plan-step-content.vue uses classes such as:
   - field-stack
   - field-help
   - cta-row
   - cta-button
   - planning-admin-checkbox
2. Confirm whether those classes are actually styled inside new-plan-step-content.vue.
3. Confirm whether similar styling exists in PlanningOpsAdminView.vue but is scoped and therefore not reusable automatically.
4. Confirm whether the current forms are structurally present for all wizard steps.
5. Confirm whether the issue is mainly missing local/shared form styling rather than missing business implementation.

Then implement the minimal correct fix.

Primary goal:
Make all Customer New Plan Wizard form elements visually consistent with the existing SicherPlan admin UI.

Required visual outcome:
- Inputs, selects, textareas, checkboxes, file inputs, and modal form fields should have consistent spacing, border, radius, background, typography, focus states, disabled states, and dark-mode compatibility.
- Step panels should look like intentional form sections, not raw browser controls.
- Dialog forms for New Equipment, New Requirement, New Template, and Planning Entity creation should also be styled.
- The visual style should be aligned with the existing PlanningOpsAdminView / PlanningOrders / PlanningShifts form patterns.

Implementation guidance:

A. Prefer reuse when practical
- First check if the branch already has a shared reusable form-style component or CSS utility.
- If such a shared form utility exists, reuse it.
- If not, add a focused local style block to new-plan-step-content.vue or extract a small shared wizard form style in the nearest appropriate location.
- Avoid broad global CSS that may unintentionally affect unrelated pages.

B. Fix scoped-style leakage
- Do not rely on styles from PlanningOpsAdminView.vue, because they are scoped to that component.
- If you reuse the pattern, copy/adapt the relevant form-control styling into the wizard component or a shared imported style.
- Make sure styles apply to:
  - normal step content
  - modal content
  - native input/select/textarea
  - file inputs
  - Ant Design modal content where applicable

C. Form field styling to add or normalize
Add/ensure styling for:
- .field-stack
- .field-stack span
- .field-stack input
- .field-stack select
- .field-stack textarea
- .field-help
- .cta-row
- .cta-button
- .cta-button.cta-secondary
- .planning-admin-checkbox
- .planning-admin-checkbox input[type="checkbox"]
- .sp-customer-plan-wizard-step__modal
- .sp-customer-plan-wizard-step__grid
- .sp-customer-plan-wizard-step__panel
- .sp-customer-plan-wizard-step__list-row

The result should match the existing admin look:
- rounded controls, similar to the PlanningOpsAdminView form controls
- soft borders using existing CSS variables
- card/surface backgrounds using existing CSS variables
- visible focus ring with the project’s teal/primary tone
- readable disabled states
- clean responsive grid behavior

D. Layout improvements
- Make label/value spacing consistent.
- Ensure fields do not stretch awkwardly across the full page unless marked as wide.
- Keep two-column or responsive grid behavior where sensible.
- On narrow widths, all controls should stack cleanly.
- Keep the action bar in new-plan.vue as-is unless it has a direct visual bug.
- Do not make the wizard page visually denser than existing admin modules.

E. Modal polish
- Ensure modal form fields are styled consistently.
- Ensure modal buttons are not affected negatively.
- Ensure modal content spacing is clean.
- If Ant Design Modal teleports content, verify the chosen scoped/global styling still applies to labels and controls inside the modal.

F. Business-flow safety
Do not change:
- step order
- save-on-next behavior
- Previous behavior
- Generate Series & Continue behavior
- Staffing Coverage handoff
- API adapter semantics
- permission guard
unless you find a real bug directly related to this styling fix.

G. Verify step completeness, but do not broaden scope
While inspecting, check whether all steps from /docs/sprint/SPR-CUST-NEWPLAN-V1.md have visible form content:
1. Planning
2. Order details
3. Equipment lines
4. Requirement lines
5. Order documents
6. Planning record
7. Planning documents
8. Shift plan
9. Series & exceptions

If any step is still only placeholder content, report it clearly.
If all steps have real form content, say so and keep this patch focused on styling.

H. Testing
Add or update focused frontend tests where practical:
- new-plan-step-content renders styled field wrappers for Planning step
- Order Details fields use the wizard form field class
- Equipment / Requirement / Template dialog content uses the styled modal form wrapper
- action buttons keep the intended cta classes
- responsive layout class exists on the form grid
- no regression in New Plan route shell

If visual regression tests are not available, add a manual QA checklist to the final report.

Manual QA checklist to include in final output:
- Planning step desktop layout
- Order Details desktop layout
- Equipment Lines with New Equipment dialog
- Requirement Lines with New Requirement dialog
- Shift Plan step
- Series & Exceptions with New Template dialog
- narrow-width layout
- dark mode, if supported
- browser focus state on input/select/textarea
- disabled/loading state

Expected final output:
1. Validation summary of the diagnosis
2. Whether all wizard step forms are structurally implemented
3. The styling approach chosen: local styles vs shared style extraction
4. Changed files
5. Tests added/updated and test results
6. Manual QA checklist
7. Any real remaining limitation

Important:
Keep the patch focused.
Avoid unrelated refactors.
Do not change the customer-to-order-to-planning-to-shift-to-staffing domain flow.
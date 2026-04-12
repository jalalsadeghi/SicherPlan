You are working in the SicherPlan repository.

Goal:
Fix the missing styling for the Create forms on `/admin/workforce-catalogs` so the
Function types and Qualification types create sections visually match the existing
SicherPlan admin UI patterns and do not look unstyled/raw.

This is a focused UI styling fix.
Do not change domain behavior, API behavior, auth/session behavior, or page structure
more than necessary.

Before coding:
1. Read `AGENTS.md`.
2. Keep the change set narrow and focused on styling/layout for the create forms.
3. Reuse existing form styling patterns already present in the repo instead of inventing a new visual system.

Start by verifying the actual implementation in the current working tree.

Files/components to inspect first:
- the page/component that renders `/admin/workforce-catalogs`
- any extracted component used for the two catalog forms
- the stylesheet/scoped styles attached to that page/component
- nearby UI references with good styling, especially:
  - `web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue`
  - `web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue`
  - any shared form/layout CSS classes used there

Relevant classes visible in the current HTML:
- `employee-catalogs-form`
- `employee-catalogs-panel__header`
- `employee-catalogs-form-grid`
- `employee-catalogs-checkbox`
- `cta-row`
- `cta-button`
- `field-stack`

What you must verify first:
1. The create forms on `/admin/workforce-catalogs` currently render with weak or missing styling for inputs/textarea/checkbox groups/layout.
2. The page likely has structural markup, but its local styles are missing, incomplete, or not aligned with existing admin form patterns.
3. Similar forms in Employees/Customers already have better visual treatment that should be reused or mirrored.

Required outcome:
A. Make both create forms visually consistent with the rest of the SicherPlan admin UI.
B. Style the following clearly:
   - input fields
   - textarea fields
   - checkbox rows/groups
   - form grid spacing
   - panel header spacing
   - form container surface/border/background
   - create/clear action row spacing and alignment
C. Preserve responsiveness and avoid breaking the page on smaller widths.
D. Keep existing class names if practical; prefer adding/fixing styles over unnecessary markup churn.
E. Use existing visual patterns/tokens from nearby admin pages where possible.
F. Do not make unrelated visual changes elsewhere in the page.
G. Do not alter API wiring, form validation logic, or create/update behavior unless absolutely required for the styling fix.

Preferred design direction:
1. The form should read as a proper admin editor card/panel.
2. Inputs and textareas should have the same visual treatment as other admin forms:
   - clear border
   - padding
   - radius
   - focus state
   - width behavior
3. Checkbox items should not look like naked browser defaults dropped into the page.
   - align checkbox + label text cleanly
   - give consistent spacing
   - support wrapping for long labels
4. Grid layout should feel deliberate:
   - consistent gap between fields
   - wide fields span appropriately
   - second checkbox grid for qualification type should align cleanly
5. Buttons should remain consistent with existing `cta-button` system.

Implementation guidance:
1. Find the actual component for `/admin/workforce-catalogs`.
2. Inspect whether scoped CSS for:
   - `.employee-catalogs-form`
   - `.employee-catalogs-form-grid`
   - `.employee-catalogs-checkbox`
   - descendant `input`, `textarea`, `select`
   is missing or insufficient.
3. Compare against existing styled admin forms in Employees/Customers.
4. Reuse existing spacing, border, background, radius, and focus patterns where appropriate.
5. If there is shared CSS worth extracting without widening scope too much, do it only if it clearly reduces duplication and remains low-risk.
6. Keep the fix maintainable and local.

Validation expectations:
- the two Create forms should no longer look unstyled
- form controls should align cleanly
- checkbox groups should look intentional
- no regression to the record list or edit buttons
- no regression to dark/light assumptions if the repo supports theme tokens
- no regression to mobile/narrow width layout

Tests / validation to run:
1. Run relevant frontend tests for the workforce catalogs page, if present.
2. Add/update focused tests only if the repo already tests class/state structure for this page.
3. Run lint/typecheck for touched files.
4. Manually inspect the rendered structure in source and confirm the styles are actually applied to:
   - inputs
   - textarea
   - checkbox rows
   - form grids
5. If available in the repo workflow, generate a quick visual verification or component snapshot.

What not to do:
- Do not redesign the page.
- Do not move sections around unless absolutely needed for the styling to work.
- Do not change business copy/text unnecessarily.
- Do not add random one-off inline styles.
- Do not break existing class hooks or test IDs.

Final response format:
1. Short diagnosis
2. Exact component/file(s) changed
3. Which style gaps were fixed
4. Whether styles were reused from existing admin patterns or added locally
5. Tests/validation run and results
6. Remaining assumptions
7. Self-validation summary

Extra instruction:
Challenge your own fix before finalizing.
Specifically verify that:
- both “Create function type” and “Create qualification type” forms look like real styled admin forms
- checkbox groups no longer look raw/unstyled
- the page still feels visually consistent with `admin/employees` and `admin/customers`
If any of those fail, the fix is incomplete.
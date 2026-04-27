You are working in the SicherPlan repository.

Goal:
Fix the layout of the action buttons in the Web/Admin Employees Overview page.

User-visible page:
secur.lumina-core.de/#/admin/employees
Employees → selected employee → Overview

Current problem:
The buttons:
- "Show address history"
- "Open login diagnostics"

are currently displayed below the section title/description text. They should be placed in the same header row as the section title/description, aligned to the right side of the card, similar in size and style to the compact header buttons shown in the employee detail header, for example "Back to employee list".

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Tests to inspect/update:
- web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.smoke.test.ts
- web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.layout.test.js, if relevant

Before coding:
1. Read AGENTS.md.
2. Inspect the current template around:
   - data-testid="employee-address-history-open"
   - data-testid="employee-access-diagnostics-open"
   - class="employee-admin-overview-section-card__header"
   - class="employee-admin-form-section__header"
   - class="employee-admin-detail-header-actions"
3. Verify the current CSS before changing it.
4. Do not change backend APIs.
5. Do not change any dialog behavior, data loading, permissions, or employee scope.
6. This task is only a layout/UX alignment fix.

Required UI behavior:

A. Address history button
1. In Overview → Addresses, place the "Show address history" button in the same horizontal row as the section title:
   - left side: Eyebrow "ADDRESSES" and title/subtitle "Address history"
   - right side: compact "Show address history" button
2. The button must not appear below the title/description block.
3. The button should be visually compact, similar to "Back to employee list":
   - not overly large
   - not a big primary pill
   - use existing secondary/header action style if available
4. The existing dialog behavior must remain unchanged.

B. Login diagnostics button
1. In Overview → App access, place the "Open login diagnostics" button in the same horizontal row as the App access section title:
   - left side: Eyebrow "APP ACCESS" and title/subtitle "IAM link for employee app access"
   - right side: compact "Open login diagnostics" button
2. The button must not appear below the title/description block.
3. The button should be visually compact, similar to "Back to employee list".
4. The existing diagnostics dialog behavior must remain unchanged.
5. If `accessLink` is missing and the button is intentionally hidden, preserve that logic.

Implementation guidance:
- Prefer introducing or reusing a split-header layout class.
- If there is already a class such as:
  - employee-admin-form-section__header--split
  - employee-admin-overview-section-card__header--split
  - employee-admin-detail-header-actions
  reuse it consistently.
- If needed, add a new class such as:
  - employee-admin-overview-section-card__header--actions
  - employee-admin-overview-section-card__header-actions
- The layout should use flex/grid:
  - display: flex
  - justify-content: space-between
  - align-items: flex-start or center
  - gap: 1rem
- On narrow screens/mobile widths, it may wrap, but the button should still stay visually tied to the header, not separated as a large block below the content.
- Keep the button size compact:
  - use cta-button cta-secondary plus an existing compact/header-action class if present
  - or add a reusable compact class with smaller padding matching header buttons
- Do not change labels unless necessary.
- Do not duplicate buttons.

Suggested data-testids to preserve:
- employee-address-history-open
- employee-access-diagnostics-open
- employee-address-history-dialog
- employee-access-diagnostics-dialog

Tests:
Update/add tests to ensure the buttons are in the header action area.

Required test coverage:
1. "Show address history" button exists.
2. It is rendered inside the Addresses section header/action area, not in a standalone block below the section text.
3. Clicking it still opens the address history dialog.
4. "Open login diagnostics" button exists when accessLink is available.
5. It is rendered inside the App access section header/action area, not in a standalone block below the section text.
6. Clicking it still opens the diagnostics dialog.
7. Existing dialog tests still pass.

A practical test approach:
- Assert that the button is contained within the closest `.employee-admin-overview-section-card__header` or the new header-action wrapper.
- Assert dialog behavior using the existing data-testid selectors.
- Do not make brittle pixel-position assertions.

Acceptance criteria:
- Both buttons are aligned to the top-right of their section header row.
- Both buttons are compact and visually similar in size/style to "Back to employee list".
- No backend changes.
- No permission/data-scope changes.
- Existing dialog open/close behavior remains working.
- Tests pass.

Run:
cd web
pnpm test -- employeeAdmin
pnpm lint
pnpm typecheck

If the exact scripts differ, inspect package.json and run the closest existing web test/lint/typecheck commands.

Final response:
- Summarize the layout fix.
- List changed files.
- List tests run and results.
- Mention that this was frontend-only.
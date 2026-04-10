You are working in the latest SicherPlan repo.

Goal
Implement a standard modal-based editor for Shift Templates in:
web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue

Current behavior
- In the "templates" tab of admin/planning-shifts, the template create/edit form is rendered inline below the template list.
- Clicking "New template" currently resets the draft inline.
- Clicking an existing template row currently loads the template into the same inline form.

Target behavior
- Move the Shift Template create/edit form into a dialog/modal.
- The modal must open when:
  1) the user clicks "New template"
  2) the user clicks an existing template row
- The modal must support both create and edit using the existing draft/submission logic.
- Do NOT change backend APIs, request payloads, endpoint contracts, or data model behavior.
- Keep all current create/update behavior intact.
- Keep the template list visible in the tab; only the editor moves into the modal.

Implementation requirements
1. Reuse the project’s existing modal pattern and styling conventions already used elsewhere in the repo.
   - Prefer ant-design-vue Modal, matching the existing repo style.
   - Keep the UX consistent with existing SicherPlan admin pages.

2. Refactor minimally and safely.
   - Extract as little logic as necessary.
   - Avoid broad rewrites.
   - Preserve existing functions where possible:
     - startCreateTemplate
     - selectTemplate
     - submitTemplate
     - resetTemplateDraft
   - Add modal open/close state and helper methods as needed.

3. Required UX behavior
   - "New template" opens the modal in create mode with a clean draft.
   - Clicking a template row opens the modal in edit mode with that template loaded.
   - Modal title should clearly reflect mode:
     - "New shift template" for create
     - "Edit shift template" for edit
   - On successful save:
     - close the modal
     - refresh the template list
     - keep the saved/selected template highlighted in the list when appropriate
   - On cancel:
     - close the modal
     - do not accidentally mutate the saved template state
   - Add a footer or action row with:
     - Save
     - Reset
     - Cancel
   - Preserve field validation and required fields exactly as today.

4. Accessibility and testability
   - Add stable test ids for the modal and key actions, for example:
     - planning-shifts-template-modal
     - planning-shifts-template-modal-save
     - planning-shifts-template-modal-cancel
   - Ensure keyboard/accessibility defaults from Modal are preserved.
   - Do not break embedded mode or other workspace tabs.

5. Layout cleanup
   - Remove the inline template form from the templates tab after moving it into the modal.
   - Keep the list section and actions row clean and compact.

6. Tests
   Update or extend:
   web/apps/web-antd/src/sicherplan-legacy/features/planning/planningShifts.smoke.test.ts

   Add/adjust tests to cover at least:
   - clicking "New template" opens the modal
   - clicking an existing template row opens the modal in edit mode
   - modal contains the expected form fields
   - cancel closes the modal
   - successful save closes the modal
   - the old inline template form is no longer rendered in the templates tab

7. Guardrails
   - No backend changes
   - No API contract changes
   - No unrelated refactors in plans/series/shifts/board tabs
   - Keep code style aligned with existing file patterns
   - Keep TypeScript/Vue style consistent with surrounding code

Deliverables
1. Implement the modal-based template editor
2. Update tests
3. Briefly summarize:
   - files changed
   - why the solution is safe/minimal
   - any edge cases considered

Before finalizing
Please self-check your solution critically and validate it against the current codebase:
- confirm you did not break the existing template create/edit flow
- confirm the modal opens from both entry points
- confirm no inline template editor remains
- confirm tests reflect the new behavior
- confirm the implementation matches existing repo modal conventions rather than inventing a new pattern

If you find a better or safer implementation detail than the prompt suggests, use it — but explain why in the final summary.
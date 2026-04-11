You are working in the SicherPlan repository.

Before any code changes:
1. Read `AGENTS.md`.
2. Open the relevant sprint file under `docs/sprint/`.
3. Check whether a planning/staffing task prompt already exists under `docs/prompts/`.
4. Anchor this work to the correct story/task ID.
5. Keep the change set narrow and focused on the Demand groups UX refactor inside `/admin/planning-staffing`.

Task goal:
Refactor the Demand groups area inside the "Shift detail" box on `/admin/planning-staffing` so that:
- the demand-group list remains visible inline on the page
- the create/edit form is moved into a dialog/modal
- clicking `New demand group` opens the dialog in create mode
- clicking a demand-group row in `planning-staffing-demand-groups` opens the dialog in edit mode
- the inline button `Edit selected demand group` is removed from the page

Current UX problem:
The current Demand groups section mixes:
- list of existing demand groups
- create/edit form
- duplicate edit button
all in the same visible area, which makes the Shift detail panel feel crowded.

Desired UX outcome:
A cleaner Demand groups section where:
- the page shows the list of demand groups clearly
- create/edit actions happen in a focused modal dialog
- edit is triggered directly by clicking a demand-group item
- the page no longer needs the `Edit selected demand group` button

Files to inspect first:
- `AGENTS.md`
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- any related type/helper files used by this view
- any existing dialog/modal pattern already used in the web app
- any shared form/dialog components already present in the admin shell

Important constraints:
- This is primarily a UI/UX refactor.
- Do not change backend contracts unless a small compatibility fix is truly required.
- Do not change planning business rules.
- Do not change demand-group validation logic, audit behavior, or staffing gating behavior.
- Preserve tenant scope, role scope, and existing data flows.
- Preserve existing `data-testid` values where practical, and update tests safely if needed.
- Keep German as default UI language and English as secondary.

Required implementation outcome:
A. Keep the `planning-staffing-demand-groups` list visible inline in the Shift detail panel.
B. Remove the always-visible inline demand-group editor form from the page body.
C. Replace it with a modal/dialog form component or local modal section that supports:
   - create mode
   - edit mode
D. `New demand group` opens the dialog in create mode with a clean form state.
E. Clicking an existing demand-group row opens the dialog in edit mode with that row loaded.
F. Remove the visible inline button `Edit selected demand group`.
G. Preserve the ability to edit the currently selected demand group, but make row click the primary edit trigger.
H. The dialog title should change by mode:
   - create mode => `Create demand group`
   - edit mode => `Edit demand group`
I. Preserve the current fields and behavior inside the form:
   - function type
   - qualification
   - minimum quantity
   - target quantity
   - mandatory checkbox
   - remark
   - save/update
   - reset/cancel behavior as appropriate
J. After successful save/update:
   - refresh the demand-group list
   - refresh shift detail / coverage state if needed
   - keep the selected shift intact
   - close the dialog only if that matches the current UX pattern cleanly
K. If save fails, keep the dialog open and preserve user input where reasonable.

Recommended UX behavior:
- Clicking `New demand group` => open empty dialog
- Clicking a row => select it and open edit dialog
- Provide a clear Cancel/Close action in the dialog
- Keep the page uncluttered and focused
- Do not hide important empty-state guidance when there are no demand groups yet

Technical guidance:
- Prefer an existing modal/dialog pattern already used in the web admin app
- If none fits, implement a simple local modal cleanly in this view
- Introduce local state such as:
  - `isDemandGroupDialogOpen`
  - `demandGroupDialogMode` (`create` | `edit`)
  - `editingDemandGroupId`
- Separate dialog open/close logic cleanly from demand-group form state
- Avoid duplicating form markup if possible
- Keep the change maintainable and scoped

Acceptance criteria:
1. Demand-group create/edit no longer clutters the main page body.
2. `New demand group` opens a dialog in create mode.
3. Clicking a demand-group row opens a dialog in edit mode.
4. `Edit selected demand group` is removed from the visible page UI.
5. Saving/updating still works correctly.
6. The list remains visible inline and still shows selection state.
7. Empty-state messaging remains clear when no demand groups exist.
8. No staffing logic is broken.
9. The Shift detail panel is visibly cleaner than before.

Tests and validation:
Add or update tests for:
- clicking `New demand group` opens create dialog
- clicking a demand-group row opens edit dialog
- dialog title changes correctly by mode
- existing form fields still render in the dialog
- save in create mode still works
- save in edit mode still works
- list refreshes after save/update
- inline `Edit selected demand group` button is no longer rendered
- empty-state path still allows create flow correctly

Manual validation checklist:
- open `/admin/planning-staffing`
- select a shift
- verify demand-group list remains visible
- click `New demand group` and confirm create dialog opens
- click an existing demand-group row and confirm edit dialog opens
- confirm save/update still works
- confirm the Shift detail panel is less crowded
- confirm no unrelated section layout broke

Important self-check before finishing:
- Verify the list stayed inline and only the form moved into a dialog
- Verify `Edit selected demand group` is removed
- Verify row click really opens edit mode
- Verify no business logic changed
- Verify no tenant/role-scope behavior regressed
- Verify the page is meaningfully less cluttered after the change
- Challenge your own implementation and confirm that create/edit is now easier, not harder

Final response format:
1. Short implementation summary
2. Exact task/story ID used
3. Exact files changed
4. What UI structure changed
5. What was intentionally left unchanged
6. Test results
7. Manual validation notes
8. Self-validation against clutter reduction and workflow preservation
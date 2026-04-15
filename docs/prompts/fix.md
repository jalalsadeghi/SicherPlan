You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth. Do NOT revert unrelated planning-staffing work. Apply only a focused fix for assignment-creation state handling in `/admin/planning-staffing`.

Task:
Fix the `Create assignment` flow in `admin/planning-staffing` so the assignment creation modal/form no longer resets unexpectedly while the user is filling it in.

Observed bug:
When the user opens `Create assignment`, the modal opens correctly.
But while filling fields, the form suddenly resets and the user must enter the values again.
This may repeat multiple times, especially when the shift already has one or more existing assignments.

Likely root cause to inspect first:
In the current implementation, the create-assignment draft is still coupled to:
- `selectedAssignmentId`
- assignment auto-selection from the assignments list
- background refresh/watcher logic that repopulates or resets the draft

Current areas to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
   Especially inspect:
   - `startCreateAssignment()`
   - `loadSelectedShiftDetails()`
   - `loadSelectedAssignmentDetails()`
   - `resetAssignmentDraft()`
   - `resetAssignmentEditor()`
   - watcher on `selectedAssignmentId`
   - watcher on `selectedBoardShift`
2. `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

What is probably happening:
- create mode clears `selectedAssignmentId`
- later, detail-loading logic auto-selects the first existing assignment
- assignment detail loading then repopulates the modal draft from that old assignment
- selected-board-shift watcher may also reset the draft again when selection is empty
This causes the create form to lose user-entered values

Required behavior after the fix:
1. Opening `Create assignment` must create a stable draft for create mode
2. While the create dialog is open, user-entered values must NOT be overwritten by:
   - background refresh
   - assignment auto-selection
   - selected-assignment watcher
   - selected-board-shift watcher
3. Existing assignment rows must still open edit mode correctly when the user clicks them
4. Edit mode may still repopulate from the selected assignment
5. Create mode must remain independent from existing assignment selection

Important design rule:
Create-mode draft must be isolated from list-selection side effects.

Recommended implementation direction:
1. Inspect the current logic that auto-selects the first assignment in `loadSelectedShiftDetails()`
2. Remove that auto-selection behavior if it still exists
3. Decouple create-mode draft from `selectedAssignmentId`
4. Guard watcher-driven draft mutations:
   - while `assignmentDialogOpen === true` and `assignmentDialogMode === "create"`,
     do NOT:
     - auto-populate from an existing assignment
     - call `resetAssignmentDraft()` because list/board state changed
5. Make `resetAssignmentEditor()` mode-aware:
   - in create mode: reset to clean create defaults
   - in edit mode: restore the selected assignment details
6. If current code keeps an outside row selection for the list, that is fine,
   but it must not mutate the create modal draft
7. If modal-only validation summary / selected-assignment UI currently depends on `selectedAssignmentId`,
   make sure create mode does not show stale edit-mode state

Preferred architectural outcome:
- user list selection state
- edit-mode source assignment state
- create-mode form draft
must not be treated as the same thing

If needed, introduce a small dedicated editor-state variable, for example:
- `assignmentEditorSourceId`
or equivalent,
instead of reusing `selectedAssignmentId` for both list selection and create-form lifecycle.

Testing requirements:
Update/add tests in:
`web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

At minimum cover these cases:
1. opening `Create assignment` with existing assignments present does NOT prefill from an old assignment
2. while create modal is open, background list/detail refresh does NOT reset user-entered form values
3. clicking an assignment row still opens edit mode with populated values
4. create-mode reset button restores create defaults, not old assignment data
5. canceling create mode closes safely without altering unrelated list state
6. if the previous tests assumed auto-selected assignment rows, update them to the new intended behavior

Suggested regression scenario:
- mount the view with one existing assignment already in the shift
- open `Create assignment`
- type/select multiple fields:
  - demand_group_id
  - team_id
  - member_ref
  - assignment_status_code
  - assignment_source_code
  - offered_at
  - confirmed_at
  - remarks
- trigger whatever refresh path currently causes the reset
- assert the entered values remain intact in create mode

Acceptance criteria:
- Create assignment form no longer resets unexpectedly
- Existing assignments no longer overwrite create-mode draft
- Edit flow still works from list row click
- Tests cover the regression

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Which files were changed
3. How create-mode draft was isolated
4. What watcher / refresh behavior was guarded
5. How edit mode still works
6. Which tests were updated or added
7. Any remaining edge cases to verify manually

Before coding, explicitly identify:
- the exact block that auto-selects the first assignment
- the exact watcher(s) that can reset or repopulate the draft during create mode
Then implement the safest fix without broad refactoring.
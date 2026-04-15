You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth. Do NOT revert unrelated planning-staffing changes. Apply only a focused behavioral fix for assignment selection state in `/admin/planning-staffing`.

Task:
In `admin/planning-staffing` → `Shift detail` → `Assignments`, stop the UI from auto-selecting any existing assignment row.
An assignment must ONLY become selected when the user explicitly clicks one assignment row, or when a workflow explicitly sets it after create/update/unassign.

Problem:
When entering the Assignments tab for a shift that already has one or more assignments, the current implementation automatically selects one assignment from the list.
This is not desired.
The UI must not preselect any assignment just because assignments exist.

Current likely cause to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
2. Specifically inspect:
   - `loadSelectedShiftDetails()`
   - assignment-related watchers
   - selected assignment state handling
3. Also inspect current tests in:
   - `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

Expected behavior after the fix:
1. When a shift is opened and assignments exist:
   - no assignment row is selected by default
   - `selectedAssignmentId` should remain empty unless explicitly set by user action or a workflow result
2. When the user clicks an assignment row:
   - that row becomes selected
   - edit/details/modal behavior can proceed as designed
3. If the user had explicitly selected an assignment and the page refreshes:
   - preserve the selection only if that same assignment still exists in the refreshed list
   - otherwise clear the selection
4. Do NOT fall back to selecting the first assignment automatically
5. Create-assignment flow must still work even when no assignment is selected
6. Validation/assignment side panels must behave safely when `selectedAssignmentId` is empty

Important design rule:
Preserve explicit user intent.
Selection should be:
- user-driven
- not list-driven

Recommended implementation direction:
1. Inspect the current logic that does:
   - “if current selected assignment is missing, select the first assignment”
2. Replace that behavior with:
   - if current explicit selection still exists, keep it
   - otherwise clear `selectedAssignmentId`
3. Make sure refresh flows do not silently reintroduce auto-selection
4. Keep explicit workflow selection only where justified, for example:
   - after a successful create, selecting the newly created assignment is acceptable
   - after editing an already selected assignment, keeping the same selected id is acceptable
5. Do not break modal behavior for manual row clicks

Testing requirements:
Update or add tests in `planningStaffing.smoke.test.ts` to verify:
1. when assignments exist on initial load, no row is auto-selected
2. clicking an assignment row selects it
3. create-assignment flow still works without a preselected existing assignment
4. explicit selection is preserved across refresh only if the same assignment still exists
5. if the selected assignment disappears after refresh, selection is cleared instead of falling back to the first row
6. old tests that assumed preselection are updated to the new intended behavior

Important constraint:
Do NOT implement a hidden fallback like “select first assignment when opening the assignments tab”.
The fix must ensure there is no automatic default selection from the assignments list.

Acceptance criteria:
- No assignment row is selected automatically when opening a shift with existing assignments
- Assignment selection happens only after user click or explicit workflow result
- Refresh preserves explicit valid selection but does not invent a new one
- Tests reflect the new behavior

At the end, provide a concise validation report with these headings:
1. Where the auto-selection came from
2. Which files were changed
3. What the new assignment-selection rule is
4. How refresh behavior now works
5. Which tests were updated or added
6. Any remaining edge cases to verify manually

Before coding, explicitly identify:
- the exact line/block that currently auto-selects the first assignment
- any tests that currently assume an assignment is preselected
Then update both code and tests accordingly.
You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
The current working tree is already dirty from previous staffing work. Do NOT revert, overwrite, or restyle unrelated changes. Treat the current working tree as the source of truth. Inspect the live file state first, then apply only the minimal safe change needed for modal-based assignment editing.

Task:
Refactor the Assignments editor in `/admin/planning-staffing` so the assignment form is no longer rendered inline inside the Assignments panel. Instead:
1. clicking `Create assignment` opens a modal dialog for creating a new assignment
2. clicking an existing assignment row opens the same modal in edit mode
3. the page remains cleaner and more compact, while preserving all current staffing behaviors

Primary target:
- current page/workspace: `P-04 Staffing Board & Coverage`
- current view file is expected to be the planning staffing coverage view in the SicherPlan web app
- use the CURRENT working tree file path, not an older clean-repo assumption

Behavioral requirements:
1. Keep the Assignments tab/panel on the page.
2. In the panel itself, keep:
   - panel header
   - `Create assignment` button
   - assignment list / rows
   - compact summary/read-only context if helpful
3. Move the editable assignment form into a modal dialog.
4. The same modal must support:
   - create mode
   - edit mode
5. When the user clicks `Create assignment`:
   - open modal with blank/default draft
   - title should clearly indicate create mode
6. When the user clicks an existing assignment row:
   - open modal with that assignment prefilled
   - title should clearly indicate edit mode
7. Preserve the current assignment field set and semantics already present in the live working tree, including:
   - demand group
   - actor kind
   - team link
   - employee/subcontractor worker member
   - assignment status
   - assignment source
   - offered at
   - confirmed at
   - remarks
8. Preserve business rules already present in the current implementation:
   - demand group and shift remain stable after creation when that is the existing rule
   - validations remain visible and usable
   - remove/unassign remains available for existing assignments
   - create/update/unassign must still refresh assignment list, board, validations, and coverage correctly
9. Do not weaken validation or audit behavior.
10. Do not regress existing assignment workflow tests.

Design and UX guidance:
- Use the same modal/dialog pattern already used elsewhere in this page for demand groups / teams / team members.
- Prefer consistency over invention.
- Keep the panel visually compact after refactor.
- The inline assignment form should be removed from the page once the modal version is in place.
- If the page currently shows an assignment validation summary and an “Open validations” action, preserve that capability in the most consistent place:
  - preferably inside the assignment modal for the currently edited record
  - or in a compact row-level summary if that better matches the current code
- Use the safest keyboard/interaction behavior:
  - modal closes on cancel
  - reset only resets modal draft, not unrelated page state
  - escape/cancel should not silently discard saved data
- Preserve or improve accessibility:
  - clear modal title
  - correct button labels
  - stable focus behavior
  - no broken tab order

Implementation constraints:
- Inspect the current dirty file state first.
- Keep the change local and minimal.
- Reuse the current state/draft model if possible.
- Do not introduce a second conflicting assignment state machine.
- Do not duplicate backend logic in frontend code.
- Do not change API contracts unless absolutely required by the current codebase.
- Prefer adapting existing draft/reset/save flows into modal open/close flows.

Expected code-level outcome:
1. Add modal open/close state for assignment editor.
2. Add explicit create/edit mode state for assignment editor.
3. Opening behavior:
   - `Create assignment` => open modal in create mode
   - clicking assignment row => open modal in edit mode
4. Move the existing assignment form markup into the modal.
5. Keep save/remove/reset/cancel actions inside the modal.
6. Keep the page-level assignment list outside the modal.
7. Ensure selected assignment state still behaves correctly after save/remove/update.
8. If the existing row click only selects the assignment, update it so row click opens the edit dialog.
   - If selection state is still needed for other tabs/interactions, preserve it while also opening the dialog.
9. Keep test ids stable where sensible, and add new ones where needed:
   - create modal open button
   - assignment modal root
   - assignment modal save
   - assignment modal cancel
   - assignment modal reset
   - assignment modal remove/unassign
10. Do not break demand-group, team, or validation modal behavior already in the page.

Validation work required:
- Inspect and update tests for the current working tree.
- Add or update tests to verify:
  1. `Create assignment` opens the modal
  2. clicking an assignment row opens modal in edit mode
  3. create mode shows default draft
  4. edit mode shows prefilled draft from selected assignment
  5. save still triggers the correct existing create/update path
  6. remove/unassign still works from modal
  7. modal close/reset behavior is correct
  8. page no longer renders the full inline assignment editor after refactor
- If the repo currently has smoke tests for planning staffing, extend them rather than creating disconnected duplicate tests.

Suggested implementation approach:
- First inspect:
  - current assignment draft state
  - current assignment save/update/unassign handlers
  - current selectedAssignment behavior
  - existing modal patterns in the same view
- Then refactor in this order:
  1. introduce assignment modal state
  2. extract or move assignment form into modal
  3. wire create button to open create mode
  4. wire row click to open edit mode
  5. keep all current handlers working
  6. remove obsolete inline form rendering
  7. update tests

Acceptance criteria:
- Assignments tab remains available.
- The page is visually cleaner because the assignment editor is no longer inline.
- `Create assignment` opens an assignment modal.
- Clicking an existing assignment opens the same modal in edit mode.
- Existing behaviors for save/update/remove/validation are preserved.
- Coverage and staffing refresh still work after mutations.
- No regression to other planning-staffing modal flows.
- Tests pass.

At the end, provide a concise validation report with these headings:
1. What changed
2. Which files were changed
3. How create mode works
4. How edit mode works
5. How existing assignment actions were preserved
6. Which tests were updated or added
7. Any remaining assumptions or working-tree risks

Before coding, explicitly sanity-check the proposal against the current live working tree and say whether any existing dirty changes would conflict with this refactor.
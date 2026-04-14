You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
The current working tree may already contain dirty changes from previous planning-shifts UI work. Do NOT revert, overwrite, or collapse nearby changes. Treat the current working tree as the source of truth and apply only a focused fix for the Series-tab interaction model.

Task:
Fix the interaction model in `/admin/planning-shifts` → "Shift planning" → "Series and exceptions" so that clicking a series row does NOT simultaneously:
1. open the edit modal
2. show/open the Series exceptions area

Instead, the user must explicitly choose between two actions:
- Edit series
- View / open Series exceptions

Problem summary:
The current behavior couples:
- selecting a series
- opening the edit modal
- opening/showing the exceptions area

This is confusing. The user should first select a series, then explicitly choose what they want to do.

Desired behavior:
1. Clicking a series row should ONLY select/highlight that series.
2. After a series is selected, the UI should expose two clear action buttons:
   - `Edit series`
   - `Show exceptions` (or `Open exceptions`)
3. Clicking `Edit series` should open the series modal in edit mode.
4. Clicking `Show/Open exceptions` should open/show the exceptions area for the selected series.
5. If the exceptions area is already open, the button may become `Hide exceptions` if that is cleaner and consistent.
6. The exceptions area must no longer appear automatically just because the row was clicked.
7. The series modal must no longer open automatically just because the row was clicked.

Context:
- Current live implementation is in the planning shifts admin view.
- The current code path likely has `selectSeries(series.id)` both selecting the series and opening the modal.
- The exceptions area is likely controlled directly or indirectly by `selectedSeriesId`, causing it to appear immediately after selection.
- This coupling must be removed.

What to inspect first:
1. `PlanningShiftsAdminView.vue`
2. The current `selectSeries` function
3. The conditions used to render the exceptions section
4. The current `seriesModalOpen` flow
5. The current tests in `planningShifts.smoke.test.ts`

Recommended solution design:
Separate these states clearly:

A. Selected series identity
- keep `selectedSeriesId`

B. Series edit modal visibility
- controlled independently, e.g. `seriesModalOpen`

C. Exceptions panel visibility
- controlled independently, e.g. `exceptionsPanelOpen` or similar

Recommended behavior:
- Row click:
  - set selected series
  - load lightweight details if needed
  - DO NOT open modal
  - DO NOT auto-open exceptions panel
- `Edit series` button:
  - requires selected series
  - opens modal
  - loads edit data if needed
- `Show/Open exceptions` button:
  - requires selected series
  - shows the exceptions section/panel
  - loads exceptions if needed
- Optional:
  - `Hide exceptions` closes the exceptions section without clearing the selected series

UI requirements:
1. Add two explicit action buttons for the selected series workflow.
2. Place them in a clear, low-friction location, for example:
   - in the series section header
   - or in a small action row below the selected series list
   Choose the most consistent option with the current UI.
3. Do not overload the row itself with too many actions unless that is already a pattern in this file.
4. Preserve compactness and clarity.

Behavioral constraints:
- Do NOT change business logic for:
  - creating series
  - editing series
  - loading series details
  - loading exceptions
  - creating/updating exceptions
  - generating series
- Do NOT change API contracts
- Do NOT break the exception modal work if it has already been refactored in the current working tree
- Do NOT break plan selection or shift selection flows

Important compatibility note:
The current smoke tests may still encode the old behavior:
- row click opens edit modal
- row click also reveals exceptions
You must update those tests to match the new intended behavior.

Implementation guidance:
1. Inspect current live state before editing.
2. Refactor `selectSeries` so it only handles selection (and maybe data preload), not UI branching.
3. Introduce a separate explicit action for opening the edit modal.
4. Introduce a separate explicit action for showing exceptions.
5. Decouple exceptions rendering from mere selection.
6. Preserve selected-series highlighting.
7. Keep the UI accessible and keyboard-friendly.

Accessibility requirements:
- Preserve button semantics for rows and actions
- Keep keyboard navigation clear
- Ensure selected state remains visible
- Ensure action buttons are clearly labeled
- Ensure focus-visible styles remain usable

Testing guidance:
Update `planningShifts.smoke.test.ts` to reflect the new behavior.

Add or update tests to verify:
1. Clicking a series row selects it but does NOT open the edit modal
2. Clicking a series row does NOT automatically show the exceptions panel
3. Clicking `Edit series` opens the series modal in edit mode
4. Clicking `Show/Open exceptions` reveals the exceptions area for the selected series
5. If implemented, clicking `Hide exceptions` hides the exceptions area
6. Selected series remains selected after closing the modal
7. Existing exception workflows still work once exceptions are explicitly opened
8. No regression to new-series action

Avoid brittle tests based on exact CSS.
Prefer behavioral assertions using test ids and visible text.

Acceptance criteria:
- Series row click no longer performs two actions at once
- The user now has two explicit choices:
  - edit series
  - open/view series exceptions
- The edit modal opens only when explicitly requested
- The exceptions area opens only when explicitly requested
- Selected series highlighting still works
- Existing planning-shifts workflows remain intact
- Tests are updated to reflect the new behavior

At the end, provide a concise validation report with these headings:
1. What the old coupled behavior was
2. Which files were changed
3. How selection, edit, and exceptions visibility were decoupled
4. Where the two explicit action buttons were added
5. Which tests were updated or added
6. Any remaining UX follow-ups you recommend

Before coding, explicitly sanity-check whether the current working tree already contains:
- a modal-based exception editor
- recent Series-tab spacing/styling changes
and confirm that your fix will layer on top of those changes rather than overwrite them.
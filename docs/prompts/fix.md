You are working in the SicherPlan repository.

Task goal:
Apply a small, focused UI polish pass to `/admin/planning-staffing` in the `PlanningStaffingCoverageView.vue` workspace.

This task has two parts:

PART A — Filters and scope
1. The three filter selects should have clear placeholder behavior:
   - Planning mode
   - Workforce scope
   - Confirmation state
2. The placeholders should make it obvious that these controls are selects and that no filter is currently chosen.

PART B — Shift coverage
1. The `Shift coverage` panel should no longer be excessively wide.
2. Its visual dimensions should be aligned more closely with the `Filters and scope` card, instead of stretching disproportionately across the workspace.
3. The clickable row/button items inside `Shift coverage` currently feel vertically cramped.
   Add proper top/bottom spacing so the list items do not look stuck together.

This is a narrow UI refinement task.
Do NOT change staffing logic, filters logic, API contracts, auth/session flow, permission behavior, or page information architecture beyond what is necessary for these UI fixes.

Before coding:
1. Read `AGENTS.md`.
2. Inspect the latest implementation of:
   - `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
3. Check if there is an exact sprint/task reference in `docs/sprint/*.md` or `docs/prompts/*.md`.
4. If there is no exact task for this refinement, state that explicitly in the final summary and keep the change tightly scoped.

Current issues to verify:
- The three filter selects do not communicate their placeholder / unselected state clearly enough.
- The `Shift coverage` panel is visually too wide relative to the left filter card.
- The coverage-result buttons/rows need more vertical breathing room.
- The page should remain responsive after these changes.

Required implementation outcome:

A. Filter select placeholders
- For these three controls:
  - Planning mode
  - Workforce scope
  - Confirmation state
- ensure there is a clear default placeholder option/value when nothing is selected.
- The placeholder text should be explicit and user-friendly, for example:
  - Select planning mode
  - Select workforce scope
  - Select confirmation state
- Keep DE-first / EN-secondary parity if the page uses translation keys.
- Preserve existing filter contract behavior:
  - unselected still maps to “no filter”
  - selected values still map to the same backend/API values as before
- Do not replace these native selects with an unrelated new component unless the repo already has an established pattern and the change remains very small.

B. Shift coverage panel width
- Reduce the excessive width of the `Shift coverage` panel.
- Make it visually closer in dimension to the `Filters and scope` card.
- Do this in a layout-safe way:
  - adjust the page grid/column contract deliberately
  - do not just hardcode an awkward width that breaks responsiveness
- The middle panel should still be usable and readable.
- Avoid making the workspace feel broken or forcing unnecessary wrapping in adjacent panels.

C. Shift coverage row/button spacing
- Improve vertical spacing for the searched/result rows rendered as buttons in the `Shift coverage` list.
- Ensure the buttons/list items have clear separation from one another.
- Ensure there is appropriate inner padding and outer gap/margin so the list no longer feels cramped.
- Keep the current selected state styling intact unless a tiny spacing correction requires minor refinement.

Implementation guidance:
1. Inspect the main layout classes controlling:
   - the overall staffing page grid
   - the filter card
   - the shift coverage panel
   - the list/button rows inside shift coverage
2. For select placeholders:
   - prefer explicit empty option + placeholder copy + consistent select styling
   - preserve current v-model behavior and existing filter serialization
3. For width alignment:
   - use a deliberate column sizing rule or max-width rule
   - keep the page responsive on desktop, tablet, and narrower widths
4. For list spacing:
   - add clean vertical gap between coverage rows/buttons
   - review padding inside the button so text and status badge do not feel crowded

Constraints:
- Do NOT change:
  - filter semantics
  - selected shift behavior
  - staffing commands
  - assignment logic
  - validation/override logic
  - auth/session/tenant scope
- Do NOT perform a broad redesign of the entire page.
- Keep the change set narrow and reviewable.

Files to inspect and likely change:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`

If additional files are touched, it must be only because a very small shared style/helper is necessary.

Acceptance criteria:
1. The three filter selects clearly show placeholder state when no value is selected.
2. Users can immediately recognize them as selects.
3. The `Shift coverage` panel no longer feels disproportionately wide.
4. The dimensions now feel visually more balanced relative to `Filters and scope`.
5. The coverage result rows/buttons have proper vertical spacing.
6. The page remains responsive.
7. No filtering or staffing behavior regressed.

Validation and tests:
- Run the relevant frontend build/typecheck/lint/tests.
- Add or update a focused UI test only if the repo already has a suitable pattern.
- If there is no viewport-aware test harness, document manual validation clearly.

Manual validation checklist:
1. Open `/admin/planning-staffing`.
2. Confirm the three filter selects show clear placeholders when empty.
3. Confirm selecting values still works and filtering still behaves as before.
4. Confirm the `Shift coverage` panel is no longer excessively wide.
5. Confirm the `Shift coverage` result rows/buttons have better top/bottom spacing.
6. Confirm the selected row styling still works.
7. Check wide desktop, medium width, and narrow width layouts.
8. Confirm no horizontal overflow or broken panel alignment.

Important self-check:
Before finalizing, challenge your own implementation and verify that:
- you improved placeholder clarity without changing filter semantics
- you did not break empty-state filtering
- you reduced the excessive width of `Shift coverage` in a responsive-safe way
- you improved row/button spacing without disrupting selected-state behavior
- you did not introduce unrelated refactors
- you did not weaken the overall layout consistency of the page

Final response format:
1. Short implementation summary
2. Exact files changed
3. What UI issues you confirmed
4. What you changed and why
5. Build/typecheck/lint/test results
6. Manual validation results
7. Remaining assumptions or blockers
8. Self-validation explaining why the page is now cleaner and more balanced without regression
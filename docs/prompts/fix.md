You are working in the SicherPlan repository.

Goal:
Fix the layout of the Planning record / Planungsdatensatz field in the Staffing Coverage filter panel.

User-visible page:
admin/planning-staffing

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue

Tests to inspect/update:
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts

Current issue:
In the "Filter und Scope" card, the Planning record / Planungsdatensatz field shows the message:

"Keine passenden Planungsdatensaetze fuer die aktuellen Filter gefunden."

This message appears directly below the select field and increases the height of only this field column. As a result, the alignment and visual rhythm of the filter row are broken compared to the other fields.

Expected behavior:
The Planning record field should display the "no matching planning records" information in a way that does not break the layout or disturb the alignment of the other filter fields.

Before coding:
1. Read AGENTS.md.
2. Inspect the current filter panel implementation around:
   - `planning-staffing-planning-record-select`
   - `filtersPlanningRecordEmpty`
   - `filtersPlanningRecordNoMatch`
   - `filtersPlanningRecordLoading`
   - `planningRecordLookupError`
3. Inspect existing field-help / Select styling patterns in the project.
4. Do not change backend APIs.
5. Do not change the planning record lookup request logic unless there is a proven bug.
6. This task is primarily a frontend layout/UX fix.

Required change:
1. Keep the Planning record select field visible and aligned with the other filter fields.
2. Do not render the long empty/help message as a normal paragraph that pushes the row height down.
3. Use one of these safe UI patterns:
   Option A — Compact inline status inside the field area:
   - render a short muted status line with fixed/reserved height under the select, using one-line ellipsis.
   - example: "Keine passenden Planungsdatensätze"
   - keep full text in a title/tooltip.
   
   Option B — Tooltip/help icon:
   - show a small info icon or compact hint next to the label.
   - full message appears on hover/title.
   
   Option C — Dropdown empty state:
   - if the Select component supports `notFoundContent`, render the no-match message inside the dropdown instead of below the field.
   - this is preferred if compatible with the current Select implementation.

4. The final layout must keep all filter fields in the same row height:
   - Von
   - Bis
   - Planungsdatensatz
   - Planungsmodus
   - Workforce-Scope
   - Bestaetigungsstatus
5. Keep loading and error states visible, but compact:
   - loading: short compact text or spinner
   - error: compact one-line warning with tooltip/full title
6. Preserve existing i18n keys if possible.
7. If needed, add a shorter translation key, for example:
   - `filtersPlanningRecordEmptyShort`
   - DE: "Keine passenden Planungsdatensätze"
   - EN: "No matching planning records"
8. Do not hardcode visible German/English labels in the template if the page uses `tp(...)`.

Implementation guidance:
- Consider adding a small helper class, for example:
  - `planning-staffing-field-help-compact`
  - `planning-staffing-planning-record-hint`
- Suggested CSS:
  - min-height reserved for compact hint, or absolute positioning within the field stack
  - font-size smaller than normal body text
  - white-space: nowrap
  - overflow: hidden
  - text-overflow: ellipsis
  - max-width: 100%
- Keep accessibility:
  - full message should be available via `title`, `aria-label`, or screen-reader friendly text.
- Do not remove the message completely; make it compact and non-disruptive.

Tests:
Update or add the smallest relevant test in `planningStaffing.smoke.test.ts`.

Required test coverage:
1. When no planning records match, the planning record field still renders.
2. The no-match message is shown in a compact form or is available as dropdown empty content/tooltip.
3. The long message is not rendered as a normal `field-help` paragraph that disrupts the filter grid.
4. Other filter fields still render in the same filter panel.
5. No API request payloads are changed.

Acceptance criteria:
- The Planungsdatensatz field no longer breaks the filter row layout.
- The no-match information is still available to the user.
- The filter panel remains clean and aligned.
- No backend changes.
- Existing staffing loading/filtering behavior is unchanged.
- Tests pass.

Run:
cd web
pnpm test -- planningStaffing
pnpm lint
pnpm typecheck

If these exact scripts are unavailable, inspect package.json and run the closest existing web test/lint/typecheck commands.

Final response:
- Explain which UI pattern you chose.
- List changed files.
- List tests run and results.
- Confirm this was frontend-only.
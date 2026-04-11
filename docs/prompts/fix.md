You are working in the SicherPlan repository.

Task goal:
Fix the "Filters and scope" UX in `/admin/planning-staffing` (P-04 Staffing Board & Coverage) by replacing the user-facing `Planning record ID` textbox with a business-friendly planning-record selector and by making the filter/header layout responsive on narrow widths.

Before coding:
1. Read `AGENTS.md`.
2. Find the relevant `US-N-TN` task in `docs/sprint/*.md` or `docs/prompts/*.md`.
3. If no official task exists for this exact refinement, say that explicitly in your final summary and keep backlog traceability clear.
4. Keep this change narrowly scoped to the filter/header UX and responsiveness. Do NOT change permissions, auth flow, staffing logic, or backend schemas unless a very small supporting fix is strictly required.

Inspect first:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `backend/app/modules/planning/router.py`
- the actual style source for:
  - `.planning-staffing-filter-grid`
  - `.planning-staffing-panel__header`
  - `.planning-staffing-panel__actions`
  - `.field-stack`
  - related filter/header classes
  This style source may be in the same `.vue` file or in a shared legacy stylesheet.
- any existing select-search / combobox pattern already used in `web/apps/web-antd`

Current facts you must verify in code before changing anything:
- `PlanningStaffingCoverageView.vue` currently renders the planning-record filter as a raw textbox bound to `filters.planning_record_id`.
- The current page already derives role/tenant/token from the auth store. Do not rework auth/session handling.
- `listPlanningRecords(...)` already exists in `planningOrders.ts`.
- `PlanningRecordListItem` already provides at least:
  - `id`
  - `name`
  - `planning_mode_code`
  - `planning_from`
  - `planning_to`
  - `release_state`
  - `status`
- Backend planning-record list supports filters such as:
  - `search`
  - `planning_mode_code`
  - `planning_from`
  - `planning_to`
- Backend staffing-board / coverage filters already support `planning_record_id` and the current date-window filters.

Required UX decision:
- The primary user-facing control must NOT remain a raw textbox.
- Replace it with a business-friendly select-search / combobox for planning records.
- Rename the user-visible label from `Planning record ID` to `Planning record` (and the DE equivalent).
- Keep the underlying selected value mapped to `filters.planning_record_id` so the backend contract remains unchanged.
- A raw ID paste field is allowed only as a secondary advanced/debug affordance, not as the main control.
- Default recommendation is a searchable selector. Only fall back to a plain select if you can explicitly justify that choice from repo-wide UI constraints and final usability.

Planning-record selector requirements:
- Reuse the existing `listPlanningRecords()` API. Do NOT add a new backend endpoint if it is not necessary.
- Prefer an existing repo-standard searchable select component/pattern (Vben / web-antd / repo-local). Do NOT add a new dependency just for this.
- Build option labels from existing list-item data, for example:
  `name · planning_mode_code · planning_from → planning_to`
  You may append release/status meta if it improves clarity.
- Support clear selection = "all planning records".
- Add loading, empty, and error states.
- Inspect the backend filter contract carefully and send only supported filters.
- Important:
  - planning-record list uses date-based filters
  - staffing board uses datetime-local filters
  Convert safely or omit those filters instead of sending unsupported values.
- Avoid unnecessary network chatter:
  - debounce remote search if remote search is used
  - and/or cache the recent option set per tenant scope if appropriate

Responsive layout requirements:
- Fix the `Filters and scope` header so CTA buttons wrap cleanly instead of colliding when width shrinks.
- Fix the filter grid so inputs/selects never overflow, overlap, or break alignment.
- Ensure `datetime-local`, native selects, text inputs, and the new planning-record selector all become full-width inside their grid cells.
- Use `min-width: 0` where needed to prevent intrinsic-width overflow.
- Prefer a responsive grid such as `repeat(auto-fit, minmax(...))` or a clearly equivalent solution.
- Add at least one narrow-screen breakpoint where the filter area stacks cleanly into a single column if needed.
- Preserve the current visual language. Do NOT redesign the entire page.

Implementation constraints:
- Keep `refreshAll()`, `queryFilters()`, and downstream use of `filters.planning_record_id` working exactly as before from the API perspective.
- Do NOT change backend response shapes unless strictly required.
- Do NOT refactor unrelated staffing actions, validation logic, dispatch, or overrides.
- Keep DE-first / EN-secondary text parity for any new labels, placeholders, helper text, or empty states.
- Prefer a focused change set over broad cleanup.

Suggested implementation direction:
1. Add planning-record option state and loading state to `PlanningStaffingCoverageView.vue`.
2. Reuse `listPlanningRecords()` from `planningOrders.ts`.
3. Map the selected planning-record option back to `filters.planning_record_id`.
4. Replace the raw textbox with a searchable selector.
5. Keep an optional advanced raw-ID input only if truly justified.
6. Update the filter/header styles at their real source so the layout wraps correctly on narrow widths.
7. Add or update targeted tests.

Tests and validation:
- Add or update tests for:
  - planning-record option loading/mapping
  - selection behavior updating `filters.planning_record_id`
  - clear behavior resetting `filters.planning_record_id`
  - supported filter conversion for planning-record lookup
  - no regression in `refreshAll()` filtering behavior
- If the repo does not have a viewport-aware UI test harness, do a documented manual responsive verification and say so explicitly.
- Run the relevant build / lint / typecheck / tests before finishing.

Manual acceptance checks:
- On `/admin/planning-staffing`, the user can choose a planning record without knowing the raw UUID.
- The chosen planning record still filters coverage/staffing correctly via `filters.planning_record_id`.
- On narrower widths, the CTA row wraps cleanly, fields align, and no control overlaps or spills horizontally.
- The page still uses the existing authenticated session and tenant scope.

Important self-check:
Before finalizing, challenge your own implementation and verify that:
- you did NOT leave the raw planning-record textbox as the primary control
- you did NOT break the existing `planning_record_id` API contract
- you did NOT send unsupported datetime values to the planning-record list endpoint
- you did NOT touch auth/session logic unnecessarily
- you did NOT leave the header/action row or filter grid broken on narrow screens
- you did NOT introduce unrelated refactors

Required final response format:
1. Short implementation summary
2. Exact files changed
3. Verified current issues
4. What changed and why
5. Test/build/typecheck/lint results
6. Manual responsive validation result
7. Remaining assumptions or blockers
8. Self-validation explaining why:
   - select-search is the correct control for P-04 here
   - the responsive layout is now fixed
   - no unrelated regressions were introduced
You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth.
A previous deep-link fix was incomplete and is now proven wrong by live logs.
Do NOT continue from the assumption that `staffing-board?shift_id=...` alone is valid.

Task:
Fix `/admin/planning-staffing` deep-link hydration from dashboard calendar links so the intended shift reliably opens and renders.

Current proven facts from the live system:
1. The dashboard/staffing deep-link currently uses route query like:
   - `date_from=2026-05-08T08:00`
   - `date_to=2026-05-09T16:00`
   - `planning_record_id=...`
   - `shift_id=...`
2. The page still fails to render the intended shift and falls back to empty/planning-context-only UI.
3. A previous attempted fix changed exact hydration to:
   - `GET /ops/staffing-board?shift_id=...`
4. That exact request is INVALID in the real backend and returns 422.
5. Backend router currently requires:
   - `date_from: datetime = Query(...)`
   - `date_to: datetime = Query(...)`
   on the staffing-board filter dependency.
6. Therefore, `shift_id` alone is not a valid exact-hydration query for staffing-board.

You must treat the above as the new ground truth.

What to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
   especially:
   - `applyRouteQueryContext()`
   - `queryFilters()`
   - `refreshAll()`
   - any exact-shift hydration helper introduced by the previous patch
   - route watcher
   - selected shift hydration/fallback logic
2. `web/apps/web-antd/src/views/sicherplan/dashboard/index.vue`
   - current dashboard calendar link generation
3. `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
4. `web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts`
   - inspect whether `getShift(...)` can help derive canonical timing even if it does not replace staffing-board
5. `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

Critical debugging requirement:
You must compare the two real cases:

A. Failing route from dashboard:
- `date_from=2026-05-08T08:00`
- `date_to=2026-05-09T16:00`
- `planning_record_id=...`
- `shift_id=...`

B. Manually working staffing page state:
- the same shift opens correctly when the time window is adjusted to a staffing-friendly daily range

Your job is to determine the real contract difference between A and B.

Most likely root cause to verify:
This is now likely a DATE WINDOW / TIMEZONE / STAFFING DAY semantics bug, not just a missing `shift_id` bug.

Hypothesis to test:
- dashboard currently generates a shift-window link
- staffing page / staffing-board endpoint actually behaves correctly only with a staffing-day window (or another canonical window)
- therefore exact hydration must use a canonical staffing window, not the raw dashboard shift window and not `shift_id` alone

Required fix direction:
You must find the safest combination of these fixes:

1. Canonical staffing window normalization
   - derive a staffing-compatible date window when `shift_id` is present
   - this may mean converting the dashboard link or staffing hydration from “shift start/end window” to “day window” or another canonical operational window
   - do NOT guess: inspect actual backend behavior and compare with the manually working case

2. Correct exact hydration query
   - if using `staffing-board`, always include the required `date_from` and `date_to`
   - do not use `shift_id` alone
   - if exact hydration is needed, combine:
     - `shift_id`
     - canonical date window
     - optionally `planning_record_id` if required and safe

3. If necessary, use `getShift(...)` as a helper
   - not as the final data source for UI
   - but to derive the correct canonical date window or to confirm the shift’s true timestamps/context

4. Fix either or both:
   - dashboard calendar link generation
   - staffing page route hydration
   whichever is necessary for the real contract

Important implementation rule:
The staffing page must not fail just because the dashboard passed a raw shift-window query that is not the canonical staffing-board filter shape.
If needed, the staffing page should normalize that route input before calling the APIs.

Important fallback rule:
Only fall back to empty/planning-context-only UI after:
- canonical deep-link normalization has been attempted
- exact hydration with valid required filters has been attempted
- and the target shift still truly cannot be resolved

Do NOT:
- keep the broken `shift_id`-only staffing-board request
- rely only on status code 200 without checking response bodies
- rely only on tests that do not model the real failing route shape

Testing requirements:
Update/add tests in:
`web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

Add a regression test that models the real scenario:
1. route query contains:
   - `date_from=2026-05-08T08:00`
   - `date_to=2026-05-09T16:00`
   - `planning_record_id=...`
   - `shift_id=...`
2. generic board/coverage calls using that raw route window fail to hydrate the target shift
3. exact hydration using `shift_id` alone is invalid and must NOT be used
4. canonical window normalization (or corrected link generation) is applied
5. the page then successfully hydrates the intended shift
6. the page renders real shift detail instead of empty/planning-context-only content

Also add tests for:
- no 422-causing `staffing-board?shift_id=...` request path remains
- canonical date window is used for exact hydration when `shift_id` exists
- route-driven selected shift is preserved until canonical hydration finishes

Acceptance criteria:
- The real failing dashboard link now opens the intended shift
- No invalid `staffing-board?shift_id=...` request is made
- The page no longer falls back incorrectly
- The fix matches actual backend contract and live behavior
- Tests cover the real regression

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Why the previous `shift_id`-only fix was wrong
3. What canonical window rule is now used
4. Whether the fix was in dashboard link generation, staffing hydration, or both
5. Which files were changed
6. Which tests were updated or added
7. Any remaining manual checks you recommend

Before coding, explicitly answer:
- What does the 422 response body for `staffing-board?shift_id=...` say?
- What is the exact difference between the failing dashboard window and the manually working window?
- Should the canonical fix live in dashboard link generation, staffing hydration, or both?
Then implement the safest real fix.
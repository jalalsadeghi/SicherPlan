You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth. Do NOT revert unrelated dashboard or planning-staffing changes. Apply only a focused fix for the broken dashboard → staffing deep-link.

Task:
Fix the calendar item link generation on `/admin/dashboard` so that clicking a staffing/coverage item opens `/admin/planning-staffing` with the correct date window and preloaded context.

Observed bug:
A dashboard calendar item currently links like this:

/admin/planning-staffing?date_from=2026-05-06T08:00&date_to=2026-05-06T16:00&planning_record_id=a469dd2c-a0a3-4f59-951f-eb3cd03ec068&shift_id=3cc76392-32f7-424c-9a84-5bb49aacc5ac

This does NOT open the correct item in the staffing page.

The same item works correctly when using this effective window instead:

date_from=2026-05-06T08:00
date_to=2026-05-07T16:00

So the dashboard is currently generating the wrong `date_to` for this deep-link.

Goal:
Make calendar item navigation into `/admin/planning-staffing` open the correct shift coverage context on first click, without manual re-entry of dates.

Critical requirement:
Do NOT blindly hardcode “always add one day” unless that is confirmed to be the real general rule.
First inspect the current working tree and determine the correct deep-link window semantics for planning-staffing.

What to inspect first:
1. `web/apps/web-antd/src/views/sicherplan/dashboard/index.vue`
   - current calendar item model
   - current href/route generation for staffing items
2. The current planning-staffing page implementation
   - how `date_from`, `date_to`, `planning_record_id`, and `shift_id` are consumed
   - whether the page expects a broader lookup window than the raw shift end
3. Any helpers already used for formatting datetime-local query values
4. Whether the target page treats `date_to` as inclusive, exclusive, or as a broader operational lookup window
5. The actual working-tree logic that already makes manual search succeed

Required outcome:
1. Clicking a dashboard coverage item must land the user in `/admin/planning-staffing` with a query window that actually opens the intended staffing context.
2. `planning_record_id` and `shift_id` must continue to be preserved in the link if they are already present.
3. The fix must be general and safe, not just a one-off string patch.

Expected implementation approach:
1. Identify the current function/computed block that builds the calendar item link/href.
2. Determine the correct rule for generating the staffing deep-link time window.
3. Update the link generator to use the correct rule.
4. Keep the rest of the calendar item rendering unchanged unless needed for the fix.
5. Verify that the planning-staffing page hydrates correctly from the corrected query string.

Important design rule:
The dashboard calendar item should link to the operational context the user expects to inspect/fix.
So the target URL must be built for *working hydration*, not just for a superficially related route.

Validation requirement using the reported regression:
Use this concrete example as a regression test case:

Broken current link:
- date_from = 2026-05-06T08:00
- date_to   = 2026-05-06T16:00

Expected working target:
- date_from = 2026-05-06T08:00
- date_to   = 2026-05-07T16:00

Do not assume the rule is “add 24h” for all cases until verified.
But this example must pass after the fix.

Things to watch carefully:
- local datetime vs UTC conversion
- truncation to `YYYY-MM-DDTHH:mm`
- inclusive/exclusive filter mismatch
- double encoding of query params
- preserving `planning_record_id` / `shift_id`
- not breaking other dashboard calendar item types

Constraints:
- Do NOT redesign the dashboard
- Do NOT redesign the staffing page
- Do NOT break existing working calendar items
- Keep the patch focused on correct query-window generation and hydration reliability

Testing guidance:
Add or update focused tests.
At minimum verify:
1. staffing calendar item link generation now produces the correct effective date window
2. the known regression example resolves to the corrected query params
3. existing `planning_record_id` and `shift_id` are preserved
4. non-staffing calendar items are not broken
5. if the planning-staffing page has query hydration tests, extend them as needed

Prefer behavioral tests over brittle string snapshots, but ensure the final URL/query parameters are asserted clearly.

Acceptance criteria:
- Dashboard calendar click opens the correct staffing context on first try
- Manual date correction is no longer required
- The fix uses the real working deep-link rule, not a guessed workaround
- Tests cover the regression

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Which files were changed
3. What rule is now used to generate `date_to`
4. Why the old link failed
5. How the corrected link now hydrates planning-staffing properly
6. Which tests were added or updated
7. Any remaining edge cases you recommend checking

Before coding, explicitly answer:
- What exact code currently generates the broken `date_to`?
- What exact rule explains why `2026-05-07T16:00` works while `2026-05-06T16:00` fails?
Then implement the safest generalized fix.
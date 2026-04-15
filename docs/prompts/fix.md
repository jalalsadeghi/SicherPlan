You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth.
Do NOT revert the existing dashboard calendar item work.
The committed `main` branch still shows only count pills in the calendar, so the slow cell-item layer is coming from the live/working-tree dashboard changes.
Your job is to optimize that new layer without removing its functionality.

Task:
Improve the loading performance of `/admin/dashboard` → `Planning calendar`, specifically the slower item content rendered inside `sp-dashboard__calendar-cell`, while preserving the already-fast `sp-dashboard__calendar-events` count pills.

Observed behavior:
- `sp-dashboard__calendar-events` loads relatively fast
- the richer content inside the calendar cells loads noticeably slower
- the dashboard should feel fast immediately, and then hydrate detailed day items efficiently

Performance goal:
Keep the count pills fast and make the richer day-item content load much faster, with fewer requests, less recomputation, and no unnecessary render-blocking.

What to inspect first:
1. The current working-tree dashboard calendar implementation
   - especially any logic that adds rich day items beyond the committed main-branch count pills
2. Whether the working tree currently fetches:
   - `listStaffingCoverage(...)`
   - `listStaffingBoard(...)`
   - or even multiple per-day/per-cell calls
3. How month changes are handled
4. Whether there is any duplicate fetch caused by watchers / focus refresh / route refresh
5. Whether cell items are regrouped/recomputed on every render instead of once per fetch

Important API guidance:
Use the lightest sufficient data source.
For dashboard calendar day items, prefer the coverage endpoint, not the heavier staffing-board endpoint, unless the current working tree proves otherwise.
Do NOT fetch assignments/board-level detail if the calendar only needs:
- shift label
- time window
- coverage state
- planning context
These should come from the coverage payload if available.

Primary optimization strategy:
1. Render dashboard shell and count pills immediately
2. Load richer calendar cell items asynchronously after the first paint
3. Fetch coverage in one bulk request per visible month
4. Cache results by tenant + visible month
5. Deduplicate in-flight requests
6. Group fetched coverage rows by day once, not on every render
7. Avoid per-cell, per-day, or per-item network calls

Required implementation direction:
A. Progressive hydration
- The calendar grid and `sp-dashboard__calendar-events` should render immediately
- The detailed cell items should hydrate separately without blocking the whole calendar

B. Use one monthly bulk fetch
- When the visible month changes, compute the month window
- Request coverage once for that month
- Do NOT issue a request per day or per cell

C. Cache + dedupe
- Cache coverage results by a stable key such as:
  `tenantId + monthStart + monthEnd`
- If the user returns to a month already loaded, reuse cached data
- If the same request is already in flight, reuse or safely ignore duplicate work

D. Pre-group once
- After receiving coverage rows, transform them once into a structure like:
  `Map<dayKey, DashboardCoverageItem[]>`
- Then let each cell do only O(1) lookup by day key
- Avoid repeatedly filtering the full coverage array for every cell

E. Use the lightest payload
- If the current working tree is using `listStaffingBoard(...)` for dashboard cell items, switch to `listStaffingCoverage(...)` unless a proven requirement blocks it
- Do not use board-level payload when coverage-level payload is enough

F. Avoid extra lookups
- Build day-item labels directly from available row fields
- Do not do follow-up fetches per item for names if the coverage row already includes enough display data

G. Prevent stale updates
- If month changes while a coverage request is in flight:
  - cancel it if current codebase supports AbortController cleanly
  - or ignore stale resolution safely
- Do not let older responses overwrite newer month data

What to look for as likely root causes:
- per-day/per-cell requests
- use of `listStaffingBoard(...)` instead of `listStaffingCoverage(...)`
- repeated full-array filtering for each of 35 cells
- request duplication from multiple watchers
- blocking first render on coverage items
- expensive reactive recomputation instead of one-time grouping

What to preserve:
- existing count pills in `sp-dashboard__calendar-events`
- existing click behavior for day items
- existing color/state semantics
- existing month navigation behavior
- existing dashboard visual structure

Testing / validation requirements:
Add or update focused tests for the working-tree dashboard calendar logic.

At minimum verify:
1. detailed calendar item loading is decoupled from the initial count-pill render
2. only one coverage request is made per visible month load
3. no per-cell or per-day request pattern remains
4. cached month data is reused when revisiting the same month
5. stale in-flight responses do not overwrite newer month state
6. day items are grouped by day once and rendered from that grouped structure
7. if the previous implementation used staffing-board, confirm the dashboard now uses coverage instead (if safe)
8. the UI still renders correctly when coverage is empty

Manual validation checklist:
- open dashboard on a tenant with visible month data
- confirm count pills appear immediately
- confirm detailed cell items hydrate shortly after without freezing the page
- confirm navigating to next/previous month causes at most one coverage request
- confirm returning to an already visited month is faster due to cache reuse
- confirm no waterfall of per-day requests in Network

Acceptance criteria:
- `sp-dashboard__calendar-events` remains fast
- `sp-dashboard__calendar-cell` detailed item content loads significantly faster
- the calendar no longer relies on heavy or repeated requests
- month-to-month navigation stays responsive
- the change is local, maintainable, and does not remove existing rich calendar functionality

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Which file(s) were changed
3. Which data source is now used for dashboard cell items
4. How monthly fetch/caching/deduplication now works
5. How render-blocking was reduced
6. Which tests were updated or added
7. Any remaining edge cases to verify manually

Before coding, explicitly answer:
- Is the current working tree using per-cell/per-day requests?
- Is it using `listStaffingBoard(...)` or `listStaffingCoverage(...)`?
- Is the rich cell content blocking first render?
Then implement the safest optimization based on those findings.
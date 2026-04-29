We need to optimize the initial search/load performance of /admin/planning-staffing after fixing repeated reloads.

Current state:
Repeated reloads after normal clicks should already be fixed.
Now focus only on making the intentional "Load staffing" action faster and more responsive.

Files:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts
- backend files only if frontend optimization is insufficient

Task:
Profile and optimize the intentional load.

Step 1 — Measure current intentional load:
For one Load staffing action with a large date range, record:
- number of coverage rows
- number of staffing-board rows
- response time for coverage
- response time for staffing-board
- time to first visible list row
- time to selected shift detail ready
- number of rendered DOM rows
- browser main-thread time if measurable

Step 2 — Keep UI responsive:
When Load staffing is clicked:
- show filter panel immediately
- show loading state only for affected panels, not the entire page if possible
- render results incrementally if feasible
- avoid blocking the UI while all support data loads

Step 3 — Avoid auto-select heavy detail:
If the first selected shift causes many support requests, consider:
- selecting first shift visually but not loading heavy detail until detail panel is visible/needed
- or loading only the default tab’s minimal data
- do not load all detail tabs for the first shift upfront

Step 4 — Large list rendering:
If coverageRows can be large:
- consider virtualized list or windowed rendering for the left shift coverage list
- at minimum, avoid expensive computed formatting for every row on every render
- memoize row labels and coverage states by shift_id/version

Step 5 — Stable computed data:
Avoid computed values that rebuild huge arrays/maps on every reactive change.
Use:
- shallowRef for large arrays
- stable Maps keyed by shift_id
- computed only over the current subset when possible

Step 6 — Planning record dropdown:
The planning record lookup should not reload the full planning records list on every filter/search keystroke.
Use:
- debounced search
- cache by tenant + date range + search term
- minimum search length if appropriate
- do not block staffing load on dropdown options unless required

Step 7 — Optional backend optimization only if necessary:
If coverage + staffing-board are inherently slow due to backend:
Propose a backend read-optimized endpoint, but do not implement unless frontend profiling proves it is needed.

Possible endpoint:
GET /api/planning/tenants/{tenant_id}/ops/staffing-workspace

It could return:
- coverage summary
- coverage rows
- staffing board rows
- planning record labels needed for the selected range
But keep it read-only and tenant-scoped.

Backend constraints:
- preserve tenant isolation
- preserve permissions
- do not include unnecessary employee/private data
- keep existing endpoints unchanged

Tests:
A. Performance-focused unit/component tests:
- one Load staffing call triggers exactly one coverage and one board call
- first row renders before selected-shift heavy details finish
- large arrays are not rebuilt when unrelated state changes

B. Lazy detail test:
- outputs/validations/teams/releases do not load until related tab is active

C. Dropdown lookup test:
- planning record search is debounced/cached

Acceptance criteria:
- Intentional Load staffing action is visibly faster.
- Main UI is responsive while data loads.
- Heavy detail data does not block list rendering.
- Large result list does not cause unnecessary recomputation.
- Backend changes are avoided unless proven necessary.
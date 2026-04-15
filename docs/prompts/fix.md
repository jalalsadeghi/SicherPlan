You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current working tree as the source of truth.
The user’s live staffing page already has an assignment modal flow and recent loading-overlay work.
Do NOT revert that work.
Your task is to reduce the latency of create/edit assignment operations as much as safely possible, by eliminating unnecessary frontend waiting and redundant requests.

Task:
Optimize `/admin/planning-staffing` assignment interactions so that:
1. opening an existing assignment for edit is much faster
2. creating/saving/updating/removing assignments feels significantly faster
3. the UI still stays correct and consistent

Observed UX problem:
Assignment actions in Staffing Coverage feel too slow:
- clicking an existing assignment takes too long before edit is ready
- saving assignment takes too long
- repeated assignment operations make the page feel heavy and frustrating

Key objective:
Reduce real waiting time, not just show more spinners.
Loading feedback is useful, but the main goal is to remove unnecessary work and reduce total round-trips.

What to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
2. `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
3. `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

Before coding, explicitly map the current request flow for these two scenarios:
A. clicking an existing assignment row to edit it
B. clicking Save assignment in create/edit mode

You must identify:
- which requests fire
- which ones are duplicated
- which ones are unnecessarily global/heavy
- which ones can be delayed, skipped, cached, or narrowed

Known likely issues to validate:
1. Opening edit mode may fetch assignment-related data more than once because:
   - explicit edit-opening logic loads details
   - watcher-based selection logic may load again
2. Save/create/update may currently trigger a broad `refreshAll()` that refetches much more than assignment flow actually needs
3. Supporting data such as employees / teams / team members may be getting reloaded even though assignment save does not require them to be refetched
4. Shift outputs and release validations may be loaded eagerly even when the user is not on those tabs

Optimization goals:
1. Open edit modal immediately (or near-immediately), without waiting for all detail requests first
2. Eliminate duplicate assignment-detail fetches
3. Replace broad post-save refresh with a targeted refresh strategy
4. Avoid refetching supporting catalogs/lists unnecessarily
5. Lazy-load or defer data that is not needed for the active tab
6. Keep correctness after create/update/remove/substitute

Preferred implementation strategy:
A. Make edit-open fast
- Do not block modal open on full assignment-detail loading
- Open modal immediately using the data already available from the selected board assignment where possible
- Load richer assignment details/validations/overrides in the background if still needed
- Show modal-local loading state while those details hydrate

B. Eliminate duplicate assignment-detail requests
- Inspect whether `selectedAssignmentId` watcher duplicates explicit detail loading
- Ensure assignment detail/validation/override fetch happens once per edit-open action
- Add in-flight deduplication if needed

C. Replace `refreshAll()` after assignment mutations
- Do NOT use a global full refresh for every create/update/remove if a narrower refresh can do the job
- Prefer a targeted refresh helper such as:
  - refresh current shift only
  - refresh current assignment only
  - refresh validations only when required
- If the backend supports filtering `listStaffingCoverage` / `listStaffingBoard` by `shift_id`, use that to narrow the refresh
- If not, patch local state optimistically from the returned `createAssignment` / `updateAssignment` payload and then do a minimal background reconciliation

D. Do not reload unrelated supporting data on every assignment action
- `refreshSupportingData()` or equivalent should not run after every assignment create/edit unless the assignment action truly invalidates that data
- Teams, team members, employees, subcontractor workers, releases, demand groups should only be refreshed when actually necessary

E. Lazy-load non-critical side data
- Do not reload `listShiftOutputs(...)` on assignment actions unless outputs are actually needed
- Do not reload shift release validations eagerly unless:
  - the active tab needs them
  - or assignment mutation requires them for visible state
- Keep assignment validations/overrides targeted to the currently edited/selected assignment

F. Add caching where safe
- Cache assignment details / validations / overrides per assignment id when safe
- Invalidate or refresh that cache after mutation
- Do not cache in a way that creates stale incorrect UI

Important correctness constraints:
- Do not break create mode
- Do not break edit mode
- Do not break remove/unassign/substitute
- Do not break validation visibility where required
- Do not silently hide backend validation failures
- Keep selected-assignment behavior user-driven and stable

Performance validation requirements:
Before and after the fix, explicitly compare the request graph for:
1. edit existing assignment
2. save assignment

You must state:
- request count before
- request count after
- which requests were removed, deduplicated, deferred, or narrowed

Testing requirements:
Update/add focused tests in:
`web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

At minimum verify:
1. clicking an existing assignment no longer triggers duplicate assignment-detail loads
2. edit modal can open before all detail fetches finish (if that is the chosen solution)
3. saving assignment no longer causes unrelated supporting-data reloads
4. assignment save uses targeted refresh or local patching instead of broad refreshAll where appropriate
5. assignment create/edit/remove still leave the UI correct
6. request-related mocks show fewer unnecessary calls than before

Good concrete assertions to add if safe:
- `getAssignment` / `getAssignmentValidations` / `listAssignmentValidationOverrides` are not called twice for one edit-open click
- `listEmployees`, `listTeamMembers`, `listShiftOutputs` are not reloaded on every assignment save unless truly necessary
- assignment list and selected shift state remain correct after mutation

Acceptance criteria:
- Edit assignment opens significantly faster
- Save/create/update/remove assignment feel significantly faster
- Duplicate and unnecessary requests are removed
- The user-visible result remains correct
- Tests cover the optimization and regression risk

At the end, provide a concise validation report with these headings:
1. Root cause found
2. Before/after request flow for edit-open
3. Before/after request flow for save
4. Which requests were removed or narrowed
5. Which files were changed
6. Which tests were updated or added
7. Any remaining bottleneck that appears to be backend-side rather than frontend-side

Before coding, explicitly answer:
- Which assignment requests are currently duplicated?
- Which post-save requests are global but do not need to be?
- Can current APIs be narrowed by `shift_id`, or is local patching the safer route?
Then implement the safest high-impact optimization.
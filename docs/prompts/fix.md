/review Please review the performance optimization for the Candidates section in the customer order wizard `Assignments` step.

Business requirement:
The Candidates section must load quickly while preserving correctness. Candidates must still be selected and ranked by suitability for the selected demand-group context, qualifications, availability, conflicts, filters, and workforce scope.

Review against:
- `web/apps/web-antd/src/views/sicherplan/customers/customer-new-plan-assignments-step.vue`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-assignments.smoke.test.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- `backend/app/modules/planning/repository.py`
- `backend/app/modules/planning/schemas.py`
- `backend/tests/modules/planning/test_staffing_engine.py`

Review focus:
1. Performance
   - Candidate loading is measurably faster.
   - Obvious N+1 patterns are removed.
   - Candidate endpoint is lighter than full snapshot.
   - Search/filter changes do not reload full snapshot.
   - Large candidate lists do not render all expensive details at once.

2. Correctness
   - Candidate qualification/function checks still work.
   - Availability/absence/conflict checks still work.
   - Team and employee group filters still work.
   - Search still works.
   - Actor kind/workforce scope still works.
   - Candidate ranking remains meaningful and deterministic.

3. Safety
   - Assignment preview/apply validation remains authoritative.
   - Optimization does not allow invalid assignments.
   - Tenant scoping is preserved.
   - Lock/editability behavior is preserved.

4. API/DTO compatibility
   - New fields are backward compatible.
   - Frontend and backend contracts match.
   - Generated artifacts are handled if schema changed.

5. UX
   - Candidate rail has its own loading state.
   - Calendar/summary can render while candidates load.
   - Empty states are clear.
   - Load more/pagination behavior is understandable if implemented.
   - No user-facing strings are hardcoded.

6. Tests
   - Backend tests cover performance-sensitive call patterns.
   - Frontend tests cover candidate loading behavior.
   - Existing assignment apply flow still works.
   - Build/tests pass.

Required output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

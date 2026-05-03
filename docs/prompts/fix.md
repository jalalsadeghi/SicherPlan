/review Please review the customer order wizard `Assignments` step for correctness, workflow fit, editability, performance, and regression risk.

Business context:
The customer order wizard currently has 8 steps. `Assignments` is step 8 after `Demand groups`. The step should assign suitable workers to generated shifts for the selected shift plan / series and selected demand-group context.

Review against:
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.steps.ts`
- `web/apps/web-antd/src/views/sicherplan/customers/customer-new-plan-assignments-step.vue`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-assignments.smoke.test.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- `backend/app/modules/planning/schemas.py`
- `backend/tests/modules/planning/test_staffing_engine.py`
- existing admin/planning-staffing semantics
- German default / English secondary localization rules

Review focus:
1. Step and prerequisite correctness
   - Assignments is step 8 after Demand groups.
   - It requires generated shifts and demand groups.
   - Empty states are correct for no shifts, no demand groups, no candidates.
   - It does not silently assign without demand-group context.

2. Candidate correctness
   - Candidate list is tenant-scoped.
   - Candidate list is demand-group scoped.
   - Qualification/function/actor/workforce/team/group/search filters are correct.
   - Ranking prefers workers who can cover more eligible project days.
   - Candidate reasons/empty state are understandable.

3. Calendar correctness
   - Default month is project start month.
   - Non-project dates are disabled.
   - Project dates are color-coded with planning-staffing semantics.
   - Assigned/target counts are accurate for the selected demand group.
   - Existing assignments are reflected.

4. Assignment behavior
   - Target shift ids are correct.
   - Ineligible days are not silently assigned.
   - Preview/apply behavior is correct.
   - Partial accepted/rejected results are communicated.
   - Repeated assignment does not create duplicates.
   - `unfilled_only` is respected.
   - Non-drag fallback remains available.

5. Completion logic
   - Completion is not triggered by just one assignment if other mandatory coverage is missing.
   - Completion rule matches the product/business rule.
   - Submit gives a clear reason if incomplete.

6. Editability and backend guards
   - Locked downstream state disables unsafe assignment actions.
   - Backend rejects unsafe mutations when locked.
   - UI read-only state matches backend rules.

7. Performance
   - Initial load does not duplicate full snapshot calls.
   - Reference data caching is safe.
   - Filter/search changes use candidate endpoint where possible.
   - Backend avoids obvious N+1 behavior.

8. UX and localization
   - Filter row is clean and responsive.
   - Candidate rail is compact and scrollable.
   - Calendar is legible.
   - User-facing strings are localized.
   - Visual style follows SicherPlan/Vben.

9. Regression risk
   - Demand groups step still works.
   - admin/planning-staffing still works.
   - Assignment APIs still work.
   - Existing tests pass.

Required output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

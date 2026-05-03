/review Please review the fixes for the customer order wizard `Assignments` step calendar no-shift days and candidate card UI.

Business requirements:
1. Days inside the project date range but without generated shifts, such as weekend/off days, must appear neutral grey, not red/blocked.
2. Days with real generated demand that is uncovered/blocked must still appear red/blocked.
3. Candidate cards in the left rail must be compact and show only profile image/initials, candidate name, and personnel number by default.
4. Raw negative score numbers must not be shown in the default candidate card UI.
5. Assignment drag/drop and Assign button behavior must remain unchanged.

Review against:
- `web/apps/web-antd/src/views/sicherplan/customers/customer-new-plan-assignments-step.vue`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-assignments.smoke.test.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `backend/app/modules/planning/staffing_service.py`
- `backend/app/modules/planning/schemas.py`
- `backend/tests/modules/planning/test_staffing_engine.py`
- German default / English secondary localization rules

Review focus:
1. Calendar semantics
   - Weekend/no-shift days are grey/neutral.
   - Outside-project-range days are disabled.
   - Real uncovered generated shifts remain red/blocked.
   - Warning and covered states remain correct.
   - No-shift days do not show misleading 0/1 or blocked bars.

2. Candidate card UI
   - Cards are visibly shorter/compact.
   - Default card does not show raw suitability score.
   - No negative score appears in the UI by default.
   - Avatar image renders if provided.
   - Initials fallback works and no broken image icon appears.
   - Name and personnel number remain visible.
   - Assign button remains usable.

3. Data correctness
   - Candidate ranking/sorting is unchanged or improved intentionally.
   - Suitability score is still available internally if needed.
   - No private HR data is exposed.
   - Avatar/profile image is only used if backed by real allowed data.

4. Regression risk
   - Assignment apply still works.
   - Drag/drop still works.
   - Candidate filtering still works.
   - Demand groups step still works.
   - admin/planning-staffing semantics are not broken.

5. Tests
   - Tests cover no-shift grey days.
   - Tests cover real blocked days.
   - Tests cover compact candidate card and score hiding.
   - Tests cover avatar/fallback.
   - Build/tests pass.

Required output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

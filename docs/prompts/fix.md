Task: Fix hidden shift-plan context in the Shift Planning UI for the “Series and exceptions” workflow.

Repository:
jalalsadeghi/SicherPlan

Problem statement:
In the current Shift Planning page, the Series form does not show which Shift Plan the series will be created under.
The component relies on an implicit selectedShiftPlanId from the Plans tab. This is hidden context and causes operator confusion.
The current UI renders a Shift template selector as the first visible field, but there is no visible Shift plan field or summary.
The submitSeries() flow injects shift_plan_id from selectedShiftPlanId, so the backend path works, but the user cannot verify the selected plan in the form.

Observed current behavior:
- A user must first select a Shift Plan in the Plans tab.
- Then the Series tab becomes usable.
- The Series form does not visibly show the selected Shift Plan.
- Save may be enabled, but the selected plan is not visible.
- This is a UX/state-visibility issue, not primarily a backend issue.

Your job:
Implement a robust frontend fix so the selected Shift Plan is clearly visible and selectable/confirmable in the Series workflow.

Primary goals:
1. In the Series tab, add a clearly visible “Shift plan” field or context card above the Series form.
2. The user must be able to see which Shift Plan is currently active before saving a series.
3. For new series creation, the UI must prevent accidental submission when no Shift Plan is selected.
4. The behavior must remain compatible with the existing API:
   - listShiftSeries(tenantId, shiftPlanId, ...)
   - createShiftSeries(tenantId, shiftPlanId, ..., payload)
5. Do not break existing create/edit/generate flows.

Recommended implementation approach:
- In PlanningShiftsAdminView.vue:
  - Add a visible “Shift plan” selector or a read-only context field in the Series tab.
  - Reuse shiftPlans / selectedShiftPlanId state already present.
  - For best UX, prefer a real select in the Series tab bound to selectedShiftPlanId.
  - When the selected shift plan changes from this selector:
    - refresh plan details
    - reload the series list for the new plan
    - clear selectedSeriesId and selectedExceptionId if they no longer belong to the selected plan
    - reset exception draft when needed
- Keep submitSeries() using the selectedShiftPlanId path parameter unless you find a stronger refactor that stays API-compatible.
- Show an inline help message if no shift plan is selected, instead of relying on hidden state.
- Disable Save and Generate in the Series tab when no shift plan is selected.
- Also review the Shifts tab for the same hidden dependency pattern and fix it if the same UX issue exists there, but do not expand scope unnecessarily if that creates risk.

Files to inspect first:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningShifts.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts
- web/apps/web-antd/src/sicherplan-legacy/i18n/planningShifts.messages.ts
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningShifts.smoke.test.ts

Acceptance criteria:
1. In the Series tab, the current Shift Plan is visible to the user.
2. A tenant admin can intentionally choose/confirm the Shift Plan from inside the Series workflow.
3. The Series form cannot be submitted without a valid selected Shift Plan.
4. Existing create/edit/generate behavior still works.
5. Smoke/integration tests are updated to cover the new visible shift-plan context.
6. The patch is minimal, readable, and consistent with the existing page architecture.

Testing requirements:
- Add or update tests to verify:
  - the Series tab visibly shows Shift Plan context
  - changing the Shift Plan updates the series list context correctly
  - Save is disabled or blocked when no Shift Plan is selected
  - no regression in current series creation flow
- Run the relevant frontend tests and report the exact results.

Important:
Before coding, validate my diagnosis against the current code and explain whether the issue is:
- purely hidden frontend state
- a state synchronization issue
- or something broader

After coding, do a self-review and explicitly check:
- whether the fix introduces stale selection bugs
- whether series editing across different plans can become inconsistent
- whether any i18n keys or tests are missing

Output format:
1. Brief diagnosis
2. Files changed
3. Patch summary
4. Test results
5. Self-review / risk check
/review Please review the customer order wizard `Demand groups` step for correctness, workflow fit, performance, and regression risk.

Business context:
The customer order wizard currently has 8 steps. `Demand groups` is step 7 and `Assignments` is step 8. The `Demand groups` step should define staffing demand across generated shifts for the selected shift plan / series. It should show aggregate applied demand-group summaries and allow controlled creation/editing before assignments start.

Review against:
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.steps.ts`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue`
- `web/apps/web-antd/src/views/sicherplan/customers/customer-order-workspace-panel.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- `backend/tests/modules/planning/test_staffing_engine.py`
- existing 8-step wizard behavior
- `admin/planning-staffing` behavior
- German default / English secondary localization rules

Review focus:
1. Step sequence and completion
   - `Demand groups` is before `Assignments`.
   - Completion is based on persisted applied demand groups, not only pending templates.
   - `Assignments` is not allowed/ready when no demand groups exist.
   - Returning to the step does not lose applied state.

2. Applied summary correctness
   - Persisted per-shift demand groups are loaded and aggregated correctly.
   - Complete/Partial/Mixed statuses are accurate.
   - `23 / 23 shifts` or similar counts are accurate.
   - Mixed or variant data is not silently collapsed.
   - Empty-state messages are not misleading.

3. Pending template behavior
   - Pending templates are separate from applied groups.
   - New templates do not create real per-shift rows before Apply.
   - Draft restore is context-safe.
   - Duplicate templates are prevented or clearly handled.

4. Apply behavior
   - Apply is blocked or disabled when no pending templates exist.
   - Apply calls `bulkApplyDemandGroups` once when templates exist.
   - Success reloads persisted summaries.
   - Repeated apply does not create duplicates.

5. Edit behavior
   - Aggregate `Edit` uses `bulkUpdateDemandGroups` or a safe equivalent.
   - `Edit shifts` uses individual `updateDemandGroup`.
   - Edits reload summaries.
   - Edits are blocked/readonly after assignments or later downstream state exists.

6. Performance
   - The page avoids one demand-group request per generated shift.
   - The page uses efficient filters or a backend aggregate endpoint.
   - Reference data is not repeatedly fetched unnecessarily.
   - No new N+1 backend pattern was introduced.

7. UX and localization
   - Applied cards are compact and clear.
   - Action buttons are aligned and usable.
   - Labels/messages are localized in German and English.
   - No hardcoded user-facing text was introduced.
   - SicherPlan/Vben visual consistency is preserved.

8. Regression risk
   - `admin/planning-staffing` still works.
   - `Assignments` step still works.
   - Demand group bulk apply/update APIs still work.
   - Existing wizard tests pass.
   - Backend tests pass if backend changed.

Required output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

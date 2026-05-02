/review Please review the implementation that adds the `New demand group` modal/dialog to the customer order wizard Demand groups step.

Business requirement:
In `/admin/customers?customer_id=...&tab=orders&...&step=demand-groups`, the final Demand groups step must let the user click `New demand group`, open a modal/dialog, define one or more demand-group templates, and then apply those templates to all generated shifts for the selected shift plan / series using the bulk apply API.

Review against:
- AGENTS.md
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- existing seven-step wizard behavior
- current Demand groups bulk-apply behavior
- German default / English secondary localization rules

Review focus:
1. UI correctness
   - `New demand group` button is visible in the Demand groups step when there is a valid shift_plan_id and the step is not read-only.
   - Clicking the button opens a modal/dialog.
   - The modal includes function type, optional qualification, min quantity, target quantity, sort order, mandatory flag, and remark.
   - The modal follows existing Vben/Ant/SicherPlan styling.
2. Data correctness
   - The wizard creates local demand-group templates first.
   - It does not create real per-shift demand groups before the user clicks `Apply demand groups`.
   - It uses `bulkApplyDemandGroups()` for final apply.
   - Payload includes shift_plan_id, shift_series_id when available, and demand_groups templates.
3. Validation
   - function type is required.
   - target quantity cannot be lower than minimum quantity.
   - duplicate local templates are prevented or clearly handled.
   - applying with no generated target shifts is blocked or clearly explained.
4. Generated shifts handling
   - If generated shifts exist, the step loads and displays target shift count correctly.
   - If no generated shifts exist, the user can still prepare templates but cannot successfully apply them until shifts exist.
   - Any previous "No generated shifts available" behavior is still accurate and no longer hides the template creation UI.
5. Draft behavior
   - Unsaved templates are restored only when actual demand-group draft data exists.
   - Drafts are not cleared before successful apply.
6. Localization
   - New labels/messages exist in German and English.
   - No hardcoded user-facing strings are introduced.
7. Regression risk
   - Existing six previous wizard steps still work.
   - `series-exceptions -> demand-groups` transition still works.
   - Staffing Coverage page behavior is not broken.
   - Build/tests pass.

Required review output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

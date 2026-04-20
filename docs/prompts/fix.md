You are working in the SicherPlan repository.

Current bug:
In Customer New Plan wizard, step 7 "Shift plan", an existing shift plan row is displayed, for example:

"Objektschutz RheinForum Köln – Nordtor Juli 2026 / Shift plan"

When the user clicks this row to select it before pressing Next, the page appears to refresh/reload. After it returns, the row is not selected and the fields are empty or not reliably populated. The UI also shows "Unsaved draft restored".

This is the current route pattern:

/admin/customers/new-plan?customer_id=84bad50d-209c-491e-b86b-13c7788c7620&order_id=...&step=shift-plan&planning_entity_id=...&planning_entity_type=site&planning_mode_code=site&planning_record_id=...

Important:
This is not about clicking Next anymore. The bug happens immediately when clicking an existing Shift Plan row.

My diagnosis:
The current implementation treats row selection as official wizard context mutation. In new-plan-step-content.vue, selectShiftPlanRow(planId) currently:
- calls getShiftPlan()
- calls syncShiftPlanDraft(plan)
- clears the shift-plan draft
- emits saved-context with { shift_plan_id: plan.id }
- marks step-completion true

That emit changes parent wizardState.shift_plan_id. In new-plan.vue, the watcher on wizardState values calls syncWizardRouteState(). The routeSyncSuspended guard is only active during goToNextStep(), not during row selection. Therefore row selection triggers router.replace while current_step is still shift-plan. That causes the step to reload/re-hydrate, which is visible as a page refresh.

There is also a second likely bug:
loadShiftPlanState() restores persistedShiftPlanDraft even when wizardState.shift_plan_id exists if persistedShiftPlanDraft.selected_shift_plan_id is empty. This can apply a stale/generic draft over a saved selected Shift Plan and show the misleading “Unsaved draft restored” message.

Validate or falsify this diagnosis. Do not just say “already fixed”.

Inspect at least:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts
- existing tests under web/apps/web-antd/src/views/sicherplan/customers/

Required validation:
1. Confirm whether clicking an existing Shift Plan row calls selectShiftPlanRow().
2. Confirm whether selectShiftPlanRow() emits saved-context immediately.
3. Confirm whether that emit changes wizardState.shift_plan_id.
4. Confirm whether the parent watcher calls syncWizardRouteState() because of that state change.
5. Confirm whether routeSyncSuspended is false during row click.
6. Confirm whether router.replace occurs with step=shift-plan and shift_plan_id.
7. Confirm whether the child step reloads because props.wizardState.shift_plan_id changes.
8. Confirm whether loadShiftPlanState() can restore a persisted shift-plan draft with empty selected_shift_plan_id over a saved plan.
9. Confirm why “Unsaved draft restored” appears even though the user clicked a saved Shift Plan row.
10. Confirm whether backend save/list/get APIs are working and whether this is frontend lifecycle/draft behavior.

Expected diagnosis output:
- Root cause confirmed or corrected.
- Exact functions causing the refresh.
- Exact functions causing selection loss or stale draft restore.
- Minimal patch plan.
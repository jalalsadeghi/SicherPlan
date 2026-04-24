You are working in the latest public SicherPlan repository.

Route / area:
customers/order-workspace?customer_id=<id>&order_id=<id>&order_mode=edit&step=planning-record-overview

Relevant files to inspect first:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts or closest existing test file

Current behavior:
In the Planning record step, the user can select one row/card in the "Existing planning records" section.
After a planning record is already selected, clicking the same selected row again currently causes unnecessary behavior:
- it may re-run the selection handler,
- it may refetch the same planning record detail,
- it may re-emit saved context,
- it may show a toast again,
- it may retrigger route/wizard sync or loading state.

Required behavior:
If the user clicks the currently selected existing planning record again, do nothing.

Definition of "do nothing":
- Do not call getPlanningRecord again for the same selected record.
- Do not call listPlanningRecords again because of this repeated click.
- Do not patch planningRecordDraft again.
- Do not emit saved-context again.
- Do not call router.replace / router.push because of this repeated click.
- Do not show "Planning entry selected" or any other toast again.
- Do not mark the step dirty.
- Do not change selectedExistingPlanningRecordId, editingExistingPlanningRecordId, committedPlanningRecordId, selectedPlanningRecord, planningRecordRows, or wizard state.
- Do not visually reload, blink, clear, or refocus the editor.

Important nuance:
Only treat the click as a no-op when the clicked row/card is already the active selected planning record and the editor is already hydrated for that same record.
If there is an inconsistent state, for example selectedExistingPlanningRecordId is set but selectedPlanningRecord/detail/editor is missing, recover the state safely, but do not produce duplicate visible feedback. In the normal healthy selected state, repeated click must be a strict no-op.

What to investigate first:
1) Find the exact click handler for rows/cards in "Existing planning records".
2) Identify which function loads/hydrates an existing planning record into the editor.
3) Identify whether this handler also:
   - emits saved-context
   - updates route query
   - loads planning record detail
   - saves/restores draft
   - updates completion/dirty state
   - shows toast feedback
4) Confirm whether selectedExistingPlanningRecordId and selectedPlanningRecord/editor state are sufficient to detect an already-selected record.

Implementation guidance:
- Add a small guard at the very start of the existing planning record selection handler.
- The guard should compare the clicked row id with the current active selected planning record id.
- Also verify that the editor/current detail belongs to the same record before treating it as a strict no-op.
- Keep the guard easy to read, for example:
  - isPlanningRecordAlreadySelected(row)
  - shouldIgnorePlanningRecordReselect(row)
  - hasHydratedSelectedPlanningRecord(row.id)
- If the current selected record is the same and hydrated, return immediately before any API call, emit, router sync, toast, or loading state change.
- Preserve all current behavior when selecting a different existing planning record.
- Preserve all current behavior when selecting a record for the first time.
- Preserve create-new planning record behavior.
- Preserve the previous race-condition fix behavior if it already exists.

Expected UX:
- First click on an existing planning record selects it and hydrates the editor.
- Second click on the same selected card does absolutely nothing visible.
- Clicking a different existing planning record still switches selection and hydrates the editor.
- The selected card remains highlighted.
- The editor values remain unchanged.
- No duplicate success toast appears.

Please validate my suggestion critically:
- If the current code has a better place to implement the idempotency guard, use it.
- If a repeated click currently causes problems due to route sync or parent wizard sync, fix the root trigger and still add the no-op guard.
- Do not implement this by disabling the card visually unless that is already the project’s standard pattern; a selected card may remain clickable-looking, but the handler must be idempotent.

Regression tests to add/update:
1) First click selects and hydrates:
   - mock one existing planning record row,
   - click it,
   - assert getPlanningRecord was called once,
   - assert editor fields are populated,
   - assert selected state is visible.

2) Second click on the same selected row is a no-op:
   - click the same row again,
   - assert getPlanningRecord call count is still one,
   - assert router.replace/router.push was not called by the repeated click,
   - assert saved-context was not emitted again,
   - assert success toast was not shown again,
   - assert editor fields remain unchanged.

3) Clicking a different row still works:
   - mock two planning records,
   - select the first,
   - then select the second,
   - assert the second detail is fetched and editor updates.

4) Inconsistent state recovery:
   - simulate selectedExistingPlanningRecordId matching row id but selectedPlanningRecord/editor missing,
   - click the row,
   - assert the code recovers safely without duplicate visual feedback or route churn.

Deliverables:
1) Apply code changes.
2) Add/update tests.
3) Summarize:
   - changed files
   - exact handler/function changed
   - how repeated clicks are detected
   - which side effects are now skipped
   - which tests were added or updated

Acceptance criteria:
- Re-clicking the currently selected existing planning record performs no visible or state-changing action.
- No duplicate API request is made.
- No duplicate toast is shown.
- No route/query update is triggered by repeated click.
- No editor clear/reload/blink happens.
- Selecting a different existing planning record still works normally.
- Create-new planning record flow still works normally.
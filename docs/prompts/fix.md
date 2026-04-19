You are working in the SicherPlan repository.

This task follows the diagnosis from the previous prompt.

Source document:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

User-visible bug:
On Customer New Plan Wizard Step 2 "Order details", unsaved form data still clears after focus/app switch/auth refresh/reference reload.

Use the root cause discovered in the previous prompt.
Do not assume the previous implementation is correct just because tests passed.

Goal:
Fix the remaining bug so Order Details and other unsaved wizard drafts cannot be cleared by focus return, auth refresh, reference reload, component remount, or route hydration.

Scope:
- Frontend only
- No backend changes
- No canonical Planning/Orders/Shift/Staffing page redesign
- No wizard step-order changes
- No unrelated refactor

Required fix areas:

A. Prevent empty/default draft overwrite
If the diagnosis shows that reset/default initialization overwrites a non-empty draft:
- Add a persistence suppression guard during reset/hydration.
- Example patterns:
  - isHydratingDraft = true
  - isInitializingStep = true
  - withDraftPersistencePaused(() => ...)
- Watchers must not save empty/default values while a step is being reset or hydrated.
- Never write an empty default draft over an existing non-empty draft unless the user intentionally clears/cancels the wizard.

B. Make draft keys stable
If the diagnosis shows a storage key mismatch:
- Ensure the same key is used for saving and restoring a step.
- The Order Details draft key must work before order_id exists.
- Key must include:
  - tenantId
  - customerId
  - planning_entity_type
  - planning_entity_id
  - step id
- If planning context is temporarily unavailable during early hydration, defer draft load/save until the context is stable.
- Do not save drafts under incomplete keys such as empty planning_entity_id if the route already contains planning context.

C. Do not reset dirty active forms during reference reload
If the diagnosis shows over-aggressive reset:
- Modify loadOrderState() so:
  - if order_id is missing and orderDraft is dirty or has user input, do not reset it.
  - if order_id is missing and a persisted draft exists, hydrate it.
  - if order_id is missing and no draft exists, initialize defaults only once.
- Apply same pattern to:
  - equipmentLineDraft
  - requirementLineDraft
  - planningRecordDraft
  - shiftPlanDraft
  - seriesDraft
where applicable.

D. Make same-customer auth refresh non-destructive
If auth/accessToken changes:
- Do not reset wizard state.
- Do not remount child content unnecessarily.
- Re-fetch reference data if needed, but do not clear active drafts.
- Re-fetch customer context with preserveContent behavior.
- Confirm that new-plan.vue does not set customer to null/loading for the same customer while an active draft exists.

E. Hydrate before rendering if remount happens
If the child component remounts:
- Hydrate persisted draft before visible fields are reset to defaults.
- Avoid a visible flash of empty fields if possible.
- Do not mark hydrated draft as dirty just because it was restored.
- Do not immediately overwrite hydrated draft with defaults via watchers.

F. Correct cleanup rules
Only clear a step draft when:
- that step is successfully saved to backend
- user cancels the wizard
- customer_id changes
- tenant changes
- user intentionally resets the step

Do not clear on:
- focus return
- auth refresh
- reference data reload
- route.replace for same context
- same-customer customer GET

G. Tests
The failing regression test from the previous prompt must pass after the fix.

Also add or update tests for:
1. Order Details typed values survive accessToken change.
2. Order Details typed values survive reference-data reload.
3. Order Details typed values survive component remount when route has planning context.
4. Existing non-empty sessionStorage draft is not overwritten by empty default initialization.
5. Dirty Order Details does not reset when loadOrderState() runs with no order_id.
6. Saved Order Details clears the draft after successful create/update.
7. Cancel clears drafts.
8. Customer switch prevents draft leakage.
9. Step 1 -> Step 2 route persistence still works.
10. Later step representative draft, such as Shift Plan or Series, survives remount/reference reload.

H. Manual QA checklist required in final output
Perform or describe exact manual QA steps:
- Open the user’s exact URL with step=order-details.
- Type Order number and Title.
- Switch to another app/monitor and return.
- Confirm values remain.
- Wait for auth refresh or force token refresh.
- Confirm values remain.
- Click inside another field.
- Confirm values remain.
- Refresh browser.
- Confirm values restore.
- Click Next and save Order Details.
- Confirm draft clears and order_id is added to context.
- Go Previous and Next again.
- Confirm no duplicated order is created.
- Switch customer_id.
- Confirm old draft does not appear.

Final output:
1. Confirmed root cause
2. Fix implemented
3. Files changed
4. Tests added/updated
5. Test results
6. Manual QA result
7. Any remaining limitation

Important:
Do not finish with “already implemented” unless the exact user scenario is reproduced and passes.
The user has already confirmed the bug still exists in the browser.
Avoid unrelated refactors.
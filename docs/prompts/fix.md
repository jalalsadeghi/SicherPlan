You are working in the SicherPlan repository.

This task follows the Planning Record UX fix in:
- /admin/customers/order-workspace
- step=planning-record-overview

Context:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Run a focused QA/hardening pass for the Planning Record step.

Do not add unrelated features.
Do not change unrelated steps.
Do not change backend APIs unless a direct bug requires it.

Validate the six user requirements:

1. Edit button removed
- Existing planning record card no longer has an Edit button.
- There is no dead/hidden edit action that affects UX.

2. Card click selects and hydrates
- Clicking the card selects the planning record.
- The editor below shows all relevant record data.
- Bottom Next can proceed to Planning Documents if the editor is valid and unchanged.

3. Changing Planning entry clears existing selection
- Select an existing planning record.
- Change Planning entry in the editor.
- Existing record selection clears.
- Old record data clears.
- New planning entry remains as context for new record entry.
- No stale planning_record_id remains committed.

4. Invalid fields block Next with red inline errors
- Missing Planning entry -> red field + inline error.
- Missing name -> red field + inline error.
- Missing start date -> red field + inline error.
- Missing end date -> red field + inline error.
- end date before start date -> red field + inline error.
- No generic-only toast as the only validation feedback.

5. Planning entry displays name
- Select options show human-readable names.
- Selected value displays name.
- UUID is not used as primary display label unless no better data exists.
- If options reload, selected label remains stable.

6. User-flow QA
- User can select existing record and continue.
- User can edit/update selected record.
- User can change planning entry and create/update a new record context.
- User can recover from validation errors.
- Existing list remains stable.

Technical validation:

A. State consistency
- selectedExistingPlanningRecordId is cleared when planning entry changes.
- selectedPlanningRecord object is cleared or replaced correctly.
- planning_record_id is not incorrectly reused after changing planning entry.
- dirty state reflects editor changes.

B. Route/state behavior
- selecting an existing record commits planning_record_id only when appropriate.
- changing planning entry removes stale planning_record_id from state/route if that record no longer applies.
- no route loop.
- no refresh loop.

C. Option handling
- options load for correct family.
- selected option is preserved while loading.
- no false "No planning entries found" message when a selected record has valid detail.

D. Non-regression
- Order Details still works.
- Order scope/documents step still works.
- Planning Documents opens after Next.
- Shift Plan and Series steps remain accessible after valid Planning Record.
- canonical /admin/planning-orders remains unchanged.

Tests:
Run and update:
- relevant order-workspace tests
- relevant new-plan/order workspace shared tests
- planning record frontend tests
- backend tests only if touched

Add missing tests for:
- no Edit button
- card selection hydrates editor
- next with selected existing record
- planning entry label display
- planning entry change clears selection
- inline field validation
- list stability during hydration

Manual QA:
- Repeat exactly the user scenario from screenshot.
- Confirm all six requirements.
- Try invalid inputs.
- Continue to Planning Documents.
- Return and edit again.

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Files changed
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Before finalizing, explicitly confirm each user requirement as PASS/FAIL.
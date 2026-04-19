You are working in the SicherPlan repository.

This task follows the unsaved-draft persistence fix for:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Run a focused QA and hardening pass for the Customer New Plan Wizard after implementing unsaved draft persistence.

Do not add unrelated features.
Do not change backend APIs.
Only fix issues directly related to:
- unsaved draft persistence
- auth refresh stability
- focus/app-switch stability
- component remount stability
- route hydration stability

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.steps.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.types.ts
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Validation checklist:

1. Order Details data stability
- Fill Order number, Title, Service dates, Security concept, Notes
- Trigger focus change / app switch / window focus
- Trigger or simulate auth refresh
- Verify data is not cleared

2. Reference reload stability
- Ensure repeated calls to service-category-options, requirement-types, patrol-routes, equipment-items, function-types, qualification-types do not reset the visible draft
- Confirm loadOrderState() does not blindly reset local form values while the user is editing

3. Remount stability
- Simulate component unmount/remount if possible
- Verify sessionStorage draft rehydrates the current step

4. Route hydration compatibility
- Refresh page on:
  - order-details
  - equipment-lines after order_id exists
  - planning-record-overview after order_id exists
  - shift-plan after planning_record_id exists
- Verify correct step and context restore

5. Successful save cleanup
- After saving Order Details, confirm unsaved order draft is cleared
- After saving later steps, confirm their drafts are cleared
- Confirm saved server state remains loadable after refresh

6. Cancel behavior
- Cancel wizard
- Confirm drafts for the current wizard context are cleared
- Reopen same customer New Plan and confirm stale unsaved data does not appear unless intentionally preserved by design

7. Customer/tenant isolation
- Change customer_id
- Confirm previous customer’s draft does not appear
- Change tenant context if feasible
- Confirm previous tenant’s draft does not appear

8. File input behavior
- Confirm raw File objects are not persisted
- Confirm user-facing behavior is clear if file selection must be repeated after refresh

9. Non-regression
- Step 1 Planning Use Existing still works
- Step 1 Create New planning entry still works
- Create new address and Pick on map still work
- Equipment / Requirement / Template dialogs still work
- Generate Series handoff still works
- canonical Operations & Planning pages are untouched

Tests:
Add or update tests for any missing coverage:
- dirty draft survives remount
- dirty draft survives auth refresh
- reference reload does not reset draft
- saved step clears draft
- cancel clears drafts
- customer switch prevents draft leakage
- malformed sessionStorage value is ignored safely
- route query context and session draft context work together

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA checklist result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches the draft-persistence proposal or required adjustment.

Avoid unrelated refactors.
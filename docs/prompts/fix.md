After implementing step-local loading indicators, perform or document this manual QA.

Manual QA target:
http://localhost:5173/admin/customers/new-plan

Scenario:
Use a customer/order/planning context that already has saved data in multiple steps.

For each step:
1. Open the step.
2. Observe while previously saved data loads.
3. Confirm a small local loading indicator appears in the relevant data area.
4. Confirm the whole page is not dimmed.
5. Confirm the whole step does not disappear.
6. Confirm already typed draft data remains visible if present.
7. Confirm loading indicator disappears when data loads.

Steps to verify:
1. Order details
2. Equipment lines
3. Requirement lines
4. Order documents
5. Planning record
6. Planning documents
7. Shift plan
8. Series & exceptions

Specific checks:
- Equipment/Requirement lines:
  loading appears in list area, not over whole page.
- Documents:
  loading appears in document list/drop zone.
- Planning record:
  loading appears around existing planning records/detail area.
- Shift plan:
  loading appears around existing shift plan list/detail area.
- Series:
  loading appears around series rows/exceptions area.

Also test:
- Click Next/Previous quickly between steps.
- Refresh browser on a step URL.
- Switch focus away and back during loading.
- Confirm no route rollback and no draft loss.

If browser QA cannot be run:
- explicitly say manual QA was not run
- provide deterministic tests covering all steps.

Final report must include:
- which steps were manually verified
- any step without a loading indicator and why
- any remaining risk.
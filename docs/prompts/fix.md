You are working in the SicherPlan repository.

This task follows the patch that makes document steps optional in:
- Customer New Plan Wizard
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Do a focused QA/hardening pass for the document steps:
- Order Documents
- Planning Documents, if it was changed too

Do not add unrelated features.
Do not change backend APIs.
Do not change other wizard steps unless fixing a direct regression from this patch.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Validation checklist:

1. Order Documents optional behavior
- Empty Order Documents step allows Next.
- It does not call createOrderAttachment or linkOrderAttachment when no file/link exists.
- It marks the step complete.
- It moves to Planning Record.
- No error message is shown.

2. Order Documents upload/link behavior
- File upload still works.
- Existing document link still works.
- orderAttachments refresh after success.
- Draft is cleared after success.
- Existing attachments remain visible.

3. Partial draft behavior
- If user typed title/label but did not choose file or document_id, behavior is clear.
- Either it blocks with a localized message or clear button lets user skip.
- No silent loss of partial user input unless user intentionally clears it.

4. Planning Documents optional behavior
If the same logic was applied:
- Empty Planning Documents step allows Next.
- It moves to Shift Plan.
- File/link still works.
- planningRecordAttachments refresh after success.
- Draft is cleared after success.

5. Draft persistence
- Optional skip clears irrelevant document-step errors.
- Document draft persistence does not re-block the step after user clears it.
- File content is not persisted unsafely.
- Metadata-only restoration still behaves as expected.

6. Non-regression
- Equipment Lines multi-save behavior still works.
- Requirement Lines multi-save behavior still works.
- Order Details existing/create order behavior still works.
- Planning Record creation still works.
- Shift Plan and Series steps are unaffected.

Tests:
Run and update:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any new focused test for optional document behavior

Add missing tests if needed:
- empty order-documents proceeds
- empty planning-documents proceeds
- partial order document draft blocks or clears
- upload/link still works
- no create/link API call when skipping empty step

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches the optional-document proposal.
Avoid unrelated refactors.
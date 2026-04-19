You are working in the SicherPlan repository.

This task follows the patch that separates Save/Update from Next for:
- Equipment Lines
- Requirement Lines

Source document:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Do a focused QA and hardening pass to ensure multi-line behavior works correctly in the Customer New Plan Wizard.

Do not add unrelated features.
Do not change backend APIs.
Do not change other wizard steps unless you find a direct regression caused by this patch.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Validation checklist:

1. Equipment Lines save behavior
- Save equipment line creates a line.
- User remains on Equipment Lines after save.
- Saved line list refreshes.
- Form resets after save.
- User can add another line.
- User can click existing line and update it.
- Update does not create duplicates.
- Clear line resets draft and update mode.

2. Requirement Lines save behavior
- Save requirement line creates a line.
- User remains on Requirement Lines after save.
- Saved line list refreshes.
- Form resets after save.
- User can add another line.
- User can click existing line and update it.
- Update does not create duplicates.
- Clear line resets draft and update mode.

3. Next behavior
- Equipment Next does not create/update a line.
- Equipment Next blocks when no saved line exists.
- Equipment Next blocks when draft has unsaved values.
- Equipment Next proceeds only when saved lines exist and draft is clean.
- Requirement Next does not create/update a line.
- Requirement Next blocks when no saved line exists.
- Requirement Next blocks when draft has unsaved values.
- Requirement Next proceeds only when saved lines exist and draft is clean.

4. Draft persistence
- Unsaved equipment draft survives focus/auth refresh.
- Unsaved requirement draft survives focus/auth refresh.
- Saved equipment line clears the unsaved equipment draft.
- Saved requirement line clears the unsaved requirement draft.
- Clear line clears the relevant draft.
- Customer switch does not leak draft data.

5. Existing flow regression check
- Planning step still works.
- Order Details still saves on Next.
- Order Documents still works.
- Planning Record still works.
- Shift Plan and Series steps still work.
- Generate Series handoff is unaffected.

6. i18n
- All new labels/messages are i18n-driven.
- German and English fallback are present.

7. UX
- Inline Save/Update/Clear buttons are visually aligned.
- Edit mode is understandable.
- Error messages for blocked Next are clear.
- Responsive layout remains usable.

Tests:
Run existing wizard tests and add missing ones if needed:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any new focused test file you create

Required final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches the Save/Update-vs-Next proposal.
Avoid unrelated refactors.
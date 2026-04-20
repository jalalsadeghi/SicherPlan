You are working in the SicherPlan repository.

This task follows the Planning Record context selector fix.

Source:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Current product decision:
- Order Details is first.
- Planning context is inside Planning Record.
- Planning is not a separate step.

Goal:
Run a focused QA and hardening pass for the Planning Record context selector.

Do not add unrelated features.
Do not reintroduce Planning as a separate step.
Do not change backend APIs.

Validate:

1. Visual layout
- Planning context panel is clean.
- Use existing / Create new options are aligned.
- Radio controls use standard wizard/admin styling.
- No awkward stretched field-stack radio layout remains.
- Mobile/narrow layout stacks cleanly.

2. Existing planning entry selection
- Clicking a row selects it locally.
- Row highlight updates immediately.
- Planning Record details appear.
- No page/step refresh occurs.
- No route.replace occurs on row click.
- No saved-context emit occurs on row click.
- No repeated backend GET burst occurs.

3. Backend request behavior
- Initial Planning Record load may fetch required order and planning option data.
- Selecting a Site/Event/Patrol row should not refetch all order state and all planning families.
- Selecting Trade Fair may fetch zones once.
- No infinite loop.
- No repeated customer/order/attachments/equipment/requirement reload after row selection.

4. Draft restore
- After selecting a planning entry, browser refresh restores the selected row.
- Restore does not emit saved-context repeatedly.
- Restore does not trigger refresh loop.
- Draft does not leak across customer/order.

5. Submit behavior
- Missing planning context blocks Next.
- Valid context + valid details saves PlanningRecord.
- saved-context is emitted on successful save with planning context and planning_record_id.
- Wizard moves to Planning Documents.

6. Create new planning entry
- Create new planning entry still opens modal.
- Create new address still works.
- Pick on map still works.
- Created entry is selected locally.
- It does not cause a full refresh loop.
- Submit commits context and planning_record_id.

7. Non-regression
- Order Details first-step behavior unchanged.
- Equipment Lines unchanged.
- Requirement Lines unchanged.
- Order Documents optional behavior unchanged.
- Planning Documents remains next after Planning Record.

Tests:
Run and update:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any focused Planning Record context tests

Add missing tests for:
- radio layout classes
- no saved-context on planning row click
- no route replace on planning row click
- no full reload after planning row click
- draft restore
- successful submit commits context

Manual QA checklist:
- Open Planning Record step.
- Select each planning family.
- Select an existing entry.
- Watch backend logs.
- Confirm no unnecessary request burst.
- Refresh and confirm restore.
- Create PlanningRecord and continue.

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Before finalizing, explicitly confirm:
- styling is fixed
- planning row selection is local
- context is committed only on Next/save
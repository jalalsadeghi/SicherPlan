You are working in the SicherPlan repository.

This task follows the patch that moved Planning Context selection into the Planning Record step.

Source:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Current product decision:
- Order Details is first.
- Planning is not a separate first step.
- Planning context is selected/created inside Planning Record.

Goal:
Run a focused QA/hardening pass for the Planning Record step.

Do not reintroduce a separate Planning step.
Do not change backend APIs unless fixing a direct regression.
Do not modify unrelated steps.

Validate:

1. Step order
- Order Details is step 1.
- Planning Record is step 5.
- No separate Planning step appears.
- Earlier steps do not require planning context.

2. Planning Record entry
- User can reach Planning Record after Order Documents with only customer_id + order_id.
- The UI shows Planning Context selection instead of a dead-end warning.
- Missing context blocks only the Planning Record submit, not reaching the step.

3. Planning context selection
- Existing Site selection works.
- Existing Event Venue selection works.
- Existing Trade Fair selection works.
- Existing Patrol Route selection works.
- planning_mode_code is derived correctly.
- route/state store planning_entity_id/type/mode after selection.

4. Planning context create-new
- Create Site works.
- Create Event Venue works.
- Create Trade Fair works.
- Create Patrol Route works.
- Create new address still works.
- Pick on map still works where applicable.
- Created entry is selected automatically.

5. Planning Record details
- Details form appears only after valid context.
- Defaults from selected order are reasonable:
  - name may default from order title
  - planning_from / planning_to may default from order service_from/service_to
- User can edit these fields.
- mode-specific detail fields map correctly:
  - site_detail
  - event_detail
  - trade_fair_detail
  - patrol_detail

6. Submit behavior
- Next with no planning context blocks with localized error.
- Next with context but invalid fields blocks.
- Next with valid context and fields creates/updates Planning Record.
- saved planning_record_id is stored in state/route.
- wizard moves to Planning Documents after success.

7. Refresh/draft behavior
- Refresh on Planning Record preserves order_id.
- Refresh after selecting planning context preserves planning context.
- Draft fields remain stable after auth refresh/reference reload.
- Changing customer/order clears incompatible planning-record draft.

8. Non-regression
- Order Details existing/create flow still works.
- Equipment Lines Save/Update-vs-Next still works.
- Requirement Lines Save/Update-vs-Next still works.
- Order Documents optional behavior still works.
- Planning Documents still follows Planning Record.
- Canonical /admin/planning remains unchanged.

Tests:
Run relevant tests:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any new Planning Record tests

Add missing tests if needed:
- context selector renders
- context missing blocks submit
- each planning family payload
- create-new context path
- refresh restores context
- earlier steps do not require context

Manual QA:
- Complete path up to Planning Record.
- Select existing Site and create Planning Record.
- Repeat with another family if available.
- Create a new Site inside this step.
- Refresh and verify restore.
- Continue to Planning Documents.

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implementation matches:
- Planning context inside Planning Record
- no separate Planning step
- Planning Record can now be completed
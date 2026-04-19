You are working in the SicherPlan repository.

This task follows the patch for stable existing-order selection and explicit edit behavior in the Customer New Plan Wizard.

Source:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Run a focused QA and hardening pass for the Order Details first step.

Do not add unrelated features.
Do not reintroduce Planning.
Do not change backend APIs.
Only fix regressions directly related to existing-order selection/edit behavior.

Validate:

1. Initial state
- Order Details is first step.
- Use Existing Order is selected by default when customer has orders.
- Create New Order remains available.

2. Row selection
- Clicking a row selects the order.
- It does not open edit form automatically.
- It does not navigate.
- It does not advance to Equipment Lines.
- It does not jump to Planning Record.
- It does not trigger route sync/order_id commit until Next.

3. Edit action
- Edit button is not nested inside a parent button.
- Edit uses stopPropagation or equivalent.
- Edit opens edit form below list.
- Edit hydrates full order details.
- Edit does not cause step reload.

4. Update action
- Update order calls updateCustomerOrder.
- User remains on Order Details.
- Order list refreshes after update.
- Selected order remains selected.
- Edit form dirty state clears.

5. Next behavior
- Selected order + Next commits order_id and moves to Equipment Lines.
- Dirty edit form + Next blocks.
- No selected order + Next blocks.
- Create new order + Next creates and moves to Equipment Lines.

6. Refetch stability
- Auth refresh/reference reload does not reset selection.
- Auth refresh/reference reload does not close edit form unexpectedly.
- Auth refresh/reference reload does not switch Create New back to Use Existing.

7. Draft persistence
- Create-new draft remains separate.
- Edit draft remains separate.
- Customer switch clears selection/edit state.
- Stale order_id query does not cause surprise jump.

8. Non-regression
- Equipment Lines Save/Update-vs-Next still works.
- Requirement Lines Save/Update-vs-Next still works.
- Order Documents optional skip still works.
- canonical /admin/planning-orders remains unchanged.

Tests:
Run relevant tests:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any focused Order Details tests

Add missing tests for:
- row click does not emit saved-context
- row click does not call router.replace
- edit button opens form
- edit button does not trigger parent row click incorrectly
- Next is the only order_id commit path for existing order selection
- dirty edit blocks Next

Manual QA checklist:
- Select first order row
- Select second order row
- Click Edit on first order
- Update a field
- Cancel edit
- Click Next after selection
- Confirm Equipment Lines opens
- Return and verify selection remains stable
- Trigger auth refresh/reference reload and verify no reset

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether implementation matches:
- row click selects only
- Edit opens form
- Next commits and advances
You are working in the SicherPlan repository.

This task follows the fixes for Order Details first-step behavior in:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Run a focused QA/hardening pass for the first step of Customer New Plan Wizard.

Do not add new product scope.
Do not reintroduce Planning.
Do not change downstream steps except to fix direct regressions.

Validate:

1. First step
- Order Details is first.
- Previous is disabled.
- Planning is not visible.

2. Use Existing Order
- Existing orders load by customer_id.
- Clicking a row selects it.
- Selection does not auto-advance.
- Selected row is highlighted.
- Next moves to Equipment Lines.

3. Create New Order
- Clicking Create New Order stays in Create New Order mode.
- Mode does not revert after list/ref data reload.
- Empty form remains visible.
- Next creates order and moves to Equipment Lines.

4. Edit Existing Order
- Edit action appears inside each order row/card.
- Edit opens form below the list.
- Update Order updates and stays on Order Details.
- Cancel Edit closes the form.
- Dirty edit blocks Next unless updated/cancelled.

5. Reload/refetch stability
- Auth refresh/reference reload does not reset order mode.
- Focus/app-switch does not reset order mode.
- Browser refresh with selected order restores order-details.

6. Route/state
- Setting order_id does not auto-jump to Planning Record.
- No missing step query causes “furthest enterable step” jump.
- order_id persists when selected or created.

7. Non-regression
- Equipment Lines works after selected/created order.
- Equipment Save/Update-vs-Next still works.
- Requirement Save/Update-vs-Next still works.
- Order Documents optional skip still works.
- Canonical /admin/planning-orders unchanged.

Run relevant tests:
- new-plan.test.ts
- new-plan-epic3.smoke.test.ts
- new-plan-epic4.smoke.test.ts
- new-plan-wizard.test.ts
- any new focused Order Details tests

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Before finalizing, confirm whether the implementation matches:
- Create New mode stays stable
- Existing row selection does not auto-advance
- Edit is explicit and separate from selection
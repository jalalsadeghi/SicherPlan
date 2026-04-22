You are working in the SicherPlan repository.

This task follows the fix for existing Planning Record hydration in:
- /admin/customers/order-workspace
- step=planning-record-overview

Goal:
Run a focused QA/hardening pass.

Do not add unrelated features.
Do not change unrelated wizard/order-workspace steps.
Do not change backend APIs unless a direct regression requires it.

Validate:

1. Existing record selection
- Clicking an existing planning record row keeps the row visible.
- Row remains highlighted/selected.
- Editor values hydrate correctly.
- Planning Entry select is not blank.

2. Planning context mapping
Confirm mapping:
- site -> site_detail.site_id
- event -> event_detail.event_venue_id
- trade_fair -> trade_fair_detail.trade_fair_id
- patrol -> patrol_detail.patrol_route_id

3. Options behavior
- Options load for the correct planning family.
- Selected option is present or safely restored.
- Options loading does not clear selected id.
- No “No planning entries found for this customer” when the record has a valid linked entry.

4. Edit behavior
- Edit opens editor.
- Edit hydrates planning entry correctly.
- Dirty edit behavior is still correct.
- Save/update keeps record selected.

5. Next behavior
- Selected unchanged existing record can continue.
- Dirty edit still blocks if required.
- Planning Documents opens next.

6. Backend/list filtering
- Existing records list is scoped correctly.
- If planning_entity filters were implemented, verify they work.
- No unrelated records appear.

7. Non-regression
- Order Details first step works.
- Equipment/Requirement/Document steps unchanged.
- Create new Planning Record path still works.
- Canonical /admin/planning-orders unchanged.

Tests:
Run and update:
- relevant order-workspace tests
- relevant planning record tests
- backend tests if filter changed

Manual QA:
- Select existing planning record.
- Check Planning Entry select.
- Edit existing planning record.
- Save/update.
- Continue with Next.
- Refresh and repeat.

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Files changed
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real data entry

Explicitly confirm:
- Planning Entry stays selected
- existing row list does not disappear
- Next still works
You are working in the SicherPlan repository.

This task follows the customer-specific title/pill cleanup for:
- /admin/customers

Context:
- list-only mode
- customer-specific detail-only mode

Goal:
Run a focused QA and hardening pass for:
- top tab/title naming in customer-specific mode
- removal of the redundant in-page customer-name pill

Do not add unrelated features.
Do not redesign unrelated customer workspace logic.
Only verify and harden the naming/presentation behavior.

Validate:

1. List-only mode
- top tab/title is still generic "Customers"
- no customer-specific label leaks into list mode

2. Customer-specific mode
- top tab/title shows the selected customer name
- multiple open customer pages are distinguishable
- long names truncate cleanly if needed

3. Redundant pill removal
- the extra customer-name pill/box inside the page content is gone
- no blank wrapper or awkward spacing remains

4. Main header preserved
- the main large customer name heading still exists
- helper text still exists
- back-to-list still exists
- status badge still exists

5. Non-regression
- list-only/detail-only page behavior still works
- back-to-list navigation still works
- selected customer routes still work
- customer detail tabs/workspace still work

Tests:
Run and update relevant tests.
Add missing tests if needed for:
- generic title in list-only mode
- customer-name title in detail mode
- no redundant pill rendered
- main header preserved

Manual QA:
- open list-only page
- open one customer page
- open multiple customer pages
- verify titles in top tab strip
- verify no duplicate pill exists in page content
- verify back-to-list and detail workspace still work

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Files changed
5. Tests added/updated
6. Test results
7. Manual QA result
8. Ready / Not ready for real user testing

Explicitly confirm:
- top tab names are now customer-specific in detail mode
- generic Customers remains in list-only mode
- redundant in-page pill is removed
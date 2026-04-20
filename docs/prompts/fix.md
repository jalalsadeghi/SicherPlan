Add/update regression tests for the Customer search dialog on /admin/customers.

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

Tests to inspect:
- existing CustomerAdminView tests under web/apps/web-antd/src/sicherplan-legacy/views/
- any SicherPlan Customers module tests

Required tests:

Test 1 — Module control hidden on Customers only
1. Mount /admin/customers through the module wrapper if possible.
2. Assert the Module control/PageIntro area is hidden or not visible for Customers.
3. Mount or inspect another module route if feasible and assert Module control is not globally hidden.

Test 2 — Search input replaced by SearchSelect-like control
1. Mount CustomerAdminView.
2. Assert customer-list-section exists.
3. Assert the Search field has the new test id, for example:
   customer-search-select
4. Assert the old plain full-width search-only behavior is no longer the only UI.
5. Assert filters.search still updates when the user types.

Test 3 — Helper sentence removed
1. Assert the text:
   "Use the sidebar customer links to open a customer dashboard."
   is not rendered.

Test 4 — Search opens result dialog
1. Mock listCustomers to return:
   - RheinForum Köln / K-1000 / active
   - HafenKontor Köln / K-1001 / active
2. Type "Rhein" in the SearchSelect.
3. Click Search or press Enter.
4. Assert:
   - listCustomers is called with filters.search = "Rhein"
   - customer-search-results-modal is visible
   - result row for RheinForum Köln is visible
   - HafenKontor Köln is not shown if the mocked filter applies, or is shown only if listCustomers mock returns it.

Test 5 — Selecting a search result opens customer dashboard
1. Open the search result dialog.
2. Click the RheinForum Köln result row.
3. Assert:
   - dialog closes
   - selectCustomer/getCustomer is called for the chosen id
   - router navigates to /admin/customers?customer_id=<id>&tab=dashboard
   - CustomerDashboardTab or dashboard panel is active.

Test 6 — Empty search result
1. Mock listCustomers to return [].
2. Search for an unknown value.
3. Assert:
   - modal opens
   - customer-search-result-empty is visible
   - no stale previous results remain.

Test 7 — include_archived is respected
1. Toggle include archived.
2. Search.
3. Assert listCustomers receives include_archived=true.
4. Untoggle.
5. Assert include_archived=false.

Test 8 — permissions/tenant safety
1. If tenantScopeId or accessToken is missing, Search should not fetch.
2. If canRead is false, Search should not fetch.
3. A useful disabled/empty state should remain.

Test 9 — existing actions still work
1. CSV export button still calls exportCustomers.
2. New customer button still opens create flow.
3. Existing route query customer_id still selects a customer.

Commands:
- pnpm --dir web/apps/web-antd exec vitest run <relevant CustomerAdminView test file>
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

If exact test paths differ, inspect package scripts and run the closest relevant tests.

Manual QA checklist:
1. Open http://localhost:5173/admin/customers.
2. Confirm Module control is hidden.
3. Confirm Customer list panel still shows:
   - SearchSelect
   - Status filter
   - Default branch
   - Default mandate
   - Include archived
   - Search / CSV export / New customer
4. Confirm the helper sentence is gone.
5. Type "Rhein" into SearchSelect.
6. Click Search.
7. Confirm modal opens and shows RheinForum Köln.
8. Click RheinForum Köln.
9. Confirm modal closes and Customer detail shows RheinForum Köln dashboard.
10. Search an unknown value and confirm empty-state modal.
11. Test responsive layout still looks clean.

Final output must include:
- files changed
- whether a built-in SearchSelect/AutoComplete was found or a local implementation was used
- tests added/updated
- commands run
- manual QA status or deterministic equivalent
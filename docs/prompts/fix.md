We need to change the SicherPlan Customers UX so each selected customer opens in its own top tab.

Current problem:
In Web Admin, /admin/customers opens the Customers list tab with the title "Kunden".
When the user clicks a customer row, for example "RheinForum Köln", the detail view opens inside the same Kunden tab.
The desired behavior is:
- /admin/customers remains the list tab, titled "Kunden".
- Clicking a customer row opens a separate top tab for that customer.
- The new tab title must be the customer display name, for example "RheinForum Köln".
- Multiple customers can be opened at the same time as separate tabs.
- Internal customer detail tabs such as Dashboard, Überblick, Kontakte & Zugang, Commercial, Aufträge must stay inside that customer’s top tab and must not create extra top tabs.

Repository context:
- Main customer route:
  web/apps/web-antd/src/router/routes/modules/sicherplan.ts
  Route name: SicherPlanCustomers
  Path: /admin/customers
  Current meta includes fullPathKey: false, domCached, keepAlive, moduleKey: customers.
- Customer UI:
  web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
  The customer row currently calls openCustomerWorkspace(customer.id).
- Tab key logic:
  web/packages/stores/src/modules/tabbar.ts
  getTabKey() already supports query.pageKey. If pageKey exists, it is used as the tab key before fullPathKey is considered.
- Existing tests:
  web/packages/stores/src/modules/tabbar.test.ts
  There is currently a test that expects only one Customers tab when customer query params change. This test must be replaced or updated because the new desired behavior is different.

Task:
Implement customer detail tabs using the existing pageKey mechanism.

Required behavior:
1. Keep the customer list route as:
   /admin/customers
   without customer_id and without pageKey.
   This tab should stay titled "Kunden" / Customers.

2. When a customer row is clicked:
   - Navigate to /admin/customers with query:
     customer_id=<customer.id>
     tab=dashboard unless another default detail tab is required
     pageKey=customers:detail:<customer.id>
   - This must open a new top tab if that customer is not already open.
   - If the customer tab is already open, activate that existing tab instead of creating a duplicate.

3. The top tab title for a customer detail tab must be the customer name:
   - RheinForum Köln
   - HafenKontor Köln
   etc.

4. Use the existing tabbar store API instead of changing the global tabbar architecture.
   Likely implementation:
   - import/use useTabbarStore from @vben/stores where appropriate.
   - after router.push to the customer detail route, call setTabTitle(currentRoute, customer.name).
   - also add a small watcher/sync function so if a customer detail tab is restored from session or loaded directly by URL, once selectedCustomer is available, the tab title updates to selectedCustomer.name.
   - if the route is the list route without customer_id/pageKey, keep/reset the title to the standard Customers/Kunden title.

5. Keep pageKey stable while changing detail sub-tabs:
   - If the user switches from Dashboard to Überblick or Aufträge inside the same customer, keep:
     pageKey=customers:detail:<customer.id>
   - Only update the query tab value.
   - Do not open a new top tab for each internal customer detail section.

6. Back to customer list:
   - The "Zur Kundenliste" / Back to list button should navigate to:
     /admin/customers
     with no customer_id and no pageKey.
   - It should activate or create the list tab titled Kunden.
   - It should not close the customer detail tab automatically.

7. Do not break the previous caching work:
   - Keep domCached and keepAlive on SicherPlanCustomers.
   - Keep the cached route provider behavior if already implemented.
   - Do not disable tabbar.
   - Do not change backend code.
   - Do not change API endpoints.

8. Do not change role authority or sidebar structure:
   - Keep SicherPlanCustomers as a direct sidebar route.
   - Keep authority, icon, moduleKey, and route title unchanged unless strictly necessary.
   - Do not create a Customers -> Customers nested group again.

9. Update tests.

Required test updates:
A. In web/packages/stores/src/modules/tabbar.test.ts:
   - Replace the old test named similar to:
     "uses one Customers tab when customer query params change inside the same module workspace"
   - New behavior:
     a) Add list tab:
        /admin/customers
        key should be /admin/customers
        title should be Customers/Kunden.
     b) Add customer c1 detail tab:
        /admin/customers?customer_id=c1&tab=dashboard&pageKey=customers:detail:c1
        key should be customers:detail:c1
     c) Add customer c2 detail tab:
        /admin/customers?customer_id=c2&tab=dashboard&pageKey=customers:detail:c2
        key should be customers:detail:c2
     d) Store should now have 3 tabs: list, c1, c2.
     e) Re-opening c1 with another internal tab query:
        /admin/customers?customer_id=c1&tab=orders&pageKey=customers:detail:c1
        should update the existing c1 tab, not create a fourth tab.

B. Add or update tests around CustomerAdminView:
   - Clicking a customer row calls router.push with query.customer_id and query.pageKey.
   - The pageKey format must be customers:detail:<customerId>.
   - The tab title is updated to the customer display name.
   - Clicking "Back to list" navigates to /admin/customers without pageKey.

C. Add/adjust route tests only if necessary:
   - SicherPlanCustomers should still have domCached and keepAlive.
   - It may keep fullPathKey: false because pageKey overrides the key for detail tabs.
   - Add a comment/test explaining that customer detail top-tabs use query.pageKey intentionally.

10. Optional but recommended smoke test:
   Run a temporary Playwright test:
   - Open http://localhost:5173/
   - Log in with the local test credentials.
   - Open /admin/customers.
   - Confirm the top tab title is Kunden.
   - Click RheinForum Köln.
   - Confirm a new top tab appears titled RheinForum Köln.
   - Click Kunden tab.
   - Confirm the list is visible.
   - Click HafenKontor Köln.
   - Confirm a new top tab appears titled HafenKontor Köln.
   - Confirm all three tabs exist: Kunden, RheinForum Köln, HafenKontor Köln.
   - Switch between these tabs and confirm the correct content remains visible.

Acceptance criteria:
- Clicking Customers in the sidebar opens the Customers list tab titled Kunden.
- Clicking RheinForum Köln opens a separate top tab titled RheinForum Köln.
- Clicking HafenKontor Köln opens another separate top tab titled HafenKontor Köln.
- Returning to Kunden shows the customer list, not the last selected customer detail.
- Re-clicking an already-open customer activates/updates that customer’s tab, not a duplicate.
- Switching internal customer detail sections does not create new top tabs.
- Closing a customer tab removes only that customer detail tab.
- Backend code and API endpoints remain unchanged.
- Existing tab caching behavior remains intact.
- All relevant tests pass.

Before coding:
Please validate the approach first. In particular, confirm that getTabKey() already prioritizes query.pageKey and that this is the correct Vben-native way to create separate top tabs for multiple records under the same route path. If you find a safer existing Vben pattern for record detail tabs, explain it and use the smallest correct implementation.
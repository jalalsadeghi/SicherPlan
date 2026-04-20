You are working in the SicherPlan repository.

Task:
Refactor the /admin/customers page layout according to the requested UX change.

User request:
1. Move the "Customer list" box, currently on the left side, above the "Customer detail" box and below the "Module control" / page intro area.
2. Make "Customer list" full-width, like the "Module control" box.
3. Make "Customer detail" full-width as well.
4. Remove the customer row list from inside the "Customer list" box:
   - remove/hide the rendered customer rows with class customer-admin-row selected / customer-admin-row.
   - customer navigation will move to the sidebar in a separate task.

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

Current code facts to validate:
- CustomerAdminView.vue currently uses:
  .customer-admin-grid {
    grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  }
- Customer list panel is:
  <section class="module-card customer-admin-panel customer-admin-list-panel" data-testid="customer-list-section">
- Customer detail panel is:
  <section class="module-card customer-admin-panel customer-admin-detail" data-testid="customer-detail-workspace">
- Customer rows are currently rendered with:
  <div v-if="customers.length" class="customer-admin-list">
    <button
      v-for="customer in customers"
      class="customer-admin-row"
      :class="{ selected: customer.id === selectedCustomerId }"
      @click="selectCustomer(customer.id)"
    >
- Those row buttons must be removed from this panel.

Required implementation:

A. Layout
1. Change the customer master/detail layout from two columns to one column.
2. "Customer list" should appear first.
3. "Customer detail" should appear below it.
4. Both panels should span the full available content width.
5. Remove sticky behavior from customer-admin-list-panel.
6. Keep responsive behavior clean; on mobile it should still be one column.

Suggested CSS:
- .customer-admin-grid should become:
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
  grid-template-columns: minmax(0, 1fr);
- .customer-admin-list-panel should no longer be sticky.
- Remove or neutralize position: sticky / top: 0.

B. Customer list panel content
1. Keep the filter/search/action controls:
   - Search
   - Status filter
   - Default branch
   - Default mandate
   - Include archived customers
   - Search button
   - CSV export
   - New customer
2. Remove the customer row list inside this panel.
3. If customers.length is zero, do not show the old "empty list" message in this panel unless it still makes sense for filter result feedback.
4. Consider showing a small helper text instead, for example:
   "Use the sidebar customer links to open a customer dashboard."
   Add i18n keys if needed.
5. Do not remove the customers data loading from this component, because the sidebar dynamic links will also need customer data or the page still needs to auto-select based on route.

C. Selection behavior
1. Do not break existing route-based customer selection:
   - /admin/customers?customer_id=<id>&tab=dashboard must still select that customer.
2. If no customer_id is provided, current behavior may auto-select first customer. Preserve or explicitly validate this behavior.
3. Start new customer flow must still work.
4. Search/export/new customer actions must still work.
5. Dashboard/detail tabs must still work.

D. Accessibility and tests
1. Keep data-testid="customer-list-section".
2. Keep data-testid="customer-detail-workspace".
3. Remove tests expecting customer-admin-row inside customer-list-section, or update them.
4. Add/adjust tests proving:
   - customer-master-detail-layout is single-column / no two-column dependency
   - customer list panel appears before detail panel
   - customer rows are not rendered inside customer-list-section
   - selecting via route query still opens customer dashboard
   - filters/search still call listCustomers
   - New customer still opens create form

E. Validate
Before implementing, validate whether my interpretation is correct.
If the current layout was already changed in the repo, report the actual current code and implement the equivalent requested result.

Do not change backend APIs.
Do not remove listCustomers calls.
Do not remove customer selection logic.
Do not remove CustomerDashboardTab or CustomerPlansTab.

Expected final behavior:
- /admin/customers shows Module Control at top.
- Below it, full-width Customer list/search/action panel.
- Below that, full-width Customer detail panel.
- No customer rows appear inside the Customer list panel.
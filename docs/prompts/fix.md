We need one small UX refinement in the Customer Orders tab.

Current status:
- Customer detail > Orders tab is working.
- Each order row shows:
  - Structure
  - Edit
- The Structure action exists and the structure content/box itself is suitable.
- The only requested change: the Structure view should open in a dialog/modal on top of the current Orders page, instead of changing the page layout or inline state.

Desired behavior:
When the user clicks "Structure" on an order row:
- Open the existing order structure content inside a modal/dialog overlay.
- Keep the user on the same page:
  /admin/customers?customer_id=<id>&tab=orders&pageKey=customers:detail:<id>
- Do not navigate to another route.
- Do not change the Orders list layout.
- Do not open a new top app tab.
- Do not change the existing Structure content except wrapping it in a dialog.

Relevant files:
- web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerOrdersTab.vue
- any newly created order structure component/modal files
- CustomerAdminView.vue only if it currently owns the structure state

Task:
Wrap the existing Structure view in a modal/dialog.

Requirements:
1. Reuse the existing structure content/component.
   Do not redesign the tree.
   Do not change hierarchy logic.
   Do not change API calls unless required for modal lifecycle.

2. Add a modal/dialog overlay similar to existing customer/order preview modals:
   - backdrop
   - centered or wide modal card
   - clear title, for example "Order structure" / "Planning tree"
   - close button
   - Escape key closes
   - clicking outside closes if consistent with existing modal behavior
   - modal max-height with internal scroll if content is tall

3. Modal content:
   - show selected order title/order number in the modal header
   - show the existing order structure/tree inside the modal body
   - keep existing node actions/links working
   - if node click opens embedded order workspace, close the modal first or keep behavior consistent and clear

4. Route/query behavior:
   - Clicking Structure may optionally set a query like structureOrderId=<orderId>, but it is not required.
   - If query is used, closing modal should remove it.
   - customer_id, tab=orders, and pageKey must remain unchanged.
   - No navigation to /admin/customers/order-workspace.

5. State:
   - Only one structure modal open at a time.
   - Opening structure for another order replaces the modal content.
   - Closing modal clears selected structure order state.
   - Keep cached/lazy-loaded hierarchy data if already implemented.

6. Do not change:
   - Edit button behavior
   - New order behavior
   - order preview card click behavior
   - Customer main tabs Dashboard / Overview / Orders
   - Customer list tab
   - backend/API files

Tests:
Add/update tests:
1. Clicking Structure opens a modal/dialog.
2. The Orders list remains visible behind the modal.
3. The modal contains the selected order structure content.
4. Close button closes the modal.
5. Escape closes the modal.
6. Clicking outside closes the modal if that is the project’s existing modal convention.
7. Clicking Edit still works unchanged.
8. No route navigation to /admin/customers/order-workspace occurs.
9. customer_id, tab=orders, and pageKey remain unchanged.

Acceptance criteria:
- Structure opens as a modal/dialog overlay.
- Existing structure content remains unchanged.
- Orders list page does not change layout.
- No new top tab opens.
- No backend/API changes.
- Existing Structure/Edit/New order behavior remains intact.

Before coding:
Please first identify where the Structure view is currently rendered and explain the smallest safe change to move/wrap it into a modal.
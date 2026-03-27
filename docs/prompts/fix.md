You are working in the SicherPlan monorepo.

Goal:
Refactor the Customer Portal information architecture so the sidebar/menu contains clear customer-facing navigation entries instead of a single monolithic “Customer portal” page.

Current root cause:
- The sidebar is route-driven.
- In the current route config, the portal section defines only one customer route:
  /portal/customer
- There are no child routes for orders, schedules, watchbooks, timesheets, invoices, reports, or history.
- Therefore the sidebar can only show a single “Customer portal” menu item.
- The current CustomerPortalAccessView.vue renders all portal sections inside one large page.
- This is a frontend routing/IA limitation, not a missing tenant permission.

Important functional clarification:
- Existing backend customer-portal APIs currently support viewing:
  - context
  - orders
  - schedules
  - watchbooks
  - timesheets
  - invoices
  - reports
  - history
- The only current customer write action is watchbook entry creation.
- There is currently NO customer-portal backend endpoint for “create order”.
- Therefore:
  1. menu links for existing datasets can be implemented mainly as a frontend route/view refactor
  2. customer order creation requires new backend + frontend work and must not be faked as a simple menu item

Relevant files to inspect:
Frontend:
- web/apps/web-antd/src/router/routes/modules/sicherplan.ts
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerPortalAccessView.vue
- related portal helper/API files

Backend:
- backend/app/modules/customers/portal_router.py
- backend/app/modules/customers/portal_service.py
- backend/app/modules/customers/schemas.py

Required work:

A. Split the customer portal into real navigable pages
1. Replace the single monolithic customer portal route with a portal section and child routes, for example:
   - /portal/customer/overview
   - /portal/customer/orders
   - /portal/customer/schedules
   - /portal/customer/watchbooks
   - /portal/customer/timesheets
   - /portal/customer/invoices
   - /portal/customer/reports
   - /portal/customer/history

2. Update the sidebar/menu so these routes appear as customer-facing navigation items under Customer portal.
3. Keep menu entries aligned with actual available capabilities.
4. If some datasets are still pending integration, the pages can exist but must clearly show a high-quality empty/pending state instead of pretending the feature is missing.

B. Refactor the current page into modular views/components
1. Break CustomerPortalAccessView.vue into smaller focused portal views/components.
2. Suggested structure:
   - overview page for context + capability summary
   - orders page
   - schedules page
   - watchbooks page
   - timesheets page
   - invoices page
   - reports page
   - history page

3. Reuse the existing API calls where possible instead of duplicating logic.

C. Keep capability-aware visibility
1. Do not blindly show actions on every page.
2. For example:
   - watchbook write form only if can_add_watchbook_entries = true
   - download buttons only where document download is supported
   - pending integration pages should still be navigable but clearly labeled as pending

D. Customer order creation
1. Do NOT add a fake “Create order” page unless backend support exists.
2. Inspect current backend portal_router.py and confirm there is no customer order creation endpoint.
3. If the product requires customers to create orders from the portal, define a separate implementation phase:
   - backend endpoint(s) for customer-submitted order/request intake
   - validation and workflow state
   - customer-scoped submission model
   - UI form and confirmation flow
4. For now, if no backend create-order capability exists, the Orders page should be read-only and clearly say so.

E. UX requirements
1. Sidebar labels should be customer-friendly and explicit:
   - Overview
   - Orders
   - Schedules
   - Watchbooks
   - Timesheets
   - Invoices
   - Reports
   - History
2. The overview page should summarize:
   - who the customer is
   - what they can do
   - what is read-only
   - what is pending integration
3. Remove reliance on one giant scrollable page for all portal content.

F. Output before coding
1. summarize the current routing limitation
2. list proposed new routes
3. identify which pages can be built immediately from existing APIs
4. identify which requested actions (especially customer order creation) require new backend work

Then implement the route/menu refactor first.
If you include a future “create order” phase, separate it clearly from the current route/sidebar work.
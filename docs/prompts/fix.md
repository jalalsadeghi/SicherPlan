We need to fix the broken Customer detail layout after the previous one-page refactor.

Current problem:
The previous implementation put almost everything into one large page and broke the Customer detail UI.
The page now looks visually broken:
- the left navigation appears as unstyled text/icons near the top
- content sections are stacked without the previous polished layout
- the old Contacts & Access side-nav styling is no longer preserved
- Dashboard, Overview and Orders are not shown as the intended main detail tabs

Correct desired behavior:
Customer detail must have exactly these main in-page tabs:
1. Dashboard
2. Overview
3. Orders

Inside the Overview tab only, show a left-side section navigation with the same visual style as the previous Contacts & Access side navigation.

Overview tab should contain these sections in this order:
1. Master data / General customer data
2. Contacts & Access
   - Contacts
   - Addresses
   - Portal & Access
3. Commercial
   - Billing profile
   - Invoice parties
   - Pricing rules
     - Rate cards
     - Rate lines
     - Surcharges
4. History
5. Employee blocks

Important:
Orders must NOT be inside the Overview side navigation.
Orders must remain a separate main tab.
Dashboard must remain a separate main tab.

Relevant files:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.layout.test.js
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.test.js

Current helper issue:
CUSTOMER_OVERVIEW_SECTION_ORDER currently includes "orders".
This is wrong for the desired UX.
Orders must be removed from the overview section registry and remain a top-level detail tab.

Task:
Repair the Customer detail structure and styling.

Step 1 — Restore top-level Customer detail tabs:
The top-level in-page tab bar must show:
- Dashboard
- Overview
- Orders

Rules:
- If isCreatingCustomer is true, show only Overview.
- If selectedCustomer exists:
  - show Dashboard
  - show Overview
  - show Orders only if canReadOrders
- Do not show Contacts & Access or Commercial as top-level tabs anymore.
- Do not show History and Employee blocks as top-level tabs.

Step 2 — Keep Dashboard as its own tab:
When activeDetailTab === "dashboard":
- render CustomerDashboardTab only
- do not render the full Overview one-page content
- keep the previous dashboard layout intact

Step 3 — Keep Orders as its own tab:
When activeDetailTab === "orders":
- render CustomerOrdersTab only
- do not render Orders inside Overview
- preserve existing order edit/start-new-order behavior

Step 4 — Build Overview tab as one-page workspace:
When activeDetailTab === "overview":
Render a clean two-column layout:
- left: sticky side navigation
- right: section content

Use the same visual style as the old Contacts & Access side nav:
- customer-admin-contact-access-nav-shell
- customer-admin-contact-access-nav
- customer-admin-contact-access-nav__link
or copy/rename these classes carefully to:
- customer-admin-overview-nav-shell
- customer-admin-overview-nav
- customer-admin-overview-nav__link

The final UI must visually match the old Contacts & Access side navigation style.

Step 5 — Fix the section registry:
Update customerAdmin.helpers.js:
- CUSTOMER_DETAIL_TAB_ORDER should effectively support only:
  dashboard, overview, orders
  for the main visible detail tabs
- Keep aliases for old URLs:
  contact_access, contacts, addresses, portal -> overview section
  commercial, billing_profile, invoice_parties, rate_cards, rate_lines, surcharges -> overview section
  history, employee_blocks -> overview section
  plans -> orders
- Remove "orders" from CUSTOMER_OVERVIEW_SECTION_ORDER.
- Remove Orders from buildCustomerOverviewSections.
- Keep History and Employee blocks inside Overview side navigation if they are still required.
- Keep commercial/rate-card gating:
  - Rate cards visible when Commercial is available
  - Rate lines and Surcharges visible only after hasRateCards is true

Step 6 — Route/query compatibility:
Old URLs must still work.

Examples:
- tab=dashboard -> activeDetailTab dashboard
- tab=overview -> activeDetailTab overview, section master_data
- tab=contact_access or tab=contacts -> activeDetailTab overview, section contacts
- tab=addresses -> activeDetailTab overview, section addresses
- tab=portal -> activeDetailTab overview, section portal_access
- tab=commercial -> activeDetailTab overview, section billing_profile
- tab=rate_cards -> activeDetailTab overview, section rate_cards
- tab=rate_lines -> activeDetailTab overview, section rate_lines, only if hasRateCards; otherwise rate_cards
- tab=surcharges -> activeDetailTab overview, section surcharges, only if hasRateCards; otherwise rate_cards
- tab=orders or tab=plans -> activeDetailTab orders
- tab=history -> activeDetailTab overview, section history
- tab=employee_blocks -> activeDetailTab overview, section employee_blocks

Do not create new top app tabs for internal Overview sections.
Keep pageKey unchanged.

Step 7 — Fix markup/layout:
In CustomerAdminView.vue:
- Do not place the side nav directly above the content.
- It must be inside a proper layout wrapper:
  <section class="customer-admin-overview-onepage">
    <aside class="customer-admin-overview-nav-shell">...</aside>
    <div class="customer-admin-overview-content">...</div>
  </section>
- Ensure the nav is visually left aligned and sticky/pinned like the old Contacts & Access nav.
- Ensure content cards start to the right of the nav and use full available width.
- Do not let nav text/icons collapse into raw inline text.

Step 8 — Preserve creation gating:
When creating a new customer:
- only Overview tab is visible
- only master data / general customer form is visible
- Contacts & Access, Commercial, History, Employee blocks are hidden until the customer exists

Step 9 — Preserve commercial gating:
Inside Overview > Commercial:
- Billing profile visible if canReadCommercial and customer exists
- Invoice parties visible if canReadCommercial and customer exists
- Pricing rules visible if canReadCommercial and customer exists
- Rate cards visible first
- Rate lines and Surcharges visible only if hasRateCards is true

Step 10 — Preserve functionality:
Do not break:
- customer creation
- customer master data edit
- lifecycle controls
- contacts create/edit/archive
- addresses create/edit/archive
- portal access/privacy controls
- billing profile
- invoice parties
- pricing rules
- rate cards/rate lines/surcharges
- orders tab
- customer top app tab title
- customer list tab
- pageKey behavior
- route-cache/session isolation
- scroll isolation

Step 11 — Do not change backend:
This is a frontend layout/navigation repair only.
Do not change backend code or API endpoints.

Tests required:
A. Top tab visibility:
- Creating customer: only Overview main tab visible.
- Existing customer: Dashboard, Overview, Orders visible according to permissions.
- Contacts & Access and Commercial are not top-level tabs.
- History and Employee blocks are not top-level tabs.

B. Overview side nav:
- Overview tab shows left side nav.
- Side nav visually/layout structurally uses overview/contact-access nav classes.
- Sections are ordered:
  Master data
  Contacts
  Addresses
  Portal & Access
  Billing profile
  Invoice parties
  Rate cards
  Rate lines if hasRateCards
  Surcharges if hasRateCards
  History
  Employee blocks

C. Orders separation:
- Orders is not inside Overview side nav.
- Orders tab renders CustomerOrdersTab.

D. Dashboard separation:
- Dashboard tab renders CustomerDashboardTab only.
- It does not render the giant Overview one-page content.

E. Route compatibility:
- tab=contact_access maps to Overview + contacts section.
- tab=commercial maps to Overview + billing_profile section.
- tab=orders maps to Orders tab.
- tab=history maps to Overview + history section.

F. Pricing gating:
- Without rate cards: Rate cards visible, Rate lines/Surcharges hidden.
- With rate cards: all three visible.

Acceptance criteria:
- Customer detail UI is no longer visually broken.
- Main tabs are exactly Dashboard, Overview, Orders.
- Overview contains the one-page side navigation.
- Side nav matches the old Contacts & Access style.
- Orders remains a separate main tab.
- Dashboard remains a separate main tab.
- Existing business actions still work.
- No backend/API changes.
- Tests pass.

Before coding:
First summarize the current broken implementation and state exactly which parts will be reverted or restructured.
Do not do a broad rewrite. Make the smallest safe repair.
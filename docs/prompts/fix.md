We need to fix Customer Overview left-nav click behavior.

Current status:
- Customer detail main tabs are correct: Dashboard, Overview, Orders.
- Customer Overview left nav is styled correctly.
- Customer Overview left nav stays visible while scrolling.
- Content cards are now aligned correctly.
- But clicking a left nav link only changes the URL query `tab=...`; it does not scroll to the target section.

Example:
Current URL:
/admin/customers?customer_id=84bad50d-209c-491e-b86b-13c7788c7620&tab=billing_profile&pageKey=customers:detail:84bad50d-209c-491e-b86b-13c7788c7620

When clicking:
- Payment, tax, and bank data
- Versioned pricing windows
- Service and function-based prices
- Time, weekday, and region surcharges

the `tab` query changes, but the page does not scroll to the corresponding card.

Reference behavior:
Use Employee Overview behavior as the reference:
web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

File to fix:
web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

Do not change:
- backend/API files
- main tabs Dashboard / Overview / Orders
- Customer list tab behavior
- customer detail pageKey behavior
- top app tab title
- route-cache/session/scroll architecture
- Employee pages
- Dashboard and Orders tabs

Task:
Fix Customer Overview nav so every visible nav link scrolls to its matching section, exactly like Employee Overview.

Step 1 — Diagnose current cause:
Inspect these functions/refs in CustomerAdminView.vue:
- selectCustomerOverviewSection
- setCustomerOverviewSectionRef
- customerOverviewSectionRefs
- customerOverviewOnePageRef
- customerOverviewNavShellRef if present
- activeOverviewSection
- sync route/query watcher that handles query.tab
- code that updates URL query tab
- useRouteCacheScrollTarget / route-cache session usage if present

Report the exact root cause before changing code:
- Is selectCustomerOverviewSection only updating the URL?
- Is the scroll function missing?
- Is the scroll target wrong?
- Are section refs missing or registered on the wrong elements?
- Is scroll executed before DOM/expanded groups are rendered?
- Does router.replace reset/interrupt the scroll?
- Is route-cache scroll restoration overriding the click scroll?

Step 2 — Required section id mapping:
Ensure every nav item maps to an actual section ref.

Required mapping:
- Overview -> master_data
- Contacts -> contacts
- Addresses -> addresses
- Portal & Access -> portal_access
- Payment, tax, and bank data -> billing_profile
- Alternative invoice recipients -> invoice_parties
- Versioned pricing windows -> rate_cards
- Service and function-based prices -> rate_lines
- Time, weekday, and region surcharges -> surcharges
- History -> history
- Employee blocks -> employee_blocks

Make sure every target has:
- a real section DOM element
- data-testid
- setCustomerOverviewSectionRef('<section_id>', element)

Step 3 — Implement real scroll on nav click:
Update selectCustomerOverviewSection(sectionId) so it does all of this:

1. Validate the section is visible and allowed.
2. Expand parent groups if needed:
   - Contacts & Access
   - Commercial
   - Pricing rules
3. Set activeOverviewSection.
4. Update URL query `tab` for compatibility, but keep:
   - customer_id
   - pageKey
   unchanged.
5. Wait for DOM update:
   await nextTick()
6. Get the local target element from customerOverviewSectionRefs.
7. Scroll the correct container to that element.

Important:
- Do not use document.getElementById as the primary mechanism.
- Do not use global querySelector as the primary mechanism.
- Use local refs.
- Use the same scroll target strategy as Employee Overview.
- If Employee Overview uses route-cache scroll target or document scrollingElement, follow the same pattern.

Step 4 — Scroll target and offset:
The target must scroll in the visible admin content area, not just update active state.

Implement robust scroll:
- find target.getBoundingClientRect()
- find scroll container used by the page / route cache
- calculate target offset with a top offset so the section is not hidden behind header/tabbar
- use scrollTo({ top, behavior: 'smooth' }) or the same behavior used in Employee Overview

If using scrollIntoView, ensure it works with the Vben layout and route-cache scroll container.

Step 5 — Prevent route update from cancelling scroll:
If current code first calls router.replace and then loses the target/scroll:
- update active section and expand groups first
- await nextTick
- perform scroll
- then update URL query
or:
- update URL query with router.replace
- await router.replace
- await nextTick
- perform scroll

Choose the sequence that is most reliable. The result must be visible scroll.

Step 6 — Direct URL compatibility:
When opening a URL directly with:
- tab=billing_profile
- tab=rate_cards
- tab=rate_lines
- tab=surcharges
- tab=contacts
- tab=addresses
- tab=portal
- tab=history
- tab=employee_blocks

the page should:
- open main tab Overview
- expand relevant groups
- mark the correct nav item active
- after data/render is ready, scroll to the correct section

If data for gated sections is not ready yet:
- wait until the section exists
- then scroll once
- do not keep repeatedly scrolling on every render

Step 7 — Collapsed groups:
If target is inside a collapsed group:
- expand parent group first
- await nextTick
- then scroll

Example:
Click "Service and function-based prices":
- expand Commercial
- expand Pricing rules
- set activeOverviewSection = rate_lines
- scroll to rate_lines

Step 8 — Do not break existing fixed nav behavior:
The left nav currently stays visible while scrolling. Keep that.
Do not regress CSS/layout/card fixes.

Step 9 — Tests:
Add/update tests.

A. Nav click scroll tests:
- clicking Payment, tax, and bank data scrolls to billing_profile
- clicking Alternative invoice recipients scrolls to invoice_parties
- clicking Versioned pricing windows scrolls to rate_cards
- clicking Service and function-based prices scrolls to rate_lines
- clicking Time, weekday, and region surcharges scrolls to surcharges
- clicking Contacts scrolls to contacts
- clicking Addresses scrolls to addresses
- clicking Portal & Access scrolls to portal_access

B. URL update + scroll test:
- clicking a nav item updates query.tab
- pageKey remains unchanged
- customer_id remains unchanged
- scroll is still executed

C. Direct route test:
- tab=billing_profile activates Overview and scrolls to billing_profile
- tab=rate_cards activates Overview and scrolls to rate_cards
- tab=rate_lines activates Overview and scrolls to rate_lines if visible
- tab=surcharges activates Overview and scrolls to surcharges if visible

D. Collapsed group test:
- collapse Commercial/Pricing rules
- click or route to rate_lines
- parent groups expand
- scroll target is rate_lines

E. Regression:
- Dashboard tab does not render Overview side nav
- Orders tab does not render Overview side nav
- main tabs remain Dashboard, Overview, Orders
- Customer list tab remains unchanged
- Employee Overview remains unchanged
- backend/API files untouched

Acceptance criteria:
- Clicking any visible Customer Overview left nav link scrolls to the correct content card.
- URL `tab` may update, but scroll must also happen.
- Versioned pricing windows scrolls to rate_cards.
- Service and function-based prices scrolls to rate_lines.
- Time, weekday, and region surcharges scrolls to surcharges.
- Collapsed groups expand before scrolling.
- Left nav remains visible while scrolling.
- Dashboard / Overview / Orders are unchanged.
- No backend/API changes.

Before coding:
Explain the exact cause of the current behavior: why the URL changes but scroll does not happen.
Then implement the smallest safe fix.
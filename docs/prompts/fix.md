We need to refine the Customer Overview left-side navigation behavior.

Current status:
The visual styling of the Customer Overview left navigation is now fixed and looks close to the Employee Overview style.

Remaining issues:
1. Clicking nav links does not scroll to the related section.
   Example: clicking "Service and function-based prices" does nothing.
2. The "Overview" link should not have a duplicated child/sub-item. It should be a single standalone nav item.
3. Groups with children should be collapsible/expandable, so the left nav is cleaner:
   - Contacts & Access
   - Commercial
   - Pricing rules
   should be collapsible groups.
   Their children should be visible only when the group is expanded.

Relevant files:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.layout.test.js
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.test.js

Do not change:
- backend/API files
- main customer detail tabs: Dashboard, Overview, Orders
- customer list tab behavior
- customer detail pageKey behavior
- customer tab titles
- Employee Overview behavior
- route-cache/session/scroll architecture

Task 1 — Fix nav click scrolling:
Find the function that handles Customer Overview nav clicks, likely:
- selectCustomerOverviewSection(sectionId)
- setCustomerOverviewSectionRef(...)
- customerOverviewSectionRefs
- customerOverviewOnePageRef
- useRouteCacheScrollTarget / route-cache scroll target if used

Fix it so clicking any visible nav link scrolls to the correct local section.

Requirements:
- Use instance-local section refs, not document.getElementById or global querySelector.
- The scroll target must be the correct route-cache pane/main scroll container.
- The function must work for:
  - Overview/master data
  - Contacts
  - Addresses
  - Portal & Access
  - Billing profile
  - Invoice parties
  - Rate cards
  - Rate lines
  - Surcharges
  - History
  - Employee blocks
- If a section is hidden because of gating, do not scroll to it.
- If the user clicks a grandchild such as "Service and function-based prices", it must scroll to the rate lines section.
- Keep pageKey unchanged.
- Do not create a new top tab.
- Optionally update query.section for deep linking, but do not break existing query.tab compatibility.

Task 2 — Remove duplicate Overview child:
Currently the nav appears to show:
- Overview
  - Overview

This is wrong.
Make Overview a single standalone nav link.

Expected:
- Overview
- Contacts & Access
  - Contacts
  - Addresses
  - Portal & Access
- Commercial
  - Billing profile
  - Invoice parties
  - Pricing rules
    - Rate cards
    - Service and function-based prices
    - Time, weekday, and region surcharges
- History
- Employee blocks

Task 3 — Make groups collapsible:
Implement collapsible groups in Customer Overview nav.

Groups:
- Contacts & Access
- Commercial
- Pricing rules

Behavior:
1. Each group header has a chevron/indicator.
2. Clicking the group header toggles expanded/collapsed.
3. If a group itself also maps to a section, clicking should either:
   - toggle only, if it is purely a group label
   - or scroll to its first child and expand
   Choose the safest/clearest UX and keep it consistent.
4. If a child/grandchild inside a collapsed group is the active section, the parent group should auto-expand.
5. On initial load:
   - Overview is standalone and active by default.
   - Groups are collapsed by default, unless the active section belongs to that group.
6. When user clicks a child:
   - scroll to the section
   - mark that child active
   - keep its parent group expanded
7. Collapsed/expanded state should be local to the customer tab/session.
   It must not affect another customer tab.

Implementation hint:
Use a local reactive state, for example:
const expandedCustomerOverviewGroups = ref(new Set(['contacts_access', 'commercial', ...]))

or a plain object:
const expandedCustomerOverviewGroups = reactive<Record<string, boolean>>({})

Add helpers:
- isCustomerOverviewGroupExpanded(groupId)
- toggleCustomerOverviewGroup(groupId)
- expandGroupsForCustomerOverviewSection(sectionId)
- getCustomerOverviewParentGroupIds(sectionId)

Task 4 — Preserve styling:
The collapsible group headers and child links must keep the polished side-nav style.
Do not return to raw inline text.

Add or reuse classes:
- customer-admin-overview-nav__group-toggle
- customer-admin-overview-nav__chevron
- customer-admin-overview-nav__children
- customer-admin-overview-nav__children--collapsed
- customer-admin-overview-nav__link--child
- customer-admin-overview-nav__link--grandchild

Use the same visual language as Employee Overview:
- vertical layout
- left active border/indicator
- proper icon spacing
- child indentation
- readable labels
- no cramped inline content

Task 5 — Tests:
Add or update tests.

A. Navigation click scroll test:
- Mount CustomerAdminView in Overview mode.
- Mock section refs / scroll target.
- Click "Service and function-based prices".
- Assert select/scroll target is rate_lines.
- Assert activeOverviewSection becomes rate_lines.

B. Overview duplicate test:
- Overview appears once as a standalone nav link.
- There is no child Overview under Overview.

C. Collapsible groups test:
- Contacts & Access group can collapse/expand.
- Commercial group can collapse/expand.
- Pricing rules group can collapse/expand.
- Children are hidden when collapsed and visible when expanded.

D. Active child auto-expand test:
- If route/query maps to rate_lines, Commercial and Pricing rules are expanded on load.
- Rate lines is active.

E. Gating test:
- Without rate cards, Rate lines and Surcharges are not visible.
- With rate cards, they appear under Pricing rules.

F. Regression:
- Main tabs remain Dashboard, Overview, Orders.
- Dashboard does not render Overview side nav.
- Orders does not render Overview side nav.
- No backend/API changes.

Acceptance criteria:
- Clicking every visible left nav item scrolls to the correct section.
- Overview is a single standalone link with no duplicate child.
- Contacts & Access, Commercial, and Pricing rules are collapsible.
- Active section auto-expands its parent groups.
- Collapsed groups make the nav cleaner.
- Styling remains consistent with the Employee Overview navigation.
- Dashboard/Overview/Orders main tabs remain unchanged.
- Backend/API files remain untouched.
- Tests pass.

Before coding:
First inspect why selectCustomerOverviewSection currently does not scroll. Report whether the cause is:
- missing refs,
- wrong section id mapping,
- wrong scroll container,
- collapsed/missing target,
- or a no-op handler.
Then implement the smallest safe fix.
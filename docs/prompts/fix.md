/review

Please review the Customer detail unified Overview workspace refactor.

Check:
1. Is there now only one in-page Customer detail workspace/tab named Overview?
2. Are the old top-level in-page tabs Dashboard, Contacts & Access, Commercial and Orders removed/hidden?
3. Does the left-side navigation use the same visual style as the old Contacts & Access side nav?
4. Is the section order correct?
   - Overview
   - Contacts & Access
   - Commercial
   - Orders
   - History
   - Employee blocks
5. Before customer creation, is only Overview/master data visible?
6. After customer creation, do other sections appear?
7. Is Commercial visible only when canReadCommercial?
8. Is Orders visible only when canReadOrders?
9. Under Commercial / Pricing rules:
   - Rate cards visible first
   - Rate lines and Surcharges hidden until at least one rate card exists
10. Do old query.tab values still map correctly to the unified Overview sections?
11. Does clicking left nav links scroll to local refs without using global document selectors?
12. Does this preserve customer top app tab/pageKey behavior?
13. Does the customer list tab remain Customers/Kunden?
14. Are Contacts, Addresses, Portal Access, Billing Profile, Invoice Parties, Rate Cards, Rate Lines, Surcharges, Orders, History and Employee Blocks still functional?
15. Did this avoid backend/API changes?
16. Did tests cover creation gating, existing customer visibility, commercial/rate-card gating and route compatibility?

Please report:
- files changed
- root cause / reason for refactor
- implementation summary
- gating rules preserved
- tests added/updated
- commands run
- remaining risks
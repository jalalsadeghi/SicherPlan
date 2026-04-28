/review

Please review the customer detail top-tab implementation.

Focus on:
1. Does /admin/customers still open the list tab titled Kunden?
2. Does clicking each customer row open a separate top tab?
3. Is the tab key generated with pageKey=customers:detail:<customerId>?
4. Is the tab title updated to the customer name, for example RheinForum Köln?
5. Does opening the same customer again activate/update the existing customer tab instead of creating duplicates?
6. Do internal customer detail sections such as Dashboard, Überblick, Kontakte & Zugang, Commercial, Aufträge stay inside the same customer top tab?
7. Does "Zur Kundenliste" navigate back to /admin/customers without pageKey?
8. Are domCached and keepAlive still working?
9. Are fullPathKey, route authority, sidebar structure, moduleKey, icons, and role scoping unchanged?
10. Were old tests that expected one Customers tab for all customer query params updated to the new desired behavior?
11. Is there any risk that pageKey affects unrelated Customers filters, CSV export, advanced filters, or the order workspace?
12. Did you run the relevant tests and, if possible, a local Playwright smoke test?

Please report:
- exact files changed
- root cause
- implementation summary
- tests added/updated
- commands run
- remaining risks
/review

Please review the employee detail top-tab implementation.

Focus on:
1. Does /admin/employees still open the list tab titled Employees?
2. Does clicking each employee row open a separate top tab?
3. Is the tab key generated with pageKey=employees:detail:<employeeId>?
4. Is the tab title updated to the employee full name, for example Leon Yilmaz?
5. Does opening the same employee again activate/update the existing employee tab instead of creating duplicates?
6. Do internal employee detail sections such as Dashboard and Overview stay inside the same employee top tab?
7. Does "Back to employee list" navigate back to /admin/employees without pageKey?
8. Are domCached and keepAlive still working?
9. Are route authority, sidebar structure, moduleKey, icons, and role scoping unchanged?
10. Are Customers detail tabs still working after this change?
11. Is there any risk that pageKey affects employee filters, import/export, create employee file, or advanced filters?
12. Did you run the relevant tests and, if possible, a local Playwright smoke test?

Please report:
- exact files changed
- root cause
- implementation summary
- tests added/updated
- commands run
- remaining risks
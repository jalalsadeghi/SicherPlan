/review

Please review the global per-tab scroll isolation fix.

Check these points carefully:
1. Is scroll state keyed by getTabKey(route), including pageKey-based tabs?
2. Does Dashboard keep its own scroll position independent of Employees and employee detail tabs?
3. Does Markus Neumann restore to its own Overview section after switching away and back?
4. Does scrolling Markus Neumann no longer affect Dashboard, Employees list, Emir Kaya, Sarah Becker, Customers, or other tabs?
5. Are new tabs initialized at top unless they have stored scroll state?
6. Is scroll saved before switching away from a tab?
7. Is scroll restored early enough to avoid visible flicker/jump?
8. Is the correct scroll container detected?
9. Are hidden domCached routes prevented from writing scroll state?
10. Is scroll state cleaned up when a cached tab is closed?
11. Does manual tab refresh/reload still work?
12. Is CachedRouteRenderer route context isolation preserved?
13. Are Customers and Employees detail pageKey tabs still working?
14. Are route authority, moduleKey, sidebar structure, icons, domCached, keepAlive, and tab titles unchanged?
15. Were backend/API files untouched?
16. Which tests were added or updated and what commands were run?

Please report:
- exact root cause
- files changed
- implementation summary
- scroll container chosen and why
- tests added/updated
- commands run
- remaining risks
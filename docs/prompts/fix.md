/review

Please review the tab caching fix carefully.

Focus areas:
1. Does each domCached tab now provide an isolated route context to its cached component tree?
2. Does useRoute() inside AdminModuleView resolve to the cached tab route instead of the global active route?
3. Does addCachedRoute update the stored route snapshot when the same tab key receives new query params?
4. Can Customers -> Employees -> Customers happen without remounting Customers?
5. Can Employees -> Customers -> Employees happen without remounting Employees?
6. Does closing a tab still remove its cached DOM entry?
7. Does manual reload/refresh still force a reload?
8. Are role authority, moduleKey, fullPathKey, route titles, icons, aliases, portal routes, and menu container routes unchanged?
9. Are there any hidden cached pages still watching global route changes and causing API calls?
10. Are the tests strong enough to prevent this regression from coming back?

Please list:
- changed files
- exact root cause
- exact fix
- tests added/updated
- commands run
- remaining risks
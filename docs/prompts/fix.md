We need to fix tab switching behavior in the SicherPlan web admin.

Problem:
In web/apps/web-antd, pages opened in the top tabbar are remounted when the user switches away and then clicks the already-open tab again. This causes repeated backend API calls and loses UX responsiveness. Example: /admin/customers -> /admin/employees -> /admin/customers triggers a fresh Customers load, even though the Customers tab was already open.

Repository context:
- Main route file: web/apps/web-antd/src/router/routes/modules/sicherplan.ts
- Vben layout already supports route-level DOM caching:
  - web/packages/effects/layouts/src/basic/content/content.vue
  - web/packages/effects/layouts/src/route-cached/route-cached-page.vue
  - web/packages/effects/layouts/src/route-cached/route-cached-view.vue
- RouteMeta already supports domCached:
  - web/packages/@core/base/typings/src/vue-router.d.ts
- The normal KeepAlive path is not sufficient for many SicherPlan pages because many routes share the same named AdminModuleView component:
  - web/apps/web-antd/src/views/sicherplan/admin-module-view.vue
  - web/apps/web-antd/src/views/sicherplan/module-registry.ts
- The tabbar cache list is built from route/tab names:
  - web/packages/stores/src/modules/tabbar.ts

Task:
1. Update web/apps/web-antd/src/router/routes/modules/sicherplan.ts.
2. Add a small typed helper, for example cachedWorkspaceMeta(), that returns route meta with:
   - keepAlive: true
   - domCached: true
3. Apply this helper to every leaf/page route that can be opened in the top tabbar, especially:
   - SicherPlanDashboard
   - SicherPlanCoreAdmin
   - SicherPlanPlatformServices
   - SicherPlanTenantUsers
   - SicherPlanHealthDiagnostics
   - SicherPlanCustomers
   - SicherPlanCustomerOrderWorkspace
   - SicherPlanRecruiting
   - SicherPlanEmployees
   - SicherPlanWorkforceCatalogs
   - SicherPlanSubcontractors
   - SicherPlanPlanning
   - SicherPlanPlanningOrders
   - SicherPlanPlanningShifts
   - SicherPlanPlanningStaffing
   - SicherPlanFinanceActuals
   - SicherPlanFinancePayroll
   - SicherPlanFinanceBilling
   - SicherPlanFinanceSubcontractorChecks
   - SicherPlanReporting
   - customer portal leaf routes
   - subcontractor portal leaf route
   - public applicant form route if it is displayed in the tabbar
4. Do not apply domCached to pure menu container/section routes such as:
   - SicherPlanAdministrationSection
   - SicherPlanWorkforceSection
   - SicherPlanOperationsSection
   - SicherPlanFinanceSection
   - SicherPlanReportingSection
   - SicherPlanPublic
   - SicherPlanPortal
   - SicherPlanCustomerPortalSection
5. Keep existing authority, moduleKey, title, icon, fullPathKey, hideInMenu, alias, props, redirect, and role-scoping behavior unchanged.
6. Update web/apps/web-antd/src/router/routes/modules/sicherplan.test.ts:
   - Keep the existing keepAlive assertions.
   - Add domCached assertions for all tabbed workspace/page routes.
   - Add a regression test that AdminModuleView-powered routes are domCached, because normal KeepAlive cannot reliably cache the shared AdminModuleView shell by route name.
7. Do not change backend code.
8. Do not change moduleRegistry behavior.
9. Do not remove or rename AdminModuleView.
10. Run the relevant web tests/type checks available in the repo and report the commands/results.

Acceptance criteria:
- Switching from Customers to Employees and back to Customers reuses the existing Customers page instance instead of remounting it.
- No backend API request should be triggered solely by clicking an already-open tab.
- Closing a tab should still remove its cached route from the DOM cache.
- Manual tab reload/refresh should still force refresh as before.
- Route tests must verify domCached + keepAlive on all SicherPlan tabbed workspace routes.
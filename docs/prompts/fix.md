You are working in the SicherPlan repository.

Bug:
The top "Module control" box is still visible on:

http://localhost:5173/admin/employees

User already asked to remove it, but it is still shown.

Important visual evidence:
The visible box contains:
- MODULE CONTROL
- Employees
- Employee administration separates private HR data...
- badges/text: HR Split, Private Data, Import Ready

This means the visible box is very likely the module page intro generated from moduleRegistry / ModuleWorkspacePage, not only the internal EmployeeAdminView hero.

Current code to inspect:
- web/apps/web-antd/src/views/sicherplan/module-registry.ts
- web/apps/web-antd/src/views/sicherplan/admin-module-view.vue
- web/apps/web-antd/src/components/sicherplan/module-workspace-page.vue
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Known current facts to validate:
1. In moduleRegistry.ts, the customers module has:
   showPageIntro: false
2. In moduleRegistry.ts, the employees module currently has:
   showWorkspaceSectionHeader: false
   but does NOT have:
   showPageIntro: false
3. The visible Employees box shows moduleRegistry employee badges:
   HR Split, Private Data, Import Ready
4. EmployeeAdminView.vue may also contain an internal:
   <section v-if="!embedded" class="module-card employee-admin-hero">
   but hiding only this internal hero is not enough if ModuleWorkspacePage intro remains visible.

Required implementation:

A. Hide the ModuleWorkspacePage intro for employees
1. In web/apps/web-antd/src/views/sicherplan/module-registry.ts, update the employees module config.
2. Add:
   showPageIntro: false
3. Keep:
   showWorkspaceSectionHeader: false
4. Do not remove badges/title/description keys from the registry unless they are used nowhere else.
5. Do not hide page intro globally.
6. Do not affect:
   - customers
   - planning
   - planning-orders
   - dashboard
   - any other module.

Expected employees config should include something like:

employees: {
  ...
  showPageIntro: false,
  showWorkspaceSectionHeader: false,
  ...
}

B. Also inspect the internal EmployeeAdminView hero
1. In EmployeeAdminView.vue, check if `employee-admin-hero` is still rendered.
2. If this internal hero is still visible after setting showPageIntro=false, hide/remove it too.
3. If it is not visible because the route uses embedded mode or the previous patch already removed it, do not add it back.
4. The final /admin/employees page must not show any top intro/Module control box from either source.

C. Preserve page content
After the intro is gone, the first visible main content should be the full-width Employee List panel.

Do not break:
- Employee List panel
- Search tab
- live suggestions while typing
- Search results modal
- Import / Export tab
- Create employee file
- Employee detail panel
- Employee detail tabs
- tenant/session/permission checks

D. Validate against Customers
1. Compare with the Customers module config.
2. Customers already hides the page intro with showPageIntro: false.
3. Employees should follow the same pattern.

E. Do not do a CSS-only global hack
Do not add global CSS like:
.module-control { display: none; }
because that may hide the module intro on other pages.

Use the supported module-level config or a page-specific class only if the config approach is not supported.

Expected final behavior:
- Open http://localhost:5173/admin/employees
- The MODULE CONTROL / Employees / HR Split Private Data Import Ready box is gone.
- Employee List panel is the first visible content block.
- The page otherwise behaves exactly as before.
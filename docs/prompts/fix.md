You are working in the SicherPlan repository.

Task title:
Refactor /admin/planning-shifts UI so it matches the visual quality and interaction structure of /admin/customers, while removing duplicate wrapper boxes.

Goal:
Fix the planning-shifts page layout and styling in the latest repo version so that:
1. the top "Module control" intro remains visible,
2. the extra "Workspace" box is removed,
3. the inner duplicate "Shift planning" hero box is removed,
4. the forms and panels get proper styling and spacing,
5. the page uses the Customer Admin page as the visual and structural reference pattern,
6. the result feels like a real embedded admin workspace, not an unstyled raw form dump.

Repository context:
Relevant files:
- web/apps/web-antd/src/views/sicherplan/admin-module-view.vue
- web/apps/web-antd/src/views/sicherplan/module-registry.ts
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

Observed issues:
1. The "Workspace" box is rendered by the shell wrapper, not by the planning-shifts page itself.
   This comes from admin-module-view.vue + module-registry.ts behavior.
2. PlanningShiftsAdminView.vue renders its own hero/intro box ("Shift planning") even when embedded.
   This duplicates the shell-level module intro ("Module control").
3. PlanningShiftsAdminView.vue currently has only minimal scoped CSS, so:
   - form controls look unstyled
   - cards feel cramped
   - field layout is weak
   - action rows and lists do not visually match the rest of the admin UI
4. /admin/customers has a much better internal structure and visual rhythm, and should be used as the design reference only.
   Do NOT copy customer business logic, but DO reuse its layout language, spacing, field styling, and tab/workspace patterns.

What to change

A) Remove the extra "Workspace" box for planning-shifts only
1. In module-registry.ts, configure the planning-shifts module so that the shell-level workspace section header does NOT render.
2. Keep the top shell intro ("Module control") intact.
3. Do not globally disable workspace headers for other modules unless needed.

Expected result:
- "Module control" stays
- "Workspace" box disappears for /admin/planning-shifts

B) Remove the duplicate inner "Shift planning" hero box
4. In PlanningShiftsAdminView.vue, add explicit embedded-mode support, similar in spirit to CustomerAdminView.
5. Accept an `embedded?: boolean` prop.
6. When embedded === true:
   - do NOT render the internal `planning-shifts-hero` box
   - relocate any essential controls from that box (tenant scope, bearer token, refresh actions) into the main workspace in a compact structured section
7. When embedded === false:
   - it is acceptable to keep a standalone intro if still useful

Expected result:
- no duplicate "Shift planning" hero when the page is shown inside the shell module wrapper
- scope/token controls remain accessible

C) Rebuild the planning-shifts page layout using Customer Admin as the UI reference
8. Use CustomerAdminView.vue only as a visual/layout reference.
9. Rework PlanningShiftsAdminView.vue to use the same design language:
   - structured card sections
   - clear headers
   - consistent action rows
   - proper field-stack spacing
   - proper form-grid layout
   - consistent textarea/input/select styling
   - responsive grid behavior
   - clean empty states
10. Prefer the same or very similar CSS patterns used in CustomerAdminView.vue for:
   - `.field-stack`
   - `.field-stack--wide`
   - `.cta-row`
   - section/panel headers
   - list/register cards
   - form section containers
   - feedback box
   - responsive behavior

D) Improve information architecture
11. The current page dumps 5 different sections at once:
   - Shift templates
   - Shift plans
   - Series and exceptions
   - Concrete shifts
   - Board preview
   This is too dense.
12. Reorganize the workspace into clearer tabs or section navigation inspired by Customer Admin.
13. Recommended tab structure:
   - Templates
   - Shift plans
   - Series
   - Shifts
   - Board
14. Only the active tab panel should be visible at one time.
15. Inside each tab, keep a clear “register + editor” rhythm similar to Customer Admin:
   - list/register area for existing records
   - editor/form area for create/update
16. For the Series tab, exceptions can remain in the same tab but visually separated as a sub-section.

E) Preserve business behavior
17. Do NOT change backend endpoints.
18. Do NOT change payload shapes.
19. Do NOT remove existing actions:
   - create template
   - create shift plan
   - create series
   - generate series
   - create exception
   - create shift
   - copy one day / copy one week
   - refresh board
20. This task is about UI structure, styling, and embedded rendering only.

F) Styling requirements
21. Inputs, selects, textareas, checkboxes, and action buttons must visually match the rest of the admin system.
22. The page must not look like unstyled browser defaults.
23. Cards must have consistent spacing and border treatment.
24. The page must remain responsive on smaller screens.
25. Avoid introducing a radically different design system.
26. Reuse existing class patterns where practical rather than inventing totally unrelated ones.

G) Empty states and disabled states
27. Keep disabled buttons functionally correct, but make them visually consistent with the rest of the admin UI.
28. Keep “No records yet.” states, but style them consistently with Customer Admin empty states.

H) Optional refactor if helpful
29. If large chunks of CustomerAdminView styling are useful across multiple admin pages, you may extract common admin-workspace styling into a shared CSS/module/composable ONLY if this stays scoped, clean, and low-risk.
30. Do not perform a huge cross-project refactor. Prefer the smallest clean change that fixes planning-shifts properly.

Acceptance criteria
1. /admin/planning-shifts still shows the shell-level "Module control" intro.
2. The extra shell-level "Workspace" box is gone for this module.
3. The inner duplicate "Shift planning" hero box is gone in embedded mode.
4. Forms and cards are styled properly and no longer look raw/unstyled.
5. The page structure is clearer and closer to /admin/customers in quality and rhythm.
6. Tabs or equivalent section switching ensure the screen is not overloaded.
7. No backend behavior is changed.
8. No route paths are changed.
9. The page works in embedded mode inside the admin shell.

Files expected to change
- web/apps/web-antd/src/views/sicherplan/module-registry.ts
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue
- optionally a small shared style/helper file ONLY if truly justified

Before coding:
Briefly explain:
- why the Workspace box appears
- why the inner Shift planning box is duplicated
- which CustomerAdminView patterns you will mirror

After coding:
Provide:
1. files changed
2. layout changes summary
3. styling changes summary
4. confirmation that Module control stayed and Workspace/inner Shift planning box were removed appropriately
5. confirmation that backend/API behavior was not changed
You are working in the SicherPlan repository.

Goal:
Fix the wrong loading text in the Dashboard calendar.

User-visible issue:
On the Customers calendar, the loading indicator text is correct. On the main Dashboard calendar, the loading indicator displays the raw i18n key:

workspace.loading.processing

Expected behavior:
The Dashboard calendar should show the translated human-readable loading text, the same way the Customers calendar does.

Primary files to inspect:
- web/apps/web-antd/src/views/sicherplan/dashboard/index.vue
- web/apps/web-antd/src/components/sicherplan/dashboard-calendar-panel.vue
- web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerDashboardTab.vue
- web/apps/web-antd/src/locales/langs/de-DE/
- web/apps/web-antd/src/locales/langs/en-US/
- any i18n/locale file where `workspace.loading.processing` or dashboard calendar labels are defined

Before coding:
1. Read AGENTS.md.
2. Inspect how `CustomerDashboardTab.vue` passes the loading label to `DashboardCalendarPanel`.
3. Inspect how `views/sicherplan/dashboard/index.vue` currently passes `loading-label`.
4. Find out why `$t('workspace.loading.processing')` is rendered as the raw key on the Dashboard page.
5. Do not change backend APIs.
6. Do not change calendar loading logic or data fetching.
7. This is only an i18n/text fix.

Required fix:
1. The Dashboard calendar loading indicator must not display `workspace.loading.processing`.
2. Use a translated label that exists in the i18n namespace used by the Dashboard page.
3. Prefer one of these safe solutions:
   - Add a Dashboard-specific key, for example:
     `sicherplan.dashboardView.calendar.loading`
   - Or use an existing correctly translated dashboard/calendar loading key if one already exists.
4. Suggested translations:
   - de-DE: `Anfrage wird verarbeitet`
   - en-US: `Processing request`
5. Update `views/sicherplan/dashboard/index.vue` to pass the correct translated key to `DashboardCalendarPanel`, for example:
   `:loading-label="$t('sicherplan.dashboardView.calendar.loading')"`
6. Do not break the Customers calendar behavior.
7. Do not hardcode English or German directly in the Vue template.

Tests:
Update or add the smallest relevant frontend test.

Suggested test files to inspect:
- web/apps/web-antd/src/views/sicherplan/dashboard/index.test.ts
- web/apps/web-antd/src/components/sicherplan/dashboard-calendar-panel.test.ts

Required test coverage:
1. Dashboard calendar loading indicator renders a human-readable translated label.
2. Dashboard calendar does not render the raw text `workspace.loading.processing`.
3. `DashboardCalendarPanel` still accepts and displays the provided loading label.
4. Customer calendar behavior is not changed.

Acceptance criteria:
- Main Dashboard calendar loading text is correct.
- No raw i18n key is visible.
- Customers calendar loading text remains correct.
- Frontend-only change.
- Tests pass.

Run:
cd web
pnpm test -- dashboard
pnpm test -- dashboard-calendar
pnpm lint
pnpm typecheck

If these exact scripts/filters do not exist, inspect package.json and run the closest existing web test/lint/typecheck commands.

Final response:
- Explain the root cause.
- List changed files.
- List tests run and results.
- Confirm no backend changes were made.
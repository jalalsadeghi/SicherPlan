Add/update regression tests for the Employee two-tab UI and one-page Overview refactor.

Files:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- employeeAdmin.layout.test.js
- EmployeeDashboardTab tests if present
- helper tests if section helpers are extracted

Required tests:

Test 1 — Existing employee shows only Dashboard and Overview top tabs
1. Mount EmployeeAdminView with an existing selected employee.
2. Assert top-level detail tabs include:
   - Dashboard
   - Overview
3. Assert top-level detail tabs do NOT include:
   - App access
   - Profile photo
   - Qualifications
   - Credentials
   - Availability
   - Private profile
   - Addresses
   - Absences
   - Notes
   - Groups
   - Documents
4. Assert Dashboard is first and Overview is second.

Test 2 — Create employee mode still only shows Overview
1. Click Create employee file.
2. Assert only Overview tab is visible.
3. Assert Dashboard is not visible.
4. Assert create employee form remains visible and usable.

Test 3 — Overview one-page nav renders
1. Select existing employee.
2. Click Overview.
3. Assert employee-overview-onepage exists.
4. Assert employee-overview-section-nav exists.
5. Assert nav items exist for:
   - Employee file
   - App access
   - Qualifications
   - Credentials
   - Availability
   - Notes
   - Groups
   - Documents
6. If canReadPrivate=true, assert nav also includes:
   - Private profile
   - Addresses
   - Absences
7. If canReadPrivate=false, assert those private sections are not rendered.

Test 4 — Overview section cards render
1. Click Overview.
2. Assert top-level section cards exist:
   - employee-overview-section-file
   - employee-overview-section-app-access
   - employee-overview-section-qualifications
   - employee-overview-section-credentials
   - employee-overview-section-availability
   - employee-overview-section-notes
   - employee-overview-section-groups
   - employee-overview-section-documents
3. Assert private cards render only with permission.
4. Assert each card has a clear heading.

Test 5 — Nav click scrolls to section
1. Mock/spy on scrollIntoView.
2. Click Addresses nav item.
3. Assert activeOverviewSection = addresses.
4. Assert activeDetailTab remains overview.
5. Assert scrollIntoView called for the addresses section.

Test 6 — Old tab id normalizes to Overview section
1. Simulate activeDetailTab = 'qualifications'.
2. Trigger normalization/watch.
3. Assert activeDetailTab becomes overview.
4. Assert activeOverviewSection becomes qualifications.
5. Assert no blank panel.

Repeat for:
- app_access
- credentials
- availability
- private_profile
- addresses
- absences
- notes
- groups
- documents

Test 7 — Functionality still works inside Overview sections
Test at least one action per category:
- save employee overview file
- create/update app access user, if permission fixture supports it
- create qualification
- create credential
- create availability rule
- save private profile
- save address
- create absence
- create note
- create group/membership
- upload/link document

If full action coverage is too large, assert existing tests were updated to find these controls inside Overview section cards.

Test 8 — Intro-only boxes removed
1. Click Overview.
2. Assert redundant intro-only headings/text are not rendered as separate boxes:
   - Structured employee file intro-only box
   - App access intro-only box
   - HR private profile intro-only box
   - other pure explanatory top blocks
3. Do not assert removal of functional section headings.

Test 9 — No excessive nested cards for field groups
1. Click Overview.
2. Assert each former tab is one top-level card.
3. Assert inner groups use flat subsection classes, not repeated nested boxed card classes.
4. Snapshot/class test is acceptable; no pixel-perfect requirement.

Test 10 — Dashboard unaffected
1. Click Dashboard.
2. Assert employee dashboard hero, assignment contexts, and calendar still render.
3. Assert photo upload behavior still works if recently implemented.

Commands:
- pnpm --dir web/apps/web-antd exec vitest run src/sicherplan-legacy/features/employees/employeeAdmin.layout.test.js
- pnpm --dir web/apps/web-antd exec vitest run <EmployeeAdminView tests>
- pnpm --dir web/apps/web-antd exec vitest run <EmployeeDashboardTab tests>
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- files changed
- tests added/updated
- commands run
- proof top-level tabs are only Dashboard and Overview
- proof create mode still only shows Overview
- proof former tabs are now Overview sections
- proof old functionality remains accessible.
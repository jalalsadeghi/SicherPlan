You are working in the latest SicherPlan repository.

Scope:
Fix two UI issues in the Employees admin page only.
Do not change backend behavior, API contracts, permissions, or business logic unless absolutely required for the frontend layout fix.
This is a focused UI/UX refinement task.

Target page:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Likely related test file:
- web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.layout.test.js

Context:
The Employees page currently has:
1. A left-side “List” panel containing both:
   - Search/filter form
   - Import / Export form
   in the same scrollable box
2. A feedback / alert box rendered after save, update, import, etc. through:
   - `feedback.message`
   - `.employee-admin-feedback`
This alert currently needs visual cleanup.

Task 1 — Put Search and Import/Export into tabs inside the List panel
Requirements:
- Keep the existing left-side List panel.
- Inside that panel, split the two areas into two tabs:
  - Tab 1: Search
  - Tab 2: Import / Export
- The Search tab should contain:
  - search input
  - status filter
  - default branch filter
  - default mandate filter
  - include archived checkbox
  - search button
  - create employee button
  - export button only if you decide it still belongs there; otherwise move export into Import / Export tab and keep it logically grouped
- The Import / Export tab should contain:
  - file input
  - load CSV
  - use template/reset template
  - CSV textarea
  - continue on error checkbox
  - validate import
  - run import
  - export controls if grouped there
  - dry-run / execute summaries
- Preserve current actions and handlers. This is a layout reorganization, not a workflow rewrite.
- Preserve entered form state when switching tabs. Do not reset search or import state just because the user changes tabs.
- Use the existing design language of the page:
  - pill/tab style similar to the employee detail tabs
  - clean spacing
  - no visual crowding
- Default open tab should be:
  - Search
- Keep the page responsive and consistent with the existing master-detail layout.

Task 2 — Fix the Alert / Feedback message styling
Requirements:
- Improve the visual style of the feedback area rendered when `feedback.message` exists.
- Make it look like a proper page-level status banner:
  - clear padding
  - rounded corners
  - readable text hierarchy
  - proper spacing between title, message, and dismiss button
  - consistent background/border per tone
- Support these tones cleanly:
  - success
  - error
  - neutral
- Ensure the banner:
  - does not look broken or collapsed
  - does not overflow awkwardly
  - aligns with the page content width
  - wraps correctly on smaller screens
  - keeps the dismiss button visually aligned
- Do not change the feedback logic itself unless necessary for class binding cleanup.

Implementation guidance:
- Keep changes local to the Employees page as much as possible.
- Reuse the existing tab styling pattern already used in the employee detail workspace if appropriate.
- Prefer small, maintainable refactoring over large rewrites.
- If needed, extract tiny computed helpers for tab labels/state, but do not over-engineer.
- Do not touch unrelated employee tabs such as Overview, App access, Profile photo, Notes, Groups, Addresses, Documents.

Testing:
Update or add frontend tests so they verify:
1. The left panel now has two tabs for Search and Import / Export
2. The relevant content switches by active tab
3. The alert/feedback container has stable markup/hooks for tone-based styling
4. Existing master-detail layout expectations still pass

Acceptance criteria:
- The left List panel contains two tabs: Search and Import / Export
- Search and Import / Export are no longer shown together in one long stacked block
- Form state is preserved when switching tabs
- The feedback/alert box has a clean, production-ready visual style
- No backend changes are required
- Existing employee page behavior still works

Before coding:
Briefly summarize:
1. impacted files
2. whether export stays in Search or moves to Import / Export
3. test changes

Then implement.
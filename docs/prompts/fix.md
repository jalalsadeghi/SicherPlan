You are working in the repository `jalalsadeghi/SicherPlan`.

Goal:
Improve the UI structure of the `admin/planning-orders` page so that the content inside the main `Planning records` tab is split into nested subtabs instead of rendering all planning-record sections in one long stacked block.

Current problem:
In `PlanningOrdersAdminView.vue`, the top-level order detail tabs already exist:
- overview
- commercial
- release
- documents
- planning_records

However, inside the `planning_records` tab, the selected planning record form is followed by:
- Commercial readiness
- Planning release
- Planning documents

These sections are currently rendered one below another, which makes the detail workspace crowded and hard to use.

Required UX target:
Inside the top-level `Planning records` tab, introduce a second-level tab system for the selected planning record, similar to the order-level detail tabs.

Nested planning-record tabs should be:
1. overview
2. commercial
3. release
4. documents

Behavior requirements:
- Keep the current master-detail layout.
- Keep the planning-record list visible at the top of the `Planning records` tab.
- Show the nested planning-record tabs only when:
  - a planning record is selected, or
  - a new planning record is being created.
- For a new unsaved planning record, show only the nested `overview` tab.
- For an existing saved planning record, show:
  - overview
  - commercial
  - release
  - documents
- Preserve current API usage and backend contracts. This should be a frontend-only refactor unless a tiny test helper change is needed.
- Do NOT change the planning-record backend endpoints.
- Do NOT change business logic for saving, releasing, attachments, or commercial readiness. Only reorganize the rendering and state handling.

Files to inspect and modify:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts` (read only unless typing support is needed)
- `web/apps/web-antd/src/sicherplan-legacy/i18n/planningOrders.messages.ts` (or the equivalent messages file)
- add/update a frontend test if the repo already has view/layout tests for this page

Implementation guidance:
1. Add a new state variable for nested planning tabs, for example:
   - `activePlanningDetailTab`
2. Add a computed tab list for planning-record detail, for example:
   - always `overview`
   - plus `commercial`, `release`, `documents` when the selected planning record already exists
3. Inside the existing top-level `planning_records` tab panel:
   - keep the header and planning-record list
   - keep the New planning button
   - insert a nested tab bar below the list/header and above the planning-record form/sections
4. Move current planning-record sections into nested panels:
   - form + mode details => nested `overview`
   - commercial readiness => nested `commercial`
   - planning release actions => nested `release`
   - planning documents upload/link/list => nested `documents`
5. Reuse the current tab styling if possible.
   - If needed, add a second-level modifier class such as:
     - `planning-orders-tabs planning-orders-tabs--nested`
     - `planning-orders-tab planning-orders-tab--nested`
6. Preserve existing `data-testid` values where possible, and add new ones for nested tabs:
   - `planning-records-tab-overview`
   - `planning-records-tab-commercial`
   - `planning-records-tab-release`
   - `planning-records-tab-documents`
   - matching tab panels as well
7. Reset nested tab state safely:
   - when switching to a different planning record, default to nested `overview`
   - when starting `New planning`, default to nested `overview`
   - when the selected planning record is cleared, do not leave a stale nested tab selected
8. Keep accessibility:
   - nested `<nav>` with clear aria-label like `Planning record detail sections`
   - buttons remain keyboard accessible

Acceptance criteria:
- Inside the main `Planning records` tab, the planning-record detail no longer appears as one long stacked block.
- Existing planning records show nested tabs for overview/commercial/release/documents.
- New planning records show only the overview tab until first save.
- No backend behavior changes.
- Save/release/document/commercial actions still work exactly as before.

Output format:
- Short summary of the UI problem
- Files changed
- Explanation of the nested-tab state model
- Note whether any tests were added or updated
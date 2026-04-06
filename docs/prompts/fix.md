You are working in the SicherPlan repository.

Goal
----
Fix a frontend layout/styling regression in the Planning master-data page for trade fairs.

Observed bug
------------
In `PlanningOpsAdminView.vue`, the page looks correct before selecting a trade fair.
After selecting a trade fair record such as `FAIR-001`, the left "Browse records" panel no longer stays pinned to the top, the `Filter records` / `CSV import` tab buttons look visually wrong, and the `planning-admin-list` container becomes unnaturally squared/stretched.

Scope
-----
Frontend only. Do not change backend code.

Primary file
------------
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`

Related reference
-----------------
- `web/apps/web-antd/src/sicherplan-legacy/components/shared/InternalCardTabs.vue`

Diagnosis
---------
This is a layout issue in the page-level CSS, triggered only after a record is selected and the detail pane becomes much taller.

In `PlanningOpsAdminView.vue`:
- `.planning-admin-grid` is a CSS grid container but does not explicitly set `align-items: start`.
- `.planning-admin-panel` and `.planning-admin-list` are grid containers, but they also do not explicitly pin content to the top with `align-content: start`.
- When the detail column grows after selecting a trade fair, the left panel stretches to the row height and its inner grid content is distributed/stretched, which makes:
  - the browse panel appear vertically displaced,
  - the tab strip look off,
  - and the list area / single selected record look blocky or squared.

What to change
--------------
Apply a minimal, targeted CSS fix in `PlanningOpsAdminView.vue` so that:
1. The two-column grid aligns panels at the top instead of stretching them vertically.
2. The left browse panel keeps its natural height/content flow after a record is selected.
3. The record list keeps a natural stacked layout and does not visually stretch when there is only one item.
4. Existing mobile behavior remains intact.

Recommended implementation direction
------------------------------------
In the scoped `<style>` block of `PlanningOpsAdminView.vue`:

- Update `.planning-admin-grid` to explicitly align items to the start:
  - `align-items: start;`

- Ensure the left browse panel and generic panel grids do not distribute content vertically:
  - add `align-content: start;` to `.planning-admin-list-panel`
  - optionally also add `align-content: start;` to `.planning-admin-panel` if needed, but do not break the detail pane

- Ensure `.planning-admin-list` does not stretch its rows unnaturally:
  - add `align-content: start;`
  - add `grid-auto-rows: max-content;`

- Preserve the existing rounded/pill appearance of `InternalCardTabs`; do not rewrite `InternalCardTabs.vue` unless strictly necessary.

Important constraints
---------------------
- Keep the fix localized to this view unless a shared style bug is proven.
- Do not regress the selected detail view, the trade-fair zones section, or the patrol checkpoints section.
- Do not remove the existing responsive breakpoint behavior.
- Do not introduce hardcoded heights.

Acceptance criteria
-------------------
- Before selection: page still looks unchanged and correct.
- After selecting a trade fair record:
  - the left "Browse records" panel remains top-aligned,
  - `Filter records` and `CSV import` keep their intended pill/tab styling,
  - the browse list remains visually natural and does not become squared/stretched,
  - the detail pane still expands normally.
- Mobile layout under the existing media query still works.

Deliverable
-----------
Make the code change and provide a concise summary of:
- the root cause,
- the exact CSS selectors changed,
- and why the fix only appeared after selecting a record.
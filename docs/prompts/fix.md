You are working in the SicherPlan repository.

Goal:
Clean up duplicated/low-value black section titles in the Staffing Coverage page.

User-visible page:
admin/planning-staffing

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue

Tests to inspect/update:
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts

Current issue:
Three cards show a green eyebrow/title and then repeat the same text again in black underneath. This creates visual clutter.

Required changes:

1. Filter und Scope card
- Remove the black title/text:
  "Filter und Scope"
- Also remove the black role/tenant line:
  "Rolle: tenant_admin · Mandant: ..."
- Keep the green eyebrow/title:
  "FILTER UND SCOPE"

2. Schicht-Coverage card
- Remove the black repeated title:
  "Schicht-Coverage"
- Keep the green eyebrow/title:
  "SCHICHT-COVERAGE"

3. Schichtdetails card
- Remove the black repeated title:
  "Schichtdetails"
- Keep the green eyebrow/title:
  "SCHICHTDETAILS"

Important:
- Do not remove the actual content, filters, counters, list, empty states, selected shift detail, tabs, or actions.
- Do not change backend APIs.
- Do not change data loading, filtering, staffing commands, or permissions.
- This is only a frontend template cleanup.

Implementation guidance:
- In `PlanningStaffingCoverageView.vue`, inspect the panel headers around:
  - `tp("filtersTitle")`
  - `tp("listTitle")`
  - `tp("detailTitle")`
- These likely render both:
  - `<p class="eyebrow">...</p>`
  - `<h3>...</h3>`
- For the three named panels, keep only the eyebrow and remove the redundant black `<h3>` / lead text.
- If the detail header uses the black `<h3>` to show selected shift context, preserve selected shift context elsewhere if needed, but do not show repeated "Schichtdetails" when no shift is selected.
- Make the smallest safe change.

Tests:
Update tests only if they assert the duplicated black titles or role/tenant line.

Acceptance criteria:
- The three panels keep their green eyebrow labels.
- The duplicate black labels are gone.
- The role/tenant line under Filter und Scope is gone.
- Staffing page layout and functionality are unchanged.
- Existing tests pass.

Run:
cd web
pnpm test -- planningStaffing
pnpm lint
pnpm typecheck

If these exact commands are not available, inspect package.json and run the closest existing web test/lint/typecheck commands.

Final response:
- Summarize the template cleanup.
- List changed files.
- List tests run and results.
- Confirm this was frontend-only.
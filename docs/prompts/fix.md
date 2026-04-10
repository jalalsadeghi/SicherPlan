You are working in the latest SicherPlan repository state.

Goal:
Refine the UI of `/admin/planning-staffing` so the page becomes cleaner and visually consistent, without removing the real P-04 staffing functionality.

Before coding:
1. Read `AGENTS.md` and keep the change narrow.
2. Inspect these files first:
   - `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
   - `web/apps/web-antd/src/views/sicherplan/module-registry.ts`
   - the module shell / wrapper file that renders the extra `Workspace` section for admin modules
   - `web/apps/web-antd/src/router/routes/modules/sicherplan.ts`
   - `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
3. Verify the currently rendered strings/areas:
   - top box headed by `Staffing validations`
   - outer wrapper box headed by `Workspace`
   - the `Filters and scope` panel

Business constraint:
P-04 must remain a real staffing board and coverage workspace.
Do NOT remove actual staffing functionality such as:
- shift coverage list
- demand groups
- assignments
- staffing assign / unassign / substitute actions
- shift/assignment validation logic
- override flow
- coverage summary
Only remove or restyle non-essential UI chrome.

Required changes:
A. Remove the top decorative hero block from `PlanningStaffingCoverageView.vue`, including the box headed by `Staffing validations` and the nested session/scope promo box.
   - Keep functional feedback/error messaging if it is still useful.
   - Do NOT remove the real validation panels inside the selected shift / selected assignment detail area.

B. Remove the extra `Workspace` box/header for `/admin/planning-staffing`.
   - Prefer a clean module-shell configuration fix over CSS hacks.
   - If this comes from module config, update the planning-staffing module entry accordingly.
   - Scope this change to this page only; do not accidentally affect unrelated modules.

C. Improve `Filters and scope` styling so it looks like a finished admin form card.
   At minimum:
   - clear card structure and spacing
   - consistent header/body layout
   - styled labels
   - styled inputs/selects/textarea/checkbox
   - proper padding, borders, radii, focus states, and vertical rhythm
   - clean responsive grid behavior
   - alignment consistent with the rest of the page

D. Audit the whole `/admin/planning-staffing` page for visual consistency and tighten styles where needed:
   - summary cards
   - list/detail card spacing
   - selected row state
   - CTA rows and wrapping
   - empty-state spacing
   - subpanel spacing
   - mobile/tablet breakpoints
Do not redesign the whole module; keep it consistent with the existing SicherPlan admin style.

E. Keep backend/API behavior unchanged unless a compile/runtime issue requires a tiny compatibility fix.

Implementation guidance:
- First identify whether the `Workspace` title/description comes from the module shell, module registry config, or page composition.
- First identify whether `Staffing validations` is part of the page’s top hero section or a deeper functional section.
- Remove only the decorative top-level version.
- For the filter panel, prefer real component/page styling improvements instead of hiding defects with one-off margins.
- If there are shared utility classes for admin forms/cards in the repo, reuse them.
- Avoid `display: none` hacks unless there is no cleaner page-scoped option.

Validation requirements:
1. `/admin/planning-staffing` must no longer show:
   - the top `Staffing validations` box
   - the extra `Workspace` wrapper box/header
2. The page must still show and preserve:
   - filters
   - coverage summary
   - shift list
   - shift detail
   - demand groups
   - assignments
   - real validation/override functionality in the detail area
3. `Filters and scope` must look intentionally styled and visually consistent.
4. Route and module registration must still work.
5. Run relevant checks available in the repo:
   - typecheck
   - lint
   - focused tests if present
   - build or page smoke validation if available

Self-check before finalizing:
- Confirm you did NOT remove the actual validation logic required by P-04.
- Confirm you removed only the decorative `Staffing validations` hero box.
- Confirm the extra `Workspace` wrapper is gone because of a proper config/composition fix, not a brittle hack.
- Confirm the filter area now has proper visual styling.
- Confirm no unrelated admin modules were changed unintentionally.

Final response format:
1. Short summary
2. Exact files changed
3. What caused the `Workspace` box
4. What caused the `Staffing validations` box
5. What styling improvements were made
6. What checks you ran
7. Self-validation result
You are working in the SicherPlan repository.

Goal:
Change the `Default planning mode` field in the Planning Setup create/edit form
(`/admin/planning`, requirement type editor) from a free textbox to a constrained select
with the correct canonical planning-mode options.

This is a focused UI + validation alignment fix.
Do not broaden scope into unrelated planning refactors.

Before coding:
1. Read `AGENTS.md`.
2. Keep the change set narrow to the Planning Setup form and related API/UI validation.
3. Verify the current repo state first.

Files to inspect first:
Frontend:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningAdmin.helpers.js`
- `web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts`
- any planning setup tests

Backend contract confirmation:
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/router.py`
- any planning service validation if relevant

Source-of-truth constraints:
- `ops.requirement_type` includes `default_planning_mode_code`
- The documented planning modes are limited to:
  - `event`
  - `site`
  - `trade_fair`
  - `patrol`
- The planning record later uses planning modes aligned with:
  - event planning
  - object/site planning
  - trade fair planning
  - patrol/route planning
- Therefore free text for `default_planning_mode_code` is too loose and can create invalid downstream values.

What you must verify first:
1. The current Planning Setup UI renders `Default planning mode` as a plain input/textbox.
2. This field belongs to the `requirement_type` record family specifically.
3. The current backend schema uses a string type, but product/docs constrain the valid business values.
4. The downstream planning model is built around only the four canonical planning modes above.

Required outcome:
A. Replace the free textbox for `Default planning mode` with a select for `requirement_type`.
B. Use canonical backend values exactly:
   - `event`
   - `site`
   - `trade_fair`
   - `patrol`
C. Use readable UI labels, for example:
   - Event
   - Object / Site
   - Trade Fair
   - Patrol / Route
D. Show this field only when it is relevant to the `requirement_type` editor state.
E. Preserve create and edit flows for existing requirement types.
F. Add frontend validation so invalid arbitrary planning-mode strings can no longer be entered from the UI.
G. Keep auth/session/tenant scope unchanged.

Recommended implementation details:
1. Add a shared options constant/helper for planning mode choices in the planning admin frontend.
2. Bind the select to `default_planning_mode_code`.
3. If editing an older record with an unknown/noncanonical stored value:
   - do not crash
   - surface a safe fallback state
   - ideally show the current value and prompt correction, or map it only if there is an explicit safe mapping
4. Update labels/help text to make clear that this is the default mode used when requirement types feed downstream planning.

Validation/tests to add or update:
1. `Default planning mode` renders as a select for requirement types.
2. The select exposes exactly the four canonical values.
3. Create requirement type submits the correct backend value.
4. Edit requirement type preserves and updates the correct backend value.
5. Other planning setup record families are not incorrectly forced to show this field.
6. Unknown legacy value handling does not break the form.

What not to do:
- Do not leave this as a textbox.
- Do not invent additional planning modes not supported by the documented model.
- Do not rename backend values away from the canonical codes.
- Do not refactor unrelated planning setup sections.

Final response format:
1. Short diagnosis
2. Exact repo state found
3. Exact files changed
4. Final option set used for `default_planning_mode_code`
5. How legacy/unknown values are handled
6. Tests/validation run and results
7. Remaining assumptions
8. Self-validation summary

Extra instruction:
Challenge your own solution before finalizing.
Specifically verify:
- the field is no longer free text
- the values match the documented planning modes exactly
- downstream create/edit still works for requirement types
If any of those fail, the fix is incomplete.
You are working in the public repo `jalalsadeghi/SicherPlan`.

Important working-mode rule:
Treat the current local working tree as the source of truth.
The public `main` repo still shows an older subcontractor UI, but the current local working tree already contains a `Create address` control in Subcontractors → Overview.
Do NOT ignore the local implementation state.
Inspect the live working tree first, then fix the broken behavior and layout.

Task:
Fix the `Create address` behavior and layout in `/admin/subcontractors` → `Overview`.

Reported problems:
1. Clicking `Create address` currently does nothing.
2. The layout should be improved so that:
   - `Primary address` becomes slightly narrower
   - `Create address` sits beside it
   - together, both controls occupy roughly the current width of the existing `Primary address` field
   - the form layout stays clean and aligned

Business context:
Subcontractor master data should support a real address workflow.
A dead `Create address` button is misleading and must be fixed.
The address UX should also remain visually tidy and practical for operator data entry.

What to inspect first:
1. The current LOCAL working tree version of:
   - `web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue`
2. Any newly added local state / methods / modal code related to:
   - `Create address`
   - address selection
   - primary address
3. Existing address-management patterns already implemented elsewhere in the app, especially:
   - employee address handling in `EmployeeAdminView.vue`
   - any customer or other address editor/modal patterns
4. Current subcontractor API support:
   - whether a real address create/link flow already exists in the current repo or local working tree
   - whether the button is intended to open a modal/editor/select flow

Critical rule:
Do NOT leave the button as a dead control.
If the backend/local API support exists, wire it fully.
If support does NOT exist yet, the button must not remain clickable without action.
In that fallback case, replace it with the safest temporary behavior:
- disabled with explanation
or
- hidden
But only if real implementation is impossible in the current working tree.

Preferred implementation direction:
A. Functional fix
- Make `Create address` actually open the intended address creation flow
- Prefer reusing an existing address editor pattern already present in the project
- If employee/customer address editor exists and is suitable, adapt/reuse it
- On successful address creation, make sure the new address becomes available to the subcontractor form and can be used as the primary address

B. Layout fix
- Create a local layout wrapper specifically for:
  - `Primary address`
  - `Create address`
- Do NOT hack global form spacing
- Use a small grid/flex layout so:
  - the address field takes most of the width
  - the button takes the remaining width
  - together they visually match one normal wide field row
- Keep it responsive and clean on narrower screens

Expected UX result:
- Clicking `Create address` produces a visible action
- The user can create/select an address without confusion
- The overview form remains visually balanced
- `Primary address` + `Create address` appear as one coherent input/action row

Important constraints:
- Do NOT redesign the whole Overview form
- Do NOT make raw `address_id` entry the main UX if a better address flow is already intended
- Keep the patch focused on the address control and its layout
- Reuse existing project patterns where possible

Validation requirements:
After implementing, verify:
1. `Create address` no longer does nothing
2. Clicking it opens the intended address flow
3. The resulting address can populate or link back into the subcontractor overview form
4. `Primary address` and `Create address` now sit side-by-side cleanly
5. The layout does not break the rest of the form
6. Responsive layout remains acceptable

Testing requirements:
Add or update focused tests for the subcontractor overview address controls.
At minimum verify:
1. the `Create address` button is wired to a real action
2. clicking it opens the modal/editor/flow
3. successful address creation updates the overview form state
4. the new address row wrapper/class exists and is scoped locally
5. no regression to other overview fields

Acceptance criteria:
- `Create address` is functional
- the layout is visually correct
- the patch is local and maintainable
- dead UI behavior is removed

At the end, provide a concise validation report with these headings:
1. Why the button was non-functional
2. Which files were changed
3. What address flow is now triggered
4. How the overview form receives the created address
5. How the `Primary address` + `Create address` layout was fixed
6. Which tests were updated or added
7. Any remaining address-management limitations you recommend addressing next

Before coding, explicitly answer:
- What exact local code currently renders the `Create address` button?
- Why does its click currently do nothing?
- Is there already a reusable address editor flow in the codebase, or must one be extracted/adapted?
Then implement the safest fix.
You are working in the LOCAL working tree of `jalalsadeghi/SicherPlan`.

Task:
Fix the `Operational scope` form in `/admin/subcontractors` → `Scope Release` so that:
- `Branch`
- `Mandate`
are rendered as proper select controls, not raw textboxes.

Why this is needed:
- In the current Subcontractors Scope form, `branch_id` and `mandate_id` are exposed as text inputs.
- These are reference/entity ids, not user-friendly free-text fields.
- Elsewhere in the project, the same kind of data is already handled correctly as selects (for example in Employee admin for branch/mandate).

Important rule:
Do NOT hardcode branch or mandate options.
Use the real branch/mandate source already available in the project.

What to inspect first:
1. The LOCAL working-tree version of:
   - `web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue`
2. The current subcontractor scope API contract:
   - `web/apps/web-antd/src/sicherplan-legacy/api/subcontractors.ts`
3. Existing working branch/mandate selection patterns elsewhere in the app, especially:
   - `web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue`
4. Any shared branch/mandate loaders/helpers already used there, such as:
   - branch list loading
   - mandate list loading
   - mandate filtering by selected branch
   - structure-label formatting

Required implementation:
1. Replace the raw `Branch` textbox with a select control backed by real branch options
2. Replace the raw `Mandate` textbox with a select control backed by real mandate options
3. Load the available branch/mandate options from the existing source already used in the app
4. Keep the submitted payload unchanged:
   - still submit `branch_id`
   - still submit `mandate_id`
5. Preserve edit mode:
   - existing saved values must be shown correctly
6. Filter mandate options by selected branch if that is the existing app pattern
7. If the selected branch changes and the current mandate is no longer valid, clear the mandate safely
8. If lookup loading fails, show a safe empty/disabled state rather than a broken control

Preferred implementation strategy:
A. Reuse the Employee/Admin branch+mandate loading pattern
- do not invent a second inconsistent implementation
- reuse or extract common helpers if needed

B. Keep the change local
- only fix the subcontractor scope controls and minimal supporting lookup state
- do not redesign the entire page

C. UX consistency
- branch select should show user-friendly labels
- mandate select should show user-friendly labels
- mandate select should behave consistently with selected branch context

Important constraints:
- Do NOT change backend API contracts
- Do NOT fall back to raw textboxes
- Do NOT hardcode fake options
- Keep the patch focused and maintainable

Testing requirements:
Add/update tests to verify:
1. `Branch` is no longer rendered as a textbox in the subcontractor scope form
2. `Mandate` is no longer rendered as a textbox in the subcontractor scope form
3. both fields render as selects
4. selecting a branch updates `scopeDraft.branch_id`
5. selecting a mandate updates `scopeDraft.mandate_id`
6. mandate options are filtered by branch if that behavior is implemented
7. existing saved scope values still render correctly in edit mode
8. save payload still submits the correct ids

Acceptance criteria:
- Branch and Mandate in Subcontractors → Scope Release → Operational scope are now selects
- They use real project data sources
- The UX is no longer raw-id based
- Existing create/edit scope behavior remains intact

At the end, provide a concise validation report with these headings:
1. What was wrong before
2. Which file(s) were changed
3. Which branch/mandate source was reused
4. How the two fields now behave in create/edit mode
5. Whether mandate filtering by branch was implemented
6. Which tests were updated or added

Before coding, explicitly answer:
- Where is the existing branch/mandate select pattern already implemented in the repo?
- Which source provides the branch and mandate options there?
- Can that same source be reused directly in Subcontractors?
Then implement the safest consistent fix.
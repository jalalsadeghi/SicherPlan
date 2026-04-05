You are working in the public repository jalalsadeghi/SicherPlan.

Goal:
Audit and standardize the "Create a new record" experience in the Planning Setup admin page (admin/planning), implemented in the legacy Vben web app. The target page is the P-01 Planning Setup workspace, not Orders/Planning Records, Shift Planning, or Staffing Coverage.

Primary file to inspect:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue

Also inspect any related files that drive this page, especially under:
- web/apps/web-antd/src/sicherplan-legacy/features/planning/
- web/apps/web-antd/src/sicherplan-legacy/components/
- web/apps/web-antd/src/sicherplan-legacy/api/
- web/apps/web-antd/src/sicherplan-legacy/i18n/
- any existing tests for admin workspace layout / create flows

Reference UX pattern:
- Use the same admin workspace pattern already used by the other legacy admin pages such as EmployeeAdminView and CustomerAdminView:
  - list/search panel on the left
  - detail/editor panel on the right
  - create/edit mode clearly visible
  - save/cancel actions always obvious
  - no child-resource editing before the parent record exists
  - only show fields relevant to the selected record type

Important domain rule:
This page is P-01 Planning Setup and must support multiple planning setup record families with entity-specific forms:
- requirement type
- equipment item
- site
- event venue
- trade fair
- trade fair zone
- patrol route
- patrol checkpoint

Problem to fix:
The current "Create a new record" flow in the Detail view is not sufficiently standardized unless it behaves like a proper entity-aware admin editor. Fix the page so that the create-new experience is consistent, safe, and aligned with the documented planning model.

Implement these requirements:

1) Create mode architecture
- When the user clicks "Create a new record", open a clean draft detail editor in the right-hand detail panel.
- Show a clear create mode state in the header, e.g. "New record" + selected record family.
- Add explicit Save and Cancel actions.
- Add dirty-state handling so unsaved edits are not silently lost.
- Do not show update-only actions in create mode.

2) Entity-aware create flow
- Add a record-family selector at the start of create mode, OR separate create actions that directly open the correct schema.
- The detail form must switch schema based on record family.
- Never use one generic flat form for all planning setup entities.

3) Field grouping and visibility
Use clear sections and only show the fields relevant to the selected entity.

Expected minimum behavior by entity:

A. Requirement type
- code
- label
- default_planning_mode_code
- status
- notes (optional)

B. Equipment item
- code
- label
- unit_of_measure_code
- status
- notes (optional)

C. Site
- site_no
- customer_id
- name
- address fields or address picker
- latitude / longitude where available
- timezone
- watchbook_enabled
- status if supported

D. Event venue
- venue_no
- customer_id
- name
- address fields or address picker
- latitude / longitude
- status if supported

E. Trade fair
- fair_no
- customer_id
- name
- address fields or address picker
- start_date
- end_date
- status if supported

F. Trade fair zone
- trade_fair_id (required parent)
- zone_type_code
- zone_code
- label
- notes (optional)

G. Patrol route
- route_no
- customer_id
- site_id (optional)
- name
- start_point_text
- end_point_text
- travel_policy_code
- status

H. Patrol checkpoint
- patrol_route_id (required parent)
- sequence_no
- checkpoint_code
- label
- latitude / longitude
- scan_type_code
- expected_token
- min_dwell_seconds
- notes (optional)

4) Parent-child safety
- A trade fair zone must not be creatable without a selected/saved parent trade fair.
- A patrol checkpoint must not be creatable without a selected/saved parent patrol route.
- In create mode, if the selected entity is a child entity, require parent selection first.
- If parent selection is impossible in the current context, disable Save and show a clear validation message.

5) Save lifecycle
- On first save, call the correct create endpoint for the selected entity type.
- After successful save:
  - switch the editor from create mode to edit mode
  - keep the saved record selected in the list
  - enable any valid post-save sections or actions
- Child collections, location projection panels, and dependent read-only cards must remain hidden or disabled until the parent record exists.

6) Validation
Implement explicit client-side validation before submit:
- required code/identifier fields
- required label/name fields
- start_date <= end_date for trade fair
- positive / sensible checkpoint sequence and dwell values
- required parent references for zone/checkpoint
- no invalid mixed field submissions from other entity types

7) UX consistency
- Keep the page consistent with the rest of the legacy admin workspace design.
- Avoid mixing P-01 data with P-02/P-03/P-04 concepts.
- Do not expose release-state, shift-visibility, dispatch, staffing, or actuals controls in this page.
- Keep labels and helper text consistent with existing i18n patterns.
- Preserve tenant-scoped and role-scoped behavior.

8) Technical cleanup
- Extract entity-specific form schemas/config into a planning form config/composable instead of keeping a giant conditional template in one file.
- Remove dead or duplicated create-form code paths if they exist.
- Keep the implementation readable and testable.

9) Tests
Add or update tests covering:
- create requirement type
- create equipment item
- create site
- create trade fair with date validation
- block zone creation without parent trade fair
- block checkpoint creation without parent route
- hide post-save-only sections during initial create mode
- save success switches to edit mode and keeps selection stable
- cancel create resets draft state cleanly

10) Deliverables
Return:
- the code changes
- the tests
- a short summary of what was fixed
- a short list of any assumptions or follow-up gaps

Constraints:
- Stay within the current web app architecture.
- Prefer minimal, focused refactoring over broad unrelated rewrites.
- Do not change behavior of P-02, P-03, or P-04 while fixing P-01.
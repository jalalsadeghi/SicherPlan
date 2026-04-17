You are working in the public repo `jalalsadeghi/SicherPlan`.

Task:
Add a `Pick location on map` capability to `/admin/subcontractors` → `Overview`, for the `latitude` and `longitude` fields, by reusing the same map-picking UX/pattern already available in the Planning area.

Important working-mode rule:
Do NOT invent a second unrelated map picker if the project already has one in Planning.
First locate the existing planning implementation and reuse it.
If it is not yet reusable, extract it into a shared component/composable and then integrate it into Subcontractors.

Current known facts:
- In `SubcontractorAdminView.vue`, the Overview form currently exposes:
  - `latitude`
  - `longitude`
  as manual number inputs only
- The subcontractor API model already supports `latitude` and `longitude`
- So this feature should mainly be a frontend UX enhancement, not a backend redesign

Files to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue`
2. `web/apps/web-antd/src/sicherplan-legacy/api/subcontractors.ts`
3. The Planning page(s) where the existing `Pick location on map` workflow already works
   - find the exact implementation in the current repo
   - identify whether it is:
     - a shared component
     - a local modal implementation
     - a composable
     - a third-party wrapper already in use

Required implementation goal:
In Subcontractors → Overview:
1. Add a clear action/button near the latitude/longitude fields:
   - e.g. `Pick location on map`
2. Clicking it should open a dialog/modal with the same map-based location picking experience already used in Planning
3. Selecting a location on the map should populate:
   - `latitude`
   - `longitude`
4. Manual editing of latitude/longitude must still remain possible
5. Reopening the map should initialize from the current lat/lng if available
6. Canceling the dialog must not change the current form values

Important UX and scope rules:
- This is a lat/lng picker, not full address management
- Do NOT pretend the address workflow is solved by this feature
- Do NOT require `address_id` to be valid before using the map picker
- Keep the current Overview form otherwise intact unless a tiny layout adjustment is needed

Preferred implementation strategy:
A. Find and reuse the existing planning map picker
- If there is already a reusable component, use it directly
- If the planning implementation is embedded in a planning-only view, extract the map dialog/picker into a shared component

B. Wire it to subcontractor draft state
- Use `subcontractorDraft.latitude`
- Use `subcontractorDraft.longitude`
- Keep string/number conversion safe and explicit

C. Initialization behavior
- If both lat/lng are already present, center marker on that location
- Otherwise use the same default behavior already used in Planning
- Do not introduce a different map default unless truly necessary

D. Confirm/apply behavior
- On confirm, write selected coordinates back into the overview form fields
- Prefer preserving the current field format used by the form/API payload builder

E. Keep backend untouched unless absolutely necessary
- Since API already accepts latitude/longitude, do not add backend changes unless the current map picker requires a tiny helper contract (unlikely)

Important constraints:
- Do NOT duplicate map libraries or add a second map stack if one already exists
- Do NOT redesign Subcontractor Overview broadly
- Do NOT mix this with unresolved address-tab work
- Keep the patch focused and reusable

Validation requirements:
After implementing, verify:
1. Overview shows a `Pick location on map` action
2. Clicking it opens the map dialog
3. Choosing a point fills latitude and longitude
4. Existing lat/lng values are respected when reopening
5. Cancel leaves existing values unchanged
6. Manual lat/lng editing still works
7. Subcontractor save still submits correct lat/lng values

Testing requirements:
Add/update focused tests.
At minimum verify:
1. the new map-picker action is rendered in Subcontractor Overview
2. opening the picker updates the draft on confirm
3. cancel leaves the draft unchanged
4. existing lat/lng values are passed into the picker initialization if present
5. no regression to subcontractor save behavior

If the current repo has no existing subcontractor view test file, add a focused smoke/behavior test near the subcontractor admin view.
Avoid brittle pixel/CSS tests.

Acceptance criteria:
- Subcontractors Overview now has the same practical map-picking convenience already available in Planning
- The implementation reuses or extracts the existing planning map picker instead of duplicating it
- Latitude/longitude entry becomes much easier for operators
- Backend contract remains stable

At the end, provide a concise validation report with these headings:
1. Where the existing planning map picker was found
2. Whether it was reused directly or extracted into a shared component
3. Which files were changed
4. How Subcontractor Overview now integrates the picker
5. How lat/lng values are initialized and saved
6. Which tests were updated or added
7. Any remaining address-management limitations that were intentionally left out of scope

Before coding, explicitly answer:
- Where exactly is the current Planning map picker implemented?
- Can it be reused directly, or must it be extracted first?
- Does the Subcontractor API already support lat/lng without backend changes?
Then implement the safest reusable solution.
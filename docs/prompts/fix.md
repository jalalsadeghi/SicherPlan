You are working in the latest public SicherPlan repository.

Context:
The issue happens in the customer order workspace on the route:
customers/order-workspace?customer_id=<id>
step = planning-record-overview

Observed behavior:
In the "Planning record" step, the section "Existing planning records" shows an already available planning record.
When the user clicks one of these existing planning-record options:
- the selected record is eventually applied correctly,
- the editor is populated correctly for editing,
- BUT the page visibly refreshes / remounts once before returning to the same state.

Goal:
Optimize this interaction so that selecting an existing planning record:
1) selects the clicked record immediately,
2) loads its values into the planning-record editor,
3) preserves the correct route/query state if needed,
4) does NOT cause a visible page refresh, hard reload, or unnecessary full remount.

Important:
Do not assume the cause.
Validate the actual root cause first.

Possible root-cause areas to inspect:
- click handler using href/full navigation instead of controlled state update
- router push/replace behavior that remounts the page
- route query sync that changes the page key
- parent component keyed by route.fullPath or order/planning-record query params
- watcher side effects that retrigger bootstrap load
- selection logic that clears and rehydrates the entire step instead of patching editor state
- global "load current step from route" logic that reruns as if entering the page fresh
- forced refresh after selecting an existing planning record to reuse old loading code

Required investigation before coding:
1) Find the exact component tree for:
   - the planning-orders workspace view
   - the order workspace stepper / step container
   - the "Planning record" step
   - the "Existing planning records" selectable list/card
   - the planning-record editor state/model
2) Identify how selection of an existing planning record currently works:
   - local state only
   - route query update
   - store update
   - fetch + re-bootstrap
3) Identify exactly why the visible refresh happens:
   - full browser reload
   - route remount
   - page-level reload state
   - component key invalidation
   - redundant async bootstrap cycle

Required fix:
- Replace the current selection flow with an in-place state update flow.
- Selecting an existing planning record should patch/update the editor state directly without causing full page remount.
- If route query synchronization is required, keep it minimal and non-disruptive.
- If the selected planning record id must be reflected in the URL, do it in a way that does not visually reload the page.
- Preserve current successful behavior:
  - selected item remains visibly selected
  - editor fields are populated correctly
  - unsaved editor state handling remains safe
  - step progression logic still works

Technical guidance:
- Prefer a local/editor-state update or controlled store update over full reinitialization.
- If the root cause is route-key remounting, narrow the key so selection does not recreate the whole page.
- If the root cause is query synchronization, use the least disruptive router update possible.
- If the root cause is a shared bootstrap watcher, separate “initial page load” from “editor selection change”.
- Avoid backend changes unless absolutely necessary and justified.
- Keep changes scoped to this planning-record step and directly related helpers/state/components.

Validation requirement:
Please validate my suggestion critically.
If my assumption about the cause is wrong, fix the true cause and explain it clearly.
Do not ship a cosmetic workaround.
Do not just hide the refresh with loading masks.
The goal is to remove the unnecessary remount/reload behavior itself.

Manual scenarios you must test in code logic:
1) initial entry into the Planning record step
2) click an existing planning record once
3) click another existing planning record
4) click the same existing planning record again
5) create-new mode then switch back to an existing record
6) edit fields after selecting an existing record
7) navigate to next step and back
8) reload the route with planning-record-related query params already present
9) verify no regression in selected-card styling, editor hydration, and next/previous navigation

Deliverables:
1) Apply the fix.
2) Summarize:
   - changed files
   - exact root cause
   - why the page refresh/remount happened
   - how the final solution avoids it
3) Mention whether URL/query synchronization was preserved, changed, or reduced.
4) Mention any remaining edge case if one still exists.

Acceptance criteria:
- Clicking an item in "Existing planning records" updates selection and editor data in place.
- No visible page refresh/remount occurs during that selection.
- The selected record remains selected.
- The editor still shows the correct planning-record data.
- No regression in step navigation, validation, or editor behavior.
- No unrelated pages changed.
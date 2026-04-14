You are working in the public repo `jalalsadeghi/SicherPlan`.

Task:
Fix the missing `Sort Order` field in the "Create demand group" / "Edit demand group" modal of the Staffing Coverage page and validate whether demand groups are actually ordered by that value.

Context:
- Route/page: `/admin/planning-staffing`
- Current view file:
  `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`
- Current API client file:
  `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- Current smoke test file:
  `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningStaffing.smoke.test.ts`

Observed inconsistency:
- The demand-group modal UI currently renders:
  - function_type_id
  - qualification_type_id
  - min_qty
  - target_qty
  - mandatory_flag
  - remark
- But the implementation already carries `sort_order` in the current contract:
  - `DemandGroupRead.sort_order`
  - `DemandGroupCreate.sort_order?`
  - `DemandGroupUpdate.sort_order?`
- The view state also already contains:
  - `demandGroupDraft.sort_order = 100`
  - reset logic restores it to 100
  - edit logic loads it from an existing demand group
  - submit logic sends it in create/update payloads
- Therefore the form is currently incomplete: the field exists in the implementation contract but is not exposed in the modal.

Important design guidance:
- Treat `sort_order` as an implementation/UI ordering field, not as a replacement for core demand-group semantics.
- Keep the existing behavior and payload contract unless inspection proves the current repo has intentionally deprecated the field.
- Do not guess. Inspect first.

What to do:
1. Inspect the current demand-group modal in `PlanningStaffingCoverageView.vue`.
2. Add a numeric input for `sort_order` to both create and edit flows.
3. Bind it to `demandGroupDraft.sort_order`.
4. Keep the default value at `100`, matching the current draft/reset behavior.
5. Validate it as an integer, preferably `>= 0`.
6. Ensure create and update continue to send `sort_order` in the payload.
7. Add a short field help text explaining that it controls the ordering of demand groups in staffing views/outputs.
8. Inspect whether the UI currently displays demand groups in stable sort order.
   - If backend already returns them sorted, document that and do not duplicate sorting unnecessarily.
   - If backend ordering is not guaranteed, apply a safe frontend sort by:
     1. `sort_order` ascending
     2. function label/code
     3. id as final fallback
9. Verify the same ordering logic is used consistently wherever demand groups are rendered or selected in this page.
10. Update or add tests in `planningStaffing.smoke.test.ts` to cover:
    - default `sort_order` value
    - visible field in create modal
    - visible field in edit modal
    - submitted create payload contains edited `sort_order`
    - submitted update payload contains edited `sort_order`
    - rendered demand-group order respects `sort_order` if frontend fallback sorting is needed

Acceptance criteria:
- The demand-group modal visibly contains a `Sort Order` field.
- A user can create a demand group with:
  - Function Type: SHIFT_SUP
  - Qualification Type: empty
  - Min Qty: 1
  - Target Qty: 1
  - Mandatory Flag: true
  - Sort Order: 100
  - Remark: Shift supervisor coverage for Objekt Süd day shift.
- Edit mode shows the current `sort_order` of an existing demand group.
- Create/update payloads include `sort_order`.
- The page uses deterministic ordering for demand groups.
- No regression to existing demand-group create/update behavior.

Implementation constraints:
- Keep the change minimal and consistent with the existing SicherPlan/Vben styling and form patterns.
- Reuse the existing modal, grid, field-stack, and CTA styles.
- Do not introduce a breaking API change.
- Do not remove `sort_order` from the contract unless you can prove from the inspected repo that the field is obsolete everywhere and update all dependent code/tests accordingly.

Required validation report at the end:
Provide a concise report with these headings:
1. What was inconsistent
2. Which files were changed
3. Why exposing `sort_order` is correct for the current repo
4. Whether backend already guarantees ordering or frontend fallback sorting was added
5. Which tests were updated or added
6. Any remaining mismatch between design docs and implementation
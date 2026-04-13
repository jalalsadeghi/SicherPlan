You are working in the SicherPlan monorepo on the latest main branch.

Task:
Fix the duplicate-validation logic for Planning -> admin/planning-orders -> Orders & planning -> Requirement lines.

Current broken behavior:
The UI blocks creation of a second active requirement line in the same order when the `requirement_type_id` is the same, even if `function_type_id` and `qualification_type_id` are different.

Concrete real-world example that should be allowed:
Existing line:
- Requirement Type: OBJECT_GUARD
- Function Type: SEC_GUARD
- Qualification Type: G34A
- Min Qty: 2
- Target Qty: 2

New line the user is trying to add:
- Requirement Type: OBJECT_GUARD
- Function Type: SHIFT_SUP
- Qualification Type: FIRST_AID
- Min Qty: 1
- Target Qty: 1

Current UI error:
"An active requirement line for this requirement type already exists in this order."

Why this looks wrong:
- The backend model for `order_requirement_line` includes:
  - `requirement_type_id`
  - `function_type_id`
  - `qualification_type_id`
- The backend schemas also include those fields.
- The frontend API type `OrderRequirementLineRead` includes those fields.
- But the frontend duplicate guard appears to check only `requirement_type_id`.

Files to inspect first:
Frontend
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningOrders.helpers.js`
- `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningOrders.helpers.test.js`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts`

Backend
- `backend/app/modules/planning/models.py`
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/order_service.py`
- `backend/app/modules/planning/repository.py`
- any backend tests for customer orders / requirement lines

Your job:
1. Validate the real intended uniqueness rule for order requirement lines.
2. Fix the bug so that multiple active requirement lines with the same `requirement_type_id` are allowed when their staffing profile differs.
3. Make frontend and backend behavior consistent.

Validation rule to test explicitly:
Determine whether uniqueness should be based on:
A. `requirement_type_id` only  ❌ likely wrong
B. tuple of (`requirement_type_id`, `function_type_id`, `qualification_type_id`) ✅ likely correct
C. no duplicate rule at all
You must validate and justify the choice.

Preferred outcome unless validation disproves it:
- Allow multiple active requirement lines for the same `requirement_type_id`
- Block only exact active duplicates of the same staffing tuple:
  (`requirement_type_id`, `function_type_id`, `qualification_type_id`)
- Treat archived lines as non-blocking
- Preserve edit behavior for the currently selected line

Important implementation guidance:
A. Fix the frontend duplicate guard in `planningOrders.helpers.js`.
B. Update helper tests accordingly.
C. Check whether backend currently enforces no uniqueness at all.
D. If backend does not enforce the intended tuple rule, add the smallest correct backend validation so the API and UI stay consistent.
E. Be careful with nullable `function_type_id` / `qualification_type_id`.
   Two lines should count as exact duplicates only if all three tuple values match after normalization, including null handling.
F. Do not block valid combinations that differ in function or qualification.

Acceptance criteria:
1. The user can create both of these lines in the same order:
   - OBJECT_GUARD + SEC_GUARD + G34A
   - OBJECT_GUARD + SHIFT_SUP + FIRST_AID
2. The UI no longer throws the old error for that case.
3. Exact duplicate active tuples are handled consistently according to the final validated rule.
4. Archived lines do not block creation.
5. Editing an existing line does not falsely trip duplicate validation against itself.
6. Frontend and backend rules are aligned.

Tests to add/update:
- frontend helper test proving same requirement type with different function/qualification is allowed
- frontend helper test proving exact active duplicate tuple is blocked if that is the chosen rule
- backend test for create/update behavior of requirement lines under the validated uniqueness rule
- compatibility test for archived lines and self-edit scenarios

What not to do:
- Do not keep the duplicate rule based only on `requirement_type_id`
- Do not remove the duplicate rule entirely without validating whether exact tuple duplicates should still be blocked
- Do not change unrelated order/planning behavior
- Do not make function/qualification required unless the domain already requires them

Required output:
1. Confirmed intended uniqueness rule
2. Root cause
3. Files changed
4. Exact fix made
5. Null-handling / archived-line handling
6. Tests added/updated
7. Final self-check confirming you validated the proposal instead of assuming it
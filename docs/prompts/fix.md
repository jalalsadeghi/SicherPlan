You are working in the repository `jalalsadeghi/SicherPlan`.

Problem:
On `admin/planning-orders`, the `Dispatcher` select inside the `Planning records for order` form does not reliably show the current tenant-scoped authenticated admin user, even when the user is logged in as Tenant Admin. The Dispatcher dropdown should be populated from tenant IAM users, not from planning setup master data.

Relevant files to inspect:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts`
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/planning_record_service.py`
- `backend/app/modules/planning/repository.py`
- any IAM models/services/routes involved in tenant user creation and role assignment
- tests under `backend/tests/modules/planning/` and any relevant frontend tests

Observed current behavior from repo:
- Frontend loads dispatcher options via `listPlanningDispatcherCandidates(...)`
- API endpoint is `/api/planning/tenants/{tenant_id}/ops/planning-records/dispatcher-candidates`
- Backend repository currently filters candidates to tenant users with:
  - same `tenant_id`
  - active/non-archived `UserAccount`
  - active/non-archived `UserRoleAssignment`
  - scope_type in (`tenant`, `branch`, `mandate`)
  - role key in (`platform_admin`, `tenant_admin`, `dispatcher`, `controller_qm`, `accounting`)

Goal:
Make the Dispatcher selector robust and predictable so that a valid current Tenant Admin user is selectable without requiring any planning-side manual setup.

Tasks:
1. Verify the current end-to-end data flow for Dispatcher candidates:
   - frontend select
   - frontend API helper
   - planning router endpoint
   - planning record service
   - repository query

2. Fix the likely failure cases:
   A. If the current authenticated tenant admin is missing because the repository query is too restrictive, adjust the query safely.
   B. If the current authenticated tenant admin exists in session/auth context but is absent from the candidate API result due to IAM bootstrap gaps, add a safe fallback path so the current user can still appear as a selectable candidate when:
      - they belong to the same tenant
      - their session is valid
      - they hold a planning-relevant admin/operator role
   C. Do NOT expose users from other tenants.
   D. Do NOT expose inactive or archived users.

3. Improve frontend behavior:
   - If the candidate list is empty, show a clear inline hint that Dispatcher values come from tenant IAM users.
   - If the current authenticated user is valid and present, optionally preselect them when creating a new planning record and `dispatcher_user_id` is empty.
   - If the API fails, keep the field usable with a clear error state and avoid silent failure.

4. Improve backend/API behavior:
   - Keep `dispatcher-candidates` tenant-safe.
   - Ensure the response contains enough label information for the select (`full_name`, `username`, `email`, `role_keys`).
   - If appropriate, add a dedicated helper that validates whether a session user is eligible as a dispatcher candidate.

5. Add/update tests:
   - candidate list includes active tenant admin users
   - candidate list excludes other tenants
   - candidate list excludes archived/inactive users
   - current tenant admin appears when valid
   - frontend shows the IAM hint when no candidates exist
   - optional auto-default to current user works only for new records

6. UX copy requirement:
   Add a short helper text near Dispatcher similar to:
   “Dispatcher options come from Tenant Users & IAM. Create or activate a tenant-scoped admin/dispatcher user there.”

Constraints:
- Do not invent unrelated new modules.
- Do not move Dispatcher creation into Planning Setup.
- Preserve tenant isolation and auditability.
- Prefer minimal, focused changes.
- Keep coding style consistent with the repo.

Deliverables:
- Short summary of root cause
- Changed files list
- Explanation of whether the fix was data-only, backend, frontend, or mixed
- Notes about any remaining IAM bootstrap limitation
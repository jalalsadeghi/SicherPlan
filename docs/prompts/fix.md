You are working in the SicherPlan monorepo.

Goal:
Fix the missing admin-side employee address entry/edit flow in the current Employees workspace.

Context:
- The current admin route for employee management is the Employees workspace mounted from the SicherPlan web shell. The module registry shows the employees admin surface is registered in the current web app and routed through the admin shell.
- The documented canonical workspace is E-01 — Employees Workspace, and its scope explicitly includes employee addresses/address history.
- Backend/admin API already exists for employee addresses:
  - GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/addresses
  - POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/addresses
  - PATCH /api/employees/tenants/{tenant_id}/employees/{employee_id}/addresses/{history_id}
- A separate self-service endpoint also exists:
  - POST /api/employee-self-service/me/current-address
  This self-service endpoint must NOT be used for the tenant-admin workflow.
- Data model expectation:
  - hr.employee_address_history stores address history
  - linked to common.address
  - fields conceptually include address_id, valid_from, valid_to, is_current
  - overlapping active/current windows should be prevented

Current bug:
In /admin/employees, the Addresses section only shows a passive timeline/empty-state text like:
- “Current address history”
- “Released address timeline”
- “No released address history is available.”
There is no usable admin form/action to create or update an employee address from the canonical Employees workspace.

What to do:
1. Locate the current Employees admin view and all related address subcomponents, composables, stores, and API client code.
2. Implement proper admin-side address CRUD inside the employee detail/editor area.
3. Add clear actions such as:
   - Add address
   - Edit address
   - Mark as current
   - Close current validity / set valid_to
4. Use the existing admin employee-address endpoints only.
5. Replace misleading employee-address copy like “Released address timeline” with employee-specific wording such as:
   - “Address history”
   - “Current and past employee addresses”
   - “No address history is available”
6. The form should support at minimum:
   - line1
   - line2
   - postal_code
   - city
   - state_region
   - country_code
   - valid_from
   - valid_to
   - is_current
   Only include additional fields if they are already supported by the backend contract.
7. After save/update, refresh the employee address timeline from the GET endpoint and render it chronologically.
8. Surface validation errors clearly in the UI.
9. Prevent overlapping current/active address windows client-side where practical, but also preserve backend validation as source of truth.
10. Keep employee self-service current-address behavior unchanged.
11. Add/update tests for:
   - creating the first employee address
   - editing an existing history row
   - showing empty state when no addresses exist
   - showing the new address immediately after save
   - preventing invalid overlapping current periods
12. Follow existing project patterns for:
   - API client structure
   - optimistic updates / refetch
   - form validation
   - i18n keys
   - role-scoped admin UI

Acceptance criteria:
- A Tenant Administrator can create an employee address directly from /admin/employees.
- The saved address appears in the employee address history/timeline immediately after save.
- Existing address history rows can be edited through the admin UI.
- The empty state is shown only when there are truly no address records.
- The admin UI uses admin endpoints, not self-service endpoints.
- Copy/labels for the Addresses section are employee-specific and no longer misleading.

Important:
- Prefer a UI fix first. Do not redesign backend contracts unless the current backend contract is genuinely insufficient.
- If backend payload shape is unclear, inspect the existing request/response models and align the UI to the current contract instead of inventing a new one.
- Keep changes minimal, coherent, and production-ready.
- At the end, provide:
  1. changed files
  2. short explanation of root cause
  3. test coverage added
  4. any backend follow-up only if strictly necessary
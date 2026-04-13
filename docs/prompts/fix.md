You are working on the SicherPlan repo.

Task:
Fix the empty "Marital status" select in Employees > Private profile.

Observed problem:
The UI now renders Marital status as a select, but the dropdown contains only the placeholder:
"Select marital status"
and no actual options.

Important:
Do NOT patch this by hardcoding frontend-only options unless you prove there is no validated backend source.
First validate the real root cause.

Source-of-truth to respect:
1. The implementation-oriented model expects a code-based private-profile field for marital status, not unrestricted free text.
2. The platform’s general modeling rule prefers lookup-backed business lists through core.lookup_value.
3. HR/private-profile fields must stay role-restricted.
4. The UI should show readable labels, but save the code.

Phase A — Validation first
Inspect the actual checked-out code and determine exactly why the select options are empty.

Validate all of the following:

1. Frontend
- Find the exact select control in EmployeeAdminView.vue or the real component currently used.
- Find how marital-status options are loaded:
  - on mount?
  - on employee selection?
  - on opening private profile?
- Find the API function used by the frontend to fetch options.
- Check the expected response shape in the frontend mapping.

2. Backend
- Find the route for marital-status options, if present.
- Find the service/repository query that returns lookup options.
- Validate whether the query is incorrectly filtering only by tenant_id and therefore excluding system lookup rows.
- Validate whether the domain name is exactly marital_status.
- Validate whether the endpoint is returning:
  - []
  - wrong shape
  - wrong labels
  - authorization error swallowed by frontend
  - 404 due to route mismatch

3. Data layer
- Check whether lookup seed/backfill actually inserted marital_status rows into the running DB.
- Confirm whether marital_status is intended as:
  - system lookup domain (tenant_id null), or
  - tenant-specific domain
- If it is system-owned, confirm the query includes system rows and optional tenant overrides correctly.
- Check whether dev/test/bootstrap/startup/onboarding actually runs the seed logic for this domain.

4. Runtime verification
- Verify the actual network request from frontend to backend.
- Verify the actual backend response payload.
- Verify the actual DB rows for domain marital_status.

Before coding, print a short validation summary with:
- exact frontend file(s)
- exact backend file(s)
- exact route/path
- actual response payload
- whether the problem is:
  a) empty DB seed
  b) wrong lookup query scope
  c) frontend mapping mismatch
  d) route mismatch / old backend running
  e) authorization issue
  f) some combination

Most likely root causes to explicitly test:
1. system lookup rows exist, but backend query filters only tenant_id = current tenant and ignores system rows
2. marital_status seed exists in code, but seed/backfill never ran against the active database
3. frontend expects a different response shape than the backend returns

Phase B — Fix the root cause properly

Required fix rules:
1. Keep Marital status as a select.
2. Do not revert to textbox.
3. Use backend-backed options as source of truth.
4. Save marital_status_code, not label text.
5. Preserve HR/private-profile permission restrictions.

If the issue is wrong lookup query scope:
- fix the query so system rows are included
- if tenant overrides are supported, merge tenant-specific rows over system defaults in a deterministic way
- keep sort_order stable

If the issue is missing seed/backfill:
- implement the smallest safe idempotent fix so existing environments get marital_status rows
- do not rely on “fresh DB only” behavior
- make sure the solution works for already-running local environments too

If the issue is frontend mapping mismatch:
- fix the response adapter only
- do not duplicate the source of truth
- keep labels readable and values code-based

If the issue is route mismatch:
- align frontend and backend on one canonical path
- remove dead/unused wiring

Testing requirements:
Add/update focused tests for:
1. marital-status options endpoint returns expected rows
2. system lookup rows are returned correctly even when tenant_id is present in request context
3. select renders real options in Employee private profile
4. saved payload uses marital_status_code
5. existing private-profile permissions remain enforced

Manual verification required:
After the fix, verify:
1. Open /admin/employees
2. Open Private profile
3. Open Marital status select
4. Confirm these options are visible with readable labels:
   - single
   - married
   - separated
   - divorced
   - widowed
   - civil_partnership
   or the exact validated approved set from backend
5. Save one value
6. Reopen and confirm round-trip persistence

Output format:
1. Validation summary first
2. Then implementation
3. Then final report with:
   - root cause
   - changed files
   - DB/seed impact
   - API response before/after
   - frontend behavior before/after
   - exact manual test result

Acceptance criteria:
- The Marital status select is populated with real options.
- The options come from the validated backend source of truth.
- The UI stores code, not label.
- No frontend-only hardcoded workaround is introduced unless explicitly justified and approved as temporary.
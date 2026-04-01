You are working in the SicherPlan repository.

Goal:
Fix the deployed-environment issue where the Employees workspace still shows empty Function Type and Qualification Type dropdowns for existing tenants after a normal code-only deployment.

Observed production behavior:
- The Employees UI now correctly shows empty-state hints:
  - “No function types are configured for this tenant yet.”
  - “No qualification types are configured for this tenant yet.”
- This means the frontend is working as designed and the backend catalog endpoints are returning empty arrays for that tenant.

Confirmed repo facts:
1. The Employees UI loads catalog data from backend APIs and disables the dropdown when the arrays are empty:
   - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   - web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts

2. Tenant baseline HR catalogs are provisioned automatically only during tenant onboarding:
   - backend/app/modules/core/admin_repository.py
   via seed_baseline_employee_catalogs(...)

3. Existing tenants can be backfilled manually with:
   - backend/scripts/seed_go_live_configuration.py
   which calls seed_baseline_employee_catalogs(...)

4. The HR baseline definitions live in:
   - backend/app/modules/employees/catalog_seed.py

Problem to solve:
A normal GitHub Action / CI-CD deployment updates application code, but existing tenants that were created before this baseline logic still remain empty unless an operator manually runs the seed script.

Required outcome:
Introduce a production-safe, explicit, idempotent post-deploy/backfill mechanism so existing deployed tenants can receive missing baseline HR catalogs without changing normal read endpoints and without relying on dev/test bootstrap.

What to implement:
1. Add an operator-safe backfill path for existing tenants in deployment/rollout automation.
   Preferred options:
   - a deploy script step
   - a dedicated post-deploy command
   - a CI/CD workflow step guarded by explicit env vars / inputs
   Do NOT add hidden request-time auto-seeding to the list endpoints.

2. Keep behavior production-safe and explicit:
   - do not seed all tenants accidentally
   - require either:
     a) a specific tenant id
     or
     b) an explicit opt-in flag for all active tenants
   - make the action idempotent

3. Add or improve a script that can be used in deployment automation.
   If backend/scripts/seed_go_live_configuration.py is already sufficient, reuse it.
   If it needs enhancement, improve it carefully.
   Good options:
   - support `--tenant-id <uuid>`
   - optionally support `--all-tenants` only with strong explicit confirmation
   - clear console output for inserted/updated counts

4. Update deployment docs or workflow docs so operators know:
   - code deploy alone is not enough for old tenants
   - how to run the backfill safely
   - when it is required

5. If this repository already contains GitHub Actions deployment workflows, update them only in a safe and optional way:
   - no dangerous auto-backfill by default
   - use workflow_dispatch input or protected env var such as:
     - RUN_HR_BASELINE_BACKFILL=true
     - HR_BASELINE_TENANT_ID=<uuid>
   - fail clearly if the flag is enabled but required inputs are missing

6. Add tests where appropriate:
   - script/service idempotency for repeated backfill
   - existing tenant with missing catalogs receives baseline rows
   - tenant with existing customized rows is not duplicated or clobbered
   - no change to read endpoint semantics

7. Preserve these constraints:
   - no auto-seeding inside GET catalog endpoints
   - keep dev/test bootstrap behavior unchanged
   - keep onboarding behavior unchanged
   - keep Employees UI empty-state behavior unchanged

Desired deliverables:
- implementation
- tests
- rollout notes
- exact operator command examples for deployed environments

Implementation notes:
- Treat this as a rollout/backfill problem, not a frontend rendering bug.
- Prefer explicit operational control over hidden side effects.
- Keep changes focused and production-safe.

Please return:
1. Root-cause summary
2. Chosen rollout/backfill design
3. Exact files changed
4. How operators should run it in deployed environments
5. Any caveats
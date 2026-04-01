You are working in the SicherPlan repository.

Goal:
Fix the production/deployed issue where the Function Type and Qualification Type dropdowns in the Employees workspace are empty for a tenant, while they are populated in local development.

Observed behavior:
- In local, the Employees page shows seeded sample values for:
  - Function types: SEC_GUARD, SHIFT_SUP, DISPATCH, FIRE_WATCH
  - Qualification types: G34A, FIRST_AID, FIRE_SAFETY, CROWD_CONTROL
- In the deployed environment, the same dropdowns are empty.
- The Employees UI loads these values from backend APIs, so the issue is data/bootstrap/setup-related, not a simple frontend rendering issue.

Confirmed repo evidence:
1. The Employees UI loads function and qualification options from backend:
   - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   - web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
   The relevant APIs are:
   - GET /api/employees/tenants/{tenant_id}/employees/catalog/function-types
   - GET /api/employees/tenants/{tenant_id}/employees/catalog/qualification-types

2. Local sample values come from:
   - backend/app/modules/employees/catalog_seed.py

3. The repo explicitly documents that this bootstrap is only for development/test and must not be relied on in production:
   - docs/configuration/hr-catalog-bootstrap.md

4. There is already a dev/test-only bootstrap endpoint in the employee router, but it is intentionally restricted outside development/test:
   - backend/app/modules/employees/router.py

Problem to solve:
Make tenant-owned HR catalogs available in production-safe deployments without relying on the dev/test bootstrap flow.

Required outcome:
A newly deployed or newly onboarded tenant must have usable baseline:
- hr.function_type
- hr.qualification_type
records, so the Employees workspace dropdowns are not empty.

Implement the fix with the most production-safe design possible.

Required design direction:
1. Do NOT rely on the existing dev/test-only bootstrap endpoint for production.
2. Keep the existing dev/test bootstrap for local/test convenience.
3. Add a proper production-safe initialization path for baseline HR catalogs.

Preferred implementation approach:
Implement tenant baseline catalog provisioning as part of tenant initialization / onboarding, with an idempotent service-level seed path.
The system should ensure that a tenant can receive baseline HR catalogs in a controlled way without duplicate rows.

Detailed tasks:
1. Identify the best production-safe integration point for baseline HR catalog provisioning.
   Prefer one of:
   - tenant onboarding flow
   - baseline tenant setup workflow
   - an explicit tenant initialization service used during onboarding
   Avoid hidden request-time auto-seeding during normal list endpoints unless there is a very strong repo-consistent reason.

2. Extract or refactor the HR catalog seed definitions if needed so they can be reused safely by:
   - existing dev/test bootstrap
   - production-safe onboarding initialization
   Keep the code DRY and small.
   If you split data definitions from the current dev/test helper, preserve current local behavior.

3. Make the production-safe seeding idempotent:
   - no duplicate codes per tenant
   - re-runs must be safe
   - archived/inactive baseline rows should be handled intentionally and consistently
   - do not overwrite tenant-customized labels/descriptions blindly unless clearly justified
   Prefer:
   - “insert missing defaults”
   over
   - “force-reset all catalog rows”

4. Ensure the following baseline records exist for a tenant after initialization:

   Function types:
   - SEC_GUARD / Security agent
   - SHIFT_SUP / Shift supervisor
   - DISPATCH / Dispatch support
   - FIRE_WATCH / Fire watch

   Qualification types:
   - G34A / 34a certified
   - FIRST_AID / First aid
   - FIRE_SAFETY / Fire safety
   - CROWD_CONTROL / Crowd control

5. Add tests that prove the production-safe path works.
   At minimum:
   - tenant initialization or onboarding creates missing baseline function types
   - tenant initialization or onboarding creates missing baseline qualification types
   - running initialization twice does not duplicate rows
   - existing tenant custom rows are not duplicated or unintentionally destroyed
   - the Employees catalog list endpoints return non-empty data for a newly initialized tenant

6. Preserve current local/dev/test behavior:
   - the explicit dev/test bootstrap endpoint must continue to work
   - existing docs/configuration/hr-catalog-bootstrap.md intent must remain true
   - do not silently make the dev/test-only endpoint available in production

7. Improve operational clarity in the UI:
   - when function/qualification APIs return empty arrays, show a clear empty-state hint instead of a silent blank dropdown
   - example message:
     “No function types are configured for this tenant yet.”
     “No qualification types are configured for this tenant yet.”
   - keep this lightweight and consistent with the current Employees workspace UX
   - do not fake client-side options

8. Update or add documentation:
   - explain how production-safe tenant baseline HR catalogs are provisioned
   - explain the difference between:
     a) baseline production tenant initialization
     b) dev/test bootstrap convenience flow

Constraints:
- Keep API paths unchanged unless absolutely necessary.
- Do not break existing Employees page behavior.
- Do not introduce production magic that seeds data on every read request.
- Prefer explicit, auditable initialization over hidden lazy side effects.
- Follow repository conventions and keep the fix focused.
- Avoid unrelated refactors.

Please do the implementation and then report back with:
1. Root cause summary
2. Chosen production-safe initialization point and why
3. Exact files changed
4. Test coverage added/updated
5. Any migration or rollout note operators should know
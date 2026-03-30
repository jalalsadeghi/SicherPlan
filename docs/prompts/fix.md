You are working in the SicherPlan repository.

Task title:
Fix empty Customer Overview metadata dropdowns for Classification, Ranking, and Customer status metadata.

Problem:
In /admin/customers -> Overview tab, these dropdowns are empty and show only "Not set":
- Classification
- Ranking
- Customer status metadata

Root cause already identified from current code:
- CustomerService.get_reference_data() loads these fields from tenant-scoped lookup domains:
  - classification_lookup_id -> customer_category
  - ranking_lookup_id -> customer_ranking
  - customer_status_lookup_id -> customer_status
- These three domains are tenant-extensible and require tenant-specific seed data.
- Legal form is visible because it is seeded as a global/system domain.
- The repository returns lookup values for tenant_id in (None, tenant_id), so global legal forms appear, but tenant-specific customer metadata domains do not appear unless seeded for the current tenant.

Relevant files to inspect:
- backend/app/modules/customers/service.py
- backend/app/modules/customers/repository.py
- backend/app/modules/core/lookup_seed.py
- backend/scripts/seed_lookup_values.py
- docs/engineering/lookup-seeding.md
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/customers.ts
- related i18n files
- relevant tests

Goal:
Make Classification, Ranking, and Customer status metadata reliably available in dev/test environments, and improve the user experience when tenant lookup seeds are missing.

Scope of work:

A) Backend / bootstrap
1. Keep the current architecture:
   - customer_category, customer_ranking, customer_status remain tenant-extensible lookup domains
   - do NOT convert them into global/system domains
   - do NOT hardcode them in frontend

2. Improve tenant bootstrap so that in dev/test/demo flows these three domains are seeded automatically or through a clearly documented and integrated setup path.

3. Preferred solution:
   - integrate tenant lookup seeding into the existing dev/bootstrap flow for a tenant
   - do not require developers to manually discover and run a separate script for basic CRM customer onboarding
   - keep production-safe behavior; do not silently seed arbitrary tenant data in production request paths

4. If there is already a tenant initialization/bootstrap path in the repo, hook into that path instead of inventing a new one.

5. Ensure these seed values exist for the tenant:
   Domain: customer_category
   - standard / Standardkunde
   - key_account / Schluesselkunde
   - prospect / Interessent

   Domain: customer_ranking
   - a / A-Kunde
   - b / B-Kunde
   - c / C-Kunde

   Domain: customer_status
   - qualified / Qualifiziert
   - on_hold / Pausiert
   - blocked / Gesperrt

6. Seeding must be idempotent and must not create duplicates.

B) Documentation
7. Update docs/engineering/lookup-seeding.md so it correctly documents:
   - customer_category
   - customer_ranking
   - customer_status
as tenant-extensible domains needed by the Customer Overview form.
8. Add a short note that if these dropdowns are empty, tenant lookup seeds are missing.

C) Frontend UX
9. In CustomerAdminView.vue, improve the empty-state UX for these three fields:
   - if option list is empty, do not just show a blank dropdown with "Not set"
   - add a small contextual help text below the field explaining that tenant CRM metadata catalogs are not seeded yet
   - if practical, add a lightweight warning banner in the Overview form when one or more of these option lists are empty

10. Do NOT hardcode fallback options in frontend.
11. Do NOT fake dropdown values from local constants.

D) Optional improvement
12. If feasible and consistent with the repo architecture, expose a small diagnostic in the reference-data response or frontend state indicating which lookup domains are empty, so the UI can show targeted help.

E) Tests
13. Add/update backend tests to verify:
   - tenant lookup seeding creates the required rows for customer_category, customer_ranking, customer_status
   - seeding is idempotent
   - get_reference_data() returns those rows for the tenant

14. Add/update frontend tests to verify:
   - populated reference data renders non-empty dropdown options
   - empty reference data shows the new help text / warning state
   - no frontend hardcoded fallback values are introduced

Hard constraints:
- Keep these domains tenant-extensible
- Do not turn them into global/system domains
- Do not hardcode CRM metadata options in frontend
- Do not change payload field names
- Do not break existing legal_form behavior
- Keep the solution production-safe

Acceptance criteria:
- In a properly bootstrapped dev/test tenant, Classification, Ranking, and Customer status metadata dropdowns are populated.
- The seed mechanism is idempotent.
- The docs correctly explain the dependency on tenant lookup seeds.
- When seeds are missing, the UI gives a clear explanation instead of silently showing only "Not set".

Before coding:
Provide a short plan listing:
- which files you will modify
- where tenant seeding will be integrated
- how production safety will be preserved

After coding:
Provide:
1. files changed
2. seed/bootstrap strategy
3. doc updates
4. UI empty-state improvements
5. test evidence
6. any follow-up items
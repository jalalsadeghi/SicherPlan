# SicherPlan RBAC Matrix

## Scope

This matrix consolidates the documented role model from:

- [AGENTS.md](/home/jey/Projects/SicherPlan/AGENTS.md)
- [authorization-and-scope-rules.md](/home/jey/Projects/SicherPlan/docs/engineering/authorization-and-scope-rules.md)
- [authentication-and-session-flows.md](/home/jey/Projects/SicherPlan/docs/engineering/authentication-and-session-flows.md)
- [sprint-02-platform-core-and-backbone.md](/home/jey/Projects/SicherPlan/docs/sprint/sprint-02-platform-core-and-backbone.md)
- [US-5-T1.md](/home/jey/Projects/SicherPlan/docs/prompts/US-5-T1.md)
- [US-35-T2.md](/home/jey/Projects/SicherPlan/docs/prompts/US-35-T2.md)

## Canonical Role Mapping

| Documented role | Implemented key | Status | Scope kind | Current permission baseline | Notes |
| --- | --- | --- | --- | --- | --- |
| Platform Administrator | `platform_admin` | implemented | platform + tenant-capable | broad admin, ops, field, finance, reporting | Over-broad compared with docs; can perform tenant operational work. |
| Tenant Administrator | `tenant_admin` | implemented | tenant | broad tenant admin, ops, field, finance, reporting | Over-broad; currently includes payroll and finance signoff. |
| Tenant Operator / Dispatcher | `dispatcher` | implemented | tenant, with object-level limits in some services | planning, field, actuals, some billing/control reads and writes | Closer to docs, but still crosses into finance write paths. |
| Tenant Accounting | `accounting` | implemented | tenant | finance-heavy plus customer billing read | Fits finance better than ops, but still lacks dedicated frontend route enforcement. |
| Tenant Controller / QM | `controller_qm` | implemented | tenant | reporting, watchbook review, actual read, info read/write | Partial implementation. Missing dedicated security/QM feature family and some documented journeys. |
| Customer User | `customer_user` | implemented | customer | portal access, info read, watchbook read | Customer scope depends on service-layer context resolution rather than route-level scope wiring. |
| Subcontractor Administrator | `subcontractor_user` | partial mapping | subcontractor | portal access, info read, watchbook read | No separate admin vs planner/operator split in IAM seed. |
| Subcontractor Planner / Operator | `subcontractor_user` | missing distinct role | subcontractor | same as above | Documentation expects a richer split than current seed. |
| Field Supervisor / Object or Event Lead | no dedicated key | missing distinct role | expected tenant/local operational scope | none | Current code sometimes treats `dispatcher` or `employee_user` as field actors. |
| Employee / Guard | `employee_user` | implemented | employee self / tenant portal | employee portal access, watchbook read/write, patrol read/write | Employee self-scope exists in services but no dedicated web route/home mapping beyond generic behavior. |

## Permission Families

Current seeded permission families from [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py):

- `core.admin.*`
- `platform.docs.*`
- `platform.comm.*`
- `platform.info.*`
- `platform.integration.*`
- `customers.customer.*`
- `customers.billing.*`
- `recruiting.applicant.*`
- `employees.employee.*`
- `employees.private.*`
- `planning.ops.*`
- `planning.order.*`
- `planning.record.*`
- `planning.shift.*`
- `planning.staffing.*`
- `field.watchbook.*`
- `field.attendance.*`
- `field.time_capture.*`
- `field.patrol.*`
- `finance.actual.*`
- `finance.approval.*`
- `finance.billing.*`
- `finance.subcontractor_control.*`
- `finance.payroll.*`
- `reporting.*`
- `subcontractors.company.*`
- `subcontractors.finance.*`
- `portal.customer.access`
- `portal.subcontractor.access`
- `portal.employee.access`

## Coverage Summary

Current seed counts:

- roles: `8`
- permissions: `70`

Portal roles are implemented as scoped actors inside a tenant, which matches the documented model. Distinct role keys for subcontractor planner/operator and field supervisor/event lead are not yet present.

## Scope Rules

Implemented scope types in [models.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/models.py):

- `tenant`
- `branch`
- `mandate`
- `customer`
- `subcontractor`

Current `require_authorization(...)` wiring in [authz.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/authz.py) actively enforces:

- `platform`
- `tenant`
- `branch`
- `mandate`
- `customer`
- `subcontractor`

Engineering guidance in [authorization-and-scope-rules.md](/home/jey/Projects/SicherPlan/docs/engineering/authorization-and-scope-rules.md) still says customer and subcontractor scopes were not yet wired during the Sprint 2 baseline, so later portal implementations have outgrown that older note.

## Current Baseline Decision

Use the following as the practical baseline for ongoing implementation work:

1. Keep `platform_admin`, `tenant_admin`, `dispatcher`, `accounting`, `controller_qm`, `customer_user`, `subcontractor_user`, and `employee_user` as the stable implemented keys.
2. Treat documented subcontractor-role splits and field-supervisor/event-lead roles as missing role-model extensions, not as aliases silently covered by current seeds.
3. Do not add more broad permissions to `platform_admin` or `tenant_admin`; future work should narrow them instead.
4. New frontend route work must stop relying on `ignoreAccess: true` for protected admin pages.

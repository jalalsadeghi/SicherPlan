## HR Catalog Bootstrap

Production-safe baseline HR catalogs are provisioned during tenant baseline initialization:

- core tenant onboarding through the Core admin onboarding flow
- explicit tenant baseline setup via `backend/scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>`

Code-only deployment does not retroactively backfill older tenants that were created before this baseline logic existed. For already deployed tenants, run an explicit backfill after deploy.

That baseline path inserts missing tenant-owned rows for:

- `hr.function_type`
- `hr.qualification_type`

and is safe to re-run without creating duplicate codes.

Customer pricing rate lines consume the tenant-owned HR catalogs:

- `hr.function_type`
- `hr.qualification_type`

In development and test environments, sample rows can be bootstrapped if those catalogs are empty for a tenant. This bootstrap is intentionally restricted to `SP_ENV=development` or `SP_ENV=test` and must not be relied on in production.

Sample function types:

- `SEC_GUARD` / `Security agent`
- `SHIFT_SUP` / `Shift supervisor`
- `DISPATCH` / `Dispatch support`
- `FIRE_WATCH` / `Fire watch`

Sample qualification types:

- `G34A` / `34a certified`
- `FIRST_AID` / `First aid`
- `FIRE_SAFETY` / `Fire safety`
- `CROWD_CONTROL` / `Crowd control`

### Explicit local/dev seed command

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_employee_catalogs.py --tenant-id <tenant_uuid>
```

### Explicit production-safe backfill commands

Single tenant:

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>
```

All active tenants, explicit confirmation required:

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_go_live_configuration.py --all-tenants --confirm-all-tenants RUN_ALL_TENANTS
```

The all-tenant mode is idempotent. It inserts missing baseline rows and reactivates matching baseline codes without clobbering customized tenant labels or descriptions.

### Dev/test API bootstrap

The employee catalog API also exposes a dev/test-only bootstrap endpoint:

```text
POST /api/employees/tenants/{tenant_id}/employees/catalog/bootstrap-sample-data
```

It is intended for local admin tooling and the customer pricing empty-state recovery flow. The endpoint requires tenant-scoped employee write permission and returns `403` outside development/test environments.

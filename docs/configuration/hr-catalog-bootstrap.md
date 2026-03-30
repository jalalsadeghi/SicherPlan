## HR Catalog Bootstrap

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

### Dev/test API bootstrap

The employee catalog API also exposes a dev/test-only bootstrap endpoint:

```text
POST /api/employees/tenants/{tenant_id}/employees/catalog/bootstrap-sample-data
```

It is intended for local admin tooling and the customer pricing empty-state recovery flow. The endpoint requires tenant-scoped employee write permission and returns `403` outside development/test environments.

# US-34 Go-Live Seed Baseline

## System lookup seed

Use the existing system lookup seeding first:

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_lookup_values.py
```

## Combined go-live seed

For staging, UAT, or a freshly onboarded tenant, use:

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>
```

This seed bundle is idempotent and covers:

- system lookup domains already approved in `core.lookup_value`
- central `docs.document_type` rows used by migration and generated outputs
- tenant-scoped numbering rules in `core.tenant_setting`
- tenant-scoped print-template metadata in `core.tenant_setting`

## Numbering rules

Tenant setting key: `numbering.rules`

Seeded rules:

- `customer_number`
- `personnel_no`
- `subcontractor_number`
- `order_no`
- `invoice_no`
- `timesheet_no`

The seed stores prefixes, next counters, pad length, and reset policy. Counter increments remain application-owned; the seed only establishes the tracked rule source.

## Print-template catalog

Tenant setting key: `print_templates.catalog`

Seeded template metadata aligns with existing generated outputs:

- watchbook PDF
- patrol report PDF
- timesheet PDF
- invoice PDF
- employee badge code
- order badge code

German labels are default, English labels are stored alongside them in metadata.

# Lookup Seeding

## Purpose

`US-4-T3` introduces the initial lookup governance and seed package for `core.lookup_value`. The goal is to provide stable machine-readable codes for downstream CRM, HR, finance, platform-service, and reporting work without hardcoding business dictionaries in application logic.

## Ownership model

Platform-managed domains:

- `legal_form`
- `invoice_layout`
- `invoice_delivery_method`
- `dunning_stage`
- `report_category`
- `notice_category`

Tenant-extensible domains:

- `customer_category`
- `customer_ranking`
- `customer_status`
- `employee_group`
- `subcontractor_category`
- `site_category`

Platform-managed domains are seeded centrally and should keep stable `code` values across environments. Tenant-extensible domains may receive tenant-specific rows later, but they still use the same `(tenant_id, domain, code)` uniqueness contract.

## Seed source

- Definitions live in `backend/app/modules/core/lookup_seed.py`.
- The executable entry point is `backend/scripts/seed_lookup_values.py`.

Run system seeds:

```bash
PYTHONPATH=backend python backend/scripts/seed_lookup_values.py
```

This system seed is required for the Customer -> Commercial -> Billing profile dropdowns. The active customer form loads these lookup-backed fields from `GET /api/customers/tenants/{tenant_id}/customers/reference-data`, which in turn depends on these system domains being present in `core.lookup_value`:

- `invoice_layout`: `standard`, `compact`, `detailed_timesheet`
- `invoice_delivery_method`: `email_pdf`, `portal_download`, `postal_print`, `e_invoice`
- `dunning_policy`: `disabled`, `standard`, `strict`

If those three dropdowns render empty and disabled, run the system seed command above against the same database your backend is using, then refresh the customer page.

Run tenant-extensible seeds for one tenant:

```bash
PYTHONPATH=backend python backend/scripts/seed_lookup_values.py --tenant-id <tenant_uuid>
```

The Customer -> Overview form depends on these tenant-extensible CRM metadata domains:

- `customer_category`: `standard`, `key_account`, `prospect`
- `customer_ranking`: `a`, `b`, `c`
- `customer_status`: `qualified`, `on_hold`, `blocked`

Those rows are already created automatically when a tenant is onboarded through the core admin flow, and they are now also created when a local tenant is created through the development `bootstrap_system_admin.py` path. If the three customer Overview dropdowns for Classification, Ranking, or Customer status metadata are empty, the tenant lookup seeds are missing for that tenant.

## Governance rules

- Add new lookup codes only when the proposal/spec or an approved task explicitly needs them.
- Do not use display labels as integration identifiers; `code` is the stable machine value.
- Prefer platform-managed domains for cross-tenant shared dictionaries.
- Prefer tenant-extensible domains for local classification lists that should vary by prime company.
- Do not use `core.lookup_value` for permissions, secrets, or opaque config blobs.

## Localization note

The seed package stores the German label as the canonical `label` because DE is the product default and the current schema has only one display label column. English readiness is handled by:

- stable domain/code identifiers, which app layers can map to EN labels later
- optional future extension via application i18n resources or explicit metadata columns once approved

This avoids introducing an unapproved translation subsystem inside Sprint 2.

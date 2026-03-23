# Subcontractor Read Contracts

`US-14-T4` defines the read-only partner contracts that later planning, field execution, and finance work may consume without crossing partner write boundaries.

## Read surfaces

- `GET /api/subcontractor-read-models/tenants/{tenant_id}/partners`
  - active subcontractor identity
  - active scope rows
  - portal-ready contacts
  - readiness summary counts
- `GET /api/subcontractor-read-models/tenants/{tenant_id}/partners/{subcontractor_id}/workers`
  - active workers only
  - valid qualifications only
  - active credentials only
  - derived readiness state and explainable issues
- `GET /api/subcontractor-read-models/tenants/{tenant_id}/partners/{subcontractor_id}/commercial-summary`
  - finance-oriented commercial settings only
  - excludes raw bank and tax identifiers
- `GET /api/subcontractor-read-models/tenants/{tenant_id}/field/credential-resolution/{encoded_value}`
  - field-safe scan resolution to worker and partner identity
  - returns `null` for missing, inactive, revoked, expired, or out-of-scope credentials

## Boundary rules

- These contracts are read-only. Planning, field, and finance must not mutate `partner.*` master rows through them.
- Readiness remains derived from authoritative subcontractor worker, qualification, proof, and credential rows.
- Customer, employee, and subcontractor portal roles remain excluded from these internal read contracts.
- Commercial summary intentionally omits bank and tax fields. If a later finance task truly needs those, it must add a narrower finance-owned contract deliberately.

## Downstream intent

- Planning uses partner and worker contracts for candidate search and release validation.
- Field execution uses credential resolution and worker identity reads for scan lookup and actor resolution.
- Finance uses commercial summary plus partner identity for invoice-control joins and settlement checks.

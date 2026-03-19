# Audit And Event Rules

## Separation of concerns

- Structured logs are technical observability.
- Audit rows are durable business/security evidence.
- Neither replaces the other.

## Current tables

- `audit.login_event`
  - captures successful and failed login attempts
  - stores tenant/user/session linkage when known
  - never stores raw passwords, raw tokens, or reset secrets
- `audit.audit_event`
  - captures sensitive business and administration mutations
  - stores stable `event_type`, `entity_type`, and `entity_id`
  - stores correlation via `request_id`

## Event-writing rules

- Audit rows are append-only; later corrections create additional events instead of rewriting history.
- Event types should stay stable and machine-readable.
- Before/after payloads should be narrow, privacy-conscious snapshots rather than full raw objects.
- Tenant-owned business events should carry the affected `tenant_id` even when the actor is a platform-scope user.
- Secrets and reusable credentials must never appear in audit payloads.
- Secret-like keys such as password, token, secret, and API-key fields are stripped from nested audit payloads before persistence.

## Sprint 2 coverage

Current audit emission includes:

- login success and login failure
- logout
- password reset confirmation
- tenant onboarding
- tenant updates and lifecycle changes
- branch creation and update
- mandate creation and update
- tenant-setting creation and update

## Follow-up expectation

Later modules should reuse the same audit writer with stable event types and entity identifiers instead of creating module-local audit tables or encoding audit evidence only in logs.

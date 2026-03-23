# Sprint 11 Performance and Optional RLS

## Scope

This note captures the hardening decisions for `US-33-T1` and `US-33-T2`.

## Query tuning

The first reporting implementation built `rpt.*` list queries with predicates shaped like:

- `(:branch_id IS NULL OR branch_id = :branch_id)`
- `(:status_code IS NULL OR status_code = :status_code)`

That pattern is easy to write but hostile to PostgreSQL index selection on the heavier Sprint 11 reports. The hardening pass switched the reporting repository to emit only active predicates for the selected report/filter combination.

Representative probe:

- `backend/scripts/reporting_query_probe.py`

## Added support indexes

The `0056_hardening_indexes_and_query_support` migration adds narrow indexes for the observed heavy paths:

- `audit.login_event`: failure-focused tenant/time lookup for security reporting
- `audit.audit_event`: tenant/event and tenant/request access for security drill queries
- `field.time_event`: actor/time lookup for attendance and finance derivation
- `finance.actual_record`: current approval-stage scans for finance and reporting
- `docs.document_link`: owner+relation lookup for generated-output and attachment reads
- `integration.import_export_job`: expression index for reporting export delivery history

## Deferred partition candidates

Partitioning was evaluated but intentionally deferred for Sprint 11. Candidate tables remain:

- `audit.login_event`
- `audit.audit_event`
- `field.time_event`

Reason for deferral:

- the repository is still using ordinary views, not materialized views
- UAT and migration rehearsal need a stable schema first
- monthly partitions would change operational backup/restore and RLS rollout complexity at the same time

The current seam is explicit: the heavy append-only tables already have date-oriented indexes, so a later partition migration can be introduced without rewriting service contracts.

## Optional RLS model

`US-33-T2` enables PostgreSQL RLS on a narrow set of high-risk tenant-owned tables:

- `docs.document`
- `docs.document_version`
- `docs.document_link`
- `finance.actual_record`

RLS is optional and controlled by trusted session context, not client parameters.

Session settings used:

- `app.rls_mode`
- `app.tenant_id`
- `app.rls_bypass`

Application helpers:

- `backend/app/db/rls.py`

Operational rules:

- default posture is still application-layer authorization first
- enable DB enforcement by setting `SP_DB_RLS_ENABLED=true`
- privileged maintenance/background flows must set `app.rls_bypass=on`
- platform admin and selected service dependencies apply bypass explicitly; normal tenant-scoped requests do not

## Materialized views

Sprint 11 still uses normal PostgreSQL views.

- no hidden refresh job was introduced
- no report correctness depends on stale cached data
- if a later story introduces materialization, refresh and indexing must be explicit in both migrations and operator docs

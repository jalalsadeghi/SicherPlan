# Sprint 11 Hardening Remediation Backlog

## Blocking

None identified from the in-repo hardening cycle.

## Major

### H-001 Distributed rate limiting

- Severity: major
- Area: API hardening
- Current posture: the new limiter is process-local and will not coordinate across multiple app instances
- Suggested owner: platform / DevOps
- Sprint 12 impact: not a blocker for migration rehearsal, but should be closed before horizontally scaled production rollout

### H-002 Live RLS rollout rehearsal

- Severity: major
- Area: database hardening
- Current posture: optional RLS is implemented and test-covered at SQL/helper level, but not yet validated against a live PostgreSQL environment in this repo
- Suggested owner: backend / DevOps
- Sprint 12 impact: required before enabling `SP_DB_RLS_ENABLED=true` in any shared environment

## Minor

### H-003 Partitioning deferred for append-only evidence tables

- Severity: minor
- Area: performance
- Current posture: `audit.login_event`, `audit.audit_event`, and `field.time_event` remain indexed but unpartitioned
- Suggested owner: backend / DBA
- Sprint 12 impact: monitor during migration rehearsal; defer unless volume evidence justifies it

### H-004 Restore drill still depends on operator-supplied object-storage sample validation

- Severity: minor
- Area: disaster recovery
- Current posture: DB validation is scripted, but binary object restoration still requires explicit sample verification
- Suggested owner: platform / DevOps
- Sprint 12 impact: include this step in cutover rehearsal

## Nice to have

### H-005 Prometheus-style rate-limit and RLS diagnostics

- Severity: nice-to-have
- Area: observability
- Current posture: failures surface through API responses and tests, but there is no dedicated hardening dashboard
- Suggested owner: platform

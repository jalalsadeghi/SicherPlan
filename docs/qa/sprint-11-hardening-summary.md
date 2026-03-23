# Sprint 11 Hardening Summary

This document captures the implemented hardening posture for `US-33`.

## Completed

- reporting query tuning and supporting indexes
- optional PostgreSQL RLS for a narrow high-risk table set
- repeatable backup/restore and secure-document drill documentation
- configurable rate limiting on refresh, report export, and docs-backed download routes
- integrated hardening command manifest in `backend/scripts/run_hardening_checks.py`

## Actual posture

- RLS exists but is optional and disabled by default unless `SP_DB_RLS_ENABLED=true`
- reporting still uses normal views, not materialized views
- backup/restore validation is scriptable and documented, but not automatically run inside routine local test flows
- rate limiting is process-local, not distributed

## Sprint 12 readiness

Ready for:

- migration rehearsal
- UAT
- go-live preparation

Carry-forward risks are tracked in:

- `docs/qa/sprint-11-hardening-remediation-backlog.md`

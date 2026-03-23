# Hypercare Runbook

## Window

Initial post-go-live support window for immediate blocker, hotfix, data-correction, and stabilization decisions.

## Severity matrix

| Severity | Meaning | Expected handling |
| --- | --- | --- |
| `sev-1` | Production blocker, privacy/scope leak, or finance-critical failure | immediate triage, rollback/hotfix decision |
| `sev-2` | Major workflow degradation with workaround | same-day owner assignment and status broadcast |
| `sev-3` | Non-blocking defect or support correction | stabilization backlog |
| `sev-4` | Improvement or polish follow-up | future release backlog |

## Routing rules

- auth / role scope / tenant leakage -> IAM or portal owner
- docs / generated outputs / downloads -> platform services owner
- planning / staffing / release -> planning owner
- field watchbook / patrol / time capture -> field execution owner
- payroll / billing / invoice checks -> finance owner
- reporting / export delivery -> reporting owner

## Evidence requirements

- timestamp
- sanitized tenant context
- actor role
- reproduction steps
- logs / request IDs / screenshots where available
- rollback or hotfix note if relevant

## Daily cadence

- morning issue review
- midday status update for open `sev-1` / `sev-2`
- end-of-day stabilization summary

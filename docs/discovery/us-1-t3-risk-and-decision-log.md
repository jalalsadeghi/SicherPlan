# US-1-T3 Risk And Decision Log

## Task anchor

- Task: `US-1-T3`

## Risks that could block Sprint 2 if unresolved

| Risk | Impact | Status |
| --- | --- | --- |
| Missing standalone proposal/spec files remain unresolved | Later tasks may drift from the intended migration-wave and service-boundary wording. | `blocking now` |
| Object-storage abstraction is not confirmed before `US-6-T1`/`US-2-T2` | Docs service design, local dev setup, and generated-output handling may fork into incompatible patterns. | `needed before Sprint 2` |
| Canonical auth/identity direction is not clarified before `US-5-*` | IAM models may overfit local auth or underprepare for SSO/MFA-ready hooks. | `needed before Sprint 2` |
| Historical migration depth is not defined for customers, employees, subcontractors, orders, and documents | Sprint 12 migration scope, storage sizing, and trial-load realism remain uncertain. | `can defer`, but should be framed early |
| Optional RLS decision is left ambiguous too long | Teams may either over-engineer early schemas or assume controls that are not part of the baseline. | `needed before Sprint 2` |

## Proposed decisions for now

| Topic | Proposed handling | Owner |
| --- | --- | --- |
| Notification channels | Build adapter-friendly message/outbox contracts without choosing providers yet. | Engineering default |
| Object storage | Design docs metadata and binary storage as separate concerns with a storage adapter boundary. | Engineering default |
| Payroll integration | Keep export/import behind finance-owned adapters driven by approved actuals. | Engineering default |
| Offline field support | Treat offline-safe design as mandatory for patrol/time-capture-capable flows from the first pass. | Engineering default |
| Historical migration depth | Request client signoff on minimum viable history per data domain before Sprint 12 planning. | Client decision |

## Follow-ups for next tasks

- `US-1-T4`: carry forward these risks into the story-to-acceptance traceability matrix and demo evidence expectations.
- `US-2-T2`: translate the integration defaults into environment/config naming rules without hardwiring vendors.
- `US-2-T4`: ensure observability guidance distinguishes operational telemetry from audit/evidence records.

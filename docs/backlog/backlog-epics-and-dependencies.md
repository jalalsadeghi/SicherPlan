# Backlog Epics And Dependencies

## Task anchor

- Task: `US-1-T2`
- Story: `US-1` — Discovery, backlog confirmation, and acceptance traceability
- Baseline inputs: `AGENTS.md`, `docs/discovery/us-1-t1-scope-review.md`, `docs/sprint/*.md`, `docs/prompts/task-index.md`

## Purpose

This document groups the approved 12-sprint backlog into stable implementation epics without changing story IDs. The goal is to keep bounded-context ownership, sprint sequencing, and cross-sprint handoffs legible for later Codex tasks, PO review, and QA traceability.

## Epic view

### Epic A — Delivery governance and UX/platform foundation

Intent: establish the delivery operating model, repository/runtime baseline, and reusable UX shells before business-domain persistence expands.

Stories:

- `US-1` — Discovery, backlog confirmation, and acceptance traceability
- `US-2` — Repository, environments, CI/CD, and observability baseline
- `US-3` — Vben Admin shell, Prokit mobile shell, theme tokens, and localization

Primary contexts:

- Cross-cutting delivery management
- Engineering platform
- UX foundation

Entry/exit significance:

- This epic is the prerequisite frame for every later story.
- Sprint 1 must finish with approved backlog assets, working delivery automation, and reusable DE/EN plus theme-ready shells.

### Epic B — Platform backbone and shared services

Intent: create the tenant, IAM, audit, documents, communication, and integration backbone that all later modules consume.

Stories:

- `US-4` — Tenant, branch, mandate, setting, and lookup foundation
- `US-5` — Identity, role scope, session management, and audit foundation
- `US-6` — Document, communication, information portal, and integration backbone

Primary contexts:

- `core`
- `iam`
- `platform_services`

Entry/exit significance:

- This epic anchors tenant isolation, role scoping, append-only audit behavior, document linking, and outbox-based integrations.
- No business module should bypass these contracts later.

### Epic C — External party master data and portal boundaries

Intent: stand up customer and subcontractor aggregates, their commercial/portal controls, and externally visible scope rules.

Stories:

- `US-7` — Customer master, contacts, addresses, and portal account linkage
- `US-8` — Customer billing profile, rate cards, surcharge rules, and invoice parties
- `US-9` — Customer portal read models, collaboration views, and customer-specific controls
- `US-13` — Subcontractor master, scope, contacts, and finance profile
- `US-14` — Subcontractor workers, qualifications, credentials, and compliance completeness
- `US-15` — Subcontractor portal self-service, shift allocation, and visibility boundaries

Primary contexts:

- `customers`
- `subcontractors`
- `iam` and `platform_services` as supporting contexts

Entry/exit significance:

- Customer and subcontractor actors remain tenant-scoped users, not separate tenants.
- Customer portal visibility must hide personal names by default unless explicitly released.
- Subcontractor portal scope is limited to own company and released operational scope.

### Epic D — Recruiting and employee system of record

Intent: build the applicant workflow and employee/HR foundation that later planning, field, and payroll flows can consume without owning HR truth.

Stories:

- `US-10` — Applicant intake, GDPR consent, and applicant workflow
- `US-11` — Employee master file with private-profile split and role-based exposure
- `US-12` — Qualifications, availability, absences, balances, allowances, and credentials foundation

Primary contexts:

- `recruiting`
- `employees`

Entry/exit significance:

- Applicant-to-employee conversion must preserve consent, files, and status history.
- The HR private-data split is non-negotiable and must remain visible in backlog decisions and later reviews.

### Epic E — Operational planning and release backbone

Intent: create the operational structures from locations and orders through planning, shift generation, staffing validation, and downstream release.

Stories:

- `US-16` — Operational master data: locations, routes, checkpoints, and equipment catalogs
- `US-17` — Customer orders, planning records, and mode-specific detail structures
- `US-18` — Shift plans, templates, recurrence series, and concrete shift generation
- `US-19` — Demand groups, teams, assignments, and subcontractor releases
- `US-20` — Validation engine, blocking/warning policies, and override audit trail
- `US-21` — Release workflows, deployment outputs, and visibility to downstream channels

Primary contexts:

- `planning`
- `customers`, `employees`, and `subcontractors` as upstream read sources

Entry/exit significance:

- Planning owns operational release truth but must not mutate HR or partner master tables.
- Release states are the gate between planning truth and downstream field/mobile/portal/finance visibility.

### Epic F — Field execution, mobile work, and raw evidence capture

Intent: expose released work to mobile and field surfaces, capture durable watchbook/patrol/time evidence, and support offline-safe execution where needed.

Stories:

- `US-22` — Employee mobile app: schedules, actions, documents, notifications, and theme/i18n parity
- `US-23` — Information feed, mandatory notice acknowledgements, and online watchbook
- `US-24` — Guard patrol control, checkpoint capture, and offline synchronization
- `US-25` — Time capture devices, policies, raw event ingest, and context validation

Primary contexts:

- `field_execution`
- `platform_services`
- `iam`

Entry/exit significance:

- Only released data may reach employee mobile and external-facing field channels.
- Watchbook, patrol, and raw time evidence are durable business evidence and must remain append-only or correction-safe.

### Epic G — Finance derivation, approvals, and commercial outputs

Intent: derive actuals from released planning plus field evidence, then generate payroll, customer billing, and subcontractor settlement outputs without bypassing finance ownership.

Stories:

- `US-26` — Attendance normalization and actual_record bridge from planning and field evidence
- `US-27` — Three-stage approval and reconciliation for operational and finance actuals
- `US-28` — Payroll tariffs, employee pay profiles, allowances, and export package
- `US-29` — Customer timesheets, invoices, layouts, and customer portal release
- `US-30` — Subcontractor invoice checks, variance analysis, and commercial control

Primary contexts:

- `finance`
- `customers`, `employees`, `subcontractors`, and `planning` as upstream sources

Entry/exit significance:

- `finance.actual_record` is the mandatory bridge from evidence to payroll, timesheets, invoices, and partner settlement.
- Finance outputs must remain reproducible from approved actuals and released upstream commercial rules.

### Epic H — Reporting, hardening, migration, and release

Intent: finish the platform with reproducible reporting, hardening controls, migration/UAT assets, and release/hypercare governance.

Stories:

- `US-31` — Operational, commercial, and finance reporting read-model layer
- `US-32` — Compliance, QM, and security reporting with scheduled export hooks
- `US-33` — Performance tuning, optional RLS, backup/restore, and security hardening
- `US-34` — Data migration package, seed/reference data, and print-template finalization
- `US-35` — UAT execution, multilingual review, training, and rollout readiness
- `US-36` — Production cutover, hypercare, KPI monitoring, and stabilization

Primary contexts:

- `reporting`
- hardening/release cross-cutting concerns

Entry/exit significance:

- Reporting must remain SQL-view/materialized-view oriented unless scale later proves otherwise.
- Migration/UAT/release work depends on the stabilized write model and approved three-workflow acceptance path.

## Sprint goals and dependency chain

| Sprint | Stories | Goal | Must land before |
| --- | --- | --- | --- |
| Sprint 01 | `US-1` to `US-3` | Delivery guardrails, shell baseline, and backlog governance | Any business-domain persistence |
| Sprint 02 | `US-4` to `US-6` | Tenant, IAM, audit, docs, communication, and integration backbone | All domain modules |
| Sprint 03 | `US-7` to `US-9` | Customer master/commercial truth and customer portal boundaries | Planning, customer billing, customer portal release |
| Sprint 04 | `US-10` to `US-12` | Recruiting flow and employee/HR foundation | Staffing, employee app, payroll |
| Sprint 05 | `US-13` to `US-15` | Subcontractor master/compliance and partner portal boundaries | Partner release, settlement, portal visibility |
| Sprint 06 | `US-16` to `US-18` | Operational master data, orders, and shift-planning backbone | Staffing, field execution, actual derivation |
| Sprint 07 | `US-19` to `US-21` | Assignments, validation, release control, and downstream visibility | Mobile, time capture, finance actuals |
| Sprint 08 | `US-22` to `US-24` | Employee mobile, watchbook, patrol, and offline field evidence | Time capture normalization, reporting on field evidence |
| Sprint 09 | `US-25` to `US-27` | Raw time ingest, actual bridge, and approval chain | Payroll, customer billing, partner settlement |
| Sprint 10 | `US-28` to `US-30` | Payroll, invoices, timesheets, and subcontractor control | Reporting, UAT for end-to-end workflows |
| Sprint 11 | `US-31` to `US-33` | Reporting and hardening | Migration rehearsal, UAT, go-live |
| Sprint 12 | `US-34` to `US-36` | Migration, UAT, cutover, and hypercare | Production stabilization closeout |

## Inter-story dependency rules

### Stable prerequisites

- `US-1` is the planning/governance prerequisite for `US-2` and `US-3`.
- `US-2` is the engineering/runtime prerequisite for implementation-heavy stories starting in Sprint 02.
- `US-3` is the reusable shell and UX baseline for later web/mobile stories, but it does not replace business acceptance.
- `US-4`, `US-5`, and `US-6` together are the platform-core prerequisite set for almost every business-domain story.

### Business ownership sequence

- Customer commercial truth must exist before planning and billing consume it: `US-7` -> `US-8` -> `US-17`/`US-29`.
- Employee and compliance truth must exist before staffing, mobile, and payroll consume it: `US-10` -> `US-11` -> `US-12` -> `US-19`/`US-22`/`US-28`.
- Subcontractor master/compliance truth must exist before partner allocation and settlement consume it: `US-13` -> `US-14` -> `US-15` -> `US-19`/`US-30`.
- Planning structures must exist before assignment, release, field, and finance derivation: `US-16` -> `US-17` -> `US-18` -> `US-19`/`US-21` -> `US-22` to `US-27`.

### Evidence and finance sequence

- Released operational scope is the precondition for mobile/portal/field distribution: `US-21` before `US-22`, `US-23`, `US-25`.
- Raw field evidence and released assignments are the precondition for `US-26`.
- `US-26` and `US-27` are the prerequisite pair for payroll, customer billing, and subcontractor settlement in Sprint 10.
- Reporting should consume approved transactional artifacts rather than invent alternate write-side truth: `US-28` to `US-30` before `US-31`.

## Sprint 1 detailed dependency notes

### `US-1` dependencies

- No incoming dependency.
- Provides the decision frame for `US-2` and `US-3`.

### `US-2` dependencies

- Depends on `US-1` backlog/discovery outputs for scope and sequencing.
- Can begin some repository/runtime scaffolding in parallel with late `US-1` documentation cleanup if no story/task IDs are affected.

### `US-3` dependencies

- Depends on `US-1` for role/scope vocabulary and backlog alignment.
- Depends on `US-2` for repo/workspace/runtime baseline.
- Theme and i18n work can progress in parallel across web and mobile once the shell structure exists.

## Earliest cross-sprint handoff into Sprint 2

Sprint 2 should assume the following from Sprint 1:

- `US-1` has locked the bounded-context map, epic grouping, sprint dependency chain, and reusable readiness/completion criteria.
- `US-2` has established repo conventions, CI/CD expectations, and observability/health-check expectations.
- `US-3` has established the Vben/Prokit shell baseline plus DE/EN and light/dark theme contracts.

Sprint 2 should not assume:

- finalized provider selections
- finalized migration workbook details
- finalized story-to-acceptance traceability matrix

Those belong to `US-1-T3` and `US-1-T4`.

## Notes for later Codex prompts

- Keep story ownership visible in prompts and implementation packages; do not flatten stories into a generic technical backlog.
- When a story spans multiple bounded contexts, preserve the owning context and describe all other contexts as read dependencies, contracts, or shared platform services.
- If a future task seems to require skipping ahead of this sequence, treat that as a dependency smell and document the exception explicitly.

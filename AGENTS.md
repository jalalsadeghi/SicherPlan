# AGENTS.md

## Mission

Build **SicherPlan** as a modular, implementation-oriented, multi-tenant security operations platform.
This repository is meant to support task-by-task Codex execution against the approved sprint plan.
Stable identifiers matter:

- Story IDs use `US-N`
- Task IDs use `US-N-TN`

Every later Codex prompt should anchor to one task ID and should keep backlog traceability intact.

## Source-of-truth order

Use the following order when implementing work:

1. The implementation-oriented data model and service-boundary specification for data ownership, table boundaries, migration sequencing, and aggregate/package design.
2. The updated SicherPlan proposal for business scope, user-visible workflows, portals, field execution, finance flows, and acceptance intent.
3. The 12-sprint delivery plan for sequencing, dependencies, and story/task packaging.
4. This `AGENTS.md` for cross-cutting implementation rules.
5. `docs/sprint/*.md` for sprint-by-sprint execution context.
6. `docs/prompts/*.md` for task-level execution instructions.

When sources overlap:

- follow the **implementation spec** for persistence, ownership, and cross-module write discipline
- follow the **proposal** for business meaning and end-to-end workflow intent
- follow the **sprint docs** for execution order and task packaging

## Non-negotiable platform qualities

The implementation must preserve these properties everywhere:

- strict tenant isolation
- role-scoped visibility for internal staff, customers, subcontractors, and employees
- append-only or archive-safe handling for audit, compliance, patrol, and time-capture evidence
- document-centered compliance with durable file metadata and generated-output tracking
- mobile-ready field execution and offline-safe workflows where required
- end-to-end traceability from master data to planning, field evidence, finance outputs, and reports
- architecture extensibility without reworking the permission model or core schema later

## Technical baseline

### Backend

- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Alembic

### Web admin / portal

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router
- **Vben Admin** as the reference admin shell

### Mobile

- Flutter
- **Prokit Flutter** as the reference template and interaction baseline

### Product-wide UI rules

- German is the **default** language
- English is the **secondary** language
- Light-mode primary color: `rgb(40,170,170)`
- Dark-mode primary color: `rgb(35,200,205)`

Any new user-facing feature must preserve these i18n and theme rules.

## Recommended bounded-context package map

Unless the repo already contains a compatible structure, prefer these module names:

- `modules/core`
- `modules/iam`
- `modules/platform_services`
- `modules/customers`
- `modules/recruiting`
- `modules/employees`
- `modules/subcontractors`
- `modules/planning`
- `modules/field_execution`
- `modules/finance`
- `modules/reporting`

Interpret them as **transactional ownership boundaries**, not just folders.

## Data and modeling rules

### Global conventions

- Use UUID primary keys for business tables.
- Keep business-facing numbers tenant-scoped and separate from UUIDs.
- Every tenant-owned major table should carry `tenant_id`.
- Favor explicit foreign keys over polymorphic references.
- Use composite foreign keys where they materially reduce cross-tenant leakage risk.
- Use UTC `timestamptz` for instants and date-only columns for date facts.
- Prefer `status + archived_at` over hard deletes.
- Use `version_no` optimistic locking on mutable aggregate roots.
- Use `numeric(12,2)` for money and integer minutes for duration math unless a stronger reason exists.

### Shared columns to expect on major tables

Most mutable aggregate roots should consistently use:

- `id`
- `tenant_id`
- `status`
- `created_at`
- `updated_at`
- `created_by_user_id`
- `updated_by_user_id`
- `archived_at`
- `version_no`

### Service-boundary rules

- Each bounded context owns its own master tables and write rules.
- Other modules may reference IDs and read projections, but must not mutate another context's master truth directly.
- Use read models, projections, or service-layer contracts instead of hidden cross-context writes.

### Cross-module rules that must stay stable

- Planning may read HR availability and qualification data, but it must not write employee master or private HR data.
- Planning may release work to subcontractors and later reference subcontractor workers, but it must not write partner master records.
- Field execution may reference released shifts, assignments, routes, and sites, but it must not mutate shift demand or commercial planning rules.
- Finance may derive actuals and outputs from released planning + field evidence, but it must preserve raw evidence and must not redefine upstream planning truth.
- Documents remain centralized in the docs service; business meaning stays with the owning module.

## Hard rules for evidence, outputs, and integrations

### Raw evidence

Keep these classes of records append-only or correction-safe:

- audit events
- login events
- patrol round events
- raw time events

Corrections should create additional records or controlled derived-status transitions instead of destructive overwrites.

### Finance bridge

Do **not** bypass `finance.actual_record`.

It is the finance-owned bridge between:

- released assignments
- attendance summaries
- payroll calculations
- timesheets
- invoices
- subcontractor invoice checks

Any payroll or billing implementation that skips this bridge is incorrect.

### Documents

Generated PDFs, exports, badge files, watchbook outputs, patrol reports, timesheets, and invoices should be represented as document rows linked back to the owning business entity.

### External side effects

Do not call external providers directly from the same transaction that writes domain data.
Use integration endpoints, jobs, and an outbox/event worker pattern for:

- email / SMS / push
- payroll export/import
- maps / scanning / terminals
- other provider integrations

## Reporting rules

- Reporting should start as SQL views or materialized views over transactional data.
- Do not create a second write-side reporting schema unless scale later forces it.
- Reports must remain reproducible from the transactional backbone and audit evidence.
- Role scope still applies to dashboards, exports, and scheduled report delivery.

## Portal and privacy rules

- Customers, subcontractors, and employees are scoped actors inside a tenant; they are not separate tenants.
- Customer and subcontractor portal queries must always apply tenant scope **and** local visibility scope.
- Customer-facing result views should hide personal names by default unless the prime company explicitly releases them.
- Finance-sensitive and HR-private data must remain least-privilege by default.

## UI and interaction rules

### Web

- Use Vben Admin patterns for navigation, permission guards, form pages, list/detail pages, and reusable CRUD workflows.
- Admin and portal flows should share stable permission and visibility semantics even if their layouts differ.

### Mobile

- Use Prokit-style navigation and screen composition as the interaction reference, not as a direct scope substitute.
- Mobile work should display only released and properly scoped operational data.
- Offline storage and sync flows are mandatory where patrol, field capture, or field execution tasks demand them.

### Localization

- German keys/resources come first.
- English keys/resources must be added alongside them.
- Do not hardcode mixed-language strings into components or API responses.
- Validation messages, document labels, push text, and email/SMS templates all follow the same DE-default / EN-secondary rule.

## SQLAlchemy / Pydantic rules

- Create one SQLAlchemy declarative model per table.
- Group models by bounded context, not only by technical layer.
- Expose separate Pydantic schemas for:
  - Create
  - Update
  - Read
  - List item
  - Filter
- Use explicit relationship loading strategies.
- Do not eager-load large child collections unless the command/query actually needs them.
- Centralize overlap checks for temporal data like rate cards, scope assignments, tariffs, pay profiles, and allowances.

## How Codex should work in this repo

### Before starting a task

1. Read `AGENTS.md`.
2. Open the relevant sprint file under `docs/sprint/`.
3. Check task dependencies.
4. Confirm whether any upstream prompt file already exists under `docs/prompts/`.
5. Keep the change set narrow to the requested task unless an explicit dependency forces a small prerequisite fix.

### Generated artifacts

Some repository artifacts are derived from multiple source areas and must be refreshed when those inputs change.

The assistant field/lookup corpus depends on:

- backend schema fields
- TypeScript API interfaces
- Vue field bindings
- locale labels
- page help seed data

If you change any of those inputs, refresh and verify the artifact locally:

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact ensure-current --repo-root ..
python -m app.modules.assistant.field_lookup_corpus_artifact check-committed --repo-root ..
```

Stage Deploy regenerates this artifact before building the backend image, but determinism is still enforced and PR CI still checks committed freshness.

### What each task-level prompt should produce

A good task prompt should tell Codex to return or implement:

- a short implementation plan
- the files it will create or modify
- migrations
- models and schemas
- services / repositories
- routers / endpoints
- UI or mobile screens where applicable
- test coverage
- any follow-up blockers or assumptions

### Traceability rules

- One prompt file normally maps to one task ID.
- Keep the task ID in the filename and title.
- Do not rename story or task IDs.
- If a task must be internally split, preserve the original task ID as the parent anchor.

## Definition of task-complete

A task is not complete until the implementation satisfies all relevant items below:

- build / lint passes
- tests exist for the implemented behavior
- tenant scoping is enforced
- role scoping is enforced
- audit or evidence behavior is correct for sensitive flows
- migrations are coherent with earlier schema waves
- user-facing work includes DE and EN resources
- theme rules are preserved where UI changes were made
- any generated file/output is linked through the docs model if applicable
- prompt and backlog traceability remain clear

## What not to do

Do **not** do any of the following without explicit instruction:

- bypass `finance.actual_record`
- let planning mutate HR or partner master tables
- let field modules change planning demand or commercial rules
- write provider calls directly inside domain transactions
- create broad tenant queries for customer/subcontractor portals
- hard-delete finance, audit, compliance, patrol, or time-capture evidence
- introduce a second write-side reporting schema early
- collapse the HR private-data split
- ignore DE/EN parity for new user-visible behavior

## Sprint and prompt files in this repo

- Sprint overviews live in `docs/sprint/`
- Future task prompts will live in `docs/prompts/`
- Use the sprint files to understand the story grouping and execution sequence
- Use task prompt files to drive atomic implementation work

This repository should stay ready for incremental Codex execution, one task at a time.

---
sprint: 11
label: "Sprint 11"
title: "Sprint 11 — Reporting & hardening"
focus: "Reporting & hardening"
proposal_phase: "Proposal Phase 6 | Spec Phase H"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-31
  - US-32
  - US-33
---

# Sprint 11 — Reporting & hardening

## Sprint summary

- **Focus:** Reporting & hardening
- **Proposal phase / migration wave:** Proposal Phase 6 | Spec Phase H
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver role-scoped reporting, QM/compliance/security views, and technical hardening.

## Exit criteria

Reporting is reproducible, security controls are verified, and performance is acceptable.

## Incoming dependencies

- US-29 — Customer timesheets, invoices, layouts, and customer portal release (Sprint 10)
- US-30 — Subcontractor invoice checks, variance analysis, and commercial control (Sprint 10)
- US-28 — Payroll tariffs, employee pay profiles, allowances, and export package (Sprint 10)
- US-20 — Validation engine, blocking/warning policies, and override audit trail (Sprint 7)
- US-23 — Information feed, mandatory notice acknowledgements, and online watchbook (Sprint 8)

## Sprint-wide Codex notes

- Reporting should be implemented as SQL views or materialized views over transactional data, not as a second write-side schema unless performance later forces it.
- Role-scoped dashboards and exports must remain reproducible from the underlying transactional evidence.
- Hardening covers query tuning, optional RLS, backup/restore, and security testing. Keep technical hardening changes isolated from business behavior unless explicitly required.
- The result of this sprint should leave the platform ready for migration rehearsals, UAT, and production cutover without architectural surprises.

## Story breakdown

### US-31 — Operational, commercial, and finance reporting read-model layer

**Domain:** Reporting  
**Owner:** Data Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-29, US-30, US-28  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Reporting views, dashboards, and exports  
**Source basis:** Proposal 5.7 reporting | Spec 7

**Acceptance emphasis**

Implement the SQL view/materialized-view reporting layer and Vben dashboards for employee activity, customer revenue, subcontractor control, planning performance, and payroll basis. AC: role-scoped reports and exports are reproducible from transactional data and support management decisions without new write-side duplication.

**Tasks**

- `US-31-T1` — Implement reporting views for employee activity, customer revenue, and subcontractor control.
- `US-31-T2` — Implement planning performance, payroll basis, and customer/order profitability views.
- `US-31-T3` — Build Vben dashboards and downloadable report endpoints with role-based scope filters.
- `US-31-T4` — Validate report reproducibility against transactional tables and released evidence.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-31-T1.md`
- `docs/prompts/US-31-T2.md`
- `docs/prompts/US-31-T3.md`
- `docs/prompts/US-31-T4.md`

### US-32 — Compliance, QM, and security reporting with scheduled export hooks

**Domain:** Compliance + QM  
**Owner:** Data Lead  
**Story points:** 5  
**Components:** DB + Backend + Web  
**Dependencies:** US-20, US-23, US-31  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Compliance/QM/security report package  
**Source basis:** Proposal 5.7 compliance reporting | Spec 7, 5

**Acceptance emphasis**

Deliver compliance and controller views for qualification expiry, missing documents, notice read evidence, free Sundays, sickness/vacation, inactive users, login failures, role changes, and sensitive edits. AC: controller/QM exports provide auditable evidence with proper scope restrictions and repeatable results.

**Tasks**

- `US-32-T1` — Implement compliance status views for qualification expiry and missing mandatory documents.
- `US-32-T2` — Implement QM views for notice read stats, free Sundays, sickness/vacation, and inactivity.
- `US-32-T3` — Implement security activity views for login failures, role changes, and sensitive edits.
- `US-32-T4` — Build controller/QM export screens and scheduled report delivery hooks.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Any user-facing strings, notifications, or printed labels introduced here must ship with German default and English secondary resources.

**Planned prompt files**

- `docs/prompts/US-32-T1.md`
- `docs/prompts/US-32-T2.md`
- `docs/prompts/US-32-T3.md`
- `docs/prompts/US-32-T4.md`

### US-33 — Performance tuning, optional RLS, backup/restore, and security hardening

**Domain:** Hardening  
**Owner:** Architect  
**Story points:** 8  
**Components:** DB + Backend + DevOps  
**Dependencies:** US-31, US-32  
**Language / UX baseline:** Shared groundwork  
**Template / reference:** N/A  
**Deliverable / exit evidence:** Hardening evidence and remediation closeout  
**Source basis:** Proposal 7, 9, 10 | Spec 2, 4.1, 8, 10

**Acceptance emphasis**

Execute the hardening wave across database, API, and document access controls, including performance tuning, optional row-level security, backup/restore drills, and resilience testing. AC: the platform meets agreed security and performance baselines and is ready for UAT and production cutover.

**Tasks**

- `US-33-T1` — Apply optimization indexes, partition candidates, and query tuning on heavy tables/views.
- `US-33-T2` — Implement optional PostgreSQL RLS policies on high-risk operational datasets.
- `US-33-T3` — Execute backup/restore, rate-limit, and secure-document permission drills.
- `US-33-T4` — Run performance, penetration-ready, and resilience test cycles with remediation backlog.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Keep the implementation narrow to the story and its task list; do not absorb future-sprint behavior unless a dependency makes it unavoidable.
- Document assumptions explicitly in the task prompt or PR notes so later task prompts can build on stable decisions.

**Planned prompt files**

- `docs/prompts/US-33-T1.md`
- `docs/prompts/US-33-T2.md`
- `docs/prompts/US-33-T3.md`
- `docs/prompts/US-33-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-31: `US-31-T1`, `US-31-T2`, `US-31-T3`, `US-31-T4`
- US-32: `US-32-T1`, `US-32-T2`, `US-32-T3`, `US-32-T4`
- US-33: `US-33-T1`, `US-33-T2`, `US-33-T3`, `US-33-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
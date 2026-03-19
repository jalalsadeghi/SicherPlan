---
sprint: 12
label: "Sprint 12"
title: "Sprint 12 — Migration, UAT & go-live"
focus: "Migration, UAT & go-live"
proposal_phase: "Proposal Phase 6 | Migration/UAT/Release"
story_points: 18
story_count: 3
task_count: 12
stories:
  - US-34
  - US-35
  - US-36
---

# Sprint 12 — Migration, UAT & go-live

## Sprint summary

- **Focus:** Migration, UAT & go-live
- **Proposal phase / migration wave:** Proposal Phase 6 | Migration/UAT/Release
- **Planned story points:** 18
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver migration package, multilingual UAT, training, cutover, and hypercare.

## Exit criteria

Go-live checklist passes and production release is accepted.

## Incoming dependencies

- US-4 — Tenant, branch, mandate, setting, and lookup foundation (Sprint 2)
- US-7 — Customer master, contacts, addresses, and portal account linkage (Sprint 3)
- US-11 — Employee master file with private-profile split and role-based exposure (Sprint 4)
- US-13 — Subcontractor master, scope, contacts, and finance profile (Sprint 5)
- US-31 — Operational, commercial, and finance reporting read-model layer (Sprint 11)
- US-33 — Performance tuning, optional RLS, backup/restore, and security hardening (Sprint 11)

## Sprint-wide Codex notes

- Migration assets should reflect the stabilized write model. Do not redesign schema late in the delivery unless a blocker is truly structural.
- This sprint ties together migration, multilingual review, print-template signoff, UAT, cutover, hypercare, and business acceptance.
- German remains default and English secondary across training, print templates, and end-user validation scenarios.
- Release readiness is not just deployment: it includes seeded configuration, realistic migrated data, acceptance evidence, handover, and stabilization governance.

## Story breakdown

### US-34 — Data migration package, seed/reference data, and print-template finalization

**Domain:** Migration + Configuration  
**Owner:** Data Lead  
**Story points:** 8  
**Components:** Data + Backend + Web  
**Dependencies:** US-4, US-7, US-11, US-13, US-31  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Migration workbook/package and seeded configuration  
**Source basis:** Proposal 8-10 | Spec 8, 10

**Acceptance emphasis**

Prepare the data migration and configuration package for customers, employees, subcontractors, orders, documents, numbering rules, document types, and print templates. AC: migration templates and seeded reference data support realistic trial loads and output generation without schema rework.

**Tasks**

- `US-34-T1` — Define migration templates for customers, employees, subcontractors, orders, and documents.
- `US-34-T2` — Seed lookup/reference data, numbering rules, document types, and print templates.
- `US-34-T3` — Pilot historical document import and barcode/QR output generation.
- `US-34-T4` — Validate migrated records against portal, planning, and finance workflows.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-34-T1.md`
- `docs/prompts/US-34-T2.md`
- `docs/prompts/US-34-T3.md`
- `docs/prompts/US-34-T4.md`

### US-35 — UAT execution, multilingual review, training, and rollout readiness

**Domain:** UAT + Enablement  
**Owner:** PO / QA  
**Story points:** 5  
**Components:** Cross-cutting  
**Dependencies:** US-34, US-33  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin + Prokit Flutter  
**Deliverable / exit evidence:** UAT signoff, training pack, and release checklist  
**Source basis:** Proposal 8-10 | Spec 7-10

**Acceptance emphasis**

Execute business UAT against the three anchor workflows, finalize German/English labels and templates, and prepare training and go-live readiness. AC: business stakeholders sign off on UAT, language QA, training material, and cutover readiness.

**Tasks**

- `US-35-T1` — Execute UAT for customer-order-to-invoice, applicant-to-payroll, and subcontractor collaboration flows.
- `US-35-T2` — Prepare admin/user training materials and role-specific onboarding sessions.
- `US-35-T3` — Complete German/English text review, print-template signoff, and accessibility QA.
- `US-35-T4` — Finalize go-live checklist, cutover rehearsals, and business acceptance signoff.

**Codex implementation notes**

- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.
- Any user-facing strings, notifications, or printed labels introduced here must ship with German default and English secondary resources.

**Planned prompt files**

- `docs/prompts/US-35-T1.md`
- `docs/prompts/US-35-T2.md`
- `docs/prompts/US-35-T3.md`
- `docs/prompts/US-35-T4.md`

### US-36 — Production cutover, hypercare, KPI monitoring, and stabilization

**Domain:** Release  
**Owner:** DevOps / PO  
**Story points:** 5  
**Components:** DevOps + Cross-cutting  
**Dependencies:** US-35  
**Language / UX baseline:** Shared groundwork  
**Template / reference:** N/A  
**Deliverable / exit evidence:** Production release and hypercare handover  
**Source basis:** Proposal 8-10 | Spec 8-10

**Acceptance emphasis**

Run the production cutover and immediate hypercare cycle with issue routing, KPI monitoring, and stabilization governance. AC: production is live, support handover is in place, and the first stabilization backlog is prioritized from real operating feedback.

**Tasks**

- `US-36-T1` — Execute production cutover, configuration freeze, and monitored release steps.
- `US-36-T2` — Run hypercare triage, issue routing, and stabilization backlog management.
- `US-36-T3` — Confirm monitoring/KPI dashboards and operational support handover.
- `US-36-T4` — Hold sprint retrospective and release lessons-learned workshop.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Validation, override, and release behavior should remain service-layer controlled and auditable. Planning may read HR/partner projections, but it must not mutate those aggregates.
- Keep the implementation narrow to the story and its task list; do not absorb future-sprint behavior unless a dependency makes it unavoidable.

**Planned prompt files**

- `docs/prompts/US-36-T1.md`
- `docs/prompts/US-36-T2.md`
- `docs/prompts/US-36-T3.md`
- `docs/prompts/US-36-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-34: `US-34-T1`, `US-34-T2`, `US-34-T3`, `US-34-T4`
- US-35: `US-35-T1`, `US-35-T2`, `US-35-T3`, `US-35-T4`
- US-36: `US-36-T1`, `US-36-T2`, `US-36-T3`, `US-36-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
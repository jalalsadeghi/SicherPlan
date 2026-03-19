---
sprint: 5
label: "Sprint 05"
title: "Sprint 05 — Subcontractor management"
focus: "Subcontractor management"
proposal_phase: "Proposal Phase 2 | Spec Phase C (Partner)"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-13
  - US-14
  - US-15
---

# Sprint 05 — Subcontractor management

## Sprint summary

- **Focus:** Subcontractor management
- **Proposal phase / migration wave:** Proposal Phase 2 | Spec Phase C (Partner)
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver subcontractor master, worker compliance, and subcontractor self-service portal scope.

## Exit criteria

Partner companies can manage staff/documents and see only released work.

## Incoming dependencies

- US-4 — Tenant, branch, mandate, setting, and lookup foundation (Sprint 2)
- US-5 — Identity, role scope, session management, and audit foundation (Sprint 2)
- US-6 — Document, communication, information portal, and integration backbone (Sprint 2)

## Sprint-wide Codex notes

- Subcontractor data is tenant-scoped and externally visible only inside the approved partner portal boundaries.
- Partner modules own subcontractor company and worker master data. Planning can release work to partners, but it must not write partner master records directly.
- Compliance completeness for subcontractor workers should be queryable before staffing and release workflows begin in later sprints.
- Portal self-service must be bounded to the subcontractor's own company, staff, documents, and released operational scope.

## Story breakdown

### US-13 — Subcontractor master, scope, contacts, and finance profile

**Domain:** Partner  
**Owner:** Backend Lead  
**Story points:** 5  
**Components:** DB + Backend + Web  
**Dependencies:** US-4, US-5  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Subcontractor master module  
**Source basis:** Proposal 5.4, Appendix B | Spec 4.5

**Acceptance emphasis**

Implement the subcontractor aggregate with company master data, contacts, branch/mandate/site scope, finance profile, history, and portal enablement. AC: subcontractor records are tenant-scoped, commercially configured, and ready for planning and settlement flows.

**Tasks**

- `US-13-T1` — Implement subcontractor master, contacts, scope assignments, and finance profile.
- `US-13-T2` — Build admin UI for company data, scope, and portal enablement.
- `US-13-T3` — Add subcontractor history, attachments, and status lifecycle controls.
- `US-13-T4` — Enforce tenant-safe access and audit trails for subcontractor master data.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-13-T1.md`
- `docs/prompts/US-13-T2.md`
- `docs/prompts/US-13-T3.md`
- `docs/prompts/US-13-T4.md`

### US-14 — Subcontractor workers, qualifications, credentials, and compliance completeness

**Domain:** Partner  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-13, US-6  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Partner workforce and compliance module  
**Source basis:** Proposal 5.4, Appendix B | Spec 4.5, 6

**Acceptance emphasis**

Implement subcontractor-worker records, their qualifications, proofs, credentials, and compliance-readiness views for planning validation. AC: worker-level readiness and missing documents/expiry gaps are visible before staffing and release.

**Tasks**

- `US-14-T1` — Implement subcontractor workers, qualifications, document proofs, and credentials.
- `US-14-T2` — Build import/export and maintenance screens for subcontractor workforce records.
- `US-14-T3` — Implement compliance completeness and validity views per worker.
- `US-14-T4` — Create partner-side read models consumed by planning, field, and finance flows.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-14-T1.md`
- `docs/prompts/US-14-T2.md`
- `docs/prompts/US-14-T3.md`
- `docs/prompts/US-14-T4.md`

### US-15 — Subcontractor portal self-service, shift allocation, and visibility boundaries

**Domain:** Partner + Portal  
**Owner:** Web Lead  
**Story points:** 8  
**Components:** Web Portal + Backend  
**Dependencies:** US-13, US-14, US-5  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Subcontractor self-service portal  
**Source basis:** Proposal 4, 5.4, 6.3 | Spec 5 portal visibility chain

**Acceptance emphasis**

Deliver the subcontractor portal so partner administrators and planners can maintain their own staff data, upload documents, self-allocate to released shifts, and view actual/invoice-check status within approved scope. AC: subcontractors only see their own company and released assignments, and allocation honors validation rules.

**Tasks**

- `US-15-T1` — Build subcontractor portal authentication, role scope, and navigation.
- `US-15-T2` — Expose released positions, schedules, actuals, and invoice-check status in portal views.
- `US-15-T3` — Enable subcontractor self-allocation of workers to released shifts with validation feedback.
- `US-15-T4` — Support partner updates to staff data, documents, and confirmations inside allowed scope.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-15-T1.md`
- `docs/prompts/US-15-T2.md`
- `docs/prompts/US-15-T3.md`
- `docs/prompts/US-15-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-13: `US-13-T1`, `US-13-T2`, `US-13-T3`, `US-13-T4`
- US-14: `US-14-T1`, `US-14-T2`, `US-14-T3`, `US-14-T4`
- US-15: `US-15-T1`, `US-15-T2`, `US-15-T3`, `US-15-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
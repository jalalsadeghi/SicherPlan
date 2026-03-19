---
sprint: 7
label: "Sprint 07"
title: "Sprint 07 — Staffing engine"
focus: "Staffing engine"
proposal_phase: "Proposal Phase 3 | Spec Phase E"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-19
  - US-20
  - US-21
---

# Sprint 07 — Staffing engine

## Sprint summary

- **Focus:** Staffing engine
- **Proposal phase / migration wave:** Proposal Phase 3 | Spec Phase E
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver demand groups, assignments, validation engine, overrides, and release outputs.

## Exit criteria

Dispatchers can assign internal/partner staff with auditable validation results.

## Incoming dependencies

- US-18 — Shift plans, templates, recurrence series, and concrete shift generation (Sprint 6)
- US-12 — Qualifications, availability, absences, balances, allowances, and credentials foundation (Sprint 4)
- US-14 — Subcontractor workers, qualifications, credentials, and compliance completeness (Sprint 5)
- US-8 — Customer billing profile, rate cards, surcharge rules, and invoice parties (Sprint 3)
- US-6 — Document, communication, information portal, and integration backbone (Sprint 2)

## Sprint-wide Codex notes

- Demand groups, assignments, validation, and release logic are the heart of dispatch execution. Keep warnings, blocking rules, and override evidence durable and auditable.
- Planning may read HR and partner compliance projections, but it must not edit HR or subcontractor master truth.
- Released planning outputs are the contract for customer portal, subcontractor portal, employee mobile, field evidence, and finance. Treat visibility flags and release states as core business controls.
- Coverage calculations, validation messages, and staffing board interactions must support later UI prompts without changing the underlying planning model.

## Story breakdown

### US-19 — Demand groups, teams, assignments, and subcontractor releases

**Domain:** Ops  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-18, US-12, US-14  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Assignment and coverage engine  
**Source basis:** Proposal 5.5, Appendix D | Spec 4.6, 5

**Acceptance emphasis**

Implement the staffing backbone for demand groups, teams, concrete assignments, and subcontractor releases before worker-level allocation. AC: internal, subcontractor, and mixed workforce scenarios are supported with clear coverage status and team logic.

**Tasks**

- `US-19-T1` — Implement demand groups, teams, team members, and assignment entities.
- `US-19-T2` — Build staffing board APIs for assign, unassign, substitute, and mixed workforce scenarios.
- `US-19-T3` — Support subcontractor releases before worker-level assignment and team lead rules.
- `US-19-T4` — Provide coverage views for min/target staffing and confirmed/unconfirmed fill rates.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-19-T1.md`
- `docs/prompts/US-19-T2.md`
- `docs/prompts/US-19-T3.md`
- `docs/prompts/US-19-T4.md`

### US-20 — Validation engine, blocking/warning policies, and override audit trail

**Domain:** Ops Validation  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** Backend + Web  
**Dependencies:** US-19, US-12, US-14, US-8  
**Language / UX baseline:** Localization-ready  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Auditable planning validation engine  
**Source basis:** Proposal 5.5, Appendix E | Spec 5, 6

**Acceptance emphasis**

Implement the validation services that enforce qualification/function match, certificate validity, mandatory documents, customer blocks, double booking, rest limits, and minimum staffing. AC: configurable block/warn behavior is applied before release, and overrides are durable and auditable.

**Tasks**

- `US-20-T1` — Implement validation services for qualification/function match and certificate validity.
- `US-20-T2` — Implement blocking/warning checks for mandatory docs, customer blocks, and double booking.
- `US-20-T3` — Implement rules for rest periods, max hours, earnings thresholds, and minimum staffing.
- `US-20-T4` — Capture override reasons in audit-safe validation records and UI alerts.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-20-T1.md`
- `docs/prompts/US-20-T2.md`
- `docs/prompts/US-20-T3.md`
- `docs/prompts/US-20-T4.md`

### US-21 — Release workflows, deployment outputs, and visibility to downstream channels

**Domain:** Ops Release  
**Owner:** Web Lead  
**Story points:** 5  
**Components:** Backend + Web + Docs  
**Dependencies:** US-19, US-20, US-6  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Released planning outputs and visibility controls  
**Source basis:** Proposal 5.5, 6.1 | Spec 4.6, 7

**Acceptance emphasis**

Implement release states, print/PDF deployment outputs, planning communication, stealth mode, and visibility flags for employees, customers, and subcontractors. AC: released planning outputs flow cleanly to portal, mobile, and finance consumers without exposing hidden data.

**Tasks**

- `US-21-T1` — Implement release workflows and visibility flags for employees, customers, and subcontractors.
- `US-21-T2` — Generate deployment plans, protocols, and print/PDF outputs from released planning data.
- `US-21-T3` — Support planning communication, stealth mode, and group-targeted dispatch messages.
- `US-21-T4` — Expose released schedule read models to portals and mobile clients.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.

**Planned prompt files**

- `docs/prompts/US-21-T1.md`
- `docs/prompts/US-21-T2.md`
- `docs/prompts/US-21-T3.md`
- `docs/prompts/US-21-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-19: `US-19-T1`, `US-19-T2`, `US-19-T3`, `US-19-T4`
- US-20: `US-20-T1`, `US-20-T2`, `US-20-T3`, `US-20-T4`
- US-21: `US-21-T1`, `US-21-T2`, `US-21-T3`, `US-21-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
---
sprint: 4
label: "Sprint 04"
title: "Sprint 04 — Recruiting & employee core"
focus: "Recruiting & employee core"
proposal_phase: "Proposal Phase 2 | Spec Phase D (HR)"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-10
  - US-11
  - US-12
---

# Sprint 04 — Recruiting & employee core

## Sprint summary

- **Focus:** Recruiting & employee core
- **Proposal phase / migration wave:** Proposal Phase 2 | Spec Phase D (HR)
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver applicant intake, employee file, HR-private split, and core compliance/availability data.

## Exit criteria

Applicant-to-employee flow works and HR-sensitive data is role-restricted.

## Incoming dependencies

- US-4 — Tenant, branch, mandate, setting, and lookup foundation (Sprint 2)
- US-6 — Document, communication, information portal, and integration backbone (Sprint 2)
- US-5 — Identity, role scope, session management, and audit foundation (Sprint 2)

## Sprint-wide Codex notes

- Keep the HR private-data split strict: operational employee data lives separately from tightly restricted private HR data.
- The applicant-to-employee conversion must preserve status history, uploaded files, and consent evidence while creating a clean employee aggregate root.
- Planning and payroll will later read HR compliance and availability data, but they must not own or mutate HR master truth.
- Self-service endpoints should be designed for later mobile and portal consumption, even when only admin flows are implemented in this sprint.

## Story breakdown

### US-10 — Applicant intake, GDPR consent, and applicant workflow

**Domain:** Recruiting  
**Owner:** Backend Lead  
**Story points:** 5  
**Components:** Web + Backend  
**Dependencies:** US-4, US-6  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Applicant intake and workflow module  
**Source basis:** Proposal 5.3, 6.2 | Spec 4.4

**Acceptance emphasis**

Implement applicant intake through web/iframe forms, file uploads, consent capture, and a status-based recruiter workflow that supports accept/reject decisions. AC: applicants move from intake through decision with a durable status history and file trail.

**Tasks**

- `US-10-T1` — Build web/iframe applicant form with configurable fields, uploads, and GDPR consent capture.
- `US-10-T2` — Implement applicant status workflow and recruiter activity trail.
- `US-10-T3` — Create recruiter UI for review, interview notes, and accept/reject decisions.
- `US-10-T4` — Implement one-click transfer from applicant to employee aggregate.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Any user-facing strings, notifications, or printed labels introduced here must ship with German default and English secondary resources.

**Planned prompt files**

- `docs/prompts/US-10-T1.md`
- `docs/prompts/US-10-T2.md`
- `docs/prompts/US-10-T3.md`
- `docs/prompts/US-10-T4.md`

### US-11 — Employee master file with private-profile split and role-based exposure

**Domain:** HR  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-10, US-5  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Employee master file and restricted HR views  
**Source basis:** Proposal 5.3, Appendix C | Spec 4.4

**Acceptance emphasis**

Implement the employee aggregate with operational master data, private HR-only data, address history, notes, groups, photos, and app-user linkage. AC: employee records support operational use while sensitive HR fields remain visible only to authorized roles.

**Tasks**

- `US-11-T1` — Implement employee master, private profile, and address history models with strict role separation.
- `US-11-T2` — Build employee file UI for operational data, reminders, notes, photo, and group assignments.
- `US-11-T3` — Implement import/export and user-account linkage for employee app access.
- `US-11-T4` — Enforce audit logging for HR-sensitive changes and archival lifecycle.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Treat field evidence as durable business evidence: raw records are append-only, offline/sync tokens must be deliberate, and generated PDFs or exports should link back through the docs service.

**Planned prompt files**

- `docs/prompts/US-11-T1.md`
- `docs/prompts/US-11-T2.md`
- `docs/prompts/US-11-T3.md`
- `docs/prompts/US-11-T4.md`

### US-12 — Qualifications, availability, absences, balances, allowances, and credentials foundation

**Domain:** HR  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-11, US-6  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** HR compliance and availability foundation  
**Source basis:** Proposal 5.3, Appendix C, Appendix E | Spec 4.4, 6

**Acceptance emphasis**

Implement the compliance and planning-supporting HR structures for functions, qualifications, availability, absences, leave balances, time accounts, allowances, advances, and ID credentials. AC: planning, payroll, and self-service can consume accurate employee compliance and availability data.

**Tasks**

- `US-12-T1` — Implement function types, qualification types, employee qualifications, and document proofs.
- `US-12-T2` — Implement availability rules, event applications, absences, and leave balances.
- `US-12-T3` — Implement time accounts, allowances, advances, and ID credentials/badges.
- `US-12-T4` — Build self-service APIs for availability, free wishes, applications, and controlled profile updates.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Finance outputs must derive from released upstream data and the `actual_record` bridge. Preserve auditability and avoid hidden recalculation paths that bypass source aggregates.

**Planned prompt files**

- `docs/prompts/US-12-T1.md`
- `docs/prompts/US-12-T2.md`
- `docs/prompts/US-12-T3.md`
- `docs/prompts/US-12-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-10: `US-10-T1`, `US-10-T2`, `US-10-T3`, `US-10-T4`
- US-11: `US-11-T1`, `US-11-T2`, `US-11-T3`, `US-11-T4`
- US-12: `US-12-T1`, `US-12-T2`, `US-12-T3`, `US-12-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
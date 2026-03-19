---
sprint: 3
label: "Sprint 03"
title: "Sprint 03 — Customer management"
focus: "Customer management"
proposal_phase: "Proposal Phase 2 | Spec Phase C (CRM)"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-7
  - US-8
  - US-9
---

# Sprint 03 — Customer management

## Sprint summary

- **Focus:** Customer management
- **Proposal phase / migration wave:** Proposal Phase 2 | Spec Phase C (CRM)
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver customer master, commercial rules, billing profiles, and scoped customer portal views.

## Exit criteria

Customer data and portal access are tenant-safe and finance-ready.

## Incoming dependencies

- US-4 — Tenant, branch, mandate, setting, and lookup foundation (Sprint 2)
- US-5 — Identity, role scope, session management, and audit foundation (Sprint 2)
- US-6 — Document, communication, information portal, and integration backbone (Sprint 2)

## Sprint-wide Codex notes

- CRM owns customer commercial settings. Finance consumes these rules but must not duplicate or silently override the CRM source of truth.
- Customer users are tenant-scoped accounts. Customer-facing result views should hide personal names by default unless the tenant explicitly releases them.
- Customer portal work must stay read-only and scope-filtered. Never expose broad tenant datasets to customer users.
- Any billing, invoice-party, e-invoice, Leitweg, and dispatch settings created here must remain reusable by later finance stories without schema rework.

## Story breakdown

### US-7 — Customer master, contacts, addresses, and portal account linkage

**Domain:** CRM  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-4, US-5  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Customer master module and admin UI  
**Source basis:** Proposal 5.2 / Appendix A | Spec 4.3

**Acceptance emphasis**

Implement the customer aggregate with master data, contacts, reusable addresses, portal-account linkage, change tracking, and import/export support. AC: customer records are tenant-safe, searchable, auditable, and ready for downstream planning/finance use.

**Tasks**

- `US-7-T1` — Implement customer master, contacts, addresses, and portal user linkage.
- `US-7-T2` — Create admin UI for customer list/detail, status control, and contact management.
- `US-7-T3` — Add import/export, vCard, and change tracking for customer records.
- `US-7-T4` — Enforce tenant-safe visibility and audit rules for customer data.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-7-T1.md`
- `docs/prompts/US-7-T2.md`
- `docs/prompts/US-7-T3.md`
- `docs/prompts/US-7-T4.md`

### US-8 — Customer billing profile, rate cards, surcharge rules, and invoice parties

**Domain:** CRM  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-7  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Customer commercial settings module  
**Source basis:** Proposal 5.2 / Appendix A | Spec 4.3, 5

**Acceptance emphasis**

Implement customer commercial controls for billing profiles, payment/tax/bank settings, rate cards, surcharge rules, and alternative invoice parties. AC: versioned commercial rules are maintained in CRM and consumable by finance without data duplication.

**Tasks**

- `US-8-T1` — Implement customer billing profile, invoice parties, and payment/tax/bank fields.
- `US-8-T2` — Implement rate cards, rate lines, surcharge rules, and effective-date validation.
- `US-8-T3` — Build commercial settings UI with validation and finance read contracts.
- `US-8-T4` — Support invoice layout, e-invoice, Leitweg, dispatch, and dunning configuration.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-8-T1.md`
- `docs/prompts/US-8-T2.md`
- `docs/prompts/US-8-T3.md`
- `docs/prompts/US-8-T4.md`

### US-9 — Customer portal read models, collaboration views, and customer-specific controls

**Domain:** CRM + Portal  
**Owner:** Web Lead  
**Story points:** 5  
**Components:** Web Portal + Backend  
**Dependencies:** US-7, US-8, US-5, US-6  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Customer portal scope and collaboration views  
**Source basis:** Proposal 4, 5.2, 6.1 | Spec 5 portal visibility chain

**Acceptance emphasis**

Deliver the customer-facing read-only portal views for orders, schedules, watchbooks, timesheets, reports, and login history, plus history attachments and customer-specific employee blocking. AC: customer users see only their own released data and default views hide personal names unless explicitly released.

**Tasks**

- `US-9-T1` — Build customer portal authentication and scope filters from role/user associations.
- `US-9-T2` — Expose released orders, schedules, watchbooks, timesheets, and report read models.
- `US-9-T3` — Add customer history, attachments, login history visibility, and employee block maintenance.
- `US-9-T4` — Validate customer-facing views hide personal names by default unless explicitly released.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-9-T1.md`
- `docs/prompts/US-9-T2.md`
- `docs/prompts/US-9-T3.md`
- `docs/prompts/US-9-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-7: `US-7-T1`, `US-7-T2`, `US-7-T3`, `US-7-T4`
- US-8: `US-8-T1`, `US-8-T2`, `US-8-T3`, `US-8-T4`
- US-9: `US-9-T1`, `US-9-T2`, `US-9-T3`, `US-9-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
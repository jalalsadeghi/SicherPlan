---
sprint: 10
label: "Sprint 10"
title: "Sprint 10 — Payroll, billing & settlement"
focus: "Payroll, billing & settlement"
proposal_phase: "Proposal Phase 5 | Spec Phase G"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-28
  - US-29
  - US-30
---

# Sprint 10 — Payroll, billing & settlement

## Sprint summary

- **Focus:** Payroll, billing & settlement
- **Proposal phase / migration wave:** Proposal Phase 5 | Spec Phase G
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver payroll basis, exports, customer timesheets/invoices, and subcontractor invoice checks.

## Exit criteria

Finance outputs are generated from approved actuals and released commercial rules.

## Incoming dependencies

- US-12 — Qualifications, availability, absences, balances, allowances, and credentials foundation (Sprint 4)
- US-26 — Attendance normalization and actual_record bridge from planning and field evidence (Sprint 9)
- US-27 — Three-stage approval and reconciliation for operational and finance actuals (Sprint 9)
- US-8 — Customer billing profile, rate cards, surcharge rules, and invoice parties (Sprint 3)
- US-17 — Customer orders, planning records, and mode-specific detail structures (Sprint 6)
- US-14 — Subcontractor workers, qualifications, credentials, and compliance completeness (Sprint 5)
- US-15 — Subcontractor portal self-service, shift allocation, and visibility boundaries (Sprint 5)

## Sprint-wide Codex notes

- Payroll, customer billing, and subcontractor settlement must all derive from approved finance actuals and released commercial rules.
- Do not bypass CRM billing settings, HR pay settings, or partner commercial profiles when generating finance outputs.
- Generated finance outputs should link back to document records where files are produced, and outward integrations should use adapters/outbox patterns.
- Portal visibility for billing and partner settlement remains scoped and permission-driven; never expose internal finance data broadly.

## Story breakdown

### US-28 — Payroll tariffs, employee pay profiles, allowances, and export package

**Domain:** Finance Payroll  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-12, US-26, US-27  
**Language / UX baseline:** Localization-ready  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Payroll basis and export module  
**Source basis:** Proposal 5.6 payroll logic | Spec 4.8

**Acceptance emphasis**

Implement the payroll basis model with tariff tables, base rates, surcharge rules, employee pay profiles, allowance/advance hooks, and export batches. AC: payroll-relevant outputs derive from approved actuals and effective pay settings without bypassing the finance actual bridge.

**Tasks**

- `US-28-T1` — Implement payroll tariff tables, base rates, and surcharge rules by region/date/function.
- `US-28-T2` — Implement employee pay profiles, overrides, allowances, advances, and time-account hooks.
- `US-28-T3` — Build payroll export batches/items and provider-specific file/API adapters.
- `US-28-T4` — Support optional payslip import/archiving and payroll reconciliation reports.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Finance outputs must derive from released upstream data and the `actual_record` bridge. Preserve auditability and avoid hidden recalculation paths that bypass source aggregates.

**Planned prompt files**

- `docs/prompts/US-28-T1.md`
- `docs/prompts/US-28-T2.md`
- `docs/prompts/US-28-T3.md`
- `docs/prompts/US-28-T4.md`

### US-29 — Customer timesheets, invoices, layouts, and customer portal release

**Domain:** Finance Billing  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-8, US-17, US-26, US-27  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Customer timesheet and invoicing module  
**Source basis:** Proposal 5.6 customer billing, 6.1 | Spec 4.8, 5

**Acceptance emphasis**

Implement timesheets and customer invoices from approved actuals, including layouts, separate invoice parties, numbering, due dates, e-invoicing, dispatch rules, and portal release. AC: customer-facing billing outputs are reproducible and remain linked to source actuals and released commercial rules.

**Tasks**

- `US-29-T1` — Implement timesheets and timesheet lines from approved actual records.
- `US-29-T2` — Implement customer invoices, invoice lines, invoice numbering, layouts, and PDF output.
- `US-29-T3` — Support separate invoice addressees, dispatch rules, e-invoicing, and due-date control.
- `US-29-T4` — Expose released timesheets/invoices to customer portal according to permissions.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-29-T1.md`
- `docs/prompts/US-29-T2.md`
- `docs/prompts/US-29-T3.md`
- `docs/prompts/US-29-T4.md`

### US-30 — Subcontractor invoice checks, variance analysis, and commercial control

**Domain:** Finance Partner Control  
**Owner:** Backend Lead  
**Story points:** 5  
**Components:** DB + Backend + Web  
**Dependencies:** US-14, US-15, US-26, US-27  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Subcontractor commercial control workflow  
**Source basis:** Proposal 5.4/5.6, 6.3 | Spec 4.8, 5

**Acceptance emphasis**

Implement subcontractor invoice checks that compare assigned, actual, and approved hours/costs against partner commercial settings. AC: partner settlement has line-level variance visibility, controller workflow, and scoped visibility back to the subcontractor portal.

**Tasks**

- `US-30-T1` — Implement subcontractor invoice checks and line-level variance analysis.
- `US-30-T2` — Compare assigned, actual, and approved hours/costs against partner commercial settings.
- `US-30-T3` — Build controller UI for review, notes, approval state, and exception handling.
- `US-30-T4` — Expose invoice-check status and approved basis to the subcontractor portal.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-30-T1.md`
- `docs/prompts/US-30-T2.md`
- `docs/prompts/US-30-T3.md`
- `docs/prompts/US-30-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-28: `US-28-T1`, `US-28-T2`, `US-28-T3`, `US-28-T4`
- US-29: `US-29-T1`, `US-29-T2`, `US-29-T3`, `US-29-T4`
- US-30: `US-30-T1`, `US-30-T2`, `US-30-T3`, `US-30-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
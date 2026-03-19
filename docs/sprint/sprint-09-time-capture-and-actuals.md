---
sprint: 9
label: "Sprint 09"
title: "Sprint 09 — Time capture & actuals"
focus: "Time capture & actuals"
proposal_phase: "Proposal Phase 4-5 | Spec Phases F-G"
story_points: 24
story_count: 3
task_count: 12
stories:
  - US-25
  - US-26
  - US-27
---

# Sprint 09 — Time capture & actuals

## Sprint summary

- **Focus:** Time capture & actuals
- **Proposal phase / migration wave:** Proposal Phase 4-5 | Spec Phases F-G
- **Planned story points:** 24
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver time capture, attendance normalization, actual bridge, and three-stage approval.

## Exit criteria

Raw time evidence converts into approved actuals without breaking auditability.

## Incoming dependencies

- US-3 — Vben Admin shell, Prokit mobile shell, theme tokens, and localization (Sprint 1)
- US-16 — Operational master data: locations, routes, checkpoints, and equipment catalogs (Sprint 6)
- US-21 — Release workflows, deployment outputs, and visibility to downstream channels (Sprint 7)
- US-19 — Demand groups, teams, assignments, and subcontractor releases (Sprint 7)
- US-20 — Validation engine, blocking/warning policies, and override audit trail (Sprint 7)

## Sprint-wide Codex notes

- Raw time capture is evidence and should stay append-only except for controlled validation-status updates. Corrections create new records or derived statuses rather than overwriting history.
- Attendance summaries are derived artifacts. Finance-owned `actual_record` is the single bridge from field evidence to payroll, timesheets, invoices, and partner control.
- Approval stages, discrepancy handling, and manual adjustment flows must preserve provenance and support later reporting.
- Device, terminal, IP, and geolocation policy violations should reject or flag captures while still preserving the raw attempt for audit.

## Story breakdown

### US-25 — Time capture devices, policies, raw event ingest, and context validation

**Domain:** Field Time Capture  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** Backend + Web + Mobile  
**Dependencies:** US-3, US-16, US-21  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin + Prokit Flutter  
**Deliverable / exit evidence:** Time capture ingest pipeline and device policy controls  
**Source basis:** Proposal 5.6, Appendix E | Spec 4.7, 6

**Acceptance emphasis**

Implement browser/mobile/shared-terminal time capture with devices, policies, credential scans, and raw append-only time events. AC: device/IP/geolocation/terminal rules can reject or flag invalid captures while retaining raw evidence for audit.

**Tasks**

- `US-25-T1` — Implement time capture devices, device types, and context policies.
- `US-25-T2` — Build browser/mobile/shared-terminal ingest flows for raw time events.
- `US-25-T3` — Enforce device/IP/geolocation/terminal validation and retain flagged raw attempts.
- `US-25-T4` — Support QR/barcode/RFID/NFC credential capture for employees and subcontractor workers.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.

**Planned prompt files**

- `docs/prompts/US-25-T1.md`
- `docs/prompts/US-25-T2.md`
- `docs/prompts/US-25-T3.md`
- `docs/prompts/US-25-T4.md`

### US-26 — Attendance normalization and actual_record bridge from planning and field evidence

**Domain:** Finance Bridge  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** Backend  
**Dependencies:** US-19, US-25  
**Language / UX baseline:** Localization-ready  
**Template / reference:** N/A  
**Deliverable / exit evidence:** Attendance summaries and finance actual bridge  
**Source basis:** Proposal 5.6, Appendix D | Spec 4.7, 4.8, 5

**Acceptance emphasis**

Normalize raw time evidence into attendance summaries and finance-owned actual records that preserve planned vs actual times, payable/billable minutes, and correction safety. AC: actuals are derived without mutating raw evidence and can feed payroll, timesheets, invoices, and partner settlement.

**Tasks**

- `US-26-T1` — Implement attendance_record derivation from raw time events and released assignments.
- `US-26-T2` — Implement finance.actual_record bridge with planned/actual times, breaks, and payable/billable minutes.
- `US-26-T3` — Surface discrepancy flags for missed checkout, duplicates, and manual corrections.
- `US-26-T4` — Keep raw evidence append-only while allowing controlled derived-status transitions.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Treat field evidence as durable business evidence: raw records are append-only, offline/sync tokens must be deliberate, and generated PDFs or exports should link back through the docs service.
- Finance outputs must derive from released upstream data and the `actual_record` bridge. Preserve auditability and avoid hidden recalculation paths that bypass source aggregates.

**Planned prompt files**

- `docs/prompts/US-26-T1.md`
- `docs/prompts/US-26-T2.md`
- `docs/prompts/US-26-T3.md`
- `docs/prompts/US-26-T4.md`

### US-27 — Three-stage approval and reconciliation for operational and finance actuals

**Domain:** Finance Workflow  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** Backend + Web  
**Dependencies:** US-26, US-20  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Approved actuals and reconciliation workflow  
**Source basis:** Proposal 5.6 | Spec 4.8, 6

**Acceptance emphasis**

Implement the approval chain from employee/field lead through operational confirmation to finance finalization, including adjustments for sickness, cancellations, replacements, expenses, flat rates, and customer-side corrections. AC: every final actual has an auditable approval history and correct adjustment lineage.

**Tasks**

- `US-27-T1` — Implement preliminary actual submission by employee/field lead and operational confirmation.
- `US-27-T2` — Implement finance reconciliation for sickness, cancellations, replacements, and customer adjustments.
- `US-27-T3` — Support allowances, expenses, flat rates, and comments on actuals.
- `US-27-T4` — Build approval UI and audit trail for three-stage signoff.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-27-T1.md`
- `docs/prompts/US-27-T2.md`
- `docs/prompts/US-27-T3.md`
- `docs/prompts/US-27-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-25: `US-25-T1`, `US-25-T2`, `US-25-T3`, `US-25-T4`
- US-26: `US-26-T1`, `US-26-T2`, `US-26-T3`, `US-26-T4`
- US-27: `US-27-T1`, `US-27-T2`, `US-27-T3`, `US-27-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
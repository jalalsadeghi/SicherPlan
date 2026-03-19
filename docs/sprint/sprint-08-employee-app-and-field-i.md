---
sprint: 8
label: "Sprint 08"
title: "Sprint 08 — Employee app & field I"
focus: "Employee app & field I"
proposal_phase: "Proposal Phase 4 | Spec Phases B/F"
story_points: 24
story_count: 3
task_count: 12
stories:
  - US-22
  - US-23
  - US-24
---

# Sprint 08 — Employee app & field I

## Sprint summary

- **Focus:** Employee app & field I
- **Proposal phase / migration wave:** Proposal Phase 4 | Spec Phases B/F
- **Planned story points:** 24
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver employee app core, information portal feed, watchbook, and patrol control flows.

## Exit criteria

Field users can work from mobile; watchbook and patrol evidence are revision-safe.

## Incoming dependencies

- US-3 — Vben Admin shell, Prokit mobile shell, theme tokens, and localization (Sprint 1)
- US-12 — Qualifications, availability, absences, balances, allowances, and credentials foundation (Sprint 4)
- US-21 — Release workflows, deployment outputs, and visibility to downstream channels (Sprint 7)
- US-6 — Document, communication, information portal, and integration backbone (Sprint 2)
- US-16 — Operational master data: locations, routes, checkpoints, and equipment catalogs (Sprint 6)

## Sprint-wide Codex notes

- Only released information should reach employee mobile and external-facing field flows.
- Watchbook, patrol, and mandatory-notice features are evidence-bearing workflows. Revision-safe outputs and read acknowledgements are part of the product, not optional extras.
- Patrol and mobile flows must be ready for intermittent connectivity. Keep offline tokens and replay-safe synchronization in mind from the first implementation pass.
- DE/EN parity and shared theme behavior must be preserved across web and mobile surfaces, not only in admin UI.

## Story breakdown

### US-22 — Employee mobile app: schedules, actions, documents, notifications, and theme/i18n parity

**Domain:** Mobile  
**Owner:** Mobile Lead  
**Story points:** 8  
**Components:** Mobile + Backend  
**Dependencies:** US-3, US-12, US-21  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Prokit Flutter  
**Deliverable / exit evidence:** Employee mobile app core  
**Source basis:** Proposal 5.3, 5.6, 6.2, 7 | Spec 4.4, 4.6, 4.7

**Acceptance emphasis**

Deliver the employee-facing mobile app for schedules, shift details, confirmations, event applications, documents, notifications, QR/barcode display, and calendar export using the Prokit reference patterns. AC: the mobile experience is usable in German and English, respects theme tokens, and surfaces only released information.

**Tasks**

- `US-22-T1` — Adapt Prokit-based mobile shell for employee login, role guard, and profile context.
- `US-22-T2` — Build monthly schedule, shift detail, maps, confirm/decline, and event-application flows.
- `US-22-T3` — Implement document download, push notifications, calendar export, and QR/barcode display.
- `US-22-T4` — Ensure mobile UI supports German default, English secondary, and light/dark theme tokens.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.
- Validation, override, and release behavior should remain service-layer controlled and auditable. Planning may read HR/partner projections, but it must not mutate those aggregates.

**Planned prompt files**

- `docs/prompts/US-22-T1.md`
- `docs/prompts/US-22-T2.md`
- `docs/prompts/US-22-T3.md`
- `docs/prompts/US-22-T4.md`

### US-23 — Information feed, mandatory notice acknowledgements, and online watchbook

**Domain:** Field + Info  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** Backend + Web + Mobile  
**Dependencies:** US-6, US-16, US-21  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin + Prokit Flutter  
**Deliverable / exit evidence:** Notice feed and watchbook execution  
**Source basis:** Proposal 5.2, 5.7, 6.1 | Spec 4.2, 4.7, 5

**Acceptance emphasis**

Deliver the information portal feed and mandatory notice consumption in web/mobile, plus the online watchbook with entries, attachments, supervisor review, and revision-safe daily PDFs. AC: field and customer-facing watchbook evidence is durable, reviewable, and exportable.

**Tasks**

- `US-23-T1` — Build information portal feed and mandatory notice read confirmation in web/mobile.
- `US-23-T2` — Implement watchbook creation, entries, attachments/photos, and supervisor review.
- `US-23-T3` — Generate revision-safe daily watchbook PDF outputs and portal-facing read models.
- `US-23-T4` — Support customer/subcontractor participation in watchbook flows where enabled.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.

**Planned prompt files**

- `docs/prompts/US-23-T1.md`
- `docs/prompts/US-23-T2.md`
- `docs/prompts/US-23-T3.md`
- `docs/prompts/US-23-T4.md`

### US-24 — Guard patrol control, checkpoint capture, and offline synchronization

**Domain:** Field Patrol  
**Owner:** Mobile Lead  
**Story points:** 8  
**Components:** Mobile + Backend  
**Dependencies:** US-16, US-23  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Prokit Flutter  
**Deliverable / exit evidence:** Patrol control workflow with offline support  
**Source basis:** Proposal 5.2 guard patrol control | Spec 4.6, 4.7

**Acceptance emphasis**

Implement smartphone-based guard patrol control with route rounds, checkpoints, scan methods, exception/abort evidence, and offline synchronization. AC: patrol events are append-only, sync correctly, and link back to watchbook/evaluation context.

**Tasks**

- `US-24-T1` — Implement patrol round start/stop flows and checkpoint capture events.
- `US-24-T2` — Support QR, barcode, NFC/manual scan methods and exception/abort evidence.
- `US-24-T3` — Implement offline storage and sync-token handling for patrol workflows.
- `US-24-T4` — Link patrol outputs into watchbook entries, evaluations, and compliance evidence.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.
- Treat field evidence as durable business evidence: raw records are append-only, offline/sync tokens must be deliberate, and generated PDFs or exports should link back through the docs service.

**Planned prompt files**

- `docs/prompts/US-24-T1.md`
- `docs/prompts/US-24-T2.md`
- `docs/prompts/US-24-T3.md`
- `docs/prompts/US-24-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-22: `US-22-T1`, `US-22-T2`, `US-22-T3`, `US-22-T4`
- US-23: `US-23-T1`, `US-23-T2`, `US-23-T3`, `US-23-T4`
- US-24: `US-24-T1`, `US-24-T2`, `US-24-T3`, `US-24-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
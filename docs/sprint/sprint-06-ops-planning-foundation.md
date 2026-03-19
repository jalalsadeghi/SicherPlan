---
sprint: 6
label: "Sprint 06"
title: "Sprint 06 — Ops planning foundation"
focus: "Ops planning foundation"
proposal_phase: "Proposal Phase 3 | Spec Phase E"
story_points: 24
story_count: 3
task_count: 12
stories:
  - US-16
  - US-17
  - US-18
---

# Sprint 06 — Ops planning foundation

## Sprint summary

- **Focus:** Ops planning foundation
- **Proposal phase / migration wave:** Proposal Phase 3 | Spec Phase E
- **Planned story points:** 24
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Deliver locations, routes, orders, planning records, and shift generation backbone.

## Exit criteria

Orders and mode-specific planning records generate reusable shifts and templates.

## Incoming dependencies

- US-7 — Customer master, contacts, addresses, and portal account linkage (Sprint 3)
- US-13 — Subcontractor master, scope, contacts, and finance profile (Sprint 5)
- US-8 — Customer billing profile, rate cards, surcharge rules, and invoice parties (Sprint 3)

## Sprint-wide Codex notes

- This is the operational backbone sprint. Use explicit foreign keys from customer order through planning record, shift structures, and operational master data.
- Do not embed finance or field-side write rules inside planning aggregates. Planning owns released operational structure; downstream modules consume it.
- Board-style dispatch and schedule queries will become performance-sensitive. Favor indexes and query paths that support heavy planning views early.
- Operational location, route, checkpoint, and map data should reuse shared addresses and geolocation patterns wherever possible.

## Story breakdown

### US-16 — Operational master data: locations, routes, checkpoints, and equipment catalogs

**Domain:** Ops  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-7, US-13  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Operational location and route master data  
**Source basis:** Proposal 5.5, Appendix D | Spec 4.6

**Acceptance emphasis**

Implement the reusable operational context entities needed for event, object/site, trade fair, and patrol planning, including maps and checkpoints. AC: dispatchers can manage sites, venues, fairs, routes, and equipment catalogs with tenant-safe geo-enabled records.

**Tasks**

- `US-16-T1` — Implement requirement types, equipment catalog, sites, venues, trade fairs, and patrol routes.
- `US-16-T2` — Implement trade fair zones and patrol checkpoints with map/geolocation data.
- `US-16-T3` — Build admin UI and import tools for operational locations and route master data.
- `US-16-T4` — Integrate address reuse, geo coordinates, and watchbook/patrol cross-links.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Treat field evidence as durable business evidence: raw records are append-only, offline/sync tokens must be deliberate, and generated PDFs or exports should link back through the docs service.

**Planned prompt files**

- `docs/prompts/US-16-T1.md`
- `docs/prompts/US-16-T2.md`
- `docs/prompts/US-16-T3.md`
- `docs/prompts/US-16-T4.md`

### US-17 — Customer orders, planning records, and mode-specific detail structures

**Domain:** Ops  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-16, US-7, US-8  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Order and planning-record backbone  
**Source basis:** Proposal 5.5, Appendix D | Spec 4.6

**Acceptance emphasis**

Implement orders/projects and planning records that connect commercial scope to operational planning across event, site, trade fair, and patrol modes. AC: orders and planning records carry requirements, equipment, attachments, release states, and mode-specific details without duplicating commercial ownership.

**Tasks**

- `US-17-T1` — Implement customer orders, equipment lines, requirement lines, and attachments.
- `US-17-T2` — Implement planning_record with mode-specific detail tables for event/site/trade fair/patrol.
- `US-17-T3` — Build order/planning APIs and UI for release states, notes, and document packages.
- `US-17-T4` — Ensure commercial scope stays linked to customer billing rules and downstream finance flows.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-17-T1.md`
- `docs/prompts/US-17-T2.md`
- `docs/prompts/US-17-T3.md`
- `docs/prompts/US-17-T4.md`

### US-18 — Shift plans, templates, recurrence series, and concrete shift generation

**Domain:** Ops  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-17  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Reusable shift-planning framework  
**Source basis:** Proposal 5.5, Appendix D | Spec 4.6

**Acceptance emphasis**

Implement the transaction-heavy shift-planning framework with templates, recurring series, copy logic, and concrete shift generation. AC: dispatchers can generate and maintain reusable shift structures for different planning modes with performant board queries.

**Tasks**

- `US-18-T1` — Implement shift plans, templates, recurrence series, and concrete shift generation.
- `US-18-T2` — Support quick copy/day-week reuse, recurring exceptions, and workforce-scope selection.
- `US-18-T3` — Build shift maintenance UI with meeting point, location, break, type, and visibility flags.
- `US-18-T4` — Optimize indexes and query paths for board-style planning performance.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Validation, override, and release behavior should remain service-layer controlled and auditable. Planning may read HR/partner projections, but it must not mutate those aggregates.

**Planned prompt files**

- `docs/prompts/US-18-T1.md`
- `docs/prompts/US-18-T2.md`
- `docs/prompts/US-18-T3.md`
- `docs/prompts/US-18-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-16: `US-16-T1`, `US-16-T2`, `US-16-T3`, `US-16-T4`
- US-17: `US-17-T1`, `US-17-T2`, `US-17-T3`, `US-17-T4`
- US-18: `US-18-T1`, `US-18-T2`, `US-18-T3`, `US-18-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
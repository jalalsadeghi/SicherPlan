---
sprint: 1
label: "Sprint 01"
title: "Sprint 01 — Inception & setup"
focus: "Inception & setup"
proposal_phase: "Proposal Phase 0 | Inception"
story_points: 21
story_count: 3
task_count: 12
stories:
  - US-1
  - US-2
  - US-3
---

# Sprint 01 — Inception & setup

## Sprint summary

- **Focus:** Inception & setup
- **Proposal phase / migration wave:** Proposal Phase 0 | Inception
- **Planned story points:** 21
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Establish delivery guardrails, environments, and UI/i18n/theme shells.

## Exit criteria

Backlog approved; CI/CD active; Vben/Prokit shells demo DE/EN and light/dark.

## Incoming dependencies

- None. This sprint establishes the baseline for later work.

## Sprint-wide Codex notes

- Treat this sprint as the baseline for every later Codex task: repository conventions, acceptance traceability, CI/CD, web shell, mobile shell, theme tokens, and DE/EN localization must exist before business modules expand.
- Do not start business-domain persistence before the core delivery guardrails are in place. The purpose here is to reduce rework in later migrations and UI scaffolding.
- Web shell work must align with Vben Admin patterns. Mobile shell work must align with Prokit Flutter patterns. Theme tokens are fixed: light `rgb(40,170,170)`, dark `rgb(35,200,205)`.
- German is the default language. English is secondary. Every user-facing message, navigation label, and form validation path created from this point onward must follow that rule.

## Story breakdown

### US-1 — Discovery, backlog confirmation, and acceptance traceability

**Domain:** Delivery Management  
**Owner:** PO / BA  
**Story points:** 5  
**Components:** Cross-cutting  
**Dependencies:** —  
**Language / UX baseline:** Shared groundwork  
**Template / reference:** N/A  
**Deliverable / exit evidence:** Approved backlog baseline, acceptance matrix, dependency map  
**Source basis:** Proposal 8-10 | Spec 8-10

**Acceptance emphasis**

Translate the updated proposal and implementation spec into a sprint-ready product backlog with clear dependencies, Definition of Ready/Done, and acceptance coverage for the three reference workflows. AC: scope baseline, dependency map, and acceptance matrix are approved.

**Tasks**

- `US-1-T1` — Review proposal, implementation spec, and the three end-to-end workflows.
- `US-1-T2` — Define backlog epics, sprint goals, dependencies, and Definition of Ready/Done.
- `US-1-T3` — Confirm migration assumptions, external integrations, and non-functional requirements.
- `US-1-T4` — Create demo checklist and traceability matrix from story to acceptance criteria.

**Codex implementation notes**

- Keep the implementation narrow to the story and its task list; do not absorb future-sprint behavior unless a dependency makes it unavoidable.
- Document assumptions explicitly in the task prompt or PR notes so later task prompts can build on stable decisions.
- Favor service-layer boundaries over shared cross-module mutation. Read projections are acceptable; remote writes are not.

**Planned prompt files**

- `docs/prompts/US-1-T1.md`
- `docs/prompts/US-1-T2.md`
- `docs/prompts/US-1-T3.md`
- `docs/prompts/US-1-T4.md`

### US-2 — Repository, environments, CI/CD, and observability baseline

**Domain:** Engineering Platform  
**Owner:** DevOps  
**Story points:** 8  
**Components:** DevOps + Cross-cutting  
**Dependencies:** US-1  
**Language / UX baseline:** Shared groundwork  
**Template / reference:** N/A  
**Deliverable / exit evidence:** Working dev/staging pipeline and runtime baseline  
**Source basis:** Proposal 7-8 | Spec 10

**Acceptance emphasis**

Create the engineering delivery platform for backend, web, and mobile development, including environments, pipelines, and runtime observability. AC: hello-world builds/deploys across stacks with lint, test, migration, and health-check automation.

**Tasks**

- `US-2-T1` — Create repository structure, branching strategy, and coding conventions across backend, web, and mobile.
- `US-2-T2` — Provision development/staging environments, secrets, and config management.
- `US-2-T3` — Build CI pipelines for lint, test, migrations, builds, and deployments.
- `US-2-T4` — Set up logging, tracing, health checks, and error handling standards.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.

**Planned prompt files**

- `docs/prompts/US-2-T1.md`
- `docs/prompts/US-2-T2.md`
- `docs/prompts/US-2-T3.md`
- `docs/prompts/US-2-T4.md`

### US-3 — Vben Admin shell, Prokit mobile shell, theme tokens, and localization

**Domain:** UX Foundation  
**Owner:** Frontend Lead  
**Story points:** 8  
**Components:** Web + Mobile  
**Dependencies:** US-1, US-2  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin + Prokit Flutter  
**Deliverable / exit evidence:** Web/mobile shells with i18n and theme switching  
**Source basis:** Proposal 7 | Spec 10 | Vben/Prokit refs

**Acceptance emphasis**

Bootstrap the web admin/portal shell on Vben Admin and the employee mobile shell on Prokit Flutter patterns, with DE/EN localization and the requested light/dark primary colors. AC: both shells support German default, English secondary, and theme switching with shared navigation and message patterns.

**Tasks**

- `US-3-T1` — Bootstrap Vben Admin workspace and role-aware navigation shell.
- `US-3-T2` — Bootstrap Flutter mobile shell from Prokit reference and define app navigation.
- `US-3-T3` — Implement theme tokens using light rgb(40,170,170) and dark rgb(35,200,205) across web/mobile.
- `US-3-T4` — Implement DE/EN i18n resource structure and shared localization rules for UI and API messages.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Mobile-facing work should use Prokit-style navigation and state patterns, and must preserve theme and DE/EN parity with the web experience.

**Planned prompt files**

- `docs/prompts/US-3-T1.md`
- `docs/prompts/US-3-T2.md`
- `docs/prompts/US-3-T3.md`
- `docs/prompts/US-3-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-1: `US-1-T1`, `US-1-T2`, `US-1-T3`, `US-1-T4`
- US-2: `US-2-T1`, `US-2-T2`, `US-2-T3`, `US-2-T4`
- US-3: `US-3-T1`, `US-3-T2`, `US-3-T3`, `US-3-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
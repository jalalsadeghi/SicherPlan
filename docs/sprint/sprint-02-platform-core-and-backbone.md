---
sprint: 2
label: "Sprint 02"
title: "Sprint 02 — Platform core & backbone"
focus: "Platform core & backbone"
proposal_phase: "Proposal Phase 1 | Spec Phases A-B"
story_points: 24
story_count: 3
task_count: 12
stories:
  - US-4
  - US-5
  - US-6
---

# Sprint 02 — Platform core & backbone

## Sprint summary

- **Focus:** Platform core & backbone
- **Proposal phase / migration wave:** Proposal Phase 1 | Spec Phases A-B
- **Planned story points:** 24
- **Story count:** 3
- **Task count:** 12

## Sprint goal

Stand up tenant foundation, IAM/RBAC, documents, communication, notices, and integration outbox.

## Exit criteria

Tenant onboarding, auth, audit, versioned docs, notices, and message pipeline work end-to-end.

## Incoming dependencies

- US-1 — Discovery, backlog confirmation, and acceptance traceability (Sprint 1)
- US-2 — Repository, environments, CI/CD, and observability baseline (Sprint 1)

## Sprint-wide Codex notes

- This sprint establishes the platform backbone: tenant isolation, IAM/RBAC, audit, documents, communications, notices, and integration outbox. Downstream modules depend on these contracts remaining stable.
- Use explicit tenant scoping and composite foreign keys wherever cross-tenant leakage would be risky. Portal actors remain scoped users inside a tenant, not separate tenants.
- All generated outputs and uploaded files should be represented through the docs service. External side effects belong behind the outbox and async integration adapters, not inside transactional business writes.
- Sensitive security and business actions must be auditable from day one. Capture login and domain audit trails before broadening business scope.

## Story breakdown

### US-4 — Tenant, branch, mandate, setting, and lookup foundation

**Domain:** Core  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-1, US-2  
**Language / UX baseline:** Localization-ready  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Core tenant administration and seeded lookup model  
**Source basis:** Proposal 5.1, 8 | Spec 4.1, 8, 9

**Acceptance emphasis**

Implement the core platform entities and administration flows that anchor tenant isolation, branch/mandate scoping, numbering rules, and tenant-extensible lookup values. AC: tenant onboarding and settings management work with audit-safe lifecycle states and seeded lookup domains.

**Tasks**

- `US-4-T1` — Create migrations/models for core.tenant, core.branch, core.mandate, core.tenant_setting, and core.lookup_value.
- `US-4-T2` — Build admin APIs/services for tenant onboarding and settings management.
- `US-4-T3` — Seed system and tenant lookup domains needed by downstream modules.
- `US-4-T4` — Create web admin screens for tenants, branches, mandates, settings, and archival states.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Any user-facing strings, notifications, or printed labels introduced here must ship with German default and English secondary resources.

**Planned prompt files**

- `docs/prompts/US-4-T1.md`
- `docs/prompts/US-4-T2.md`
- `docs/prompts/US-4-T3.md`
- `docs/prompts/US-4-T4.md`

### US-5 — Identity, role scope, session management, and audit foundation

**Domain:** IAM  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-4  
**Language / UX baseline:** Localization-ready  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** IAM/RBAC services with audit trail  
**Source basis:** Proposal 4, 5.1 | Spec 4.1

**Acceptance emphasis**

Implement unified login, role-based access control, scoped role assignments, session handling, and immutable security/business audit trails. AC: authentication, scoping, and sensitive action auditability are enforced across modules.

**Tasks**

- `US-5-T1` — Implement user_account, roles, permissions, role scopes, sessions, and external identity models.
- `US-5-T2` — Build login/logout, password reset, session refresh, and MFA/SSO-ready hooks.
- `US-5-T3` — Enforce RBAC middleware and tenant/branch/mandate scoping on APIs.
- `US-5-T4` — Capture login events and business audit events for sensitive actions.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- Any user-facing strings, notifications, or printed labels introduced here must ship with German default and English secondary resources.

**Planned prompt files**

- `docs/prompts/US-5-T1.md`
- `docs/prompts/US-5-T2.md`
- `docs/prompts/US-5-T3.md`
- `docs/prompts/US-5-T4.md`

### US-6 — Document, communication, information portal, and integration backbone

**Domain:** Platform Services  
**Owner:** Backend Lead  
**Story points:** 8  
**Components:** DB + Backend + Web  
**Dependencies:** US-4, US-5  
**Language / UX baseline:** DE default + EN secondary  
**Template / reference:** Vben Admin  
**Deliverable / exit evidence:** Docs/comm/info/integration services and admin UI  
**Source basis:** Proposal 5.1, 5.7 | Spec 4.2

**Acceptance emphasis**

Stand up the shared platform-service aggregates for versioned documents, templated communications, mandatory notices/read confirmations, and external integration jobs/outbox events. AC: files, messages, notices, and async integration events work as reusable cross-module services.

**Tasks**

- `US-6-T1` — Implement docs.document, document_version, document_link, and object-storage integration.
- `US-6-T2` — Implement communication templates, outbound messages, recipients, and delivery attempts.
- `US-6-T3` — Build info.notice, audience, read confirmation, and attachment flows.
- `US-6-T4` — Implement integration endpoints, import/export jobs, and transactional outbox workers.

**Codex implementation notes**

- Lead with migration-safe database design: Alembic revisions, SQLAlchemy models, explicit foreign keys, and Pydantic Create/Update/Read/List schemas should be planned before controller wiring.
- Web-facing work should follow Vben Admin conventions for route guards, list/detail pages, form state, and reusable CRUD patterns.
- External-facing scopes must remain tenant-safe and role-scoped. Default to least-privilege visibility, especially for names, finance data, and released operational results.

**Planned prompt files**

- `docs/prompts/US-6-T1.md`
- `docs/prompts/US-6-T2.md`
- `docs/prompts/US-6-T3.md`
- `docs/prompts/US-6-T4.md`

## Task-order reminder

When creating a future task prompt for this sprint, keep the backlog order:

- US-4: `US-4-T1`, `US-4-T2`, `US-4-T3`, `US-4-T4`
- US-5: `US-5-T1`, `US-5-T2`, `US-5-T3`, `US-5-T4`
- US-6: `US-6-T1`, `US-6-T2`, `US-6-T3`, `US-6-T4`

## Related files

- `AGENTS.md`
- `docs/prompts/README.md`
- `docs/prompts/task-index.md`
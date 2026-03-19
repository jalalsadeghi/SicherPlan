# Repository Structure

## Task anchor

- Task: `US-2-T1`

## Repository decision

SicherPlan should remain a single repository with multiple app workspaces.

### Reasoning

- The delivery plan couples backend, web, mobile, docs, and platform conventions tightly in Sprint 1 and Sprint 2.
- Tenant isolation, role scope, theme/i18n rules, and workflow traceability are cross-cutting concerns that benefit from one shared docs and CI surface.
- The current repository is greenfield and documentation-led; splitting it now would create coordination overhead without reducing implementation risk.
- Later CI/CD can still build and deploy backend, web, and mobile independently inside one repository.

## Top-level layout

- `backend/` FastAPI backend workspace
- `web/` Vue 3 + Vben Admin web workspace
- `mobile/` Flutter mobile workspace
- `infra/` infrastructure and environment support files
- `docs/` sprint plans, prompts, discovery, backlog, engineering, and QA docs

## Backend layout

### Purpose

The backend must expose bounded contexts as first-class packages from day one so later tasks do not drift into a generic layered monolith.

### Structure

- `backend/app/`
- `backend/app/modules/`
- `backend/alembic/`
- `backend/tests/`

### Bounded-context packages

- `backend/app/modules/core`
- `backend/app/modules/iam`
- `backend/app/modules/platform_services`
- `backend/app/modules/customers`
- `backend/app/modules/recruiting`
- `backend/app/modules/employees`
- `backend/app/modules/subcontractors`
- `backend/app/modules/planning`
- `backend/app/modules/field_execution`
- `backend/app/modules/finance`
- `backend/app/modules/reporting`

### Expected evolution inside each module

As implementation starts, each module may grow its own:

- models
- schemas
- services
- repositories
- routers
- read models
- tests

The key rule is ownership by bounded context. Shared technical helpers may exist, but business truth should not be collapsed into a generic global `services` package.

## Web layout

- `web/` is the single web workspace boundary for admin and portal surfaces.
- `web/src/` is reserved for the application source tree.
- Vben Admin is the shell reference for navigation, route guards, list/detail patterns, and CRUD flows.

The web app should remain one workspace even if it later exposes separate admin and portal route groups, because permission and theme/i18n behavior are shared.

## Mobile layout

- `mobile/` is the single Flutter workspace boundary.
- `mobile/lib/` is reserved for application source code.
- Prokit is an interaction reference, not a direct template dump target.

Offline-capable field features will extend this same workspace later.

## Infrastructure and docs layout

- `infra/` contains operational and environment support files, not application business code.
- `docs/` remains the shared location for sprint plans, prompts, discovery outputs, engineering decisions, and QA assets.

## Why this layout is compatible with later work

- Sprint 02 can add migrations, models, auth, docs service, and environment files without moving app boundaries.
- Sprint 03 onward can add web/mobile implementations without inventing new roots.
- Sprint 12 migration and UAT assets already have clear homes under `docs/` and `infra/`.

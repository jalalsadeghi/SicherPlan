# SicherPlan

SicherPlan is a modular, multi-tenant security operations platform delivered as a single repository with separate backend, web, mobile, infrastructure, and shared documentation areas.

## Repository layout

- `backend/` FastAPI backend workspace and bounded-context packages
- `web/` Vue 3 + Vben Admin web workspace area
- `mobile/` Flutter + Prokit-inspired mobile workspace area
- `infra/` infrastructure, local environment, and deployment support files
- `docs/` sprint plans, task prompts, discovery, backlog, engineering, and QA artifacts

## Current state

Sprint 1 currently establishes the planning and engineering baseline:

- backlog, discovery, dependency, migration/NFR, and QA traceability docs under `docs/`
- repository structure and coding conventions for later implementation tasks
- empty but intentional app boundaries for backend, web, mobile, and infra

Business-domain implementation has not started yet. The current repository structure is designed to reduce rework when Sprint 2 platform-core work begins.

## Where to start

1. Read [AGENTS.md](/home/jey/Projects/SicherPlan/AGENTS.md).
2. Read the relevant sprint guide under [docs/sprint](/home/jey/Projects/SicherPlan/docs/sprint).
3. Read the matching task prompt under [docs/prompts](/home/jey/Projects/SicherPlan/docs/prompts).
4. Use the engineering conventions in [repository-structure.md](/home/jey/Projects/SicherPlan/docs/engineering/repository-structure.md) and [branching-and-coding-standards.md](/home/jey/Projects/SicherPlan/docs/engineering/branching-and-coding-standards.md).

## Delivery rules that already apply

- German is the default language and English is secondary for user-facing work.
- Web work should follow Vben Admin patterns.
- Mobile work should follow Prokit-inspired Flutter patterns.
- Tenant isolation, role scoping, append-only evidence handling, and `finance.actual_record` are non-negotiable platform rules.

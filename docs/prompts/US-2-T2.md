---
task_id: US-2-T2
story_id: US-2
story_title: "Repository, environments, CI/CD, and observability baseline"
sprint: Sprint 01
status: ready
owner: "DevOps"
---

# Codex Prompt — US-2-T2

## Task title

**Provision development/staging environments, secrets, and config management**

## Objective

Create safe and repeatable configuration patterns for development and staging across backend, web, mobile, and shared infrastructure, without committing real secrets.

## Source context

- Updated proposal: technical architecture and quality requirements; security baseline; operational delivery; assumptions and dependencies.
- Implementation specification: cross-cutting decisions; docs/comm/integration backbone needs; migration waves A-B; implementation notes.
- Cross-cutting rules: `AGENTS.md`.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.

## Dependencies

- `US-2-T1` should establish the repo layout first.
- `US-1-T3` should inform environment assumptions, provider categories, and NFRs.

## Scope of work

- Implement environment/config loading for backend, web, and mobile using a pattern that keeps local development easy and staging safe.
- Create example environment files and configuration documentation; never commit real credentials.
- Provision local/shared dev infrastructure as needed for Sprint 1 and Sprint 2 foundations, such as PostgreSQL and object storage emulation, using containerized or scripted setup where appropriate.
- Define secret-handling and environment-injection rules for development and staging, including how CI/CD will consume them later.
- Keep configuration names aligned with real platform concepts: tenant-aware backend settings, object storage, auth/session settings, messaging stubs, and mobile/web API endpoints.

## Preferred file targets

- App-level example env files such as `apps/api/.env.example`, `apps/web/.env.example`, `apps/mobile/.env.example` (adapt to the actual repo layout)
- Config modules/loaders for backend, web, and mobile
- Local infrastructure bootstrap files such as `docker-compose.dev.yml` or equivalent
- `docs/engineering/environment-and-secret-management.md`

## Hard constraints

- Never commit real passwords, tokens, signing keys, or provider secrets.
- Environment configuration must support at least `development` and `staging` separation.
- Backend configuration should remain compatible with FastAPI + SQLAlchemy + Alembic workflows.
- Keep room for later integrations (OIDC, object storage, messaging, payroll adapters) without hard-wiring vendor logic into config names.

## Expected implementation outputs

- Repeatable local/dev/staging configuration patterns.
- Example env files and documentation for contributors and CI.
- A clear secret-handling approach that later deployment work can adopt.

## Non-goals

- Do not build the CI workflows themselves here; that belongs to `US-2-T3`.
- Do not implement production infrastructure, app-store signing, or provider contracts.
- Do not add business-domain runtime configuration beyond what is needed for the platform baseline.

## Verification checklist

- A contributor can start the local environment from docs and example configs.
- Environment selection is explicit and not hidden in ad hoc code.
- No real secrets are stored in the repository.
- The setup leaves a clean path for CI/CD and staging deployment.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

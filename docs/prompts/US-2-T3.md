---
task_id: US-2-T3
story_id: US-2
story_title: "Repository, environments, CI/CD, and observability baseline"
sprint: Sprint 01
status: ready
owner: "DevOps"
---

# Codex Prompt — US-2-T3

## Task title

**Build CI pipelines for lint, test, migrations, builds, and deployments**

## Objective

Create the first continuous-integration baseline so backend, web, and mobile changes are validated automatically and migration safety becomes part of routine delivery.

## Source context

- Updated proposal: operational delivery, automated test/deployment workflow, and quality attributes.
- Implementation specification: migration sequence and implementation notes; migration-safe modeling patterns should already influence the pipeline.
- Cross-cutting rules: `AGENTS.md`.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.

## Dependencies

- `US-2-T1` repository structure must exist.
- `US-2-T2` environment and example config patterns should exist before pipeline setup.

## Scope of work

- Implement CI workflows for backend, web, and mobile linting, static checks, tests, and build validation.
- Add a database migration check that runs Alembic (or the repo's migration equivalent) against an ephemeral PostgreSQL instance.
- Create staging/deployment workflow stubs or first-pass automation that match the chosen CI provider and repository layout.
- Cache dependencies and keep workflows maintainable; avoid fragile or overly clever pipeline logic.
- Document how to interpret pipeline stages and how failures should block merges.

## Preferred file targets

- CI workflow definitions (for example `.github/workflows/*.yml` if GitHub Actions is used)
- `docs/engineering/ci-cd.md`
- Any helper scripts needed for migrations, app builds, or smoke checks

## Hard constraints

- Pipelines must cover backend, web, and mobile, even if early mobile checks are limited to analysis/test/build smoke validation.
- Migration validation is required; do not treat schema changes as optional.
- Deployment automation should not require production credentials at this stage.
- Keep pipeline outputs readable so Codex-generated changes are easy to review.

## Expected implementation outputs

- A working CI baseline that runs on pull requests or equivalent review events.
- A migration-check stage for the backend.
- A documented path for dev/staging deployment automation.

## Non-goals

- Do not implement full production release signing or store-distribution flows.
- Do not replace observability or runtime error handling; that belongs to `US-2-T4`.
- Do not over-engineer deployment infrastructure before the platform core exists.

## Verification checklist

- Pipelines run successfully on a clean branch with the current repo state.
- Backend, web, and mobile all have at least one automated validation stage.
- Migration checks fail when schema consistency is broken.
- The CI/CD documentation matches the workflow files.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

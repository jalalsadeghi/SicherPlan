# CI/CD Baseline

## Task anchor

- Task: `US-2-T3`

## Goal

Provide a first-pass CI baseline that validates backend, migration, web, and mobile changes automatically on review events and leaves a clean path for staging delivery automation.

## Chosen provider

GitHub Actions is used as the CI provider for the repository baseline.

### Why

- The repository already uses Git and is structured as a single monorepo.
- GitHub Actions supports matrix-free, readable workflows that are easy to review in early delivery.
- It can run PostgreSQL service containers for migration smoke checks without committing to production deployment tooling.

## Workflow files

- [ci.yml](/home/jey/Projects/SicherPlan/.github/workflows/ci.yml)
- [staging-delivery.yml](/home/jey/Projects/SicherPlan/.github/workflows/staging-delivery.yml)

## CI stages

### Backend lint and smoke

What it does:

- installs Python tooling
- runs `ruff` against the backend workspace
- byte-compiles backend and Alembic Python files

Why it exists:

- catches syntax and basic lint failures early
- keeps backend changes reviewable before full application bootstrapping exists

### Migration check

What it does:

- starts ephemeral PostgreSQL in CI
- installs Alembic/SQLAlchemy/psycopg tooling
- runs `upgrade head`, `downgrade base`, and `upgrade head` against the Alembic workspace

Why it exists:

- makes migration safety part of routine delivery from the start
- ensures the repo has a real migration harness, not only a directory placeholder

### Web config smoke

What it does:

- validates that the web env example and config loader exist
- checks for the required environment and theme/i18n-related keys

Why it exists:

- the Vben workspace is not bootstrapped yet
- this still gives the web area an automated review gate tied to the current repo state

### Mobile config smoke

What it does:

- validates the mobile env example and config loader
- checks for compile-time environment usage
- formats the current Dart config file

Why it exists:

- the Flutter app is not bootstrapped yet
- this keeps the mobile workspace under automated validation until fuller analysis/build stages arrive

## Staging delivery stub

The staging workflow is intentionally minimal at this stage.

It exists to:

- reserve a staging automation path
- document that staging should use injected secrets and the same config keys as development
- avoid coupling early Sprint 1 work to production delivery or release-signing concerns

## Failure interpretation

- Any failed CI stage should block merge for the affected change.
- Migration failures should be treated as structural problems, not optional warnings.
- Web/mobile smoke failures indicate repo-structure or config-contract drift and should be fixed before the next bootstrap tasks land.

## Helper scripts

- [check_backend_ci.sh](/home/jey/Projects/SicherPlan/infra/scripts/check_backend_ci.sh)
- [check_migration_ci.sh](/home/jey/Projects/SicherPlan/infra/scripts/check_migration_ci.sh)
- [check_web_ci.sh](/home/jey/Projects/SicherPlan/infra/scripts/check_web_ci.sh)
- [check_mobile_ci.sh](/home/jey/Projects/SicherPlan/infra/scripts/check_mobile_ci.sh)
- [staging_delivery_stub.sh](/home/jey/Projects/SicherPlan/infra/scripts/staging_delivery_stub.sh)

These scripts keep workflow logic readable and make it easier to run equivalent checks locally later.

## Current limitations

- No production deployment automation is implemented here.
- Web and mobile are validated by config smoke checks rather than full app builds because the real Vben and Flutter workspaces belong to `US-3-T1` and `US-3-T2`.
- Observability, runtime error handling, and deployment credentials remain out of scope until later tasks.

## Follow-ups

- `US-2-T4` should add observability/error-handling expectations that fit these workflows.
- `US-3-T1` should replace the web smoke stage with install/lint/build checks once the Vben workspace exists.
- `US-3-T2` should replace the mobile smoke stage with `flutter analyze` and build/test smoke checks once the Flutter app exists.

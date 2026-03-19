# Environment And Secret Management

## Task anchor

- Task: `US-2-T2`

## Goal

Provide a repeatable and safe configuration pattern for development and staging across backend, web, mobile, and shared infrastructure without committing secrets.

## Environment model

Supported baseline environments:

- `development`
- `staging`

Production-specific delivery is intentionally out of scope for this task.

## Configuration principles

- Configuration must be explicit and environment-backed.
- Real secrets must never be committed.
- Variable names should describe platform concepts, not vendor brands.
- Backend, web, and mobile should each have their own example env file or equivalent input contract.
- Staging should use the same config shape as development, with different injected values.

## Files established by this task

- [backend/.env.example](/home/jey/Projects/SicherPlan/backend/.env.example)
- [backend/app/config.py](/home/jey/Projects/SicherPlan/backend/app/config.py)
- [web/.env.example](/home/jey/Projects/SicherPlan/web/.env.example)
- [web/src/config/env.ts](/home/jey/Projects/SicherPlan/web/src/config/env.ts)
- [mobile/.env.example](/home/jey/Projects/SicherPlan/mobile/.env.example)
- [mobile/lib/config/app_config.dart](/home/jey/Projects/SicherPlan/mobile/lib/config/app_config.dart)
- [docker-compose.dev.yml](/home/jey/Projects/SicherPlan/infra/docker-compose.dev.yml)

## Backend configuration pattern

### Variable prefix

Use `SP_` for backend platform settings.

### Covered config groups

- application environment and URLs
- database and Alembic connection settings
- object storage endpoint and bucket settings
- auth/session and external-identity placeholders
- outbound messaging toggles
- integration capability toggles
- logging level

### Why this shape

- It remains compatible with FastAPI, SQLAlchemy, and Alembic workflows.
- It leaves room for OIDC, object storage, messaging, and payroll/map adapters later.
- It keeps tenant-aware and integration-aware concepts visible without hardcoding vendors.

## Web configuration pattern

### Variable prefix

Use `VITE_SP_` for Vite-exposed frontend settings.

### Covered config groups

- environment name
- app title
- API base URL
- default/fallback locale
- fixed light/dark primary colors
- feature toggles for portal entry points and mock auth

### Rule

Never expose secrets through Vite env variables. Web env files are for public runtime configuration only.

## Mobile configuration pattern

### Input model

Use compile-time Dart defines for environment-backed mobile settings.

### Covered config groups

- environment name
- API base URL
- locale defaults
- fixed theme colors
- mock-auth flag
- offline-cache flag

### Rule

Do not store signing keys, tokens, or backend secrets in the mobile repository or in compile-time defaults.

## Local development infrastructure

Use [docker-compose.dev.yml](/home/jey/Projects/SicherPlan/infra/docker-compose.dev.yml) for the baseline local foundation:

- PostgreSQL for backend and Alembic work
- MinIO for object-storage-compatible local development
- Mailpit for safe local email capture

These services are sufficient for Sprint 1 and Sprint 2 foundations without committing to production providers.

## Local startup outline

1. Copy the example env files to local, ignored variants as needed.
2. Start infrastructure with `docker compose -f infra/docker-compose.dev.yml up -d`.
3. Point backend, web, and mobile local configs at the local service endpoints.
4. Use staging-specific injected variables in deployment or CI/CD, not committed files.

## Secret handling rules

- Never commit passwords, tokens, signing keys, or provider credentials.
- Keep example values obviously fake, such as `change-me` or empty values.
- Inject staging secrets through the deployment platform or CI secret store later.
- Rotate any accidentally exposed value immediately and remove it from history through the team’s incident process.

## CI/CD handoff rules

This task does not implement pipelines, but later CI/CD should follow these rules:

- CI uses the same variable names as local/staging config.
- CI may load non-secret defaults from committed examples, but secrets must come from the CI secret store.
- Staging deployments should fail fast when required injected values are missing.
- CI should be able to stand up local-like dependencies for tests using the same compose services or equivalent service containers.

## Staging rules

- Staging must use `SP_ENV=staging` or the equivalent web/mobile environment switch.
- Staging should not use development secrets or local object-storage endpoints.
- Staging may keep mock auth or provider stubs disabled by default unless explicitly needed for smoke tests.

## Open follow-ups

- `US-2-T3` should wire these config contracts into CI workflows and smoke-test automation.
- `US-2-T4` should define logging/tracing/error-handling expectations using the same environment model.
- `US-3-T1` and `US-3-T2` should consume the web/mobile config loaders when the real app workspaces are bootstrapped.

# Observability And Error Handling

## Task anchor

- Task: `US-2-T4`

## Goal

Establish a reusable baseline for backend logging, request correlation, API health checks, error contracts, and tracing-ready hooks without replacing business audit behavior.

## Files established by this task

- [backend/app/logging_utils.py](/home/jey/Projects/SicherPlan/backend/app/logging_utils.py)
- [backend/app/middleware.py](/home/jey/Projects/SicherPlan/backend/app/middleware.py)
- [backend/app/errors.py](/home/jey/Projects/SicherPlan/backend/app/errors.py)
- [backend/app/health.py](/home/jey/Projects/SicherPlan/backend/app/health.py)
- [backend/app/main.py](/home/jey/Projects/SicherPlan/backend/app/main.py)
- [check_observability_ci.py](/home/jey/Projects/SicherPlan/infra/scripts/check_observability_ci.py)

## Logging standard

### Format

- Backend logs should be structured JSON lines.
- Every log entry should include:
  - timestamp
  - level
  - logger name
  - message
  - request ID when available

### Request correlation

- `X-Request-ID` is accepted from callers when present.
- A new request ID is generated when the caller does not provide one.
- The response echoes `X-Request-ID` so downstream debugging remains correlation-friendly.

### Data protection rules

- Never log passwords, tokens, signing keys, HR-private data, or raw personal/finance-sensitive payloads by default.
- Logs are for technical observability, not business audit substitution.
- Append-only audit evidence remains in domain audit tables later; logs must not be treated as their replacement.

## Error contract

### Envelope

Backend API errors should follow this shape:

```json
{
  "error": {
    "code": "platform.validation_error",
    "message_key": "errors.platform.validation",
    "request_id": "…",
    "details": {
      "field": "demo"
    }
  }
}
```

### Rules

- `code` is the stable machine-readable error code.
- `message_key` is the localization-friendly client message key.
- `request_id` allows support and log correlation.
- `details` is optional structured context and must not leak secrets or restricted fields.

### Exception handling approach

- Known application errors should raise a typed exception with status, code, and message key.
- Unhandled exceptions should return a stable internal-error envelope rather than ad hoc HTML or traceback output.
- Localized human-readable strings should be resolved client-side or through later localization layers, not hardcoded into low-level error contracts.

## Health endpoints

### Endpoints

- `GET /health/live`
- `GET /health/ready`
- `GET /health/version`

### Intent

- `live` proves the application process is up.
- `ready` checks lightweight dependency readiness.
- `version` exposes app/version/environment metadata for smoke checks and release verification.

### Readiness coverage

- database connectivity check using a lightweight `SELECT 1`
- object-storage configuration presence check

Health checks must stay safe to call frequently and should not perform expensive cross-system operations.

## Tracing-ready hooks

- Request IDs are the baseline correlation primitive.
- Future OpenTelemetry or trace propagation can build on the existing middleware and error envelope without changing client-visible contracts.
- Trace adoption later should enrich, not replace, the request-correlation pattern already established here.

## Client consumption guidance

### Web

- Treat `error.code` and `error.message_key` as the canonical error contract.
- Map `message_key` into DE/EN UI resources rather than relying on raw backend prose.
- Surface `request_id` in support/debug contexts, not necessarily in every user-facing toast.

### Mobile

- Apply the same rule: translate `message_key`, keep `request_id` available for support, and avoid exposing raw backend internals in user-facing screens.
- Preserve consistent handling across online and offline-retry flows.

## CI and smoke validation

- CI backend smoke now includes an observability check script that boots the FastAPI app, calls health endpoints, and verifies the stable error envelope.
- Migration checks remain separate and must not be replaced by health checks.

## Verification commands

When dependencies are available locally, the baseline can be checked with:

```bash
python3 -m compileall backend/app backend/alembic
python3 infra/scripts/check_observability_ci.py
```

## Follow-ups

- `US-3-T4` should align web/mobile localization resources with the `message_key` convention.
- Later backend tasks should reuse the same error envelope and request-ID pattern instead of inventing module-local formats.
- Future telemetry integration can layer tracing/exporters on top of this baseline when staging/runtime needs justify it.

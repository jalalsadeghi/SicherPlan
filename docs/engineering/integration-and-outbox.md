# Integration And Outbox

## Scope

- `integration.endpoint` stores tenant-scoped provider configuration with public config separated from sealed secret config.
- `integration.import_export_job` tracks requested, running, completed, and failed integration jobs.
- `integration.outbox_event` stores retry-aware publication state for asynchronous side effects.

## Secret handling

- Endpoint secret config is sealed before it is written to the database.
- API read models never return `secret_ciphertext` or opened secret payloads.
- Logs and tests should use placeholder or derived values, never real secrets.

## Outbox rules

- Import/export job requests create the job row and its initial outbox row in one repository transaction.
- Worker processing is retry-aware and idempotent: published rows are not processed again, retry rows wait until `next_attempt_at`.
- Publication updates status fields only; the original payload and identity metadata stay intact for investigation.

## Result-document rules

- Export or import result artifacts stay in the docs service.
- Integration jobs link result documents through `docs.document_link` using owner type `integration.import_export_job`.

---
task_id: US-6-T4
story_id: US-6
story_title: "Document, communication, information portal, and integration backbone"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Integration Lead"
---

# Codex Prompt — US-6-T4

## Task title

**Implement integration endpoints, import/export jobs, and transactional outbox workers**

## Objective

Deliver the integration backbone so provider configuration, tracked import/export jobs, and asynchronous outbox processing are available before later payroll, maps, scanner, and messaging integrations arrive.

## Source context

- Updated proposal: section 5.1 integration framework; section 7 REST/OpenAPI, payroll import/export, terminal/scanner, maps/geolocation, and messaging-provider expectations.
- Implementation specification: global eventing rule that domain tables must not call external providers in the same transaction; section 4.2 `integration.endpoint`, `integration.import_export_job`, and `integration.outbox_event`.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md` and the Sprint 1 CI/observability baseline.

## Dependencies

- `US-6-T1` and `US-6-T2` should already provide docs and communication foundations that the integration layer may reference.
- Use the queue/worker/runtime patterns already approved by the repo and Sprint 1 environment, rather than introducing an incompatible background-processing stack.

## Scope of work

- Implement provider endpoint configuration, tracked import/export jobs, and transactional outbox-event persistence according to the approved schema.
- Create API/service flows to register integration endpoints, request import/export jobs, inspect job status, and attach result documents where appropriate.
- Implement background worker or job-processing wiring that reads unpublished outbox events, publishes or dispatches them through provider adapters, and marks publication state safely.
- Keep endpoint configuration protected and encrypted or equivalently secured at rest according to the repo's approved secret-handling pattern.
- Make the worker and job system idempotent and retry-aware so failures do not corrupt business state or double-publish silently.
- Write tests for outbox persistence, worker publication, retry behavior, and import/export job lifecycle state transitions.

## Preferred file targets

- Backend integration/outbox module files under the actual platform-services or infrastructure package.
- Worker/background-job entry points, adapter interfaces, and job-status APIs.
- Tests such as `apps/api/tests/modules/platform_services/test_integration_outbox.py` or equivalent.
- Optional docs such as `docs/engineering/integration-and-outbox.md` if the repo benefits from it.

## Hard constraints

- Do not call external providers directly from the same transaction that writes domain/business data.
- Outbox rows should remain append-only until publication and preserve enough metadata for retry and investigation.
- Endpoint configuration must not leak secrets through logs, API reads, or test fixtures.
- Import/export jobs are infrastructure records, not a shortcut for embedding provider side effects inside business tables.
- Do not implement every concrete production provider in Sprint 2; build the backbone and at most a small dev/staging-safe adapter set.

## Expected implementation outputs

- Integration endpoint/job/outbox tables and models.
- Provider-configuration and job-management APIs/services.
- A working outbox processing path or worker scaffold with idempotent publication behavior.
- Automated tests covering event publication and job lifecycle behavior.

## Non-goals

- Do not build full customer/employee/subcontractor migration templates here; those belong to Sprint 12.
- Do not ship production-specific payroll/map/scanner vendor integrations in depth unless a minimal dev-safe stub is needed.
- Do not bypass the docs service when a job produces a result file or export artifact.
- Do not embed secret values in repo files or logs.

## Verification checklist

- Integration endpoints can be configured and stored securely.
- Import/export jobs move through requested/started/completed or failure states predictably and can reference result documents.
- Transactional outbox rows are created and processed without violating domain-transaction boundaries.
- Retry/idempotency behavior prevents silent double processing in common failure cases.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-6-T4 — Implement integration endpoints, import/export jobs, and transactional outbox workers** is finished.

```text
/review Please review the implementation for task US-6-T4 (Implement integration endpoints, import/export jobs, and transactional outbox workers) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-6-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- External side effects are decoupled from domain transactions through the outbox/worker pattern.
- Endpoint configuration and secret handling are secure and do not leak.
- Job and outbox state transitions are deterministic, idempotent, and test-covered.
- Result documents and provider payload boundaries stay aligned with the docs/integration ownership rules.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-6.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

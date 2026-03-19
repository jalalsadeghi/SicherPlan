---
task_id: US-2-T4
story_id: US-2
story_title: "Repository, environments, CI/CD, and observability baseline"
sprint: Sprint 01
status: ready
owner: "DevOps / Backend Lead"
---

# Codex Prompt — US-2-T4

## Task title

**Set up logging, tracing, health checks, and error handling standards**

## Objective

Establish the operational guardrails for runtime visibility and failure handling so early platform work is observable, diagnosable, and consistent across services and clients.

## Source context

- Updated proposal: audit and traceability; communication backbone; technical architecture/security baseline; quality attributes.
- Implementation specification: audit/login tables; append-only evidence rules; integration outbox; reporting and read-model guidance.
- Cross-cutting rules: `AGENTS.md`.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.

## Dependencies

- `US-2-T1` and `US-2-T2` should exist first.
- `US-2-T3` should inform how health checks and observability hooks participate in CI smoke tests.

## Scope of work

- Implement structured backend logging with correlation/request IDs and a consistent format suitable for local development and staging.
- Define a standard API error envelope and exception-handling approach that later modules can reuse without inventing incompatible formats.
- Add live/ready/version or equivalent health endpoints that cover application, database, and critical dependency readiness where appropriate.
- Lay down tracing hooks or OpenTelemetry-ready instrumentation points without overbuilding full production telemetry.
- Document how web and mobile clients should consume API errors and surface them consistently.

## Preferred file targets

- Backend logging/error/health modules under the actual API app structure
- `docs/engineering/observability-and-error-handling.md`
- Client-side API error helper utilities if the repo already has web/mobile client shells

## Hard constraints

- Sensitive data, secrets, and HR/private fields must not be dumped into logs.
- Error contracts should favor stable machine-readable codes and localized message keys over ad hoc strings where practical.
- Health/readiness checks must remain lightweight and safe to call frequently.
- Logging and tracing decisions must not conflict with append-only audit/evidence rules.

## Expected implementation outputs

- A baseline structured logging implementation.
- Health/readiness endpoints or equivalent service checks.
- A documented standard for API errors and client consumption.

## Non-goals

- Do not implement full dashboards, alerts, or third-party monitoring stacks in depth.
- Do not replace business-audit tables with log-based audit substitutes.
- Do not add finance/reporting observability that depends on future modules.

## Verification checklist

- Health endpoints respond as documented.
- Errors follow a consistent contract in normal and exceptional flows.
- Logs include correlation-friendly context without leaking secrets or private data.
- Basic observability behavior is covered by smoke tests or documented verification commands.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-2-T4 — Set up logging, tracing, health checks, and error handling standards** is finished.

```text
/review Please review the implementation for task US-2-T4 (Set up logging, tracing, health checks, and error handling standards) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-2-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- CI/CD and automation changes are minimal, reproducible, and do not weaken quality gates.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-2.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

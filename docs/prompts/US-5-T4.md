---
task_id: US-5-T4
story_id: US-5
story_title: "Identity, role scope, session management, and audit foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Security Lead"
---

# Codex Prompt — US-5-T4

## Task title

**Capture login events and business audit events for sensitive actions**

## Objective

Implement the immutable security and business audit foundation so sensitive platform actions can be reconstructed reliably across authentication, administration, and later operational modules.

## Source context

- Updated proposal: section 5.1 audit and traceability; section 7 security baseline and structured audit records; section 8 Phase 1 audit trail deliverable.
- Implementation specification: append-only/audit-safe rules; `audit.audit_event` and `audit.login_event` in section 4.1; shared correlation/timestamp conventions; security/QM reporting expectations.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md` and the Sprint 1 observability/error-handling baseline.

## Dependencies

- `US-5-T1` and `US-5-T2` should provide IAM identities and login/session flows first.
- `US-4-T2` and any other sensitive admin APIs created in Sprint 2 should be available so business-audit hooks can be applied to real actions.

## Scope of work

- Create migrations/models/schemas for `audit.login_event` and `audit.audit_event` if they do not already exist.
- Capture successful and failed login attempts with the required metadata while keeping secrets and private data out of the audit payload.
- Add a reusable audit-writing service or helper that sensitive business/admin operations can call with entity metadata, actor user, correlation ID, and before/after snapshots where appropriate.
- Apply audit-event capture to the sensitive Sprint 2 actions already present, such as tenant onboarding/changes, branch/mandate/settings changes, role/permission-sensitive changes, and other clearly security-relevant mutations.
- Preserve append-only behavior; corrections or follow-up actions should create additional events rather than rewriting history.
- Write tests proving audit rows are created for key success and failure paths and are not silently mutable after creation.

## Preferred file targets

- Audit models/services under the actual IAM or shared security package.
- Auth/core service updates that emit login or business audit events.
- Tests such as `apps/api/tests/security/test_audit_and_login_events.py` or equivalent.

## Hard constraints

- Audit tables are not a substitute for app logs, and logs are not a substitute for audit tables; keep the two concerns separate.
- Never write secrets, raw passwords, raw tokens, or unnecessary private HR/finance data into audit payloads.
- Maintain append-only semantics for audit rows.
- Use stable event types and entity identifiers so later reporting can query the data cleanly.
- Do not overcapture noisy read-only events that would reduce signal without clear compliance value.

## Expected implementation outputs

- Immutable audit/login tables and ORM models.
- Reusable audit-event emission utilities applied to the Sprint 2 sensitive actions.
- Tests for append-only behavior and expected event creation.
- A clear event-typing approach that later reporting/security tasks can build on.

## Non-goals

- Do not build reporting dashboards for audit data here; that belongs to Sprint 11.
- Do not store whole secrets, credentials, or full private payload snapshots just because it is easy.
- Do not implement broad client-facing audit UIs in this task.
- Do not replace domain-state versioning or document revision history with audit rows alone.

## Verification checklist

- Login attempts create login-event rows with success/failure outcomes and actor linkage when available.
- Sensitive admin/business mutations create audit-event rows with stable event metadata and correlation information.
- Audit rows are append-only in practice and cannot be casually overwritten through normal services.
- The resulting data is queryable and meaningful for later security/QM reporting.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-5-T4 — Capture login events and business audit events for sensitive actions** is finished.

```text
/review Please review the implementation for task US-5-T4 (Capture login events and business audit events for sensitive actions) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-5-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Audit and login events are truly append-only and free of secret leakage.
- Before/after snapshots and entity metadata are useful but privacy-conscious.
- Sensitive actions in Sprint 2 actually emit audit events instead of only relying on generic logs.
- Correlation/request metadata makes the events useful for later investigation and reporting.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-5.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

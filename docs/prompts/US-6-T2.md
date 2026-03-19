---
task_id: US-6-T2
story_id: US-6
story_title: "Document, communication, information portal, and integration backbone"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Platform Lead"
---

# Codex Prompt — US-6-T2

## Task title

**Implement communication templates, outbound messages, recipients, and delivery attempts**

## Objective

Build the reusable communication service so SicherPlan can render and track email, SMS, and push communication in a centralized, auditable way across later business workflows.

## Source context

- Updated proposal: section 5.1 communication backbone with templates, placeholders, attachments, recipient groups, send history, and read confirmation; section 7 integration approach for email/SMS/push providers.
- Implementation specification: section 4.2 `comm.message_template`, `comm.outbound_message`, `comm.message_recipient`, and `comm.delivery_attempt`; append-only delivery-attempt rules; docs-backed attachments and later outbox integration.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-6-T1` should already provide the document backbone for attachments.
- `US-5-T1` should provide user references for internal recipients.
- Do not wait for the full outbox worker from `US-6-T4` to design the message model correctly.

## Scope of work

- Create the communication tables/models/schemas for templates, rendered outbound messages, recipient rows, and provider attempt history.
- Implement template management with channel + template key + language code, supporting German default and English secondary templates where user-facing messages exist.
- Implement message rendering and recipient expansion APIs/services that can create outbound messages and per-recipient rows without sending them inline inside business transactions.
- Support attachments through the docs service and stable related-entity metadata so business workflows can point messages back to their source entity.
- Store delivery attempts append-only and keep outbound message bodies immutable once send processing has started.
- Write tests for template uniqueness, render behavior, recipient fan-out, attachment linkage, and attempt-history integrity.

## Preferred file targets

- Backend communication service files under the actual platform-services package.
- Template/rendering helpers and adapter interfaces for later provider workers.
- Tests such as `apps/api/tests/modules/platform_services/test_communication_backbone.py` or equivalent.

## Hard constraints

- Do not call concrete messaging providers directly from the same domain transaction that creates business data.
- Message templates and rendered messages must respect DE default / EN secondary language handling.
- Once send processing starts, the rendered outbound message content should be treated as immutable history.
- Do not collapse recipient rows into one opaque blob; delivery status belongs per destination.
- Keep provider payload details in attempt logs or integration layers, not in business tables.

## Expected implementation outputs

- Communication tables/models/schemas and template/render services.
- Recipient-expansion support and attachment linkage through docs.
- Append-only delivery-attempt tracking.
- Automated tests covering render and persistence behavior.

## Non-goals

- Do not implement every external provider worker here; `US-6-T4` handles the integration/outbox worker side.
- Do not build a full chat or conversational messaging system.
- Do not hardcode specific business templates for every future module unless a platform-core case truly needs them now.
- Do not bypass the docs service for attachments.

## Verification checklist

- Templates are uniquely addressable by channel/template key/language.
- Outbound messages can be rendered and split into recipient rows without provider side effects in the same transaction.
- Delivery attempts are append-only and clearly linked to one recipient row.
- Attachments and related-entity references are preserved for later reporting and audit use.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-6-T2 — Implement communication templates, outbound messages, recipients, and delivery attempts** is finished.

```text
/review Please review the implementation for task US-6-T2 (Implement communication templates, outbound messages, recipients, and delivery attempts) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-6-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Message immutability and per-recipient delivery modeling are correct.
- Language handling follows the DE-default / EN-secondary rule for templates and rendered content.
- Provider coupling is kept behind adapters/outbox-friendly seams.
- Attempt logging is append-only and useful for later diagnostics/reporting.

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

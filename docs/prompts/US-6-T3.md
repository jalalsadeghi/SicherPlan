---
task_id: US-6-T3
story_id: US-6
story_title: "Document, communication, information portal, and integration backbone"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Frontend Lead"
---

# Codex Prompt — US-6-T3

## Task title

**Build info.notice, audience, read confirmation, and attachment flows**

## Objective

Implement the information-portal foundation for mandatory notices, audience targeting, acknowledgement tracking, and notice attachments so internal communication and compliance evidence are reusable across the platform.

## Source context

- Updated proposal: company/enterprise information portal scope, internal communication, read confirmations, management/QM oversight, and communication backbone requirements.
- Implementation specification: section 4.2 `info.notice`, `info.notice_audience`, `info.notice_read`, and `info.notice_link`; attachments via `docs.document_link`; audience types including role, employee group, qualification, function, all employees/customers/subcontractors.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md` and the Sprint 1 web shell/i18n baseline.

## Dependencies

- `US-6-T1` should already provide document attachments and links.
- `US-5-T1` / `US-5-T3` should provide user identities and scope-aware access enforcement.
- Because some audience targets depend on later HR/CRM/partner modules, design the resolver abstraction now without blocking on all target tables existing today.

## Scope of work

- Implement the notice tables/models/schemas and the backend flows to create, publish, unpublish, acknowledge, and list notices.
- Implement audience targeting with the approved audience kinds, using resolver logic or deferred validation where later-sprint target aggregates are not yet available.
- Implement read/open/acknowledgement tracking so mandatory notices become durable compliance evidence.
- Support notice attachments and curated links through the docs service and `info.notice_link`.
- If the web app is ready, provide a minimal Vben admin surface for notice authoring/publishing and a minimal scoped read/acknowledgement view; otherwise, at least leave the API contracts and route placeholders ready for UI hookup.
- Write tests for audience resolution, publish windows, mandatory acknowledgement, attachment/link handling, and scope-restricted visibility.

## Preferred file targets

- Backend info/notices module files under the actual platform-services package.
- Optional web files for minimal notice admin/read views under the existing Vben workspace.
- Tests such as `apps/api/tests/modules/platform_services/test_notice_flows.py` and/or frontend smoke tests if UI is included.

## Hard constraints

- Audience resolution must remain tenant-safe and role-scoped.
- Do not hardcode cross-module writes into HR/customer/subcontractor tables just to target audiences.
- Mandatory-read evidence must be durable and queryable for later QM/compliance reporting.
- Attachments must flow through the docs service instead of bespoke file fields on the notice table.
- Do not overbuild a social intranet; keep the scope on notices, audience targeting, links, and acknowledgements.

## Expected implementation outputs

- Notice/audience/read/link models and APIs.
- A durable read/acknowledgement tracking mechanism.
- Attachment and link flows tied to docs/document links.
- Tests (and optionally minimal UI) for publish/read/ack paths.

## Non-goals

- Do not implement the full later reporting dashboards for notice stats.
- Do not require all future audience target aggregates to exist before delivering the backbone.
- Do not build chat threads, comments, or reaction systems.
- Do not bypass RBAC and tenant scoping in the read or publish flows.

## Verification checklist

- Notices can be drafted, published, targeted, read, and acknowledged through stable API contracts.
- Read/ack evidence is stored once per user/notice as the approved schema expects.
- Audience resolution is tenant-safe and extensible toward later HR/customer/subcontractor targets.
- Attachments and curated links appear through the approved document/link structures.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-6-T3 — Build info.notice, audience, read confirmation, and attachment flows** is finished.

```text
/review Please review the implementation for task US-6-T3 (Build info.notice, audience, read confirmation, and attachment flows) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-6-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Audience targeting logic is safe even while some later-sprint target tables are not yet present.
- Read/acknowledgement evidence is durable, unique per user/notice, and report-ready.
- Attachments and links use the approved docs/notices structures instead of shortcuts.
- Any included UI follows the Vben shell and localization rules without leaking scope.

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

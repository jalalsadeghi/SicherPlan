---
task_id: US-7-T3
story_id: US-7
story_title: "Customer master, contacts, addresses, and portal account linkage"
sprint: Sprint 03
status: ready
owner: "Backend Lead / Platform Services"
---

# Codex Prompt — US-7-T3

## Task title

**Add import/export, vCard, and change tracking for customer records**

## Objective

Add controlled customer-data import/export and CRM-friendly change tracking so tenant teams can migrate customer records, export customer/contact data, and audit meaningful master-data changes without losing traceability.

## Source context

- Updated proposal: section 5.2 customer account/contact scope, vCard export, customer history and controls; Appendix A contacts, history, and customer data export expectations.
- Implementation specification: section 4.3 `crm.customer_history_entry`; docs-link integration for attachments; `integration.import_export_job` and docs backbone from section 4.2; aggregate/package guidance in section 9.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T1` must already provide stable customer/contact/address persistence and service contracts.
- `US-6-T1` should already provide docs storage/linking for generated exports or import result files.
- `US-6-T4` should already provide import/export job tracking and outbox-friendly async execution seams where the repo supports them.
- `US-5-T4` audit foundations should be available for change-tracking and import attribution.

## Scope of work

- Implement customer and contact import/export services with stable file formats, validation, row-level error reporting, and tenant-safe execution.
- Support generated exports through the docs/integration backbone instead of unmanaged local files when the repository already includes those platform services.
- Implement customer-contact vCard export for relevant contact records, with sensible field mapping from stored contact details and DE/EN-safe labels where exposed.
- Add customer-history or change-tracking behavior that records meaningful master-data changes such as status changes, primary-contact changes, important address changes, and portal-link changes without duplicating raw audit logs blindly.
- Expose API endpoints or service commands for import dry-run, import execute, export request/download, and vCard generation consistent with the repo's existing patterns.
- If a web hook or action is required to make the feature usable, keep it light and aligned with the existing customer-admin screens instead of building a second UI system.
- Add tests for import validation, export content shape, vCard generation, history-entry creation, tenant scoping, and failure handling.

## Preferred file targets

- Customer import/export services under `modules/customers/` or equivalent.
- Use of `modules/platform_services/integration/` job tracking or equivalent async job abstractions if already present.
- Use of `modules/platform_services/docs/` or equivalent for export artifact linkage.
- Tests for import/export services, vCard rendering, and change tracking.

## Hard constraints

- Do not bypass the docs or integration backbones if those foundations already exist in the repository.
- Keep imports tenant-scoped, auditable, and safe to retry; do not let one bad row silently corrupt a whole dataset.
- vCard export should be derived from current contact truth and must not expose unrelated finance or internal-only metadata.
- Do not treat raw audit events and customer-history entries as the same thing; history should remain business-readable while audit remains system-grade.
- Do not introduce direct external CRM/provider synchronization here unless the repo already has a narrow, approved integration seam for it.

## Expected implementation outputs

- Customer import/export flows with job tracking or equivalent execution control.
- Usable customer-contact vCard export.
- Business-readable customer change tracking/history tied to customer records and actors.
- Tests covering success, failure, scoping, and content integrity.

## Non-goals

- Do not build the main admin CRUD pages here; that is `US-7-T2`.
- Do not implement finance invoice export pipelines here; those belong to later finance prompts.
- Do not replace or redesign the global audit framework; only integrate with it appropriately.

## Verification checklist

- Customer imports validate required columns, reject unsafe or cross-tenant data, and produce actionable error reporting.
- Customer/contact exports are generated predictably and can be linked to docs/job records when applicable.
- vCard output reflects current contact data and excludes unrelated sensitive fields.
- Meaningful customer-history entries are created for important tracked changes without duplicating every low-level write event.
- All import/export and history flows are attributable to the acting user or job context.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-7-T3 — Add import/export, vCard, and change tracking for customer records** is finished.

```text
/review Please review the implementation for task US-7-T3 (Add import/export, vCard, and change tracking for customer records) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-7-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Import/export execution is tenant-safe, retry-aware, and aligned with the integration/docs backbone instead of ad hoc file handling.
- vCard generation is correct, minimal, and based on current contact truth.
- Business-readable customer history is useful and not just a noisy copy of raw audit logs.
- Error handling and validation make bulk data work safe for real migration and maintenance scenarios.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-7.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, unsafe defaults, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

---
task_id: US-9-T3
story_id: US-9
story_title: "Customer portal read models, collaboration views, and customer-specific controls"
sprint: Sprint 03
status: ready
owner: "Web Lead / Backend Lead"
---

# Codex Prompt — US-9-T3

## Task title

**Add customer history, attachments, login history visibility, and employee block maintenance**

## Objective

Extend the customer portal and CRM collaboration surface with customer history, linked attachments, filtered login-history visibility, and the customer-specific employee-block management seam required by the business workflow.

## Source context

- Updated proposal: section 5.2 customer history and controls, customer portal, and login-history visibility for administrators; Appendix A history/CRM, attachments, portal access, and employee blocks.
- Implementation specification: `crm.customer_history_entry`, docs links, audit/login foundations, and `crm.customer_employee_block`; portal visibility chain and migration sequence notes.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T3` should already provide customer-history/change-tracking support and docs-linked exports/attachments.
- `US-9-T1` must already provide portal auth/customer scope resolution.
- `US-5-T4` should already provide audit and login-event visibility seams.
- Be aware that `hr.employee` arrives later; if employee master tables are not yet present in the repo, customer-employee blocking must stay migration-safe and must not duplicate HR master truth.

## Scope of work

- Expose customer-history timeline data and linked attachments in admin and/or portal-facing collaboration views as appropriate to the approved scope.
- Add customer-login-history visibility for the appropriate customer-administrator audience, filtered strictly to the customer's own portal users and login events.
- Implement the customer-owned API/service seam for customer-specific employee blocks, including reason and effective dates, while preserving the intended normalized relationship to `hr.employee`.
- If `hr.employee` is not yet present in the repository, do not create a duplicate employee table; instead build the service/UI seam, capability flag, and migration note needed to attach the real FK safely when Sprint 4 lands.
- Ensure attachments flow through the docs service and remain linked to the owning customer/history entry rather than unmanaged file storage.
- Add tests for history visibility, attachment linkage, login-history filtering, and employee-block behavior or graceful deferment.

## Preferred file targets

- Customer history and portal collaboration services under `modules/customers/` or equivalent.
- Docs-link integration for history attachments via the shared docs module.
- Audit/login read services or filtered endpoints that surface customer-owned login history safely.
- UI or portal components that render history timelines, attachments, and login-history summaries.

## Hard constraints

- Do not expose global or tenant-wide login history to customer users; visibility must stay limited to the customer's own portal accounts and approved administrators.
- Do not duplicate employee master truth just to support customer blocks before Sprint 4.
- Customer-employee blocks are customer-owned controls, but they must not write into HR master data or bypass future HR constraints.
- Attachments must remain docs-backed and traceable.
- History and login views remain read-oriented except for explicit customer-block maintenance commands.

## Expected implementation outputs

- Customer history and attachment views backed by durable data and docs links.
- Scoped login-history visibility for customer-administrator use cases.
- A migration-safe customer-employee block maintenance path or clearly feature-gated seam pending HR-table availability.

## Non-goals

- Do not build the full employee module here.
- Do not expose internal audit details that exceed the customer's approved visibility scope.
- Do not redesign the docs or audit systems; integrate with them.

## Verification checklist

- Customer-history entries and linked attachments are visible only within the correct customer scope.
- Customer-login history is filtered to the customer's own portal users and appropriate roles.
- Employee-block maintenance either works against the real HR employee table or is safely feature-gated without creating duplicate truth.
- All new views and commands remain tenant-safe and auditable.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-9-T3 — Add customer history, attachments, login history visibility, and employee block maintenance** is finished.

```text
/review Please review the implementation for task US-9-T3 (Add customer history, attachments, login history visibility, and employee block maintenance) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-9-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- History and attachment flows are useful, scoped correctly, and tied to the docs backbone.
- Login-history visibility is filtered correctly and does not leak tenant-wide security telemetry.
- Customer-employee block maintenance is migration-safe despite later HR-table delivery.
- The task does not create hidden writes into HR or audit master truth.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-9.
- Call out any attempt to invent a duplicate employee registry or to expose overly broad audit/login data to customer users.
- If no real issue exists, say so clearly and do not invent problems.
```

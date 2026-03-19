---
task_id: US-7-T4
story_id: US-7
story_title: "Customer master, contacts, addresses, and portal account linkage"
sprint: Sprint 03
status: ready
owner: "Backend Lead / Security Lead"
---

# Codex Prompt — US-7-T4

## Task title

**Enforce tenant-safe visibility and audit rules for customer data**

## Objective

Harden the CRM customer module so every customer read/write path applies correct tenant scope, role scope, and audit behavior before downstream portal, planning, and finance work depends on it.

## Source context

- Updated proposal: role model in section 4; permission principle; section 5.2 customer history and controls; privacy note that customer-facing views hide personal names by default unless explicitly approved.
- Implementation specification: section 2 tenant-safety, shared columns, and service-ownership rules; section 4.3 customer tables; portal visibility chain and security/reporting notes in sections 6 and 8.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T1` must already define the customer aggregate and service/API boundaries.
- `US-5-T1`, `US-5-T3`, and `US-5-T4` should already provide role scope, authorization seams, and audit infrastructure.
- `US-7-T2` and `US-7-T3` should already expose the practical CRUD and import/export paths that need hardening.

## Scope of work

- Enforce tenant and role scoping across customer CRUD, search, import/export, portal-link management, and change-tracking paths.
- Define and implement the role/permission expectations for tenant administrators, allowed tenant staff, accounting-oriented readers, and customer-scoped users where applicable.
- Record durable audit events or audit hooks for customer master-data changes, portal-link changes, status transitions, important commercial-reference changes, and bulk import/export actions.
- Add integration tests that prove users cannot access another tenant's customer records and cannot widen their effective scope via crafted IDs, linked contacts, or import/export parameters.
- Ensure archived or inactive customer states behave predictably in list endpoints, detail endpoints, and downstream visibility filters.
- Document or codify the privacy boundary between internal tenant users and future customer-portal users so later portal work cannot reinterpret it loosely.

## Preferred file targets

- Authorization/service-layer code under `modules/customers/` and/or shared auth-policy helpers.
- Audit integration points under the existing IAM/audit/platform-services packages.
- Service/API tests covering scoping, permissions, archive visibility, and audit side effects.

## Hard constraints

- Do not rely on client-side filtering for customer isolation; scope enforcement must exist on the backend.
- Customer-scoped access must flow through explicit role/user/customer associations rather than ad hoc query parameters.
- Do not make internal audit history mutable or suppress important state transitions to keep screens simple.
- Keep customer-commercial data owned by CRM even when finance reads it later; authorization hardening must not invite cross-module hidden writes.
- Do not conflate internal tenant privileges with external customer-user privileges.

## Expected implementation outputs

- Backend-enforced tenant-safe visibility rules for the customer module.
- Durable audit coverage for sensitive customer-data changes and bulk actions.
- Automated permission and scoping tests that future portal and finance work can trust.

## Non-goals

- Do not implement customer-portal pages or released operational read models here; those are `US-9-*`.
- Do not redesign the shared IAM system; consume its existing role-scope and permission structures.
- Do not implement name-masking for customer-facing result views here beyond documenting and preserving the seam for `US-9-T4`.

## Verification checklist

- Cross-tenant CRUD, search, export, and linkage attempts are denied consistently.
- Customer-related actions are visible in the audit trail with enough context to investigate who changed what and when.
- Archived/inactive status affects visibility in a predictable, test-covered way.
- Role-scope combinations cannot widen customer access unexpectedly through contacts, portal links, or bulk operations.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-7-T4 — Enforce tenant-safe visibility and audit rules for customer data** is finished.

```text
/review Please review the implementation for task US-7-T4 (Enforce tenant-safe visibility and audit rules for customer data) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-7-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Tenant and role scoping are enforced at the service/API layer rather than inferred from UI behavior.
- Audit coverage is durable, useful, and applied to the sensitive customer actions that matter operationally.
- Archive/inactive semantics remain consistent across list, detail, and bulk-operation paths.
- The customer module remains a safe dependency for later finance and portal work.

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

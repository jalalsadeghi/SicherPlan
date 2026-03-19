---
task_id: US-7-T1
story_id: US-7
story_title: "Customer master, contacts, addresses, and portal account linkage"
sprint: Sprint 03
status: ready
owner: "Backend Lead"
---

# Codex Prompt — US-7-T1

## Task title

**Implement customer master, contacts, addresses, and portal user linkage**

## Objective

Build the CRM customer aggregate so tenant teams can manage customer master data, contact persons, reusable addresses, and optional portal-account linkage from a stable, normalized backend foundation.

## Source context

- Updated proposal: section 5.2 customer account and contact data; customer portal intent; Appendix A customer identification, contacts, portal access, and corporate data.
- Implementation specification: section 4.3 `crm.customer`, `crm.customer_contact`, and `crm.customer_address`; section 2 shared columns and tenant-safety rules; section 9 `CustomerAggregate` package map.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-4-T1` and `US-4-T2` should already provide tenant, branch, mandate, lookup, and reusable address foundations.
- `US-5-T1` should already provide `iam.user_account` and role-scope structures for optional customer-user linkage.
- `US-5-T4` should provide the preferred audit seam, even if some business-audit hooks land fully in later tasks.

## Scope of work

- Create migrations, SQLAlchemy models, Pydantic schemas, services, and API endpoints for `crm.customer`, `crm.customer_contact`, and `crm.customer_address`.
- Support customer numbers, active/inactive/archived lifecycle, legal-form/classification/ranking/status codes, and default branch/mandate linkage using `core.lookup_value`, `core.branch`, and `core.mandate`.
- Support one or more named contacts per customer, including primary-contact and billing-contact markers, phone/email/mobile fields, and optional `user_id` linkage to `iam.user_account`.
- Use `common.address` as the reusable address source and implement customer-address linking for registered, billing, mailing, and service addresses with one default per address type.
- Implement tenant-safe list/detail/search services and stable Create/Update/Read/List schemas suitable for later Vben Admin pages and portal linkage workflows.
- Add service validation for duplicate customer numbers, duplicate contact emails where constrained, one-primary-contact rules, one-default-address-per-type rules, and optimistic-lock behavior where the repo already uses `version_no`.
- Add automated tests for CRUD success cases, validation failures, tenant scoping, and optional portal-user linkage.

## Preferred file targets

- Alembic migration(s) for the CRM customer tables.
- `modules/customers/` or equivalent customer-domain models, schemas, services, routers, and tests.
- Shared lookup/address integration helpers only where needed to preserve module boundaries.
- No UI files yet except minimal API contract notes if the repo requires them.

## Hard constraints

- Customer users remain tenant-scoped actors inside the tenant security model; do not model customers as separate tenants.
- Use explicit foreign keys and tenant-aware access paths; do not introduce polymorphic shortcuts or cross-tenant joins that bypass customer ownership.
- Keep address truth in `common.address`; customer tables should link to reusable addresses instead of duplicating postal fields.
- Do not implement password-reset, login, or portal-session flows here; this task only links customer contacts to existing user-account infrastructure.
- Do not add billing-profile, invoice-party, rate-card, or surcharge-rule logic here; that belongs to `US-8-*`.
- Any user-visible validation or error content introduced here must respect German default and English secondary behavior.

## Expected implementation outputs

- A stable backend customer aggregate for master data, contacts, addresses, and portal-account linkage.
- Tenant-safe service and API contracts reusable by admin UI, portal scope logic, planning references, and finance readers.
- Automated migration and service/API tests covering core customer constraints.

## Non-goals

- Do not build the Vben Admin pages here; that is `US-7-T2`.
- Do not implement import/export, vCard generation, or change tracking here; that is `US-7-T3`.
- Do not finalize customer-specific audit/visibility policies here beyond leaving clean seams; that is `US-7-T4`.
- Do not implement customer portal read models here; that is `US-9-*`.

## Verification checklist

- New CRM migrations apply cleanly on a fresh database and do not break Sprint 2 foundations.
- Customers can be created, updated, listed, archived, and linked to multiple contacts and reusable addresses.
- One-primary-contact and one-default-address-per-type rules are enforced consistently.
- Tenant scoping prevents reading or mutating another tenant's customers or linked contacts.
- Optional portal-user linkage points only to valid tenant-scoped user accounts and does not create orphan references.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-7-T1 — Implement customer master, contacts, addresses, and portal user linkage** is finished.

```text
/review Please review the implementation for task US-7-T1 (Implement customer master, contacts, addresses, and portal user linkage) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-7-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- The customer aggregate matches the normalized schema and does not duplicate address or user-account truth.
- One-primary-contact, one-default-address-per-type, and uniqueness rules are enforced cleanly in both service logic and persistence where appropriate.
- Portal user linkage is optional, tenant-safe, and compatible with later role-scope enforcement.
- API contracts are stable enough for Vben Admin CRUD pages and later portal-auth work.

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

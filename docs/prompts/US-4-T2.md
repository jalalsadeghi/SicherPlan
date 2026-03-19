---
task_id: US-4-T2
story_id: US-4
story_title: "Tenant, branch, mandate, setting, and lookup foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead"
---

# Codex Prompt — US-4-T2

## Task title

**Build admin APIs/services for tenant onboarding and settings management**

## Objective

Implement the backend service and API layer for tenant onboarding, branch/mandate administration, and tenant configuration so platform operators can create and maintain prime-company records safely.

## Source context

- Updated proposal: section 4 roles for Platform Administrator and Tenant Administrator; section 5.1 system administration; section 7 security baseline; section 8 Phase 1.
- Implementation specification: bounded contexts and ownership for `core + iam`; normalized schema section 4.1 for tenant, branch, mandate, and tenant settings; shared columns and optimistic-lock expectations.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-4-T1` must land first so the persistence model and migrations are stable.
- Use the route/auth shell from Sprint 1, but do not block service/API work on the final RBAC middleware from `US-5-T3`.

## Scope of work

- Implement service-layer onboarding flows that can create a tenant and its initial administrative structure, including at least the first branch, mandate, and baseline settings shell where appropriate.
- Create CRUD-style API endpoints for tenant list/detail, branch management, mandate management, and tenant settings retrieval/update.
- Support lifecycle operations such as activate, deactivate, and archive where the approved workflow expects them.
- Use optimistic locking or equivalent concurrency protection for mutable configuration records such as `core.tenant_setting`.
- Return machine-readable validation and conflict responses that later web screens can consume without reinterpreting backend rules.
- Keep service methods explicit and bounded-context-owned; later modules may read tenant metadata, but they should not rewrite it through side paths.

## Preferred file targets

- Backend service/repository/router files under the actual core package, for example `apps/api/modules/core/services/tenant_service.py`, `routers/tenant_router.py`, and related schemas.
- Policy/helper files for lifecycle validation or conflict checking if the repo already separates them cleanly.
- API tests such as `apps/api/tests/modules/core/test_tenant_admin_api.py` or the repo equivalent.

## Hard constraints

- Platform-scope actions such as tenant creation must remain clearly separated from in-tenant administrative actions.
- Do not hardcode customer, subcontractor, or employee business logic into the onboarding flow.
- Any settings API must preserve tenant scoping, version safety, and predictable key ownership; avoid arbitrary unsafe JSON mutation patterns.
- Keep German default / English secondary behavior in mind for any returned message keys or user-facing validation labels.
- If audit hooks are not fully implemented yet, leave a clear integration seam rather than baking in an incompatible custom audit path.

## Expected implementation outputs

- Tenant onboarding and maintenance services with clear bounded-context ownership.
- HTTP APIs for tenant, branch, mandate, and settings management.
- Validation rules for status transitions, uniqueness conflicts, and settings updates.
- Automated API/service tests for success, failure, and scoping scenarios.

## Non-goals

- Do not seed the downstream lookup catalogs here; that is `US-4-T3`.
- Do not build the admin UI pages here; that is `US-4-T4`.
- Do not implement full audit-event persistence here beyond wiring a clean seam for `US-5-T4`.
- Do not create business-module defaults that belong to CRM, HR, partner, ops, or finance.

## Verification checklist

- A platform admin can onboard a tenant and create/update branches, mandates, and settings through stable API contracts.
- Conflict handling is deterministic for duplicate codes and stale-setting updates.
- Tenant admins cannot access or mutate another tenant's core records.
- The service layer remains reusable by later admin UI work.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-4-T2 — Build admin APIs/services for tenant onboarding and settings management** is finished.

```text
/review Please review the implementation for task US-4-T2 (Build admin APIs/services for tenant onboarding and settings management) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-4-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Authorization and tenant scoping are enforced at the service/API boundary, not deferred to UI assumptions.
- Lifecycle operations do not leave orphaned or inconsistent branch/mandate/settings records.
- Settings updates are version-safe and cannot silently overwrite concurrent changes.
- API contracts are stable enough for Vben admin pages and future automation to consume.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-4.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

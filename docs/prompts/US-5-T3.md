---
task_id: US-5-T3
story_id: US-5
story_title: "Identity, role scope, session management, and audit foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead"
---

# Codex Prompt — US-5-T3

## Task title

**Enforce RBAC middleware and tenant/branch/mandate scoping on APIs**

## Objective

Turn the IAM schema into enforceable authorization so every API request is evaluated against stable permission keys and the approved tenant/branch/mandate scope rules.

## Source context

- Updated proposal: section 4 role table and permission principle; section 7 security baseline; role-scoped visibility rules for tenant staff, customers, subcontractors, and employees.
- Implementation specification: IAM ownership and `iam.user_role_scope`; bounded-context write rules; cross-module scoping expectations; portal actors as scoped users within a tenant.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-5-T1` must provide the permission catalog and scoped role assignments.
- `US-5-T2` should provide authenticated request context or equivalent auth identity resolution.
- Core APIs from `US-4-T2` should already exist so the guards can be applied to real routes.

## Scope of work

- Implement request-time authorization helpers, middleware, dependencies, or decorators that evaluate module/action permissions against the current user's assigned roles and scopes.
- Support at least platform-scope, tenant-scope, branch-scope, and mandate-scope enforcement now, while keeping the same abstraction ready for future customer/subcontractor/employee view filters.
- Provide a reusable request context object or equivalent that carries tenant, user, role, and scope information cleanly into service code.
- Apply the new guard pattern to the platform-core APIs already delivered in Sprint 2, including tenant administration, settings, and other sensitive endpoints that should not be left open.
- Document the permission-key and route-guard conventions so later modules can add endpoints without inventing incompatible authorization patterns.
- Write authorization tests for allow/deny behavior, scope narrowing, cross-tenant blocking, and missing-permission cases.

## Preferred file targets

- Shared authorization middleware/dependency files under the actual backend app, for example `apps/api/modules/iam/authz/*` or `common/security/*`.
- Router updates across the already-created core/platform APIs.
- Tests such as `apps/api/tests/security/test_rbac_scope_enforcement.py` or equivalent.
- Optional engineering docs such as `docs/engineering/authorization-and-scope-rules.md`.

## Hard constraints

- Default to deny unless a route or service explicitly declares the required permission and the current scope authorizes it.
- Do not treat authentication alone as authorization.
- Customer, subcontractor, and employee actors must remain scoped to their own approved visibility slice even if they share the same `iam.user_account` table.
- Keep authorization rules explicit and inspectable; avoid magic string checks scattered across handlers.
- Do not overfit the guard system to only the current core endpoints; later modules must be able to reuse it.

## Expected implementation outputs

- Reusable RBAC + scope enforcement utilities.
- Protected APIs for the core platform surfaces already available in Sprint 2.
- Documentation for permission keys, route guards, and scope resolution.
- Automated authorization tests for common and edge cases.

## Non-goals

- Do not build management UIs for role assignment here unless the repo already needs a tiny helper screen; the main scope is backend enforcement.
- Do not implement customer/subcontractor portal business read models yet.
- Do not duplicate row-level business filtering logic inside every route handler.
- Do not skip tests because the rules seem 'obvious'; authorization regressions are high risk.

## Verification checklist

- Routes deny access when permission keys or scope context do not match.
- Branch- and mandate-scoped users cannot read or mutate data outside their allowed scope.
- Platform-level admins retain the explicitly approved broader scope without bypassing all checks invisibly.
- The authorization abstraction is usable by later CRM/HR/partner/ops modules without redesign.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-5-T3 — Enforce RBAC middleware and tenant/branch/mandate scoping on APIs** is finished.

```text
/review Please review the implementation for task US-5-T3 (Enforce RBAC middleware and tenant/branch/mandate scoping on APIs) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-5-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Authorization is explicit, default-deny, and consistently applied across real endpoints.
- Tenant, branch, and mandate scope resolution cannot be bypassed through route parameters or missing filters.
- Permission-key usage is coherent between backend guards and future UI route metadata.
- Tests meaningfully cover allow/deny and cross-scope edge cases.

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

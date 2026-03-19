---
task_id: US-5-T1
story_id: US-5
story_title: "Identity, role scope, session management, and audit foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Security Lead"
---

# Codex Prompt — US-5-T1

## Task title

**Implement user_account, roles, permissions, role scopes, sessions, and external identity models**

## Objective

Build the normalized IAM persistence foundation so every later module can authenticate users, assign scoped roles, and reason about permissions from one stable source of truth.

## Source context

- Updated proposal: section 4 target user groups and access model, especially the baseline roles and permission principle; section 5.1 identity and access; section 7 security baseline.
- Implementation specification: module ownership for `core + iam`; normalized schema section 4.1 for `iam.user_account`, `iam.external_identity`, `iam.role`, `iam.permission`, `iam.role_permission`, and `iam.user_session`; role-scope references to branch/mandate/customer/subcontractor scopes.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-4-T1` must already provide the tenant/branch/mandate backbone.
- Use the repo's existing password-hash and auth utility baseline from Sprint 1 if present; do not duplicate it.

## Scope of work

- Create migrations, SQLAlchemy models, and Pydantic schemas for the IAM tables: users, external identities, roles, permissions, role-permission links, user-role scopes, and refresh-session storage.
- Seed or otherwise bootstrap the baseline role and permission catalog needed for platform-core work, using the approved role model from the proposal and stable permission keys by module/action.
- Support scoped role assignments that can be tenant-wide or narrowed by branch/mandate today, with a future-ready path for customer/subcontractor scopes as those aggregates land in later sprints.
- Handle the sequencing gap explicitly: if CRM/partner tables do not yet exist, keep `customer_id` / `subcontractor_id` scope fields migration-safe and document when their FKs should be added later.
- Store refresh-session or session-identity data in a way that supports revocation, device metadata, and last-login views.
- Write model and constraint tests that prove usernames/emails/roles/scope tuples behave correctly.

## Preferred file targets

- Backend IAM models/schemas/seeds under the actual package structure, for example `apps/api/modules/iam/models/*`, `schemas/*`, `seed_permissions.py`, and related migration files.
- Tests such as `apps/api/tests/modules/iam/test_models_and_scope_constraints.py` or equivalent.

## Hard constraints

- Portal actors (customers, subcontractors, employees) remain scoped users inside a tenant, not separate tenants.
- Permission keys must be stable and machine-readable; do not couple them to translated display names.
- Do not hardwire future CRM/partner foreign keys in a way that breaks Sprint 2 migration sequencing.
- Store session tokens securely (hashed or equivalently protected), not as raw reusable secrets.
- Do not implement login APIs or password-reset flows here; that belongs to `US-5-T2`.

## Expected implementation outputs

- Normalized IAM tables and ORM models.
- Permission and role bootstrap data aligned with the approved role model.
- Scoped-role assignment support ready for middleware and API guards.
- Automated tests covering uniqueness, scope-tuple rules, and session persistence.

## Non-goals

- Do not implement auth endpoints or refresh-token issuance here.
- Do not implement full RBAC middleware here; that is `US-5-T3`.
- Do not implement audit/login-event persistence here; that is `US-5-T4`.
- Do not invent separate account systems for customers, subcontractors, and employees.

## Verification checklist

- Baseline roles and permissions can be loaded predictably and queried by module/action.
- User/role/scope assignments behave correctly for tenant-wide and narrowed scopes.
- Session rows are revocation-ready and avoid raw-token storage.
- Migration sequencing remains valid even though some later-sprint scope targets are not yet present.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-5-T1 — Implement user_account, roles, permissions, role scopes, sessions, and external identity models** is finished.

```text
/review Please review the implementation for task US-5-T1 (Implement user_account, roles, permissions, role scopes, sessions, and external identity models) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-5-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- The IAM schema matches the approved normalized model and migration sequence realities.
- Scoped role assignments are future-ready without creating invalid foreign-key dependencies on not-yet-built tables.
- Permission keys are stable and suitable for middleware, UI guards, and audit reporting.
- Session/token persistence is security-conscious and revocation-capable.

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

---
task_id: US-4-T1
story_id: US-4
story_title: "Tenant, branch, mandate, setting, and lookup foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead"
---

# Codex Prompt — US-4-T1

## Task title

**Create migrations/models for core.tenant, core.branch, core.mandate, core.tenant_setting, and core.lookup_value**

## Objective

Establish the normalized core tenant backbone in code so every later business module can rely on stable tenant, branch, mandate, setting, and lookup contracts from the first real migration onward.

## Source context

- Updated proposal: section 4 (target user groups and access model), section 5.1 (system administration), and section 8 Phase 1 platform core/security.
- Implementation specification: shared columns and lifecycle conventions; bounded contexts/service ownership; module ownership for `core + iam`; normalized schema section 4.1 for `core.tenant`, `core.branch`, `core.mandate`, `core.tenant_setting`, `core.lookup_value`, and the reusable `common.address` dependency.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-2-T1`, `US-2-T2`, and `US-2-T3` should already provide repo structure, environment setup, and migration validation tooling.
- Use the current SQLAlchemy/Alembic baseline from Sprint 1 instead of inventing a second migration or model pattern.

## Scope of work

- Create forward-only Alembic migrations and SQLAlchemy models for `core.tenant`, `core.branch`, `core.mandate`, `core.tenant_setting`, and `core.lookup_value`.
- Add Pydantic schemas that at minimum cover Create, Update, Read, and List-item shapes for the named core tables.
- Implement the key uniqueness and FK rules from the implementation spec, especially: tenant code uniqueness; branch code unique within tenant; mandate code unique within tenant; `(tenant_id, branch_id)` composite linkage for mandates; unique tenant setting key per tenant; lookup uniqueness across system-level and tenant-level values.
- Apply the shared lifecycle/audit columns consistently where the approved schema expects them, including `status`, timestamps, actor metadata, `archived_at`, and `version_no` on mutable aggregate roots.
- If the repository does not yet have `common.address`, introduce the minimum reusable address model needed for `core.branch.address_id`, but keep the main scope centered on the named core tables.
- Write migration and model tests that prove the uniqueness rules, FK behavior, and optimistic-lock-ready fields are all wired correctly.

## Preferred file targets

- API/backend module files under the actual core package, for example `apps/api/modules/core/models/*`, `schemas/*`, and `repositories/*` (adapt to the repo layout).
- Alembic revisions under the actual migration directory, for example `apps/api/alembic/versions/*_core_tenant_backbone.py`.
- Tests such as `apps/api/tests/modules/core/test_tenant_backbone.py` or the repo equivalent.

## Hard constraints

- `core.tenant` is platform-scope and must not be treated as a tenant-owned row.
- Use explicit foreign keys and composite constraints where the implementation specification calls for them; do not replace them with loose JSON or string references.
- Do not bake business-module assumptions into the core tables beyond what the proposal/spec already approved.
- Keep the lookup model extensible for future modules, but do not turn every narrow technical state into a lookup if the implementation spec expects a DB enum or similarly strict state model.
- Do not implement admin APIs or UI here; those belong to later tasks in `US-4`.

## Expected implementation outputs

- Alembic revisions that can be applied on a clean database and survive CI migration checks.
- SQLAlchemy declarative models grouped inside the core bounded context.
- Pydantic Create/Update/Read/List schemas for the new tables.
- Automated tests covering constraints, FK integrity, and lifecycle defaults.

## Non-goals

- Do not build tenant onboarding services or HTTP endpoints here; that is `US-4-T2`.
- Do not seed downstream lookup content here; that is `US-4-T3`.
- Do not build Vben admin pages here; that is `US-4-T4`.
- Do not pull customer, subcontractor, or employee master data into the core module.

## Verification checklist

- The migration runs cleanly on an empty database and passes the repo's migration smoke tests.
- The SQLAlchemy models reflect the actual approved FK and uniqueness rules from the implementation spec.
- A tenant cannot accidentally reuse another tenant's branch or mandate code through missing composite scoping.
- The result is ready for later API/service work without schema rewrites.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-4-T1 — Create migrations/models for core.tenant, core.branch, core.mandate, core.tenant_setting, and core.lookup_value** is finished.

```text
/review Please review the implementation for task US-4-T1 (Create migrations/models for core.tenant, core.branch, core.mandate, core.tenant_setting, and core.lookup_value) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-4-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Migrations are forward-only, deterministic, and aligned with the approved normalized schema.
- Tenant isolation is structural, not only enforced in service code.
- Lookup scoping correctly separates system-level and tenant-level values without uniqueness collisions.
- No speculative schema drift is introduced beyond the approved core foundation.

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

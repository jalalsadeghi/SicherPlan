---
task_id: US-4-T3
story_id: US-4
story_title: "Tenant, branch, mandate, setting, and lookup foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Data Lead"
---

# Codex Prompt — US-4-T3

## Task title

**Seed system and tenant lookup domains needed by downstream modules**

## Objective

Create an idempotent lookup seeding package that gives later modules a dependable catalog of system-level and tenant-extensible business values without hardcoding them in application logic.

## Source context

- Updated proposal: section 5.1 platform foundation and section 5.2+ downstream modules that reference legal forms, statuses, invoice layouts, shipping, and report/compliance categories.
- Implementation specification: `core.lookup_value` in section 4.1; cross-module references showing lookup-backed codes across CRM, HR, finance, and reporting; DE-default / EN-secondary platform rules.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-4-T1` must provide the lookup table and related schemas first.
- Coordinate with `US-5-T1` so permission/role dictionaries do not get conflated with business lookups unless the repo already has a deliberate shared seeding mechanism.

## Scope of work

- Create an idempotent seed mechanism for system-scoped lookup domains that downstream modules will rely on immediately after Sprint 2 and Sprint 3.
- Define the initial domain/code set conservatively and clearly, covering only approved cross-module business lists such as legal forms, common statuses where lookup-backed, invoice/shipping/dunning/report categories, and other explicitly referenced business dictionaries.
- Support tenant-level extension or override where the approved model expects tenant-extensible values rather than platform-fixed dictionaries.
- Document which domains are platform-managed versus tenant-extensible, and how later modules should add new values without breaking stable codes.
- Where localized labels are needed, keep German as the default label and include an English-ready path only if it fits the approved schema and existing repo conventions (for example, translation metadata in `extra_json` or a separate app-level i18n map).
- Add tests or repeatable verification commands proving the seed process is safe to rerun.

## Preferred file targets

- Seed scripts/fixtures in the repo's actual backend data/bootstrap location, for example `apps/api/scripts/seed_lookup_values.py` or equivalent.
- Supporting constants or YAML/JSON seed source files if the repo already uses them.
- Docs such as `docs/engineering/lookup-seeding.md` or a module-local README if helpful.

## Hard constraints

- Stable lookup `code` values matter; do not use human display labels as integration identifiers.
- Do not seed speculative business catalogs that are not grounded in the proposal or implementation specification.
- Keep the seed process idempotent and environment-safe; rerunning it must not create duplicates.
- Do not misuse `core.lookup_value` for security permissions, secrets, or config blobs that belong in IAM or tenant settings.

## Expected implementation outputs

- A deterministic seed package for approved system and tenant-extensible lookup domains.
- A documented governance rule for adding new lookup values later.
- Tests or smoke-check commands that prove re-runs are safe.

## Non-goals

- Do not seed actual customer, employee, subcontractor, or order data.
- Do not implement tenant onboarding APIs or screens here.
- Do not create a full translation subsystem solely for lookup values if the repo has not approved one yet.
- Do not replace stricter enum-backed technical states with lookup rows just for convenience.

## Verification checklist

- Seed execution is idempotent and does not create duplicate rows.
- System-managed and tenant-extensible domains are clearly separated.
- The chosen domains are demonstrably useful for upcoming CRM/HR/finance/reporting tasks.
- Stable codes exist for machine use while display labels remain user-facing.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-4-T3 — Seed system and tenant lookup domains needed by downstream modules** is finished.

```text
/review Please review the implementation for task US-4-T3 (Seed system and tenant lookup domains needed by downstream modules) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-4-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Seed data is narrowly scoped to approved business domains and avoids future cleanup debt.
- System-level versus tenant-level lookup ownership is implemented correctly.
- Localization handling for labels is deliberate and does not conflict with the approved schema.
- Seed scripts are reproducible in local, CI, and staging contexts.

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

---
task_id: US-4-T4
story_id: US-4
story_title: "Tenant, branch, mandate, setting, and lookup foundation"
sprint: Sprint 02
status: ready
owner: "Frontend Lead / Backend Lead"
---

# Codex Prompt — US-4-T4

## Task title

**Create web admin screens for tenants, branches, mandates, settings, and archival states**

## Objective

Deliver the Vben-based administrative web flows for the core tenant backbone so platform and tenant administrators can manage tenant structures through a professional, localized UI.

## Source context

- Updated proposal: section 4 roles and data scopes; section 5.1 system administration; section 7 client/web stack and security baseline.
- Implementation specification: section 4.1 core tables; service-boundary rules for core ownership; shared lifecycle/status conventions.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md`, plus the Sprint 1 shell/theme/i18n prompts already completed for Vben Admin.

## Dependencies

- `US-4-T2` should expose the backend APIs first.
- `US-3-T1`, `US-3-T3`, and `US-3-T4` should already provide the web shell, theme tokens, and DE/EN localization baseline.

## Scope of work

- Create Vben Admin routes, pages, and API bindings for tenant overview, tenant detail, branch maintenance, mandate maintenance, and tenant settings editing.
- Use list/detail/form patterns that fit the existing shell, including route metadata, breadcrumbs, permission keys, stateful filters, and status badges.
- Support activate/deactivate/archive actions and clearly surface lifecycle state in tables and detail views.
- Provide safe settings editing UX for key/value or typed settings models without exposing raw unsafe internals unnecessarily.
- Ship German default and English secondary resources for all user-facing strings introduced here.
- Design the UI so final permission wiring from `US-5-T3` can attach cleanly through route metadata and guard keys instead of requiring page rewrites later.

## Preferred file targets

- Web views/components under the actual Vben workspace, for example `apps/web/src/views/admin/tenants/*`, `branches/*`, `mandates/*`, and shared form/table components.
- Web API client bindings under the actual service/request layer.
- Locale resources such as `de-DE` / `en-US` files in the repo's existing i18n structure.
- Frontend tests such as route/page smoke tests or component tests if the web app already uses them.

## Hard constraints

- Respect the approved Vben Admin shell, theme tokens, and DE-default / EN-secondary localization rules from Sprint 1.
- Do not expose cross-tenant data in list pages, search, or route-based detail views.
- Keep archival controls explicit and auditable; avoid destructive-delete UX for core records.
- Do not invent customer, employee, or subcontractor admin screens here.
- Use permission-friendly route metadata and action keys; do not hardcode security assumptions into component visibility only.

## Expected implementation outputs

- Vben-based admin pages for tenant, branch, mandate, and settings management.
- Localized UI resources for German and English.
- API bindings and page-level validation/error handling.
- Basic automated coverage or smoke verification for the new routes/pages.

## Non-goals

- Do not implement login/auth flows here; those belong to `US-5-*`.
- Do not build global reporting or dashboard features.
- Do not embed undocumented business workflow logic into the UI that belongs in backend services.
- Do not bypass the backend APIs by mutating local mock state as the source of truth.

## Verification checklist

- The pages follow the existing Vben shell and render correctly in German default and English secondary modes.
- Users can list, create, edit, archive, and reactivate the core records allowed by the backend APIs.
- Permission metadata is present and ready for RBAC middleware/route-guard integration.
- No tenant-crossing data appears in the UI under normal navigation or direct-link attempts.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-4-T4 — Create web admin screens for tenants, branches, mandates, settings, and archival states** is finished.

```text
/review Please review the implementation for task US-4-T4 (Create web admin screens for tenants, branches, mandates, settings, and archival states) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-4-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Vben Admin patterns, route metadata, and reusable CRUD conventions are followed cleanly.
- Localization is complete for newly introduced UI text and validation feedback.
- Archival and lifecycle actions are obvious, safe, and wired to backend truth.
- Frontend data loading and cache/update logic do not leak cross-tenant records.

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

---
task_id: US-9-T2
story_id: US-9
story_title: "Customer portal read models, collaboration views, and customer-specific controls"
sprint: Sprint 03
status: ready
owner: "Web Lead / Backend Lead"
---

# Codex Prompt — US-9-T2

## Task title

**Expose released orders, schedules, watchbooks, timesheets, and report read models**

## Objective

Create the customer-portal read-model layer for released customer-facing operational outputs so the portal can present customer-owned orders and published results safely, with clean contracts that can be extended as later operational modules land.

## Source context

- Updated proposal: section 5.2 customer portal, online watchbook, and customer-facing report/timesheet scope; section 5.5 released outputs; section 5.6 customer billing/timesheet visibility; Appendix A portal collaboration scope.
- Implementation specification: portal visibility chain; docs backbone for generated outputs; migration sequence where ops/field/finance source tables arrive in later phases; aggregate/package map.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-9-T1` must already provide portal auth and customer-scope filtering.
- Some upstream write models for orders, schedules, watchbooks, timesheets, and reports land later in the delivery plan; this task must remain contract-first and not invent incompatible source tables if they are not yet present in the repo.
- `US-6-T1` and shared docs/output infrastructure should already exist for report/timesheet/document references.

## Scope of work

- Implement customer-portal query services, DTOs, endpoints, and page/view scaffolding for released customer-facing orders, schedules, watchbooks, timesheets, and report/result packages.
- Use a projection/query-service pattern so portal reads remain decoupled from upstream write models; where the source modules already exist in the repository, wire real released-data queries, and where they do not, provide explicit contract stubs, feature flags, or empty-state adapters rather than fake domain tables.
- Apply released-only filters, customer scope filters, and visibility flags consistently across every read model.
- Represent document-backed outputs through the shared docs service rather than file-path shortcuts.
- Provide customer-friendly list/detail views or DTOs that support later extension as ops, field, and finance modules come online, without breaking portal contracts.
- Add tests for released-only filtering, customer scoping, empty-state behavior, and contract stability.

## Preferred file targets

- Portal query services and read DTOs under `modules/customers/`, `modules/reporting/`, or a portal-query package that matches the repo's structure.
- Customer-portal API endpoints and web pages/components for released customer-facing results.
- Use of docs-backed output metadata rather than unmanaged export files.
- Integration tests for portal read-model security and release gating.

## Hard constraints

- Do not invent incompatible operational source tables just to make the portal look complete before later sprints land.
- Portal views must remain read-only and released-only.
- Customer scope must apply to every query and document lookup path; no broad tenant datasets in the portal.
- Default visibility must be least privilege, especially around personal names and commercial totals.
- Use explicit, versionable read contracts so later operational modules can plug in without reworking the portal surface.

## Expected implementation outputs

- Customer-portal read-model contracts and pages/endpoints for released customer-facing outputs.
- Feature-safe empty states or contract stubs where later source modules are not yet present.
- Security and release-filter tests for customer-facing reads.

## Non-goals

- Do not build the upstream planning, watchbook, time-capture, or finance write models here.
- Do not allow customers to edit or approve tenant operational data through these views.
- Do not expose unreleased draft or internal-only operational artifacts.

## Verification checklist

- Only released, customer-scoped records are returned by portal read-model endpoints.
- Portal views behave predictably when upstream source modules are not yet implemented in the repository.
- Document/result links resolve through the shared docs/output backbone.
- Read contracts are explicit enough that later ops/field/finance tasks can plug in without breaking the portal.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-9-T2 — Expose released orders, schedules, watchbooks, timesheets, and report read models** is finished.

```text
/review Please review the implementation for task US-9-T2 (Expose released orders, schedules, watchbooks, timesheets, and report read models) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-9-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Portal read models are contract-first, released-only, and do not create fake or incompatible upstream truth.
- Customer scope and release filters are applied consistently across data and document paths.
- Empty-state or feature-flag behavior is clean and honest where later modules are still pending.
- The implementation creates extensible customer-facing contracts rather than brittle one-off joins.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-9.
- Call out hidden assumptions about source modules that are not yet in the repository, along with any brittle query coupling that would break once planning, field, or finance modules land.
- If no real issue exists, say so clearly and do not invent problems.
```

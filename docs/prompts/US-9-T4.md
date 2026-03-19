---
task_id: US-9-T4
story_id: US-9
story_title: "Customer portal read models, collaboration views, and customer-specific controls"
sprint: Sprint 03
status: ready
owner: "Web Lead / Backend Lead / QA Lead"
---

# Codex Prompt — US-9-T4

## Task title

**Validate customer-facing views hide personal names by default unless explicitly released**

## Objective

Implement and verify the privacy rule that customer-facing result views, exports, and document-linked outputs hide personal names by default, with any explicit name-release behavior controlled, auditable, and narrow.

## Source context

- Updated proposal: permission principle in section 4; section 5.2 customer portal; section 5.5 operational note that customer-facing result views and reports should omit personal names by default; Appendix A portal collaboration and customer controls.
- Implementation specification: portal visibility chain; reporting/security view guidance; shared docs/output patterns; cross-cutting tenant/privacy rules.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-9-T1` and `US-9-T2` must already provide the portal auth and customer-facing read-model surfaces that need privacy enforcement.
- `US-7-T4` should already provide backend visibility hardening and audit seams.
- `US-9-T3` may already surface history/login views that also need privacy review where personal names are involved.

## Scope of work

- Implement backend and frontend/privacy-contract rules so customer-facing views default to masked, anonymized, or pseudonymized person references instead of real employee names where the proposal says names must stay hidden by default.
- Apply the rule not only to on-screen portal views but also to exported/read-only documents, report metadata, file names, and DTO fields that could leak personal names indirectly.
- Define and implement the narrow release mechanism for cases where the prime company explicitly approves personal-name visibility, including an auditable flag or decision point rather than an implicit UI toggle.
- Ensure commercial totals remain visible only where explicitly approved, consistent with the proposal's permission principle.
- Add test coverage for default-masked behavior, explicit-release behavior, document/export behavior, and regression checks against accidental name leakage.
- If some upstream source modules are not yet implemented, still place the masking/release policy at the shared portal DTO or serializer layer so later modules inherit it cleanly.

## Preferred file targets

- Shared portal read-model/DTO serializers or privacy-masking helpers under the web/backend portal stack.
- Customer-portal views/components that render masked versus explicitly released identity labels correctly.
- Tests for portal responses, document/export metadata, and permission/audit behavior around name release.

## Hard constraints

- Do not rely on UI-only hiding; privacy masking must exist in backend response shaping or equivalent shared contracts.
- Any explicit release of personal names must be narrow, intentional, and auditable.
- Do not mutate upstream operational truth just to hide names in the portal; privacy belongs in the customer-facing read layer.
- Masking must cover documents, exports, and metadata paths, not just primary list/detail screens.
- Do not expose commercial totals unless explicit approval rules allow it.

## Expected implementation outputs

- A shared privacy-masking rule for customer-facing read models and outputs.
- An auditable explicit-release mechanism for approved name visibility cases.
- Regression tests that protect against accidental personal-name leakage.

## Non-goals

- Do not redesign the entire permission model here; enforce the specific customer-facing privacy rule on top of existing auth/scope work.
- Do not create a new shadow copy of reports/documents solely for masking purposes if shared read-layer masking can solve it.
- Do not expose additional HR-sensitive data under the guise of customer-name release.

## Verification checklist

- Customer-facing views hide personal names by default.
- Explicitly released views show names only when the required approval/release condition is present.
- Documents, exports, DTOs, and metadata paths do not leak personal names by accident.
- Name-release decisions are auditable and test-covered.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-9-T4 — Validate customer-facing views hide personal names by default unless explicitly released** is finished.

```text
/review Please review the implementation for task US-9-T4 (Validate customer-facing views hide personal names by default unless explicitly released) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-9-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Privacy masking is enforced in shared read contracts and not only in UI templates.
- Explicit release of names is narrow, auditable, and free of broad side effects.
- Documents, exports, and metadata paths receive the same privacy treatment as on-screen portal views.
- The implementation protects against regressions and future module leakage.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-9.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, unsafe defaults, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

---
task_id: US-1-T1
story_id: US-1
story_title: "Discovery, backlog confirmation, and acceptance traceability"
sprint: Sprint 01
status: ready
owner: "PO / BA"
---

# Codex Prompt — US-1-T1

## Task title

**Review proposal, implementation spec, and the three end-to-end workflows**

## Objective

Create a concise discovery baseline that translates the updated proposal and the implementation-oriented data model into an execution-ready understanding of product scope, bounded contexts, and workflow priorities.

## Source context

- Updated proposal: Executive summary; design principles; target user groups and access model; end-to-end workflows; technical architecture; delivery phases; deliverables and assumptions.
- Implementation specification: Purpose; platform foundation and modeling conventions; bounded contexts and service ownership; cross-module relationship map; migration waves; aggregate/code-package map; SQLAlchemy/Pydantic implementation notes.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- No upstream task dependency. This is the first execution task in the backlog.
- Read the repository state first; do not assume missing docs unless they truly do not exist.

## Scope of work

- Review the proposal and the implementation spec as one combined source of truth, and extract the scope that matters for early delivery decisions.
- Summarize the three reference workflows: customer order to report/invoice, applicant to payroll-ready employee, and subcontractor collaboration.
- Map each workflow to the planned bounded contexts (`core`, `iam`, `platform_services`, `customers`, `recruiting`, `employees`, `subcontractors`, `planning`, `field_execution`, `finance`, `reporting`).
- Highlight non-negotiables that must shape every later task: tenant isolation, role-scoped visibility, append-only evidence handling, DE default / EN secondary, Vben web shell, Prokit-inspired Flutter shell, and fixed light/dark primary colors.
- List open questions, assumptions, and decision points that could materially affect Sprint 1 or Sprint 2.

## Preferred file targets

- `docs/discovery/us-1-t1-scope-review.md`
- `docs/discovery/us-1-t1-workflow-context-map.md` (optional if you want a separate workflow appendix)

## Hard constraints

- Do not rewrite backlog IDs or reorder the approved 12-sprint baseline.
- Do not invent business scope that is not grounded in the proposal or implementation specification.
- Treat the implementation specification as authoritative for data ownership, migration sequence, and service boundaries.
- Treat the proposal as authoritative for workflow meaning, portals, field behavior, finance flows, and acceptance intent.

## Expected implementation outputs

- A discovery review document that clearly explains platform scope, workflow scope, and module boundaries in implementation language.
- A workflow-to-bounded-context mapping that later prompts can reference without reinterpretation.
- A short open-questions / assumptions section tagged by impact (`blocking now`, `needed before Sprint 2`, `can defer`).

## Non-goals

- Do not define Definition of Ready / Definition of Done here; that belongs to `US-1-T2`.
- Do not formalize the migration/integration/NFR register here; that belongs to `US-1-T3`.
- Do not create the traceability matrix or demo checklist here; that belongs to `US-1-T4`.

## Verification checklist

- The review references all three end-to-end workflows.
- The review reflects the actual bounded contexts and migration waves from the implementation specification.
- The resulting document is concise, implementation-oriented, and free of contradictory statements.
- No stable IDs (`US-*`) are changed or renamed.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-1-T1 — Review proposal, implementation spec, and the three end-to-end workflows** is finished.

```text
/review Please review the implementation for task US-1-T1 (Review proposal, implementation spec, and the three end-to-end workflows) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-1-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Tenant isolation, scoping, and data ownership boundaries are enforced.
- Role-based visibility and authorization rules match the prompt and service boundaries.
- Vben Admin integration follows the agreed shell, navigation, theme, and i18n conventions.
- Flutter shell or mobile-related changes stay aligned with the Prokit-inspired structure and localization rules.
- Workflow assumptions stay consistent with the proposal and do not skip required states or approvals.
- CI/CD and automation changes are minimal, reproducible, and do not weaken quality gates.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-1.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

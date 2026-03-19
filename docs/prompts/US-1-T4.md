---
task_id: US-1-T4
story_id: US-1
story_title: "Discovery, backlog confirmation, and acceptance traceability"
sprint: Sprint 01
status: ready
owner: "PO / BA / QA"
---

# Codex Prompt — US-1-T4

## Task title

**Create demo checklist and traceability matrix from story to acceptance criteria**

## Objective

Produce a durable acceptance-traceability asset that links story IDs, source requirements, demo evidence, and later UAT/go-live validation.

## Source context

- Updated proposal: executive summary; target users and access model; functional scope; end-to-end workflows; delivery phases; deliverables and acceptance; appendices for planning and validation/report catalogue.
- Implementation specification: cross-module relationship map; validation rules mapped to persistence; reporting guidance; migration waves.
- Sprint references: Sprint 1 file plus the remaining sprint files under `docs/sprint/`.
- Task index baseline: `docs/prompts/task-index.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-1-T1`, `US-1-T2`, and `US-1-T3` should inform this task.
- Keep the already-approved Story IDs intact.

## Scope of work

- Create a traceability matrix that maps each story to its acceptance intent, source documents, main deliverable, and expected evidence/demo form.
- Explicitly track the three reference workflows across the relevant stories so end-to-end acceptance is visible before implementation starts.
- Create a Sprint 1 demo checklist that can be used in review meetings and that can serve as a template for later sprint demo checklists.
- Include acceptance evidence types such as docs, UI demo, API behavior, migration proof, test run, report/PDF output, or audit evidence, depending on the story.
- Keep the matrix practical and readable; it should help implementation and QA, not become a bureaucracy artifact.

## Preferred file targets

- `docs/qa/traceability-matrix.md`
- `docs/qa/sprint-demo-checklist.md`

## Hard constraints

- Traceability must use stable Story IDs and Task IDs exactly as published.
- Do not reduce acceptance to generic pass/fail text; preserve business-specific evidence expectations.
- Customer/subcontractor privacy, HR-private restrictions, and append-only evidence rules should be visible in the acceptance notes where relevant.

## Expected implementation outputs

- A story-to-acceptance matrix covering the 12-sprint backlog at story level.
- A Sprint 1 demo checklist with concrete review points for backlog, CI/CD, and Vben/Prokit shell readiness.
- A visible mapping of the three reference workflows across later stories.

## Non-goals

- Do not implement automated tests or demo scripts here.
- Do not redefine story scope or acceptance text outside clarifying wording.
- Do not create Sprint 2+ detailed demo scripts unless you can do so cheaply without distracting from the matrix.

## Verification checklist

- Every story in the sprint backlog appears once in the traceability matrix.
- The three reference workflows are traceable across multiple stories, not isolated to one row.
- The Sprint 1 demo checklist can be executed by a reviewer without additional explanation.
- IDs and source references remain consistent.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-1-T4 — Create demo checklist and traceability matrix from story to acceptance criteria** is finished.

```text
/review Please review the implementation for task US-1-T4 (Create demo checklist and traceability matrix from story to acceptance criteria) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-1-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Migrations are forward-only, deterministic, and aligned with the implementation data model.
- Workflow assumptions stay consistent with the proposal and do not skip required states or approvals.
- CI/CD and automation changes are minimal, reproducible, and do not weaken quality gates.
- Auditability, append-only evidence, and traceability requirements are preserved.

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

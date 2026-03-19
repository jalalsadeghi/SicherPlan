---
task_id: US-1-T2
story_id: US-1
story_title: "Discovery, backlog confirmation, and acceptance traceability"
sprint: Sprint 01
status: ready
owner: "PO / BA"
---

# Codex Prompt — US-1-T2

## Task title

**Define backlog epics, sprint goals, dependencies, and Definition of Ready/Done**

## Objective

Convert the approved proposal/spec baseline into a disciplined backlog management package that preserves stable story IDs and gives later Codex tasks a dependable planning frame.

## Source context

- Updated proposal: delivery approach and phased implementation; deliverables and acceptance; assumptions and dependencies.
- Implementation specification: migration order and implementation sequence; aggregate and code-package map; implementation notes for SQLAlchemy and Pydantic.
- Sprint references: `docs/sprint/sprint-01-inception-and-setup.md` and the remaining sprint files under `docs/sprint/`.
- Task tracking baseline: `docs/prompts/task-index.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-1-T1` should exist or its conclusions should be available before finalizing this task.
- Preserve the story/task structure already published in the sprint plan and prompt index.

## Scope of work

- Create a backlog-epic view that groups stories by platform capability and bounded context without changing existing Story IDs.
- Document sprint goals and inter-story dependencies so later task prompts know what must land first and what can proceed in parallel.
- Define a practical Definition of Ready that covers source clarity, dependency clarity, acceptance clarity, and testability before a task is started.
- Define a practical Definition of Done that reflects AGENTS rules: build/lint/tests, tenant scoping, role scoping, audit/evidence handling, migration coherence, DE/EN coverage, and theme consistency where UI work is involved.
- Capture dependency notes for Sprint 1 and the earliest cross-sprint handoffs into Sprint 2.

## Preferred file targets

- `docs/backlog/backlog-epics-and-dependencies.md`
- `docs/backlog/definition-of-ready-and-done.md`
- Update existing sprint or prompt index docs only if the references need clarification; do not renumber anything.

## Hard constraints

- Stable identifiers (`US-N`, `US-N-TN`) are non-negotiable.
- Do not collapse bounded contexts into a generic backlog; keep module ownership legible.
- Definition of Done must explicitly include DE default / EN secondary for user-facing changes.
- Definition of Done must explicitly include audit/evidence rules for sensitive or append-only flows.

## Expected implementation outputs

- A clear epic and dependency overview aligned with the 12-sprint plan.
- A written Definition of Ready and Definition of Done that later Codex tasks can reuse verbatim.
- A dependency section that highlights the prerequisite chain from Sprint 1 into Sprint 2 platform-core work.

## Non-goals

- Do not create detailed migration assumptions or provider decisions here; that belongs to `US-1-T3`.
- Do not build the story-to-acceptance traceability matrix here; that belongs to `US-1-T4`.
- Do not rewrite story titles unless there is a typo-level correction and it preserves the original intent.

## Verification checklist

- All Sprint 1 stories (`US-1`, `US-2`, `US-3`) have clear dependencies and Done criteria.
- Definitions are specific enough to guide implementation and review, not generic agile filler.
- Backlog grouping aligns with the aggregate/package model in the implementation specification.
- The result remains readable by PO, engineering, and QA stakeholders.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-1-T2 — Define backlog epics, sprint goals, dependencies, and Definition of Ready/Done** is finished.

```text
/review Please review the implementation for task US-1-T2 (Define backlog epics, sprint goals, dependencies, and Definition of Ready/Done) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-1-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Tenant isolation, scoping, and data ownership boundaries are enforced.
- Role-based visibility and authorization rules match the prompt and service boundaries.
- Migrations are forward-only, deterministic, and aligned with the implementation data model.
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

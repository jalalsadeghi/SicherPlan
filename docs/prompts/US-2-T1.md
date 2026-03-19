---
task_id: US-2-T1
story_id: US-2
story_title: "Repository, environments, CI/CD, and observability baseline"
sprint: Sprint 01
status: ready
owner: "DevOps / Tech Lead"
---

# Codex Prompt — US-2-T1

## Task title

**Create repository structure, branching strategy, and coding conventions across backend, web, and mobile**

## Objective

Establish a repository structure and engineering conventions that support a modular FastAPI backend, a Vben-based Vue web client, and a Prokit-inspired Flutter mobile client without creating future rework.

## Source context

- Updated proposal: technical architecture and quality requirements; phased implementation; deliverables and acceptance.
- Implementation specification: bounded contexts and service ownership; migration waves; aggregate/code-package map; SQLAlchemy/Pydantic notes.
- Cross-cutting rules and module map: `AGENTS.md`.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.

## Dependencies

- `US-1-T2` should define dependency and Done rules first.
- If the repo already contains structure, adapt it conservatively instead of duplicating whole app trees.

## Scope of work

- Inspect the current repository and decide whether it should remain a monorepo or structured multi-app repo; document the reasoning instead of assuming from scratch.
- Establish or refine top-level folders for backend, web, mobile, infrastructure, and docs. If greenfield, prefer a clean layout that keeps FastAPI, web, and mobile clearly separated while allowing shared docs and CI.
- Apply the bounded-context package map for backend code (`modules/core`, `modules/iam`, `modules/platform_services`, `modules/customers`, `modules/recruiting`, `modules/employees`, `modules/subcontractors`, `modules/planning`, `modules/field_execution`, `modules/finance`, `modules/reporting`).
- Define branching, pull-request, commit, and release conventions suited to incremental Codex-driven delivery.
- Set coding conventions and baseline tooling for Python, TypeScript/Vue, and Dart/Flutter.

## Preferred file targets

- `README.md` (update if needed to explain repo entry points)
- `docs/engineering/repository-structure.md`
- `docs/engineering/branching-and-coding-standards.md`
- Root tooling/config files such as `.editorconfig`, `.gitignore`, formatter/linter configs, and any workspace manifests that fit the repo

## Hard constraints

- Do not force a second, conflicting repository layout if one already exists.
- Keep backend package ownership aligned with the implementation specification; do not flatten all business logic into a generic `services` folder.
- Preserve room for migrations, Pydantic schemas, tests, and UI/mobile apps from day one.
- Document choices clearly enough that later Codex tasks can follow them consistently.

## Expected implementation outputs

- A practical repository layout with clear app boundaries.
- Written engineering conventions for backend, web, and mobile.
- A documented branching/release convention suitable for short sprint cycles and task-by-task Codex work.

## Non-goals

- Do not provision secrets or runtime environments here; that belongs to `US-2-T2`.
- Do not implement CI workflows here; that belongs to `US-2-T3`.
- Do not implement business modules or persistence models yet.

## Verification checklist

- A new contributor can understand where backend, web, mobile, infra, and docs live.
- Bounded contexts are visible in the backend package structure.
- Branching and coding conventions are explicit, not implied.
- The layout is compatible with Vben Admin for web and Flutter for mobile.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-2-T1 — Create repository structure, branching strategy, and coding conventions across backend, web, and mobile** is finished.

```text
/review Please review the implementation for task US-2-T1 (Create repository structure, branching strategy, and coding conventions across backend, web, and mobile) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-2-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Vben Admin integration follows the agreed shell, navigation, theme, and i18n conventions.
- Flutter shell or mobile-related changes stay aligned with the Prokit-inspired structure and localization rules.
- CI/CD and automation changes are minimal, reproducible, and do not weaken quality gates.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-2.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

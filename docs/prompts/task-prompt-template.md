---
task_id: US-X-TY
story_id: US-X
sprint: Sprint NN
status: draft
---

# Codex Prompt — US-X-TY

## Objective

Describe exactly what this task should implement.

## Source context

- `AGENTS.md`
- `docs/sprint/sprint-NN-...md`

## Dependencies

- List upstream story IDs, task IDs, or repo prerequisites here.

## Hard constraints

- Preserve tenant isolation and role scoping.
- Keep changes inside the intended bounded context unless the task explicitly requires a contract update.
- Use German as default UI language and English as secondary language for any user-facing output introduced here.
- Respect the fixed theme tokens where UI work is involved.

## Expected implementation outputs

- Migrations
- SQLAlchemy models
- Pydantic schemas
- Services / repositories
- Routers / controllers
- Web or mobile UI changes
- Tests
- Docs / prompt status updates

## Non-goals

State what should not be implemented in this prompt even if it appears nearby in the backlog.

## Verification checklist

- [ ] Build / lint passes
- [ ] Tests cover the task
- [ ] Tenant scoping is enforced
- [ ] Role scoping is enforced
- [ ] Audit / evidence handling is correct
- [ ] DE/EN resources are updated when needed
- [ ] Prompt and task traceability remain intact

# Prompt Files

This folder is reserved for task-level Codex prompts.

## Naming convention

Create one Markdown file per task using the task ID as the filename:

- `docs/prompts/US-4-T1.md`
- `docs/prompts/US-22-T3.md`
- `docs/prompts/US-31-T2.md`

## Working rule

Every new task prompt should be written only after reading:

1. `AGENTS.md`
2. The matching sprint file under `docs/sprint/`
3. Any earlier task prompt files that the new task explicitly depends on

## Expected prompt structure

Each task prompt should contain:

- task objective
- source sprint and story context
- dependencies and blockers
- hard constraints
- expected implementation outputs
- test and verification expectations
- non-goals / out-of-scope notes

## Scope rule

One prompt should normally target one task ID.  
If a task is too large, split execution internally, but keep the original task ID in the filename and title so backlog traceability stays intact.

## Status tracking

Update `task-index.md` when a new prompt file is added or completed.

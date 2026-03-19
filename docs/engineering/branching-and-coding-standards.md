# Branching And Coding Standards

## Task anchor

- Task: `US-2-T1`

## Branching model

SicherPlan should use a short-lived branch model suited to task-by-task Codex execution.

### Protected long-lived branches

- `main`: always releasable, protected, merge-by-review only
- `develop`: optional integration branch if the team needs sprint-level staging before promoting to `main`

If the team wants the simplest possible model, it can operate with `main` only plus short-lived feature branches. Do not maintain multiple long-lived branches unless they are actively used.

### Short-lived working branches

Recommended naming:

- `feature/US-2-T1-repo-structure`
- `feature/US-4-T1-core-migrations`
- `fix/US-5-T3-scope-guard`
- `docs/US-1-T4-traceability`

### Merge rules

- Keep branches narrow to one task ID whenever practical.
- Rebase or merge from the protected base branch before review if drift becomes material.
- Do not batch unrelated stories into one branch.

## Pull request conventions

- PR title format: `US-2-T1: create repository structure and engineering conventions`
- Include the story/task ID in the title and summary.
- Describe scope, files changed, verification performed, and remaining blockers.
- Call out any assumptions made because source documents were missing or still unresolved.

## Commit conventions

Recommended commit format:

- `US-2-T1: add monorepo structure and engineering docs`
- `US-4-T1: add core tenant and lookup migrations`

Commit messages should:

- include the task ID
- describe the actual change
- stay narrow to the branch purpose

## Release convention

- Sprint work should be reviewable incrementally throughout the sprint rather than held for a large end-sprint merge.
- `main` should remain deployable after each accepted merge.
- Release tags can later follow sprint or milestone notation such as `sprint-01-close` or semantic versions once production packaging exists.

## Python standards

- Python version baseline: `3.12+`
- Use `ruff` as the default linter and formatter baseline.
- Prefer explicit typing on service boundaries and schemas.
- Keep SQLAlchemy models, Pydantic schemas, and routers grouped by bounded context.
- Avoid cross-context imports that imply hidden write ownership.

## Web standards

- Vue baseline: Vue 3 + TypeScript + Vite
- State and routing baseline: Pinia + Vue Router
- UI shell baseline: Vben Admin conventions
- Formatting/linting baseline: ESLint + Prettier are the intended defaults once the web workspace is bootstrapped

Web-specific rules:

- German is the default language and English is secondary.
- Do not hardcode user-visible strings once i18n resources exist.
- Preserve the fixed light/dark primary colors.
- Keep admin and portal permission semantics aligned even if route groups diverge.

## Mobile standards

- Flutter is the mobile baseline.
- `dart format` and `flutter analyze` are the intended default tooling once the mobile app is bootstrapped.
- Prokit is a navigation/composition reference, not a substitute for product requirements.

Mobile-specific rules:

- Display only released and properly scoped operational data.
- Keep architecture ready for offline-safe field workflows.
- Preserve DE default / EN secondary and the fixed theme colors.

## Cross-stack review standards

Every implementation task should be reviewable against:

- task/story traceability
- tenant isolation
- role-scoped visibility
- audit/evidence handling
- document-linking expectations where outputs exist
- DE default / EN secondary behavior for user-facing changes
- compatibility with bounded-context ownership rules

## Tooling files currently established

- root `.editorconfig`
- root `.gitignore`
- `backend/pyproject.toml`

Additional stack-specific lint/build configs should be added in the relevant workspace when that workspace is actually bootstrapped, not as empty placeholder noise.

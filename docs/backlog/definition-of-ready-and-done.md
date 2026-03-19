# Definition Of Ready And Done

## Task anchor

- Task: `US-1-T2`
- Story: `US-1` — Discovery, backlog confirmation, and acceptance traceability

## Purpose

This document defines the minimum readiness bar before a SicherPlan task is started and the minimum completion bar before a task is treated as done. It is written to be reused by later Codex tasks without reinterpretation.

## Definition of Ready

A task is ready when all items below are true:

### Scope clarity

- The task is anchored to one stable task ID in the form `US-N-TN`.
- The matching sprint file has been read and the story/task appears unchanged in the approved backlog.
- The task objective, hard constraints, expected outputs, and non-goals are explicit enough to avoid inventing business scope.

### Source clarity

- The relevant source-of-truth inputs are identified in the prompt or nearby docs.
- If an expected source file is missing, that gap is called out explicitly before implementation proceeds.
- The owning bounded context and any read-only upstream dependencies are named clearly.

### Dependency clarity

- Incoming task, story, and sprint prerequisites are known.
- Cross-context write restrictions are understood before any design or code change starts.
- Required platform primitives are already available or the prompt explicitly accepts a narrow prerequisite addition.

### Acceptance clarity

- The user-visible or system-visible outcome is concrete enough to verify.
- For docs/discovery tasks, the required document outputs and review audience are clear.
- For implementation tasks, the expected migrations, models, services, APIs, UI/mobile surfaces, and tests are clear enough to scope the change set.

### Testability and reviewability

- There is a defined way to verify completion: docs review, lint/build/test command, manual UI check, API exercise, migration check, or another concrete mechanism.
- The task can be reviewed against tenant isolation, role scoping, audit/evidence handling, and localization expectations where relevant.
- The change can be kept narrow enough that unrelated repo noise does not need to be edited.

### Operational guardrails

- No step in the planned implementation would bypass `finance.actual_record`, cross-context ownership boundaries, document linking requirements, or outbox/integration separation where those apply.
- Any external-facing surface is understood to require tenant scope plus local visibility scope.
- Any user-facing surface is understood to require German default and English secondary behavior.

## Definition of Done

A task is done only when all relevant items below are true.

### Backlog and traceability

- Stable story and task IDs remain unchanged.
- The result is still traceable to the approved sprint/story structure.
- Any assumptions needed to complete the task are documented in the output or final notes.

### Build, lint, and tests

- Relevant build, lint, or validation commands have been run when applicable.
- Tests exist for implemented behavior where code changed and the task type reasonably allows tests.
- If tests or validation could not be run, that gap is stated explicitly.

### Data ownership and migration coherence

- Bounded-context ownership is preserved; no hidden cross-context master-data writes were introduced.
- Migrations, schemas, and implementation sequence remain coherent with earlier waves and with forward-only change discipline.
- Multi-tenant tables, foreign keys, and scoping assumptions do not weaken tenant isolation.

### Tenant and role scope

- Tenant scoping is enforced for relevant data access paths.
- Role-scoped visibility is enforced for internal users, customers, subcontractors, and employees where relevant.
- Portal-facing changes apply both tenant scope and local visibility scope.

### Audit and evidence handling

- Sensitive flows preserve auditability.
- Append-only or correction-safe evidence rules are respected for audit events, login events, patrol events, watchbook evidence, and raw time events where relevant.
- Finance derivation does not bypass `finance.actual_record`.

### Documents, outputs, and integrations

- Generated files or durable outputs are linked through the docs model where relevant.
- External side effects are not embedded directly in domain transactions.
- Integration behavior stays behind jobs, adapters, or outbox-style boundaries where relevant.

### UX, localization, and theme rules

- Any user-facing work ships with German as default and English as secondary.
- UI work preserves the fixed primary colors: light `rgb(40,170,170)`, dark `rgb(35,200,205)`.
- Web work follows Vben Admin patterns where applicable.
- Mobile work follows Prokit-inspired Flutter patterns where applicable.

### Security, privacy, and least privilege

- Customer-facing views hide personal names by default unless explicitly released.
- Finance-sensitive and HR-private data remain least-privilege by default.
- No broad tenant query is exposed to customer or subcontractor portals.

### Documentation and reviewer usability

- New docs are concise, implementation-oriented, and internally consistent.
- Code or config changes include the minimum supporting documentation needed for later prompts and reviewers.
- The final task summary identifies files changed, key assumptions, verification performed, and follow-up blockers if any remain.

## Sprint 1 story-specific Done interpretation

### `US-1`

- Discovery, backlog, dependency, and acceptance artifacts are updated and consistent with the sprint plan.
- Open questions are visible enough to guide `US-1-T3` and `US-1-T4`.

### `US-2`

- Repo, environment, pipeline, and observability changes are reproducible and do not weaken quality gates.
- Migration, lint, build, test, and health-check expectations are encoded clearly enough for later stories.

### `US-3`

- Web/mobile shells demonstrate DE default, EN secondary, and light/dark theme parity.
- Vben Admin and Prokit-inspired structure are visible enough that later stories can build on them rather than replace them.

## Review checklist reuse

Reviewers and later prompts should reuse these questions:

- Is the owning bounded context obvious and intact?
- Are tenant and role scopes preserved?
- Does the task respect append-only or correction-safe evidence rules where relevant?
- Does any finance behavior correctly route through `finance.actual_record`?
- Are DE/EN and theme requirements satisfied for user-facing work?
- Are build/lint/tests or equivalent verification steps present and reported honestly?

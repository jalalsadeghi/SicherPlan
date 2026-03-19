# Sprint Demo Checklist

## Task anchor

- Task: `US-1-T4`
- Scope: Sprint 1 demo baseline, reusable as a template for later sprint reviews

## How to use this checklist

- Walk the list in order during the sprint review.
- Mark each item as `done`, `partial`, or `blocked`.
- Capture evidence references next to each line: doc path, pipeline run, screenshot, command result, or reviewer note.

## Sprint 1 review objective

Confirm that Sprint 1 established the delivery guardrails required before business-domain implementation expands: backlog traceability, CI/CD/runtime expectations, and DE/EN plus theme-ready Vben/Prokit shells.

## Review prerequisites

- [ ] Reviewer has [sprint-01-inception-and-setup.md](/home/jey/Projects/SicherPlan/docs/sprint/sprint-01-inception-and-setup.md) open.
- [ ] Reviewer has [traceability-matrix.md](/home/jey/Projects/SicherPlan/docs/qa/traceability-matrix.md) open.
- [ ] Reviewer has the `US-1`, `US-2`, and `US-3` task outputs or PR notes available.

## Story `US-1` review points

- [ ] Discovery outputs exist for scope baseline, workflow/context mapping, backlog dependencies, DoR/DoD, migration/NFR assumptions, and QA traceability.
- [ ] The three anchor workflows are visible across multiple later stories, not reduced to one backlog row each.
- [ ] Stable IDs `US-1` through `US-36` remain unchanged in the backlog artifacts.
- [ ] Open questions for Sprint 2 are explicit: proposal/spec gap, object-storage direction, IAM/identity direction, optional RLS status, and migration depth expectations.

## Story `US-2` review points

- [ ] Repository/runtime setup is documented clearly enough for backend, web, and mobile work to proceed without inventing structure.
- [ ] CI/CD expectations include lint, test, migration/build, and health-check automation.
- [ ] Observability/health-check expectations are visible and do not replace business audit requirements.
- [ ] Config and environment guidance leaves room for tenant-aware settings, object storage, auth/session settings, messaging stubs, and later provider adapters.

## Story `US-3` review points

- [ ] Web shell follows Vben Admin direction rather than a generic blank admin shell.
- [ ] Mobile shell follows Prokit-inspired structure rather than an unrelated app scaffold.
- [ ] German is the default language and English is the secondary language in Sprint 1 shell behavior or documented localization baseline.
- [ ] Theme behavior uses the fixed primary colors: light `rgb(40,170,170)` and dark `rgb(35,200,205)`.
- [ ] Shell/navigation structure is reusable for later role-scoped module work and does not conflict with portal/privacy requirements.

## Cross-cutting acceptance checks

- [ ] Tenant isolation, role scope, append-only evidence rules, docs-service linking, and `finance.actual_record` are called out as non-negotiables in the Sprint 1 baseline artifacts.
- [ ] No Sprint 1 artifact weakens the customer-name privacy default or HR-private least-privilege rule.
- [ ] No Sprint 1 artifact assumes direct provider calls inside domain transactions.
- [ ] Sprint 2 dependencies are concrete enough that `US-4`, `US-5`, and `US-6` can start without reinterpretation.

## Suggested Sprint 1 demo flow

1. Review [us-1-t1-scope-review.md](/home/jey/Projects/SicherPlan/docs/discovery/us-1-t1-scope-review.md) and [us-1-t1-workflow-context-map.md](/home/jey/Projects/SicherPlan/docs/discovery/us-1-t1-workflow-context-map.md) for workflow/bounded-context alignment.
2. Review [backlog-epics-and-dependencies.md](/home/jey/Projects/SicherPlan/docs/backlog/backlog-epics-and-dependencies.md) and [definition-of-ready-and-done.md](/home/jey/Projects/SicherPlan/docs/backlog/definition-of-ready-and-done.md) for execution governance.
3. Review [us-1-t3-migration-integrations-nfr.md](/home/jey/Projects/SicherPlan/docs/discovery/us-1-t3-migration-integrations-nfr.md) and [us-1-t3-risk-and-decision-log.md](/home/jey/Projects/SicherPlan/docs/discovery/us-1-t3-risk-and-decision-log.md) for Sprint 2 blockers and engineering defaults.
4. Review Sprint 1 engineering/web/mobile artifacts for repo baseline, CI/CD expectations, shell structure, DE/EN behavior, and theme evidence.
5. Close by checking the workflow coverage rows in [traceability-matrix.md](/home/jey/Projects/SicherPlan/docs/qa/traceability-matrix.md).

## Reusable checklist template for later sprints

- [ ] Sprint goal and exit criteria are restated before demo starts.
- [ ] Each story is demonstrated against its acceptance emphasis, not only against implementation detail.
- [ ] Evidence includes the right artifact type for the story: docs, UI demo, API behavior, migration proof, test run, report/PDF output, or audit evidence.
- [ ] Workflow impact on `COI`, `APE`, and/or `SC` is called out where relevant.
- [ ] Tenant scope, role scope, privacy, and append-only evidence concerns are explicitly reviewed for any affected story.
- [ ] DE default / EN secondary and theme consistency are reviewed for any user-facing change.
- [ ] Open blockers and client-owned decisions are captured with a named follow-up task or story reference.

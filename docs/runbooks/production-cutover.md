# Production Cutover

## Scope

This is the single authoritative cutover path for Sprint 12 release execution.

## Automation boundary

- Automated where repository assets already exist:
  - migration/config seed verification
  - rollout-readiness asset checks
  - migration validation script entry points
- Manual where production access or secrets are required:
  - freeze approval
  - production credential handling
  - actual deployment execution
  - live monitoring signoff

## Freeze and rollback gates

### Freeze

- configuration and migration package version frozen
- no untracked hotfixes
- release evidence templates ready

### Rollback

Rollback must be prepared before release proceeds if any of the following fail:

- tenant or portal scope leak
- document/version/link integrity check fails
- planning to finance bridge smoke check fails
- release asset checks or migration validation cannot be replayed

## Ordered path

1. Confirm [us-35-go-live-checklist.md](/home/jey/Projects/SicherPlan/docs/runbooks/us-35-go-live-checklist.md).
2. Confirm backup/restore evidence from [backup-restore-and-security-drills.md](/home/jey/Projects/SicherPlan/docs/qa/backup-restore-and-security-drills.md).
3. Run `backend/scripts/run_production_cutover_dry_run.py`.
4. Execute migration/config steps in the approved environment.
   For tenants created before HR baseline onboarding existed, include an explicit `seed_go_live_configuration.py --tenant-id <uuid>` backfill step, or use the guarded all-tenant variant only with approved confirmation.
5. Run secured smoke checks and monitoring gates.
6. Record outputs in [production-cutover-evidence.md](/home/jey/Projects/SicherPlan/docs/runbooks/production-cutover-evidence.md).

## Smoke expectations

- authentication works
- tenant scoping holds
- docs download remains permission-safe
- customer and subcontractor portals show only released scoped data
- planning/finance critical reads remain healthy
- reporting/export entry points remain available

## Honesty rule

If this repository does not execute a real production deploy, record the dry-run result only. Do not mark the release executed.

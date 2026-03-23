# US-35 Cutover Rehearsal

## Roles

- release lead
- migration lead
- platform admin
- tenant admin / business owner
- finance/controller representative
- support / incident recorder

## Rehearsal checkpoints

1. Freeze communication sent
2. Backup/restore prerequisites confirmed
3. Migration/config seed rehearsal completed
4. Portal/mobile smoke checks completed
5. Finance/reporting smoke checks completed
6. Rollback decision gate reviewed
7. Evidence and issues captured

## Rollback gate

Rollback remains mandatory if any of the following fail:

- tenant or portal scope leakage
- finance actual/timesheet/invoice chain not reproducible
- generated docs inaccessible for authorized actors
- migration package cannot be replayed cleanly

## Issue capture

Use [us-35-defect-and-evidence-templates.md](/home/jey/Projects/SicherPlan/docs/uat/us-35-defect-and-evidence-templates.md) and copy blocker outcomes into the release risk register.

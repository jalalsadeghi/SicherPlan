# US-34 Trial Migration Validation

## Scope

This validation cycle proves that migrated master data, historical docs, and seeded configuration are sufficient for representative:

- customer portal flows
- subcontractor portal flows
- planning release and staffing validation
- finance actual, payroll, timesheet, invoice, and subcontractor-control flows
- reporting/export reproducibility

## Rules

- Use normal service, portal, or read-model paths only.
- Do not patch database rows manually without recording the defect and rerun.
- Keep `finance.actual_record` as the finance bridge.
- Keep document access on central docs links and existing scope rules.

## Replay order

1. Run `backend/scripts/seed_go_live_configuration.py`.
2. Validate migration templates and document manifests.
3. Run the historical-document pilot.
4. Run the scenario suite from `backend/scripts/run_trial_migration_validation.py`.
5. Store command outputs and rerun notes in the evidence index and remediation log.

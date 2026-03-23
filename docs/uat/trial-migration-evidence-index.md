# Trial Migration Evidence Index

## Run template

- Environment: staging/UAT-like
- Tenant: `<tenant_uuid>`
- Migration package version: `v1`
- Config seed command: `backend/scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>`
- Validation suite command: `backend/scripts/run_trial_migration_validation.py`

## Evidence checklist

- [ ] Template preflight output captured
- [ ] Historical document pilot output captured
- [ ] Customer portal validation output captured
- [ ] Subcontractor portal validation output captured
- [ ] Planning release/staffing output captured
- [ ] Finance actual/payroll/billing output captured
- [ ] Reporting/export output captured

## Attach command outputs here

- `portal_customer_visibility`:
- `portal_subcontractor_visibility`:
- `planning_release_and_assignment_validation`:
- `finance_actual_to_invoice_bridge`:
- `reporting_export_reproducibility`:

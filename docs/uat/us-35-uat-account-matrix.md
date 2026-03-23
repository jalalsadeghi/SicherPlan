# US-35 UAT Account Matrix

## Sanitized UAT personas

| Role cluster | Example account | Main surfaces | Scope reminder |
| --- | --- | --- | --- |
| Platform admin | `uat.platform.admin@example.test` | Core admin, reporting, seed/config review | Cross-tenant admin only for platform governance; do not use for business UAT evidence unless required |
| Tenant admin | `uat.tenant.admin@example.test` | Web admin across CRM/HR/planning/finance | Tenant-only scope |
| Dispatcher | `uat.dispatcher@example.test` | Planning orders, shifts, staffing, releases | Tenant-only, no HR-private data |
| Accounting | `uat.accounting@example.test` | Actuals, payroll, timesheets, invoices, partner checks | Finance scope only |
| Controller/QM | `uat.controller.qm@example.test` | Reporting, compliance/QM, exports | Reporting and QM scope only |
| Customer portal user | `uat.customer.portal@example.test` | Customer portal schedules, watchbooks, timesheets, invoices | Customer-local scope only, names released only if explicitly allowed |
| Subcontractor portal admin | `uat.subcontractor.admin@example.test` | Subcontractor portal workers, schedules, invoice checks, watchbooks | Subcontractor-local scope only |
| Employee mobile user | `uat.employee.mobile@example.test` | Mobile schedule, docs, watchbook, patrol, time capture, profile | Own employee scope only |

## Environment preflight

- UAT tenant seeded with `numbering.rules` and `print_templates.catalog`
- migrated customers, employees, subcontractors, orders, and documents loaded
- portal role assignments active and scoped
- mobile employee linkage active
- generated docs and pilot historical docs available
- finance actual/timesheet/invoice basis prepared for the scenario period

## Reset path

1. Re-seed configuration with [seed_go_live_configuration.py](/home/jey/Projects/SicherPlan/backend/scripts/seed_go_live_configuration.py).
2. Re-run [run_trial_migration_validation.py](/home/jey/Projects/SicherPlan/backend/scripts/run_trial_migration_validation.py).
3. Reset evidence sheets and defect log entries for the new run date.

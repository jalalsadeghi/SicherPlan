# Reporting Reproducibility

`US-31` keeps reporting read-only and view-driven. No report in Sprint 11 owns business truth.

## Report families

- `employee-activity`
  Source chain: `hr.employee` -> `ops.assignment` / `ops.shift` -> `finance.actual_record` plus `hr.employee_event_application`, `hr.employee_absence`, `hr.employee_time_account_txn`, and `audit.login_event`
- `customer-revenue`
  Source chain: `finance.customer_invoice` -> `finance.timesheet` -> `finance.timesheet_line` -> `finance.actual_record` with `crm.customer`, `ops.customer_order`, and `ops.planning_record`
- `subcontractor-control`
  Source chain: `finance.subcontractor_invoice_check` -> `finance.subcontractor_invoice_check_line` with released `ops.shift` context and partner worker qualification evidence
- `planning-performance`
  Source chain: `ops.shift` -> `ops.shift_plan` -> `ops.planning_record` with `ops.demand_group`, `ops.assignment`, and approved `finance.actual_record`
- `payroll-basis`
  Source chain: `finance.actual_record` with `finance.employee_pay_profile`, `finance.payroll_export_item`, `finance.payroll_export_batch`, `finance.payroll_payslip_archive`, `hr.employee_allowance`, and `hr.employee_advance`
- `customer-profitability`
  Source chain: `finance.customer_invoice` -> `finance.customer_invoice_line` plus `rpt.payroll_basis_v` and `finance.actual_expense`

## Export behavior

- CSV exports come from the same reporting service used by the API list endpoints.
- The export path does not rerun a separate business calculation; it serializes the already-resolved row contracts.
- `X-Report-Generated-At` and `X-Report-Row-Count` headers provide the basic generation trace for QA and UAT checks.

## Staleness and refresh

- Sprint 11 uses normal PostgreSQL views, not materialized views.
- There is no hidden refresh job in this story wave.
- Later performance work in `US-33-*` may introduce materialization, but any refresh strategy must then be explicit in both tests and operator docs.

## QA expectations

- Reconciliation should compare report rows to the transactional chains above, not to hand-maintained spreadsheets or golden files.
- Tenant and role scope still apply during QA validation. Customer- or subcontractor-scoped users must never receive broader reporting datasets through export endpoints than through the API list view.

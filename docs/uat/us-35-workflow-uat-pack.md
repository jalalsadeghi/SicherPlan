# US-35 Workflow UAT Pack

## Purpose

This pack turns the three anchor business workflows into repeatable UAT runs with:

- stable preconditions
- named actor accounts
- step-by-step actions
- expected results
- negative cases
- evidence capture points

German is the default execution language. English labels are referenced where the UI exposes bilingual behavior.

## Shared preflight

1. Seed go-live configuration with [go-live-seed-baseline.md](/home/jey/Projects/SicherPlan/docs/configuration/go-live-seed-baseline.md).
2. Validate migrated data with [trial-migration-validation.md](/home/jey/Projects/SicherPlan/docs/uat/trial-migration-validation.md).
3. Confirm the scenario accounts from [us-35-uat-account-matrix.md](/home/jey/Projects/SicherPlan/docs/uat/us-35-uat-account-matrix.md).
4. Reset evidence and defect notes using [us-35-defect-and-evidence-templates.md](/home/jey/Projects/SicherPlan/docs/uat/us-35-defect-and-evidence-templates.md).

## Workflow 1 — Customer order to invoice (`COI`)

### Preconditions

- Migrated customer `K-1001` exists with portal-linked contact.
- Migrated order `A-4001` exists with planning record, released shifts, and generated operational outputs.
- Approved `finance.actual_record`, released timesheet, and issued invoice are available for the scenario period.
- Customer portal user can access only the customer scope.

### Main actors

- Tenant admin / dispatcher
- Field employee mobile user
- Accounting user
- Customer portal user

### Main path

1. Dispatcher opens the planning order and verifies released planning/shift data.
Expected: order number, customer scope, and released documents are visible.
Evidence: screenshot or API response of order + released planning record.

2. Employee mobile user opens the released shift, confirms it, and reviews released documents.
Expected: only released schedule/documents are visible in the employee context.
Evidence: mobile screenshot and response payload.

3. Field/finance flow derives attendance and current `finance.actual_record`.
Expected: no direct bypass of finance actuals; current actual is linked to planning/attendance provenance.
Evidence: finance actual detail view or API payload.

4. Accounting generates/releases the timesheet and issues the invoice.
Expected: totals, due date, and docs-backed outputs are reproducible.
Evidence: timesheet/invoice read views plus linked docs output.

5. Customer portal user downloads released timesheet and invoice.
Expected: only customer-scoped released finance docs are visible; no unrelated names or records leak.
Evidence: portal screenshot and successful authorized download.

### Negative path

- Customer portal user attempts access outside own customer scope.
Expected: scope denied or empty result, never cross-customer data.
Evidence: denial response or empty-state proof.

## Workflow 2 — Applicant to payroll-ready employee (`APE`)

### Preconditions

- Applicant exists with consent and workflow history.
- Employee master, qualification, availability, credential, and pay-profile records exist after conversion.
- Approved actuals and payroll basis exist for at least one payroll period.

### Main actors

- Recruiting/tenant admin
- HR/private-data user
- Employee self-service/mobile user
- Accounting/payroll user

### Main path

1. Admin verifies applicant history and conversion target employee.
Expected: source applicant evidence remains intact and employee master data is operationally usable.
Evidence: applicant detail + employee detail read paths.

2. HR user reviews private profile, qualifications, and credentials.
Expected: HR-private fields stay restricted; qualification docs remain linked through central docs.
Evidence: HR detail screenshot or API response.

3. Employee mobile user signs in, opens released schedules/documents, and reviews credentials.
Expected: only own released/authorized data is visible; DE default labels render correctly.
Evidence: mobile screenshots for schedule, documents, and profile credentials.

4. Payroll user resolves pay profile and export/payslip archive context.
Expected: payroll derives from approved actuals and finance bridge, not ad hoc edits.
Evidence: payroll admin view/API payload, export batch or payslip archive output.

### Negative path

- Non-HR role attempts access to HR-private employee data.
Expected: permission denied or redacted response.
Evidence: denial response.

## Workflow 3 — Subcontractor collaboration (`SC`)

### Preconditions

- Subcontractor company, workers, qualifications, and credentials exist.
- Released planning/assignment data exists for the subcontractor.
- Invoice-check data exists for a released finance period.

### Main actors

- Dispatcher / controller
- Subcontractor admin or portal user
- Customer user where released watchbook visibility applies

### Main path

1. Dispatcher verifies subcontractor release and worker readiness.
Expected: release/readiness are derived from current partner truth and validation rules.
Evidence: staffing or readiness view.

2. Subcontractor portal user opens released schedules and invoice checks.
Expected: only own subcontractor scope is visible, and internal notes remain hidden.
Evidence: portal screenshots or API payloads.

3. Subcontractor portal user maintains own worker/proof data through portal self-service.
Expected: writes are constrained to own subcontractor and central docs links.
Evidence: updated worker qualification/proof state.

4. Customer/subcontractor watchbook collaboration path is reviewed where released.
Expected: comments/entries remain scoped and auditable.
Evidence: released watchbook detail or entry output.

### Negative path

- Subcontractor portal user attempts to access another subcontractor or hidden invoice-check detail.
Expected: scope denied or no data leak.
Evidence: denial response.

## Defect routing

- `blocker`: flow cannot continue or acceptance criterion fails materially.
- `major`: workflow completes with incorrect business result, privacy/scope issue, or missing required output.
- `minor`: cosmetic, copy, or low-risk usability issue.

Log every failure in [us-35-defect-and-evidence-templates.md](/home/jey/Projects/SicherPlan/docs/uat/us-35-defect-and-evidence-templates.md).

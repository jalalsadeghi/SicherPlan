# US-1-T1 Workflow Context Map

## Task anchor

- Task: `US-1-T1`
- Purpose: map the three reference workflows onto the bounded-context model used by later prompts

## Workflow map

| Workflow | Primary sequence | Owning contexts | Key handoff rules |
| --- | --- | --- | --- |
| Customer order to report/invoice | Customer setup -> commercial setup -> order/planning -> release -> field evidence/actuals -> timesheet/invoice -> reporting | `customers` -> `planning` -> `field_execution` -> `finance` -> `reporting` | `customers` owns commercial truth; `planning` owns operational release; `finance` derives billable outputs via `finance.actual_record`; outputs link through `platform_services` docs |
| Applicant to payroll-ready employee | Applicant intake -> recruiter workflow -> employee creation -> compliance/availability -> released work participation -> approved actuals -> payroll basis | `recruiting` -> `employees` -> `planning`/`field_execution` consume -> `finance` | `recruiting` must preserve consent/history/files into employee transition; `employees` owns HR truth; payroll derives from approved finance actuals, not direct HR-only values |
| Subcontractor collaboration | Partner setup -> worker compliance -> released assignment visibility -> self-allocation -> actuals/invoice check -> reporting/portal visibility | `subcontractors` -> `planning` -> `field_execution`/`finance` -> `reporting` | `subcontractors` owns partner master/workers; `planning` may release but not edit partner master; partner portal stays limited to own company plus released scope |

## Cross-cutting contexts used by all workflows

| Context | Role in every workflow |
| --- | --- |
| `core` | tenant, branch, mandate, numbering, and lookup backbone |
| `iam` | user accounts, scoped roles, sessions, audit, portal access control |
| `platform_services` | document storage/linking, generated outputs, communications, notices, integration jobs, outbox |

## Workflow priority for early delivery

1. `core`, `iam`, and `platform_services` must stabilize first because all three workflows depend on tenant scoping, role scoping, documents, and audit.
2. Customer, recruiting/employee, and subcontractor master data come next because planning and finance should not invent upstream truth.
3. Planning/release flows precede field execution and finance derivation because downstream modules consume released scope.
4. Reporting comes last as a reproducible read layer over the transactional backbone.

## Non-negotiable checks for later prompts

- No workflow may bypass tenant scope or local role visibility.
- No workflow may bypass `finance.actual_record` once payroll/billing/settlement begin.
- No workflow may store generated files outside the docs model without a linked document record.
- No workflow may let planning mutate HR or partner master data.
- No workflow may weaken DE-default/EN-secondary behavior or Vben/Prokit/theme constraints on user-facing surfaces.

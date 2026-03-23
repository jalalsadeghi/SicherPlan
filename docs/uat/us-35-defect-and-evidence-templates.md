# US-35 Defect and Evidence Templates

## Evidence record

| Run date | Workflow | Step | Actor | Expected result | Actual result | Evidence link/path | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| _yyyy-mm-dd_ | _COI/APE/SC_ | _step id_ | _role_ | _expected_ | _actual_ | _screenshot/log/doc path_ | _pass/fail_ |

## Defect record

| ID | Severity | Workflow | Step | Summary | Reproducible on rerun | Suspected area | Follow-up owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-001` | blocker/major/minor | `COI` / `APE` / `SC` | `step id` | _short defect statement_ | yes/no | _module or surface_ | _role/persona_ | open |

## Severity rules

- `blocker`: prevents acceptance of the workflow or violates privacy, role scope, or finance correctness.
- `major`: workflow completes but a business-critical outcome or generated output is wrong.
- `minor`: non-blocking UX, terminology, or formatting issue.

# KPI and Alert Mapping

| KPI / alert area | Source of truth | Threshold / trigger | Owner | Runbook |
| --- | --- | --- | --- | --- |
| auth failures spike | `rpt.security_activity_v` | abnormal login failure concentration | IAM owner | [hypercare-runbook.md](/home/jey/Projects/SicherPlan/docs/support/hypercare-runbook.md) |
| reporting delivery backlog | reporting delivery history | queued deliveries not draining | reporting owner | [production-cutover.md](/home/jey/Projects/SicherPlan/docs/runbooks/production-cutover.md) |
| import/export backlog | integration jobs | failed or stuck jobs | platform services owner | [hypercare-runbook.md](/home/jey/Projects/SicherPlan/docs/support/hypercare-runbook.md) |
| finance bridge integrity | finance actual/timesheet/invoice smoke evidence | missing or inconsistent downstream finance outputs | finance owner | [production-smoke-checks.md](/home/jey/Projects/SicherPlan/docs/runbooks/production-smoke-checks.md) |
| portal visibility regression | portal smoke evidence | wrong scope or missing released data | customer/subcontractor owner | [production-smoke-checks.md](/home/jey/Projects/SicherPlan/docs/runbooks/production-smoke-checks.md) |

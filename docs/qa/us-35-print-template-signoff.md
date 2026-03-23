# US-35 Print Template Signoff

## Reviewed output families

- watchbook PDF
- patrol report PDF
- timesheet PDF
- invoice PDF
- employee badge/code output
- order badge/code output

## Signoff criteria

- translated labels are present or intentionally language-neutral
- date and number formatting follow the generated output’s intended locale
- required business identifiers are present
- branding and title naming remain consistent with seeded print-template metadata
- generated docs remain linked through the central docs service

## Evidence source

- use actual generated outputs from the UAT tenant, not config-only review
- attach or reference evidence in [trial-migration-evidence-index.md](/home/jey/Projects/SicherPlan/docs/uat/trial-migration-evidence-index.md)

## Current status

- configuration baseline exists through `print_templates.catalog`
- manual visual signoff remains required during formal UAT/cutover rehearsal

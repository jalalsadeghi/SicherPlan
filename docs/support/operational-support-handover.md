# Operational Support Handover

## Core ownership

- IAM / auth / role scope
- platform services / docs / integration / notices
- planning
- field execution
- finance
- reporting

## Common failure modes

- invalid or expired session / refresh failures
- document link exists but storage/object access fails
- portal user sees no released records due to release/scope mismatch
- finance outputs missing because upstream actual signoff chain is incomplete
- report/export queue delayed because integration delivery path is unavailable

## Expectations

- use the dashboard catalog as index, not as a duplicate monitoring system
- route incidents through the hypercare runbook and stabilization backlog
- keep sanitized tenant context in shared support artifacts

# Operational Dashboard Catalog

## Platform health

- Source: health endpoints and release smoke checks
- Audience: release lead, ops support

## Authentication and security activity

- Source: `rpt.security_activity_v`
- Audience: ops support, controller/QM, security stakeholders

## Import/export and delivery backlog

- Source: integration job/outbox reads and reporting delivery history
- Audience: ops support, release lead

## Document and generated-output integrity

- Source: docs service read paths and generated document flows validated during smoke checks
- Audience: ops support

## Business KPI references

- operational/commercial/payroll/compliance KPIs come from the implemented reporting views and dashboard contracts from `US-31` and `US-32`
- do not treat this catalog as a second data source; it points to the real read models

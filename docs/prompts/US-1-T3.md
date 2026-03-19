---
task_id: US-1-T3
story_id: US-1
story_title: "Discovery, backlog confirmation, and acceptance traceability"
sprint: Sprint 01
status: ready
owner: "PO / BA"
---

# Codex Prompt — US-1-T3

## Task title

**Confirm migration assumptions, external integrations, and non-functional requirements**

## Objective

Document the assumptions and cross-cutting constraints that will drive migration planning, infrastructure design, provider selection, and delivery sequencing before platform-core implementation expands.

## Source context

- Updated proposal: platform foundation and communication backbone; technical architecture and quality requirements; assumptions and dependencies; appendices for customer, subcontractor, employee, planning, validation, and reporting scope.
- Implementation specification: cross-cutting decisions; documents/communication/integration tables; migration waves; aggregate boundaries; implementation notes.
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-1-T1` should be reviewed first so assumptions are grounded in the actual platform scope.

## Scope of work

- Create a migration-assumptions register covering at least customers, employees, subcontractors, orders/planning data, documents/media, and lookup/reference data.
- Identify external-integration categories that the platform must remain ready for: email/SMS/push, payroll export/import, maps/geolocation, scanner/terminal devices, identity providers, object storage, and PDF/export handling.
- Document non-functional requirements that must guide implementation: tenant isolation, security, observability, backup/restore, offline behavior for field flows, auditability, performance, localization, and revision-safe output handling.
- Separate confirmed assumptions from unresolved questions and client-owned decisions.
- Where concrete providers are not yet chosen, define the abstraction boundary instead of hardcoding a vendor.

## Preferred file targets

- `docs/discovery/us-1-t3-migration-integrations-nfr.md`
- `docs/discovery/us-1-t3-risk-and-decision-log.md` (optional if you want a short companion file)

## Hard constraints

- Do not commit real credentials, provider secrets, or environment-specific values.
- Do not over-specify provider implementations that should stay behind integration abstractions.
- Respect the implementation spec rule that external side effects should flow through integration jobs/outbox patterns, not domain-table direct calls.
- Treat offline support as mandatory where patrol, watchbook, or time-capture workflows require it.

## Expected implementation outputs

- A migration/NFR/integration register that engineering can use as a reference during environment and CI setup.
- A clear list of client-owned decisions versus engineering-owned defaults.
- A short risk section that calls out what could block Sprint 2 platform-core work if left unresolved.

## Non-goals

- Do not implement infrastructure or CI in this task; those belong to `US-2-*`.
- Do not create delivery demos or traceability matrices here; that belongs to `US-1-T4`.
- Do not finalize migration templates for actual import files; that belongs to later migration stories in Sprint 12.

## Verification checklist

- Every assumption is labeled as confirmed, proposed default, or open decision.
- The register covers both technical and operational non-functional requirements.
- Integration items are defined as categories/capabilities, not guessed vendor lock-ins.
- The document is specific enough to support environment and CI task execution.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

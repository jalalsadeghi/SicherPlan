# US-1-T1 Scope Review

## Task anchor

- Task: `US-1-T1`
- Story: `US-1` — Discovery, backlog confirmation, and acceptance traceability
- Sprint: `Sprint 01`

## Source baseline used

This repository does not currently contain separate proposal or implementation-spec files. This review is therefore grounded in the available source set:

- `AGENTS.md`
- `docs/sprint/sprint-01-inception-and-setup.md`
- Sprint guides in `docs/sprint/` used as the best available proxy for proposal phase, workflow intent, bounded contexts, and migration sequencing
- Prompt files in `docs/prompts/` used only where they clarify task intent or workflow references

Assumption status: `needed before Sprint 2`

- When the standalone proposal/spec files are added, this review should be checked for wording drift.
- Until then, the sprint plan plus `AGENTS.md` are the operational source of truth available in-repo.

## Executive scope baseline

SicherPlan is scoped as a modular, multi-tenant security operations platform for internal staff, customers, subcontractors, and employees inside one tenant model. The implementation baseline is not a generic CRUD system; it is an evidence-bearing operational platform where planning, field execution, finance outputs, and reporting must remain traceable back to owned source aggregates.

The near-term delivery shape is clear from Sprint 01 through Sprint 03:

- Sprint 01 establishes delivery guardrails, backlog traceability, CI/CD expectations, and the Vben/Prokit/i18n/theme shell baseline.
- Sprint 02 establishes the platform backbone: tenant isolation, IAM/RBAC, audit, documents, communication, notices, and integration outbox.
- Sprint 03 onward begins business modules, starting with customers and customer portal scope, before recruiting/employees, subcontractors, planning, field flows, finance, and reporting expand in later sprints.

## Product scope that matters for early delivery decisions

### Actor and access model

- Internal users operate inside tenant-scoped roles such as platform admin, tenant admin, dispatcher/operator, accounting, and controller/QM.
- Customers, subcontractors, and employees are scoped actors inside a tenant, not separate tenants.
- Portal visibility is least-privilege by default and additionally constrained by local scope, not just tenant membership.

### Architectural intent

- Bounded contexts own their master truth and downstream modules consume references, read models, or service contracts.
- Documents, generated outputs, and uploads are centralized in platform services, while business meaning remains with the owning module.
- External side effects are async/integration driven through jobs or outbox flows, not inline transactional writes.
- Reporting starts from SQL views/materialized views over transactional data, not a second early write-side schema.

### Workflow intent

- Customer workflow moves from customer/commercial setup into orders, planning, released work, actuals, timesheets/invoices, portal release, and reporting.
- Applicant workflow moves from intake and consent capture into recruiting decisions, employee creation, HR compliance/availability, actuals, payroll basis, and reporting.
- Subcontractor workflow moves from partner master/commercial setup into worker compliance, released assignments, partner self-allocation, actual-based settlement control, portal visibility, and reporting.

## Bounded-context baseline

The repository-wide context map is stable and should shape package ownership and future prompts:

- `core`: tenants, branches, mandates, numbering rules, tenant settings, lookup values
- `iam`: user accounts, roles, scoped permissions, sessions, login events, business audit events
- `platform_services`: documents, document versions/links, communications, notices, recipients, integration jobs, outbox
- `customers`: customer master, contacts, addresses, portal linkage, billing profiles, rate cards, surcharge rules, invoice parties, customer portal read models
- `recruiting`: applicant intake, consent, recruiter workflow, applicant-to-employee transition
- `employees`: employee master, HR-private split, qualifications, availability, absences, balances, allowances, credentials, self-service contracts
- `subcontractors`: subcontractor company master, partner finance profile, partner workers, compliance completeness, partner portal self-service
- `planning`: operational master data, locations/routes/checkpoints, customer orders, planning records, shift plans, assignments, release structures
- `field_execution`: employee app, notices/watchbook, patrol control, time capture, raw field evidence
- `finance`: attendance normalization, `finance.actual_record`, approvals, payroll basis, customer billing, subcontractor invoice checks
- `reporting`: SQL read models, dashboards, exports, compliance/QM/security reporting

## Early migration-wave interpretation from the sprint plan

The repo does not expose a standalone migration-wave table, but the sprint sequence gives a usable implementation order:

- Wave A/B equivalent: `core`, `iam`, `platform_services`
- Wave C equivalent: `customers`, `subcontractors`
- Wave D equivalent: `recruiting`, `employees`
- Wave E equivalent: `planning`
- Wave F equivalent: `field_execution`
- Wave G equivalent: `finance`
- Wave H equivalent: `reporting` and hardening

This ordering matches the cross-module constraints in `AGENTS.md`: downstream modules may read upstream truth, but should not own or mutate it.

## Three reference workflows

### 1. Customer order to report/invoice

This workflow starts with customer master/commercial setup, then moves into operational planning and released work, then into field evidence/actuals, then finance outputs and customer-facing reporting.

Implementation reading:

- Customer commercial truth is owned in `customers`.
- Operational structures and release states are owned in `planning`.
- Raw execution evidence is owned in `field_execution`.
- Derived actuals and billing artifacts are owned in `finance`.
- Dashboards/exports are owned in `reporting`.

Critical traceability rule:

- Customer invoices and timesheets must derive from approved finance actuals and released customer commercial rules, with generated outputs linked through the docs service.

### 2. Applicant to payroll-ready employee

This workflow starts with applicant intake, consent, and recruiter status handling, then creates an employee aggregate with HR-private separation, then extends into qualifications/availability and later into actuals/payroll basis.

Implementation reading:

- Applicant truth is owned in `recruiting`.
- Employee and HR-private truth are owned in `employees`.
- Mobile/app linkage and field participation consume employee data but do not own it.
- Payroll must consume released and approved downstream actuals through the finance bridge, not direct HR mutation.

Critical traceability rule:

- Applicant status history, consent evidence, and uploaded files must survive the applicant-to-employee transition.

### 3. Subcontractor collaboration

This workflow starts with subcontractor company/commercial setup, adds partner worker compliance, then exposes only released operational scope in the partner portal, then supports self-allocation and invoice-check visibility.

Implementation reading:

- Partner master and worker truth are owned in `subcontractors`.
- Planning may release work to partners but may not edit partner master records.
- Field and finance flows consume released partner assignments and evidence.
- Portal visibility must remain limited to the subcontractor's own company and released scope.

Critical traceability rule:

- Subcontractor settlement and invoice checks must derive from approved actuals and partner commercial settings, with no bypass around finance-owned control data.

## Platform non-negotiables that must shape every later task

- Strict tenant isolation is mandatory across tables, APIs, portals, and generated outputs.
- Role-scoped visibility is mandatory for internal staff, customers, subcontractors, and employees.
- Audit, login, patrol, and raw time evidence must be append-only or correction-safe.
- `finance.actual_record` is the mandatory bridge between planning/field evidence and payroll, timesheets, invoices, and partner settlement.
- Documents and generated outputs must be represented in the docs service.
- German is the default language and English is secondary for all user-facing behavior.
- Web foundations must follow Vben Admin patterns.
- Mobile foundations must follow Prokit-inspired Flutter patterns.
- Theme primary colors are fixed: light `rgb(40,170,170)`, dark `rgb(35,200,205)`.
- Customer and subcontractor portals require tenant scope plus local visibility scope; customer-facing views hide personal names by default unless explicitly released.

## Sprint 1 and Sprint 2 decision implications

### Sprint 1 implications

- Discovery outputs should lock vocabulary, context boundaries, and workflow references before CI/CD or shell work expands.
- Web/mobile shell tasks should be treated as platform primitives, not disposable prototypes, because DE/EN and theme rules are contract-level.
- Task prompts after `US-1-T1` should assume the bounded-context map above unless a later in-repo proposal/spec file contradicts it.

### Sprint 2 implications

- Sprint 2 must land `core`, `iam`, and `platform_services` before business modules create persistent truth.
- Document and integration abstractions cannot be deferred if later modules need file evidence, generated PDFs, messages, or async provider calls.
- Audit and role-scope enforcement need to exist before external portal or HR-sensitive modules appear.

## Open questions, assumptions, and decision points

### Blocking now

- No standalone proposal or implementation-spec file exists in the repository. Later discovery tasks should either add them or explicitly confirm that sprint docs remain the approved substitute.

### Needed before Sprint 2

- Confirm whether the implied migration-wave mapping in this document is the authoritative sequence or only a sprint-level proxy.
- Confirm the canonical role catalog to be used in IAM and web navigation so shell work and RBAC do not drift.
- Confirm whether PostgreSQL row-level security is intended as an early baseline or an optional hardening-layer control, since Sprint 11 mentions it as optional.
- Confirm the primary document/object-storage abstraction shape before `platform_services` implementation starts.

### Can defer

- Exact external providers for email/SMS/push, payroll export/import, maps/geolocation, and storage can remain abstracted until `US-1-T3` and later platform tasks.
- Detailed report catalogue, KPI formulas, and dashboard layouts can wait until reporting stories as long as reproducibility from transactional data remains fixed now.

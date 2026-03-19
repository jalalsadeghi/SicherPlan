# US-1-T3 Migration, Integrations, And NFR Register

## Task anchor

- Task: `US-1-T3`
- Story: `US-1` — Discovery, backlog confirmation, and acceptance traceability
- Baseline inputs: `AGENTS.md`, `docs/discovery/us-1-t1-scope-review.md`, `docs/backlog/backlog-epics-and-dependencies.md`, `docs/sprint/*.md`

## Purpose

This register captures the assumptions and cross-cutting constraints that should guide migration planning, platform-core design, environment setup, CI/CD design, and future provider selection. It is intentionally capability-oriented and does not lock the product to specific vendors.

## Status labels used

- `confirmed`: directly supported by the current in-repo baseline
- `proposed default`: a pragmatic engineering default that fits the current baseline but still needs confirmation
- `open decision`: unresolved and likely client-owned or architecture-owned

## Source constraint note

The repository still does not contain standalone proposal or implementation-spec source files. This register therefore uses the sprint plan, prompt set, and `AGENTS.md` as the available source baseline and should be reconciled if the missing source documents are later added.

## Migration assumptions register

### Customers

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Customer master | Customer records, contacts, addresses, and portal linkages should be imported before planning/order go-live activities. | `confirmed` | Sprint 03 establishes customer master before planning and finance consume it. |
| Commercial settings | Billing profiles, invoice parties, rate cards, surcharge rules, and dispatch/e-invoice settings are part of customer-owned commercial truth and must migrate without finance-side duplication. | `confirmed` | Later billing depends on released customer commercial rules. |
| Privacy defaults | Customer-facing views should default to hidden personal names unless explicitly released. | `confirmed` | Portal privacy rule is fixed in `AGENTS.md`. |
| Import sequencing | Initial migration should treat customer master and commercial settings as separate import stages so data can be validated before finance outputs depend on them. | `proposed default` | Reduces rework and allows cleaner validation of customer-owned truth. |

### Employees

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Employee split | Operational employee data and private HR data must remain separated in migration inputs and target tables. | `confirmed` | Sprint 04 and `AGENTS.md` require a strict HR private-data split. |
| Applicant lineage | Applicant status history, consent evidence, and uploaded files must be preserved or traceably linked when applicant records convert into employees. | `confirmed` | The applicant-to-employee workflow depends on this continuity. |
| Workforce readiness | Qualifications, availability, absences, balances, allowances, and credentials should migrate after employee core data but before staffing, mobile, and payroll work starts. | `confirmed` | Downstream stories depend on HR readiness data. |
| Historical depth | Historical HR-private notes and payroll-adjacent balances may need scoped cutover rules rather than unlimited historical backfill. | `open decision` | Affects data-cleanup effort, privacy review, and migration scope. |

### Subcontractors

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Company master | Subcontractor company master, contacts, scope assignments, and partner commercial settings should migrate before released assignments are exposed in the portal. | `confirmed` | Sprint 05 establishes partner truth before allocation and settlement. |
| Worker readiness | Partner workers, qualifications, proofs, and credentials must be queryable before release/self-allocation workflows begin. | `confirmed` | Staffing and settlement depend on compliance completeness. |
| Portal scope | Migrated subcontractor portal users must remain limited to own-company and released operational scope. | `confirmed` | External visibility boundaries are fixed. |
| Historical partner data | Whether historical inactive partner workers are migrated in full or summarized for reference only is not yet decided. | `open decision` | Impacts migration volume and privacy/compliance review. |

### Orders and planning data

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Operational sequence | Orders, planning records, routes, checkpoints, shift structures, assignments, and release states must migrate only after customer and core platform truth are stable. | `confirmed` | Planning depends on core/customer contexts and is downstream in the sprint sequence. |
| Commercial linkage | Planning imports must preserve links to customer-owned commercial rules instead of denormalizing copied billing truth into planning tables. | `confirmed` | Planning must not take ownership of finance/commercial source truth. |
| Historical planning | Historic orders/shifts may need a distinction between fully actionable records and archived reference-only records. | `proposed default` | Supports realistic reporting and trial migration without reopening historical operations. |
| Release semantics | Only released operational data should feed downstream mobile, portal, time-capture, and finance derivation paths. | `confirmed` | Release state is a stable downstream visibility gate. |

### Documents and media

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Centralization | Uploaded files and generated outputs should be represented through the docs service with business links back to owning entities. | `confirmed` | `AGENTS.md` makes document centralization mandatory. |
| Versioning | Migration must preserve enough metadata to distinguish document identity, version lineage, owning entity, and retention-safe timestamps. | `proposed default` | Needed for later document versioning and audit-safe output handling. |
| Generated outputs | Historical PDFs/exports such as timesheets, invoices, watchbooks, patrol reports, and badge files should be linkable as document rows where retained. | `confirmed` | Explicitly required in `AGENTS.md`. |
| Binary retention | The retention scope for historical binaries versus metadata-only placeholders is not yet decided. | `open decision` | Affects storage size, compliance review, and migration timeline. |

### Lookup and reference data

| Area | Assumption | Status | Why it matters |
| --- | --- | --- | --- |
| Seed before business import | Tenant, branch, mandate, numbering rules, document types, and lookup domains should exist before business-data migration begins. | `confirmed` | Sprint 02 and Sprint 12 sequencing rely on seeded shared reference data. |
| Tenant extensibility | Lookup/reference migration must allow both system-wide seed values and tenant-specific extensions. | `confirmed` | Core lookup design is tenant-extensible by requirement. |
| Stable codes | Imported reference data should favor stable business codes over display labels to preserve DE/EN localization flexibility. | `proposed default` | Helps later localization and avoids data cleanup from label drift. |

## Integration capability register

Concrete providers are intentionally deferred. The platform should stay ready for the following integration categories.

### Email, SMS, and push

| Capability | Boundary | Status |
| --- | --- | --- |
| Outbound notifications | Template/message/recipient/delivery-attempt records owned by `platform_services`; actual delivery performed asynchronously by adapter workers. | `confirmed` |
| Channel abstraction | Email, SMS, and push should share a common job/outbox model with channel-specific adapters. | `proposed default` |
| Provider choice | Specific vendors remain unset. | `open decision` |

### Payroll export and import

| Capability | Boundary | Status |
| --- | --- | --- |
| Export basis | Payroll outputs must derive from approved finance actuals and effective pay settings. | `confirmed` |
| Adapter isolation | Provider-specific file/API logic should sit behind export/import adapters and not leak into finance domain tables. | `confirmed` |
| Provider choice | Payroll vendor/file format selection is unresolved. | `open decision` |

### Maps and geolocation

| Capability | Boundary | Status |
| --- | --- | --- |
| Map support | Planning and mobile should consume geo coordinates, routes, checkpoints, and site/location data through service boundaries, not hardwired vendor SDK assumptions in domain logic. | `confirmed` |
| Geocoding/routing abstraction | Geocoding, route preview, and map rendering concerns should remain replaceable behind integration/service contracts. | `proposed default` |
| Provider choice | Mapping provider is unresolved. | `open decision` |

### Scanner and terminal devices

| Capability | Boundary | Status |
| --- | --- | --- |
| Time-capture devices | Device, terminal, and credential-capture policy logic belongs in the application domain; hardware protocols and device adapters remain replaceable. | `confirmed` |
| Scan modes | QR, barcode, RFID, NFC, manual, and terminal/browser capture should be treated as capability variants rather than provider lock-ins. | `confirmed` |
| Device fleet | Exact terminal/scanner hardware and management model is unresolved. | `open decision` |

### Identity providers

| Capability | Boundary | Status |
| --- | --- | --- |
| Local auth baseline | The IAM model should support local login/session handling and leave room for MFA/SSO-ready hooks. | `confirmed` |
| External identity abstraction | OIDC/SAML or comparable external identity integration should plug into external identity models and auth adapters rather than rewiring user ownership. | `proposed default` |
| Provider choice | Whether external IdP is needed at initial go-live is unresolved. | `open decision` |

### Object storage

| Capability | Boundary | Status |
| --- | --- | --- |
| Storage abstraction | The docs service should own document metadata and versions while binary persistence stays behind a storage adapter. | `confirmed` |
| Environment parity | Local/dev should support an object-storage-compatible stub or emulator rather than filesystem-specific coupling. | `proposed default` |
| Provider choice | Actual object storage vendor/service is unresolved. | `open decision` |

### PDF and export handling

| Capability | Boundary | Status |
| --- | --- | --- |
| Generated outputs | PDF/export generation should produce document rows linked to the owning business entity. | `confirmed` |
| Render pipeline | Document rendering should be isolated behind application services/jobs so templates can evolve without domain schema changes. | `proposed default` |
| Engine choice | PDF/render/export engine selection is unresolved. | `open decision` |

## Non-functional requirements register

### Technical and operational requirements

| NFR area | Requirement | Status | Delivery implication |
| --- | --- | --- | --- |
| Tenant isolation | Tenant scoping is mandatory in schema, APIs, portals, and generated outputs; composite keys/FKs should be used where they materially reduce leakage risk. | `confirmed` | Shapes schema, repository filters, authz middleware, and portal query rules from Sprint 02 onward. |
| Role-scoped visibility | Internal staff, customers, subcontractors, and employees require least-privilege views tied to role and local scope. | `confirmed` | Required before customer/subcontractor portals and HR-private views expand. |
| Security auditability | Login events and sensitive business actions need immutable or correction-safe audit trails. | `confirmed` | Sprint 02 IAM/audit work cannot be deferred. |
| Evidence durability | Audit, patrol, watchbook-related evidence, and raw time events must be append-only or correction-safe. | `confirmed` | Prevents destructive overwrite patterns in field and finance stories. |
| Offline behavior | Patrol, watchbook-adjacent field work, and time-capture-related mobile flows require offline-safe storage, replay-safe sync, and deliberate sync tokens where applicable. | `confirmed` | Mobile/backend contracts must avoid server-only assumptions. |
| Observability | The platform needs health checks, logging, and tracing that support CI smoke tests and operations without replacing business audit tables. | `confirmed` | Guides `US-2-T4` and production readiness. |
| Backup and restore | Backup/restore verification is required before go-live and should be rehearsed during hardening. | `confirmed` | Sprint 11/12 need explicit drills and evidence. |
| Performance | Planning boards, heavy reporting views, and field/time-capture ingest paths need indexed, predictable query patterns. | `confirmed` | Requires early schema/index thinking in planning and reporting stories. |
| Localization | German is the default language and English is secondary across UI, notifications, documents, labels, and validation messaging. | `confirmed` | Affects all user-facing tasks; cannot be bolted on later. |
| Revision-safe outputs | Watchbook PDFs, patrol outputs, timesheets, invoices, and similar generated files should remain reproducible and document-linked. | `confirmed` | Output generation belongs behind docs-aware services/jobs. |
| Reporting reproducibility | Reporting must derive from transactional data via SQL views/materialized views, not a parallel early write schema. | `confirmed` | Constrains reporting architecture and migration design. |
| Privacy and least privilege | HR-private and finance-sensitive data must stay least-privilege by default; customer views hide names unless explicitly released. | `confirmed` | Shapes portal design, exports, and review criteria. |
| Optional RLS | PostgreSQL RLS is mentioned as optional hardening, not yet baseline architecture. | `proposed default` | Do not block Sprint 02 implementation on RLS-specific design decisions. |

## Engineering-owned defaults vs client-owned decisions

### Engineering-owned defaults

- Use capability-based adapters for notifications, storage, payroll, identity, map/geolocation, and PDF/export functions.
- Route external side effects through outbox/jobs, not domain transactions.
- Keep migration sequencing aligned to the bounded-context order: core/iam/platform services first, then party master data, then planning, then field, then finance, then reporting.
- Treat offline support as a design requirement for patrol/time-capture-capable field flows.
- Preserve document metadata and business linkage even when historical binaries may be selectively imported later.

### Client-owned decisions

- Which providers will be used for email/SMS/push, payroll, object storage, mapping, PDF/export, and external identity.
- How much historical data is required per entity class at go-live versus archived reference-only scope.
- Whether historical document binaries must all migrate or whether some can remain outside the system with metadata placeholders.
- Whether external SSO is in scope for initial release or a later phase.
- Whether RLS should remain optional hardening or become a mandatory platform control.

## Sprint 2 relevance

This register should directly inform Sprint 2 execution:

- `US-2-T2`: config naming, environment stubs, object storage emulation, and room for later adapters
- `US-2-T3`: CI checks that acknowledge migrations, docs, and integration boundaries
- `US-2-T4`: observability/error-handling choices that do not conflict with audit/evidence rules
- `US-4` to `US-6`: data ownership, tenant scoping, docs service, auth, and outbox/integration design

## What this task intentionally does not decide

- Actual provider/vendor contracts
- Final import templates or file layouts for Sprint 12 migration execution
- Detailed SLA/SLO numbers
- Final cutover and data-cleaning playbooks

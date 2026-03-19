# Story Traceability Matrix

## Task anchor

- Task: `US-1-T4`
- Purpose: map each approved story to acceptance intent, source basis, expected evidence, and reference-workflow coverage

## Workflow keys

- `COI`: customer order to report/invoice
- `APE`: applicant to payroll-ready employee
- `SC`: subcontractor collaboration

## Matrix

| Story | Story title | Sprint | Primary context | Acceptance intent | Main deliverable | Expected evidence/demo form | Workflow coverage | Acceptance notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `US-1` | Discovery, backlog confirmation, and acceptance traceability | 01 | Cross-cutting | Backlog baseline, dependency map, and acceptance frame are approved. | Discovery/backlog/QA docs | Docs review, dependency map, acceptance matrix | `COI`,`APE`,`SC` | Must preserve stable IDs and make all three workflows visible across later stories. |
| `US-2` | Repository, environments, CI/CD, and observability baseline | 01 | Engineering platform | Backend/web/mobile hello-world builds, tests, migrations, and health checks run in delivery automation. | Repo/runtime/CI baseline | Pipeline run, lint/test/build outputs, health-check demo | `COI`,`APE`,`SC` | Quality gates must not weaken auditability or future tenant isolation. |
| `US-3` | Vben Admin shell, Prokit mobile shell, theme tokens, and localization | 01 | UX foundation | Web/mobile shells show DE default, EN secondary, and fixed light/dark theme behavior. | Web/mobile shell baseline | UI demo, theme switch, locale switch | `COI`,`APE`,`SC` | Vben/Prokit alignment and exact color tokens are part of acceptance. |
| `US-4` | Tenant, branch, mandate, setting, and lookup foundation | 02 | `core` | Tenant onboarding and settings management work with audit-safe lifecycle states and seeded lookup domains. | Core tenant model and admin flows | Migration proof, API behavior, admin UI demo | `COI`,`APE`,`SC` | Tenant isolation is foundational for every later story. |
| `US-5` | Identity, role scope, session management, and audit foundation | 02 | `iam` | Authentication, scoping, and sensitive action auditability are enforced across modules. | IAM/RBAC and audit services | Login/API demo, scope enforcement proof, audit evidence | `COI`,`APE`,`SC` | Portal/local scope and immutable audit behavior matter as much as login success. |
| `US-6` | Document, communication, information portal, and integration backbone | 02 | `platform_services` | Versioned docs, templated communications, notices, and async integration events work as shared services. | Docs/comm/info/outbox services | Document upload/version demo, message pipeline demo, outbox job evidence | `COI`,`APE`,`SC` | Generated files must link through docs service; no direct provider calls in domain transactions. |
| `US-7` | Customer master, contacts, addresses, and portal account linkage | 03 | `customers` | Customer master is tenant-safe, auditable, searchable, and ready for planning/finance use. | Customer master module | API/UI demo, import/export proof, audit evidence | `COI` | Customer truth must stay tenant-scoped and portal-safe. |
| `US-8` | Customer billing profile, rate cards, surcharge rules, and invoice parties | 03 | `customers` | Versioned commercial rules are maintained in CRM and consumable by finance without duplication. | Customer commercial settings | UI/API demo, overlap validation proof | `COI` | Finance must consume CRM commercial truth rather than redefine it. |
| `US-9` | Customer portal read models, collaboration views, and customer-specific controls | 03 | `customers` + portal | Customer users see only their own released data, with names hidden by default unless explicitly released. | Customer portal read models | Portal demo, scope-filter proof, privacy demo | `COI` | Customer privacy defaults must be visible in acceptance. |
| `US-10` | Applicant intake, GDPR consent, and applicant workflow | 04 | `recruiting` | Applicants move from intake through decision with durable status history and file trail. | Applicant workflow module | Form/UI demo, API behavior, consent/history evidence | `APE` | Consent evidence and file history are required, not optional extras. |
| `US-11` | Employee master file with private-profile split and role-based exposure | 04 | `employees` | Employee records support operational use while sensitive HR data remains role-restricted. | Employee master and HR-private views | Migration proof, API/UI demo, authz proof, audit evidence | `APE` | HR-private restrictions must be explicitly demonstrated. |
| `US-12` | Qualifications, availability, absences, balances, allowances, and credentials foundation | 04 | `employees` | Planning, payroll, and self-service can consume accurate employee compliance and availability data. | HR readiness foundation | API behavior, admin/self-service demo, validation proof | `APE` | Upstream HR truth must stay separate from planning/finance ownership. |
| `US-13` | Subcontractor master, scope, contacts, and finance profile | 05 | `subcontractors` | Subcontractor records are tenant-scoped, commercially configured, and ready for planning/settlement flows. | Partner company master | Migration proof, API/UI demo, audit evidence | `SC` | Partner truth must stay isolated from planning writes. |
| `US-14` | Subcontractor workers, qualifications, credentials, and compliance completeness | 05 | `subcontractors` | Worker readiness and missing/expired compliance are visible before staffing and release. | Partner workforce/compliance module | UI/API demo, compliance view proof, import/export evidence | `SC` | Compliance completeness must be queryable before allocation. |
| `US-15` | Subcontractor portal self-service, shift allocation, and visibility boundaries | 05 | `subcontractors` + portal | Subcontractors only see own company and released assignments, and self-allocation respects validation rules. | Subcontractor portal | Portal demo, validation feedback demo, scope proof | `SC` | Released-scope-only visibility is a core acceptance criterion. |
| `US-16` | Operational master data: locations, routes, checkpoints, and equipment catalogs | 06 | `planning` | Dispatchers can manage sites, venues, fairs, routes, and equipment with tenant-safe geo-enabled records. | Operational master data | Admin UI demo, map/geo proof, import tools | `COI`,`SC` | Geo data and patrol/watchbook cross-links should remain traceable. |
| `US-17` | Customer orders, planning records, and mode-specific detail structures | 06 | `planning` | Orders and planning records carry requirements, attachments, release states, and mode-specific details without duplicating commercial ownership. | Order/planning backbone | API/UI demo, release-state behavior, document package proof | `COI` | Planning must link to customer commercial truth without owning it. |
| `US-18` | Shift plans, templates, recurrence series, and concrete shift generation | 06 | `planning` | Dispatchers can generate and maintain reusable shift structures with performant board queries. | Shift-planning framework | UI demo, generation proof, performance/query evidence | `COI`,`APE`,`SC` | Board/query performance is part of acceptance, not only correctness. |
| `US-19` | Demand groups, teams, assignments, and subcontractor releases | 07 | `planning` | Workforce and partner assignments can be built against demand with tenant-safe staffing structures. | Assignment/release model | API/UI demo, release contract proof | `COI`,`APE`,`SC` | Assignment release is a downstream visibility gate. |
| `US-20` | Validation engine, blocking/warning policies, and override audit trail | 07 | `planning` | Staffing and release validation rules are enforced with auditable override handling. | Validation engine | Validation demo, override audit trail, rule evidence | `COI`,`APE`,`SC` | Override auditability must be explicit in acceptance evidence. |
| `US-21` | Release workflows, deployment outputs, and visibility to downstream channels | 07 | `planning` | Released operational data is packaged and exposed correctly to downstream channels. | Release workflow and downstream visibility | UI/API demo, release package proof, docs/output evidence | `COI`,`APE`,`SC` | Only released data may reach mobile, portals, field, and finance flows. |
| `US-22` | Employee mobile app: schedules, actions, documents, notifications, and theme/i18n parity | 08 | `field_execution` mobile | Employee mobile experience surfaces only released information in DE/EN with correct theme behavior. | Employee mobile app core | Mobile demo, locale/theme demo, released-data scope proof | `APE`,`COI` | Mobile visibility must remain scoped and release-based. |
| `US-23` | Information feed, mandatory notice acknowledgements, and online watchbook | 08 | `field_execution` + `platform_services` | Notice/read evidence and watchbook flows are durable, reviewable, and exportable. | Notice feed and watchbook | Web/mobile demo, read-confirmation evidence, daily PDF output | `COI`,`SC`,`APE` | Revision-safe outputs and evidence preservation are mandatory. |
| `US-24` | Guard patrol control, checkpoint capture, and offline synchronization | 08 | `field_execution` patrol | Patrol events are append-only, sync correctly, and link back to watchbook/evaluation context. | Patrol workflow with offline support | Mobile demo, offline sync proof, patrol event evidence | `COI` | Offline-safe behavior and append-only evidence must be demonstrated. |
| `US-25` | Time capture devices, policies, raw event ingest, and context validation | 09 | `field_execution` time capture | Device/IP/geolocation/terminal rules reject or flag invalid captures while preserving raw evidence. | Raw time ingest pipeline | API/mobile/browser demo, policy violation proof, audit/raw-event evidence | `COI`,`APE`,`SC` | Raw attempts must remain preserved even when rejected or flagged. |
| `US-26` | Attendance normalization and actual_record bridge from planning and field evidence | 09 | `finance` | Actuals are derived without mutating raw evidence and can feed payroll, timesheets, invoices, and partner settlement. | Attendance summaries and `finance.actual_record` | Derivation proof, reconciliation demo, schema/API evidence | `COI`,`APE`,`SC` | This story is the finance bridge for all three workflows. |
| `US-27` | Three-stage approval and reconciliation for operational and finance actuals | 09 | `finance` | Every final actual has auditable approval history and correct adjustment lineage. | Approval/reconciliation workflow | UI/API demo, approval audit trail, discrepancy handling proof | `COI`,`APE`,`SC` | Provenance and correction lineage matter as much as final totals. |
| `US-28` | Payroll tariffs, employee pay profiles, allowances, and export package | 10 | `finance` payroll | Payroll outputs derive from approved actuals and effective pay settings without bypassing the finance bridge. | Payroll basis and export package | UI/API demo, export batch proof, reconciliation report | `APE` | Payroll logic must remain bridge-driven and auditable. |
| `US-29` | Customer timesheets, invoices, layouts, and customer portal release | 10 | `finance` billing | Customer billing outputs are reproducible from approved actuals and released commercial rules. | Timesheets/invoices and portal release | Invoice/timesheet demo, PDF output, portal visibility proof | `COI` | Customer-facing billing outputs must stay reproducible and document-linked. |
| `US-30` | Subcontractor invoice checks, variance analysis, and commercial control | 10 | `finance` partner control | Partner settlement has line-level variance visibility, controller workflow, and scoped portal visibility. | Invoice-check workflow | Controller UI demo, variance proof, portal read-model evidence | `SC` | Portal exposure must not leak internal finance data. |
| `US-31` | Operational, commercial, and finance reporting read-model layer | 11 | `reporting` | Role-scoped reports and exports are reproducible from transactional data without new write-side duplication. | Reporting views/dashboards/exports | Dashboard demo, SQL/view proof, export evidence | `COI`,`APE`,`SC` | Role scope and reproducibility are central acceptance points. |
| `US-32` | Compliance, QM, and security reporting with scheduled export hooks | 11 | `reporting` compliance/QM | Controller/QM/security exports provide auditable evidence with proper scope restrictions and repeatable results. | Compliance/QM/security report package | Report demo, scheduled export hook proof, audit/security evidence | `APE`,`SC`,`COI` | Qualification expiry, read evidence, login/security activity must remain traceable. |
| `US-33` | Performance tuning, optional RLS, backup/restore, and security hardening | 11 | Hardening | Platform meets agreed security and performance baselines and is ready for UAT/cutover. | Hardening evidence and remediation closeout | Performance results, backup/restore drill, security test evidence | `COI`,`APE`,`SC` | Optional RLS, secure-doc access, and resilience drills must stay visible. |
| `US-34` | Data migration package, seed/reference data, and print-template finalization | 12 | Migration/configuration | Migration templates and seeded reference data support realistic trial loads and output generation without schema rework. | Migration workbook/package | Migration proof, seeded config demo, print/output evidence | `COI`,`APE`,`SC` | Trial loads must preserve portal/planning/finance readiness. |
| `US-35` | UAT execution, multilingual review, training, and rollout readiness | 12 | UAT/enablement | Business stakeholders sign off on UAT, language QA, training material, and cutover readiness. | UAT signoff and enablement pack | UAT run evidence, multilingual review notes, training/demo artifacts | `COI`,`APE`,`SC` | All three anchor workflows must be explicitly exercised. |
| `US-36` | Production cutover, hypercare, KPI monitoring, and stabilization | 12 | Release | Production is live, support handover is in place, and the first stabilization backlog is prioritized. | Cutover and hypercare package | Release checklist, monitoring evidence, hypercare log | `COI`,`APE`,`SC` | Operational support and stabilization governance are part of acceptance. |

## Workflow traceability summary

### Customer order to report/invoice (`COI`)

Primary story chain:

- `US-7`, `US-8`, `US-9`
- `US-16`, `US-17`, `US-18`, `US-19`, `US-20`, `US-21`
- `US-22`, `US-23`, `US-24`, `US-25`
- `US-26`, `US-27`, `US-29`, `US-31`, `US-34`, `US-35`, `US-36`

### Applicant to payroll-ready employee (`APE`)

Primary story chain:

- `US-10`, `US-11`, `US-12`
- `US-18`, `US-19`, `US-20`, `US-21`
- `US-22`, `US-23`, `US-25`
- `US-26`, `US-27`, `US-28`, `US-31`, `US-32`, `US-34`, `US-35`, `US-36`

### Subcontractor collaboration (`SC`)

Primary story chain:

- `US-13`, `US-14`, `US-15`
- `US-16`, `US-18`, `US-19`, `US-20`, `US-21`
- `US-23`, `US-25`
- `US-26`, `US-27`, `US-30`, `US-31`, `US-32`, `US-34`, `US-35`, `US-36`

## Notes for reviewers

- Story titles and IDs are intentionally copied from the approved sprint backlog.
- The matrix is story-level on purpose; task-level traceability should stay in prompt files and implementation deliverables.
- Privacy, HR-private restrictions, append-only evidence, and `finance.actual_record` are surfaced in acceptance notes where they materially affect review.

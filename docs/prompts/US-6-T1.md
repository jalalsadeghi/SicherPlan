---
task_id: US-6-T1
story_id: US-6
story_title: "Document, communication, information portal, and integration backbone"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Platform Lead"
---

# Codex Prompt — US-6-T1

## Task title

**Implement docs.document, document_version, document_link, and object-storage integration**

## Objective

Create the shared document backbone so all later modules can attach, version, and retrieve files through one centralized, revision-safe service instead of scattered ad hoc storage logic.

## Source context

- Updated proposal: section 5.1 documents and media; section 6 end-to-end workflows where documents, reports, IDs, invoices, and evidence stay linked; section 7 data/storage baseline with object storage.
- Implementation specification: docs service ownership; section 4.2 tables `docs.document_type`, `docs.document`, `docs.document_version`, and `docs.document_link`; document-link polymorphic exception; generated-output tracking rules.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md` and the environment/config baseline from Sprint 1.

## Dependencies

- `US-4-T1` / `US-5-T1` should already provide tenant and user references.
- Local/staging object-storage configuration from Sprint 1 should exist or be expandable.

## Scope of work

- Implement the central document tables and models, including `docs.document_type` if required by the approved schema and not already present in the repo.
- Provide upload, versioning, metadata, and link-management services/APIs so business modules can create logical documents, add immutable versions, and link documents to owning entities.
- Integrate object storage through a swappable storage adapter that works in local/staging and is not hardwired to one provider implementation.
- Preserve checksum, file-size, upload actor, upload timestamp, and `is_revision_safe_pdf` metadata on document versions.
- Respect the intentional polymorphic exception of `docs.document_link`: keep the FK to `docs.document`, validate owner existence in service code, and do not invent a second generic linking mechanism.
- Write tests for upload/version incrementing, duplicate-check metadata, storage adapter behavior, and secure scoped retrieval.

## Preferred file targets

- Backend docs module files under the actual package structure, for example `apps/api/modules/platform_services/docs/*` or similar.
- Storage adapter/integration files under the repo's existing infrastructure package.
- Tests such as `apps/api/tests/modules/platform_services/test_document_backbone.py` or equivalent.

## Hard constraints

- The docs service stores file metadata and links; it must not infer business meaning that belongs to the owning module.
- Document versions are immutable once stored.
- Object-storage integration must remain provider-abstracted and environment-safe.
- Secure document permissions matter: downloading or viewing a document must still respect tenant and role scope.
- Do not implement every business-specific document workflow in this task.

## Expected implementation outputs

- Document tables/models/schemas plus a reusable storage abstraction.
- Upload/version/link services and APIs.
- Tests for immutability, linkage, and scoped access.
- A foundation that later reporting, finance, and field modules can reuse directly.

## Non-goals

- Do not generate every future PDF/report type here.
- Do not implement customer, employee, or subcontractor document business rules in full.
- Do not call object storage directly from random business modules outside the docs service.
- Do not create a second parallel attachment system in CRM/HR/partner modules.

## Verification checklist

- A logical document can be created, versioned, and linked to an owning entity through the approved API/service path.
- Document versions remain immutable and correctly numbered.
- Storage access works through the configured adapter and is not leaking across tenants.
- Document metadata is rich enough for later compliance, reporting, and generated-output workflows.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-6-T1 — Implement docs.document, document_version, document_link, and object-storage integration** is finished.

```text
/review Please review the implementation for task US-6-T1 (Implement docs.document, document_version, document_link, and object-storage integration) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-6-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Document/version immutability and checksum/metadata handling are correct.
- The object-storage integration is abstracted, secure, and testable.
- Document-link semantics stay aligned with the approved polymorphic exception and do not create hidden coupling.
- Access control around file retrieval respects tenant and role scoping.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-6.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```

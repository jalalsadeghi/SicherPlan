# Document Storage And Versioning

## Scope

- `docs.document` is the logical document aggregate owned by the platform-services docs boundary.
- `docs.document_version` stores immutable file revisions and storage metadata.
- `docs.document_link` is the approved polymorphic exception for linking a document to an owning business entity.

## Storage rules

- File content goes through the docs service only, never directly from random business modules.
- Storage is provider-abstracted behind an adapter. The current baseline uses a filesystem-backed adapter for local and staging-safe execution.
- Stored version metadata keeps `checksum_sha256`, `file_size_bytes`, `uploaded_by_user_id`, `uploaded_at`, and `is_revision_safe_pdf`.

## Versioning rules

- Document versions are immutable and version-numbered per document.
- Duplicate payloads are still allowed as new revisions, but later reporting can detect them through `metadata_json.duplicate_of_version_no`.
- Download access remains tenant-scoped and permission-scoped through the API layer.

## Link rules

- `docs.document_link` keeps only the FK to `docs.document`.
- Owner existence is validated in service code for the supported owner types instead of adding a second generic attachment system.
- The docs service stores attachment metadata only; business meaning remains with the owning module.

# Notice And Acknowledgement Backbone

## Scope

- `info.notice` stores authored notice content, publish windows, and related-entity references.
- `info.notice_audience` stores tenant-safe audience targets without forcing early cross-module writes.
- `info.notice_read` stores one durable evidence row per `notice + user`.
- `info.notice_link` stores curated URLs, while attachments stay in the docs service.

## Audience rules

- Current resolver support is role-based and tenant-safe.
- Audience kinds for `employee_group`, `qualification`, and `function` are persisted now and resolved through a trait-provider seam later.
- `all_employees`, `all_customers`, and `all_subcontractors` rely on scoped actor roles rather than separate-tenant logic.

## Evidence rules

- Opening a notice upserts one `info.notice_read` row and updates `last_opened_at`.
- Acknowledgement reuses the same row and stamps `acknowledged_at`.
- Reporting can later query durable evidence without reconstructing it from logs.

## Attachment rules

- Notice attachments use `docs.document_link` with owner type `info.notice`.
- Curated links remain in `info.notice_link` so URL references do not pollute the docs model.

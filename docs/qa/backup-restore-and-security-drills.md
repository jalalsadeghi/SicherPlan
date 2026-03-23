# Backup, Restore, and Security Drills

This runbook is the `US-33-T3` drill package.

## Backup and restore drill

1. Restore the target PostgreSQL snapshot into a non-production environment.
2. Point the backend to the restored database with `SP_DATABASE_URL`.
3. Run:

```bash
PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/restore_validation.py --database-url "$SP_DATABASE_URL"
```

Expected validation:

- tenant, IAM, docs, watchbook, time, actual, and invoice tables all return non-zero or expected counts
- `document_links_without_document` is `0`

Object-storage validation:

- sample at least one restored generated document and one uploaded document
- verify the `docs.document_version.object_bucket` / `object_key` pair resolves in the target storage backend
- do not treat restored database rows as sufficient evidence if object storage was not validated

## Rate-limit drill

Covered endpoints:

- `POST /api/auth/refresh`
- `GET /api/platform/tenants/{tenant_id}/documents/{document_id}/versions/{version_no}/download`
- `GET /api/reporting/tenants/{tenant_id}/{report_key}/export`
- `POST /api/reporting/tenants/{tenant_id}/{report_key}/delivery-jobs`
- customer and employee document download paths that proxy docs-backed outputs

Configuration seam:

- `SP_SECURITY_RATE_LIMIT_ENABLED`
- `SP_SECURITY_RATE_LIMIT_WINDOW_SECONDS`
- `SP_SECURITY_RATE_LIMIT_AUTH_REFRESH_MAX`
- `SP_SECURITY_RATE_LIMIT_DOCUMENT_DOWNLOAD_MAX`
- `SP_SECURITY_RATE_LIMIT_REPORT_EXPORT_MAX`

## Secure-document drill

Repeat these checks before UAT or go-live:

1. Customer portal user can download only timesheets/invoices for the linked customer scope.
2. Employee self-service user can download only documents surfaced through the employee mobile read service.
3. Cross-tenant document download is denied.
4. Platform docs routes still require authenticated tenant/platform permission.

Repo evidence:

- `backend/tests/modules/finance/test_billing_flows.py`
- `backend/tests/modules/employees/test_employee_mobile_read.py`
- `backend/tests/modules/platform_services/test_document_backbone.py`
- `backend/tests/modules/platform_services/test_hardening_drills.py`

## Notes

- The in-process rate limiter is intentionally lightweight for Sprint 11 and should be treated as an app-node control, not a distributed edge gateway replacement.
- If RLS is enabled, rerun the same drills with `SP_DB_RLS_ENABLED=true` to confirm app-layer auth and DB-layer tenant filtering stay aligned.

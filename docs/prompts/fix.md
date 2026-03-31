You are working in the latest SicherPlan repository.

Problem:
In the Employees admin workspace, the Documents tab is currently not actionable.
The current implementation only lists already-linked employee documents and allows download, but it does not allow:
- uploading a new employee document
- linking an existing shared document to the employee file
- creating a document record for the employee
- adding new versions to an existing employee-linked document

Current findings:
1. Frontend documents tab in:
   web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   only renders a read-only list and calls downloadDocument(document).
   There is no upload input, no create/link form, and no save handler for employee documents.

2. Frontend API layer in:
   web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
   only provides:
   - listEmployeeDocuments(...)
   - downloadEmployeeDocument(...)
   and has no create/link/upload employee-document API methods.

3. Backend router in:
   backend/app/modules/employees/router.py
   only exposes:
   - GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents
   - GET /{employee_id}/photo
   - POST /{employee_id}/photo
   There is no POST/link/upload endpoint for generic employee documents.

4. Backend file service in:
   backend/app/modules/employees/file_service.py
   currently supports:
   - list_documents(...)
   - get_profile_photo(...)
   - upsert_profile_photo(...)
   but no generic employee-document create/upload/link flow.

Goal:
Upgrade the Employees -> Documents tab from read-only to a proper document-management area for the employee file.

Requirements:
1. Keep the existing master-detail Employees page and current tab structure.
2. Extend the Documents tab so authorized users can:
   - upload a new employee document
   - link an existing document to the employee
   - optionally add a new version to an existing employee-linked document
   - see metadata such as title, relation_type, file name, content type, current version, linked_at
   - download documents as before
3. Reuse the shared platform document service and document-link backbone.
4. Use owner_type = "hr.employee" for employee-linked documents.
5. Support relation types explicitly, e.g.:
   - employee_document
   - id_proof
   - contract
   - certificate
   - residence_permit
   - misc
   Keep this extensible and avoid hardcoding brittle UI-only logic.
6. Add backend endpoints for generic employee documents, for example:
   - POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads
   - POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/links
   - POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/{document_id}/versions
   Adjust naming only if needed for consistency with existing project conventions.
7. Add backend schemas for:
   - employee document upload/create
   - employee document link
   - employee document version add
8. Add service methods in EmployeeFileService for:
   - upload_employee_document
   - link_employee_document
   - add_employee_document_version
9. Preserve profile-photo behavior as a separate dedicated feature; do not break the existing photo flow.
10. Enforce permissions correctly:
   - viewing employee documents should require employees.employee.read
   - creating/linking/updating employee documents should require employees.employee.write
   - do not expose private-only fields unless already allowed elsewhere
11. Update the UI copy/i18n for the new document actions.
12. Add/adjust tests:
   - frontend layout/render test for new documents controls
   - frontend API tests if present
   - backend router/service tests for upload/link/version flows
   - permission tests
13. Backward compatibility:
   - existing employees with no documents must still load cleanly
   - existing profile-photo behavior must remain unchanged

Files to inspect and update:
Frontend:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
- web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts
- related frontend tests

Backend:
- backend/app/modules/employees/router.py
- backend/app/modules/employees/file_service.py
- backend/app/modules/employees/schemas.py
- backend/app/modules/platform_services/docs_service.py
- backend/app/modules/platform_services/docs_schemas.py
- backend/app/modules/platform_services/docs_repository.py
- related tests

Implementation notes:
- Prefer using the existing shared document service instead of inventing a separate employee-only file subsystem.
- Keep the Documents tab structured similarly to other employee tabs: intro section, library/register section, editor/actions section.
- Be explicit about relation types and document metadata.
- Keep code production-ready, not a placeholder.

Before changing code, first provide:
1. impacted files
2. API contract changes
3. permission implications
4. test plan

Then implement the fix.
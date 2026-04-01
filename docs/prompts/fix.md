You are working in the SicherPlan repository.

Goal:
Fix the 404 business error `docs.document_type.not_found` that occurs when the Employees workspace uploads a document via:

POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads

Observed behavior:
- The route exists and must remain unchanged.
- The backend returns 404 with:
  code: docs.document_type.not_found
  message_key: errors.docs.document_type.not_found
- The failing flow is the Employees > Documents > Upload document form.

Root-cause evidence already confirmed in the repo:
1. Frontend hardcodes employee document type options in:
   web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.helpers.js
   Keys currently used:
   - employment_contract
   - identity_card
   - passport_copy
   - residence_permit
   - driving_licence
   - qualification_certificate
   - employee_misc

2. Upload request is built and sent from:
   web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts

3. Backend upload handler is:
   backend/app/modules/employees/router.py
   backend/app/modules/employees/file_service.py

4. Backend document creation resolves `document_type_key` in:
   backend/app/modules/platform_services/docs_service.py
   If the key is non-null and not found in `docs.document_type`, it raises:
   `docs.document_type.not_found`

5. The docs backbone migration creates `docs.document_type` but does not seed the employee document types:
   backend/alembic/versions/0006_docs_backbone.py

Required fix:
Implement a production-safe, minimal fix so that the Employees upload form works when one of the hardcoded employee document types is selected.

Tasks:
1. Add a new Alembic migration that seeds the canonical employee document types used by the Employees UI.
   Required keys:
   - employment_contract
   - identity_card
   - passport_copy
   - residence_permit
   - driving_licence
   - qualification_certificate
   - employee_misc

2. Make the migration idempotent.
   - It must be safe on existing databases.
   - Use INSERT ... ON CONFLICT (key) DO NOTHING, or an equivalent safe upsert.
   - Do not delete or replace existing rows unnecessarily.
   - Preserve existing user data.

3. Keep current API paths and payload shapes unchanged.
   - Do not rename `/documents/uploads`
   - Do not remove the ability to upload with `document_type_key = null`

4. Improve frontend error handling for this specific case.
   - Add a dedicated UI mapping for `errors.docs.document_type.not_found`
   - Show a user-friendly message like:
     “The selected document type is not configured in the backend.”
   - Implement this in the existing employee admin error-mapping flow only; do not introduce a new global pattern unless already consistent with the repo.

5. Add automated tests:
   - Backend test proving that employee document upload with `document_type_key="employment_contract"` succeeds once the seed exists.
   - Keep or extend existing route-registration tests; do not remove them.
   - If there is already a suitable platform-services or employee module test file, extend it instead of creating unnecessary duplicates.

6. Verify no regression:
   - Upload still works when document_type_key is omitted/null
   - Link existing document flow still works
   - Add document version flow still works
   - Profile photo flow still works

Implementation constraints:
- Follow existing repo conventions and naming.
- Keep the change set focused on this issue.
- Do not refactor unrelated modules.
- Do not change business semantics outside employee document upload + error messaging.
- If a helper constant or shared seed list improves maintainability, keep it small and local.

Please do the work and then return:
1. A short root-cause summary
2. The exact files changed
3. The migration behavior
4. The tests added/updated
5. Any remaining caveats
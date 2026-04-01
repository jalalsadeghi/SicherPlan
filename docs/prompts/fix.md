Task: Fix employee document upload failures caused by unknown document_type_key values in the SicherPlan employee admin workflow.

Repository:
- jalalsadeghi/SicherPlan
- branch: inspect current branch state first and work on top of the latest code

Problem summary:
In the current employee documents tab, the frontend exposes a free-text "Document type key" field.
The backend route exists and is correct:
POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads
However, the backend passes document_type_key into DocumentService.create_document().
If the key is non-empty and not present in docs.document_type, DocumentService raises:
404 docs.document_type.not_found
This makes the employee document upload UX fragile and causes avoidable failures during normal UAT/manual data entry.

Confirmed code locations to inspect first:
- backend/app/modules/employees/router.py
- backend/app/modules/employees/file_service.py
- backend/app/modules/platform_services/docs_service.py
- backend/app/modules/platform_services/document_type_seed.py
- backend/scripts/seed_go_live_configuration.py
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
- backend/tests/modules/employees/test_employee_file_service.py

Goal:
Make employee document uploads reliable and operator-safe, without weakening backend validation for truly unknown keys.

Required changes:
1. Extend the document type seed set with employee-facing document types that are actually used in the employee documents workflow.
   Add at least:
   - employment_contract
   - identity_card
   - passport_copy
   - residence_permit
   - driving_licence
   - qualification_certificate
   - employee_misc
   Keep existing keys unchanged.

2. Preserve current backend behavior:
   - blank/null document_type_key must remain allowed
   - unknown non-empty keys should still be rejected by the backend
   Do not silently auto-create arbitrary keys from user input.

3. Improve the employee documents UI so operators are not forced to guess valid keys:
   - replace the free-text "Document type key" input with a controlled select
   - include an empty/none option
   - include the seeded employee-facing keys above
   - keep relation_type as a separate field
   - add helper text that document_type_key is optional and relation_type controls employee-side relation semantics

4. Do not break existing flows:
   - qualification proof upload must still work
   - profile photo flow must still work
   - generic employee document upload, link, and add-version flows must still work

5. Add/update tests:
   Backend:
   - test that seeded document types include the new employee-facing keys
   - test employee document upload succeeds with null document_type_key
   - test employee document upload succeeds with a seeded employee document type key
   - test employee document upload still fails for an unknown non-empty key
   Frontend:
   - test the documents tab renders a controlled document type select, not a raw free-text field
   - test submit payload sends null when the document type select is empty
   - test selecting a seeded key submits that key unchanged

Implementation constraints:
- keep changes minimal and scoped to this problem
- do not redesign the whole platform services API unless necessary
- do not remove backend validation of document_type_key
- do not introduce tenant-specific document type duplication for these system-level keys
- keep the code style consistent with the current repo

Acceptance criteria:
- Uploading an employee document with an empty document_type_key succeeds
- Uploading with document_type_key=employment_contract succeeds after seeding
- Uploading with document_type_key=identity_card succeeds after seeding
- Uploading with an unknown key still returns a clear API error
- The employee documents UI no longer invites invalid manual key entry
- Tests pass

Deliverables:
- code changes
- tests
- short change summary
- exact commands to run migrations/seeds/tests locally
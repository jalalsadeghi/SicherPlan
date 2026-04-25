You are working in the latest public SicherPlan repository.

Target page:
admin/employees

Observed bug:
On first load of admin/employees, employee list rows show only initials/avatar fallback.
When the user opens one employee dashboard/detail and returns to the list, that employee’s photo appears in the list.
After opening another employee dashboard, that second employee’s photo also appears in the list.
This means employee photos are currently loaded lazily only after opening employee detail/dashboard, not during initial list rendering.

Goal:
Fix employee list photos so that, on the first list load, all employees that already have profile photos show their real photo thumbnails immediately.
Employees without photos should keep initials fallback.

Relevant frontend files to inspect:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/components/employees/EmployeeDashboardTab.vue
- web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
- employeeAdmin layout/smoke tests

Relevant backend/API areas to inspect:
- employee list endpoint implementation:
  GET /api/employees/tenants/{tenant_id}/employees
- employee photo endpoint implementation:
  GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/photo
- employee DTO/read models/schemas for list and detail
- document/photo storage/linking logic

Important current finding to validate:
The frontend EmployeeListItem type appears not to contain photo/profile image metadata. If this is true, the initial list cannot reliably render photos without either:
1) extending the list endpoint/read model to include safe photo thumbnail metadata/url, or
2) adding a batch-safe frontend preload strategy, or
3) adding/using an existing batch endpoint for employee photos.

Do not implement an N+1 solution blindly.
Do not fetch one full photo endpoint per employee without evaluating performance and list size.
Do not rely on “open detail first” cache behavior.

Please audit and decide the best implementation approach.

Preferred solution if backend supports it:
- Extend the employee list response with optional photo metadata suitable for list thumbnails, for example:
  - photo_document_id
  - photo_version_no
  - photo_url / photo_download_url / profile_photo_url
  - has_photo
  - photo_content_type if needed
- Update frontend EmployeeListItem type accordingly.
- Render photo thumbnail from this data in employee list rows.
- Keep initials fallback for rows without photo.

Alternative solution if backend already has a safe helper:
- Reuse any existing photo URL builder or document download route.
- Avoid per-row full photo fetches if possible.

Fallback solution only if backend change is not feasible in this task:
- Implement a bounded/concurrency-limited preload for visible list rows only.
- Cache photo results by employee_id.
- Do not block list rendering.
- Do not preload archived/hidden rows unnecessarily.
- Explain why this fallback was chosen.

Required investigation:
1) Find how EmployeeDashboardTab receives/displays the photo.
2) Find where the detail photo is loaded and cached in EmployeeAdminView.
3) Check whether listEmployees returns any photo metadata.
4) Check whether backend EmployeeListItem/EmployeeRead schema has photo fields.
5) Check whether the backend can cheaply include current profile photo metadata in the list query without loading binary data.
6) Check whether there is already a document/version download URL builder that can be safely used for thumbnails.
7) Decide whether the fix should be frontend-only or frontend+backend.

Expected output of this audit:
- exact reason photos only appear after opening detail
- whether list API currently lacks photo metadata
- recommended implementation plan
- files to change
- test plan

Please validate my suggested direction critically:
If the list API already contains the required metadata but frontend ignores it, fix frontend only.
If the list API truly lacks photo data, implement the safest API/read-model extension or explain why a frontend-only fallback is required.
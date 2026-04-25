You are working in the latest public SicherPlan repository.

Target page:
admin/employees

Main file to inspect:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Related files to inspect:
- EmployeeDashboardTab component used in the employee detail/dashboard view
- employee admin API/types used by EmployeeAdminView
- employeeAdmin layout/smoke tests:
  - web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.layout.test.js
  - web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.smoke.test.ts

Observed UI:
- In the employee detail/dashboard view, the employee photo is displayed correctly.
- In the admin/employees list view, each employee row currently shows only initials/avatar fallback such as "MN", "LY", "EK", etc.
- The user wants the real employee photo to be displayed in the list row as well, when available.

Goal:
Show the employee photo at the beginning of each employee row in the admin/employees list, using the same available photo source/pattern that already works in the employee dashboard/detail view.

Important:
Do not solve this by making one API request per employee row if the list can contain many employees.
Do not introduce an N+1 photo loading problem.
Do not change backend APIs unless you first prove that the frontend has no safe existing source or endpoint pattern for row photos.
Do not break the initials fallback.
Do not change employee detail/dashboard photo upload behavior.
Do not change list/detail navigation.
Do not change search/filter behavior.

Required investigation:
1) Find how EmployeeDashboardTab receives and displays the employee photo.
2) Identify where `photoPreviewUrl` or equivalent employee photo state is created in EmployeeAdminView.
3) Check whether employee list rows already have any photo metadata, for example:
   - photo_url
   - photo_document_id
   - avatar_url
   - profile_photo_url
   - current_photo_version
   - document link / photo endpoint reference
4) Check the employee admin API/types to see whether list employees include photo information.
5) Check whether there is an existing safe helper/composable/API function for employee photos.
6) Determine whether the list can reuse cached/loaded photo previews for employees whose detail was already opened.
7) Validate whether a lightweight batch-safe approach exists before changing anything.

Preferred implementation:
- If the employee list item already includes a photo URL or photo metadata, render it directly in the list avatar.
- If the photo URL can be derived safely from existing list fields without additional per-row requests, derive it with a helper.
- If the photo is only available after opening employee detail, then:
  - keep initials fallback for rows without loaded photo,
  - optionally use a small cache for photos already loaded in detail,
  - do not fetch every row photo individually.
- If a backend/API improvement is truly required, do not implement it blindly. First explain why and keep the frontend fallback stable.

UI requirements:
- The employee row still starts with the avatar area.
- If photo is available:
  - show image thumbnail in the avatar area.
  - use object-fit: cover.
  - keep the avatar size compact and aligned with the 2-line row layout.
- If photo is not available or image load fails:
  - show initials fallback exactly as now.
- Add an image error handler so broken photo URLs fall back to initials.
- Keep row height compact.
- Keep status badge on the right.
- Keep row clickable.

Suggested helper names:
- getEmployeeListPhotoUrl(employee)
- getEmployeeInitials(employee)
- markEmployeeListPhotoFailed(employee.id)
- shouldShowEmployeeListPhoto(employee)

Validation scenarios:
1) Employee with photo:
- list row displays real photo thumbnail.
2) Employee without photo:
- list row displays initials fallback.
3) Broken photo URL:
- image error hides broken image and shows initials fallback.
4) Detail dashboard still displays photo correctly.
5) Upload/change photo in detail:
- if the list photo cache can be updated safely, update the selected employee row thumbnail after upload.
- if not, do not break anything and mention limitation.
6) Search/filter keeps photos/fallbacks correct.
7) No extra API request per list row is introduced.

Testing:
Add/update tests in the closest employeeAdmin test file:
- list row renders an img when photo data exists.
- list row renders initials when photo data is missing.
- image error falls back to initials if feasible in the test environment.
- clicking a row still opens detail.
- detail dashboard photo behavior is unchanged.

Acceptance criteria:
- Employee list rows show real employee photo thumbnails when available.
- Rows without photo still show initials.
- Broken images fall back to initials.
- No N+1 row photo fetching is introduced.
- Employee detail/dashboard photo remains unchanged.
- No regression in search, advanced filters, import/export, create, or detail navigation.

Deliverables:
1) Apply code/CSS changes.
2) Add/update tests.
3) Summarize:
   - changed files
   - exact photo source used for list rows
   - whether the list API already had photo data
   - fallback behavior
   - validation performed
You are working in the SicherPlan repository.

Goal:
Make the logged-in employee’s real profile photo available to the mobile app so the Start/Home hero banner can render it instead of only showing initials.

Primary files to inspect first:
- backend/app/modules/employees/schemas.py
- backend/app/modules/employees/self_service_service.py
- backend/app/modules/employees/self_service_router.py
- backend/app/modules/employees/repository.py
- mobile/lib/api/mobile_backend.dart
- mobile/lib/session/mobile_session_controller.dart
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Observed symptom:
The mobile Start screen now shows employee initials ("MN") instead of the old placeholder, but it still does not show the actual employee photo.
The web/admin employee page already shows a real employee photo for Markus.
So the mobile side is still missing real photo data or a usable download path.

Tasks:
1. Trace how employee photo is currently stored and surfaced in the web/admin employee flow.
   - Reuse the existing employee photo/document structure already present in the system.
   - Do not introduce a new media subsystem.

2. Extend the employee mobile self-service contract with the smallest correct additive photo fields needed by mobile.
   Prefer one of these patterns:
   - photo_document_id + photo_current_version_no + photo_content_type
   - or a resolved self-photo download path/url
   Use the smallest robust solution that matches the existing employee photo model.

3. If a photo download endpoint is required for mobile, add the smallest secure self-service endpoint for the authenticated employee to fetch only their own photo.
   - Strictly scoped to the current authenticated employee.
   - No cross-employee access.
   - Reuse existing document/download infrastructure where possible.

4. Ensure the contract works for both cases:
   - employee has a photo
   - employee has no photo

Constraints:
- Keep auth strict.
- Do not redesign unrelated employee APIs.
- Do not broaden scope into full profile editing.
- Keep changes additive and minimal.

Validation:
- Add/update backend tests proving:
  - mobile self-service returns photo metadata when the employee has a photo
  - mobile self-service returns null/empty photo data when the employee has no photo
  - any new self-photo endpoint only allows the authenticated employee to access their own image
- Ask Codex to self-check whether the chosen solution is fully aligned with existing web/admin employee photo handling.

Before coding:
- Summarize where the employee photo currently lives in the codebase and why mobile cannot render it yet.
- State whether an existing document/photo flow can be reused directly.

After coding:
- List changed files.
- Explain why the chosen contract is the smallest safe implementation.
- Mention any runtime assumptions that still need local verification.
You are working on the SicherPlan repo.

Task:
Validate and correct the "Marital status" field in the Employees > Private profile section.

Goal:
Decide whether the field should be a free-text textbox or a controlled select, based on the project’s documented source of truth and the current codebase. If the current implementation is wrong, fix it.

Source-of-truth constraints to validate first:
1. In the implementation-oriented data model, hr.employee_private_profile contains marital_status_code, not a free-text marital_status field.
2. The platform-wide modeling convention prefers lookup-backed business lists via core.lookup_value for extensible business classifications/codes.
3. In the proposal, marital status is part of tax/social/family data in the employee personnel file.
4. HR-private profile fields must remain restricted to authorized HR/payroll roles.
5. Do not hardcode business/legal wording unless no validated lookup source exists and the fallback is explicitly approved.

What to do first:
Phase A — Validation
1. Find the real frontend source file(s) responsible for Employees > Private profile and the Marital status control.
2. Find the backend DTO/schema/model for employee private profile.
3. Validate the actual persisted field name:
   - marital_status_code?
   - marital_status?
   - something else?
4. Validate whether there is already an existing lookup source for marital status, such as:
   - core.lookup_value domain
   - workforce catalog endpoint
   - tenant settings or bootstrap seed
   - any shared option registry/composable
5. Print a short validation summary before coding:
   - exact frontend file(s)
   - exact backend file(s)
   - current control type
   - current payload field
   - whether an approved lookup source already exists

Decision rule:
- If the persisted field is a code field such as marital_status_code, implement it as a SELECT, not a textbox.
- Only keep textbox if validation proves the domain intentionally expects unrestricted free text. That would be surprising and must be explicitly justified in the summary.

Required implementation if validation confirms select is correct:
1. Replace textbox with a select control in Private profile.
2. The visible UI must show user-friendly labels.
3. The saved payload must send the code value.
4. Load options from the validated source of truth:
   - existing lookup endpoint/domain if present
   - existing seeded constants if already approved in backend
5. Do NOT invent or duplicate a second source of truth for the same options.
6. Preserve existing role restrictions so only authorized HR/payroll users can edit the field.

Fallback behavior:
- If a legacy stored value exists that is no longer in active options, still display it safely in read/edit mode with a clear legacy/inactive marker.
- If no lookup source exists yet, implement the smallest correct backend+frontend change set needed to support a lookup-backed select, but only after clearly stating that this source was missing.

UX expectations:
1. Label: "Marital status"
2. Control: select
3. Optional placeholder: "Select marital status"
4. Option labels should be clear and business-appropriate
5. Avoid raw code display in the main UI
6. If the field is required by payroll/business rules, enforce validation accordingly
7. If it is optional, allow empty/null cleanly

Important:
- Do not hardcode German legal wording unless the repo already uses an approved option list.
- If you must add seed options because no source exists, first propose the exact domain name and option set, then implement only the smallest approved version.
- Keep the implementation aligned with current app patterns and existing form components.

Tests:
Add or update focused tests for:
1. Private profile renders Marital status as a select
2. Select options load from the validated lookup source
3. Saving persists marital_status_code, not the label text
4. Existing legacy/unknown code still renders safely
5. Unauthorized roles cannot edit HR-private fields

Output format:
1. Validation summary first
2. Then implementation
3. Then final report with:
   - changed files
   - old behavior
   - new behavior
   - source of option values
   - saved payload before/after
   - any backend/schema/lookup gap found
   - manual test steps

Acceptance criteria:
- Marital status is implemented as a select if the schema is code-based.
- UI shows readable labels; backend stores code.
- HR-private access restrictions remain intact.
- No duplicate or invented source of truth is introduced without explicit validation.
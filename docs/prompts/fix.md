You are working in the SicherPlan repository.

Task:
Reduce clutter in Employee Overview by moving heavy editor forms from inline section cards into modal dialogs.

Page:
- /admin/employees
- Existing employee > Overview

User request:
The right-side Overview sections should show lists/status/data and action buttons. Large editor forms should not always be visible inline. Instead, each editor should open in a dialog when the user clicks its related button.

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Existing modal style to reuse:
EmployeeAdminView.vue already has modal/backdrop styling for employee search:
- employee-admin-modal-backdrop
- employee-admin-modal

Reuse this pattern for editor dialogs where possible.

General requirements:
1. Keep the section cards visible and compact.
2. Keep existing lists/registers inline.
3. Replace inline editor forms with action buttons:
   - Add / Edit / Manage
4. Opening an editor button shows a modal dialog.
5. Modal contains the existing editor form fields and submit/cancel/reset actions.
6. Submitting from modal must call the same existing methods and API payloads as before.
7. On successful save:
   - close the modal
   - refresh relevant data
   - stay on Overview
   - preserve activeOverviewSection
8. On validation error:
   - keep modal open
   - show existing feedback/error
9. Do not change backend APIs.

Create a central modal state if useful, for example:
type EmployeeOverviewEditorDialog =
  | 'qualification'
  | 'qualification_proof'
  | 'credential'
  | 'availability'
  | 'absence'
  | 'note'
  | 'group_catalog'
  | 'group_assignment'
  | 'address'
  | 'document_upload'
  | 'document_link'
  | 'document_version'
  | null

const activeEmployeeOverviewEditor = ref<EmployeeOverviewEditorDialog>(null)

Or use separate booleans if simpler, but prefer a maintainable central approach.

Sections to update:

A. Qualifications
Current inline content:
- Existing qualifications list/register
- Qualification editor form
- Proof upload editor

Required:
1. Keep existing qualifications list inline.
2. Add button:
   - "Add qualification"
3. Each existing qualification row should have Edit button or row click opens qualification editor modal.
4. Move qualification create/update form to modal:
   - employee-overview-editor-qualification-modal
5. Proof upload:
   - keep proof list inline for selected qualification if currently useful.
   - add "Upload proof" button that opens proof upload modal:
     employee-overview-editor-qualification-proof-modal
6. Reuse:
   - editQualification(...)
   - resetQualificationDraft()
   - submitQualification()
   - submitQualificationProof()
7. Do not break selectedQualification / selectedQualificationProofs behavior.

B. Credentials
Current inline content:
- credential list/register
- credential editor form

Required:
1. Keep credential list inline.
2. Add "Add credential" button.
3. Existing credential Edit opens credential modal.
4. Move credential editor form to:
   employee-overview-editor-credential-modal
5. Keep "Issue credential badge" action available from list row.

C. Availability
Current inline content:
- availability rules list
- availability editor form

Required:
1. Keep availability list inline.
2. Add "Add availability rule" button.
3. Row click/Edit opens availability modal.
4. Move availability editor to:
   employee-overview-editor-availability-modal
5. Preserve weekday checkbox behavior.

D. Absences
Current inline content:
- absence list
- absence editor form

Required:
1. Keep absence list inline.
2. Add "Add absence" button.
3. Row click/Edit opens absence modal.
4. Move absence editor to:
   employee-overview-editor-absence-modal

E. Notes
Current inline content:
- notes list
- note editor form

Required:
1. Keep notes list inline.
2. Add "Add note" button.
3. Row click/Edit opens note modal.
4. Move note editor to:
   employee-overview-editor-note-modal

F. Groups
Current inline content:
- group catalog editor
- group assignment editor
- current memberships

Required:
1. Keep current memberships list inline.
2. Add button:
   - "Create/update group catalog" or "Manage group catalog"
   opens group catalog modal:
   employee-overview-editor-group-catalog-modal
3. Add button:
   - "Assign group"
   opens group assignment modal:
   employee-overview-editor-group-assignment-modal
4. Existing membership Edit opens group assignment modal with populated draft.
5. Reuse:
   - submitGroup()
   - resetGroupDraft()
   - submitMembership()
   - resetMembershipDraft()
   - editMembership(...)

G. Addresses
Current inline content:
- current address
- address editor form
- address history

Required:
1. Keep current address inline.
2. Keep address history inline.
3. Add button:
   - "Add address"
   opens address modal.
4. Edit current/history address opens address modal.
5. Close validity / mark current can either:
   - open the address modal with appropriate mode, or
   - keep the existing action if it does not require a large inline editor.
6. Move address editor form to:
   employee-overview-editor-address-modal
7. Reuse:
   - editAddress(...)
   - prepareAddressAsCurrent(...)
   - prepareAddressValidityClose(...)
   - submitAddress()
   - resetAddressDraft()

H. Documents
Current inline content:
- document library
- upload new document form
- link existing document form
- add version form

Required:
1. Keep document library inline.
2. Add buttons:
   - "Upload document" -> document upload modal
   - "Link existing document" -> document link modal
   - "Add version" -> document version modal
3. Existing document row "Use document for version" should open document version modal with selected document.
4. Move upload form to:
   employee-overview-editor-document-upload-modal
5. Move link form to:
   employee-overview-editor-document-link-modal
6. Move version form to:
   employee-overview-editor-document-version-modal
7. Reuse:
   - submitEmployeeDocumentUpload()
   - submitEmployeeDocumentLink()
   - submitEmployeeDocumentVersion()
   - useEmployeeDocumentForVersion()
8. Do not change the existing document API.
9. If there is already a document picker pattern elsewhere, do not expand this task unless the raw document ID UX is also being addressed.

I. Modal accessibility
Every modal must:
1. role="dialog"
2. aria-modal="true"
3. labelled by heading
4. have Close/Cancel button
5. close on backdrop click if current app pattern allows it
6. ideally close on Escape
7. use stable data-testid

J. Preserve current section card data
After moving editors:
- cards should show lists/data and action buttons only.
- cards should be significantly shorter.
- no large editor form should be visible until a modal opens.

K. Safety
Do not move Employee file primary editor into modal unless explicitly requested.
Do not move App access into modal unless needed.
This task targets the heavy editors listed by the user:
- Qualifications
- Credentials
- Availability
- Absences
- Notes
- Groups catalog/assignment
- Addresses
- Documents upload/link/version

Expected final behavior:
Overview card lists remain visible.
Editor forms appear only inside modals opened by buttons.
All existing create/update/save actions still work.
You are working in the SicherPlan repository.

This task is part of the Customer New Plan Wizard work:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Important current product decision:
- Order Details is now the first step.
- Planning is not currently part of the first wizard segment.
- Order Documents is an optional step.
- The user must be able to continue without adding any document.

Current concern:
Before entering real data, the Order Documents step should be reviewed and hardened.

Current UI in Order Documents:
- Document title
- Document label
- File
- Document ID
- Document label

This technically supports:
- uploading a new document
- linking an existing document

But the UX is ambiguous:
- upload and link fields are mixed in the same panel
- two fields are both called “Document label”
- there is no explicit Attach/Link button
- the bottom Next button doubles as “save document and continue”
- the user may need to attach multiple order documents

Relevant files to inspect first:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- backend/app/modules/planning/router.py
- backend/app/modules/planning/order_service.py
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Before coding, validate this proposal:
1. Confirm that Order Documents currently uses listOrderAttachments, createOrderAttachment, and linkOrderAttachment.
2. Confirm that Order Documents is optional in this wizard.
3. Confirm that the current bottom Next can attach/link a document and immediately move to the next step.
4. Confirm whether the current UI supports multiple attachments only awkwardly, because Next advances after save.
5. Confirm whether upload and link fields are visually mixed and confusing.
6. Confirm whether Planning Record Documents has similar code, but do not change it in this task unless the branch already shares the same component/logic and the change is safe.
7. State clearly whether this proposal is correct, partially correct, or needs adjustment before changing code.

Goal:
Make the Order Documents step safe and user-friendly for real data entry.

Scope:
- Customer New Plan Wizard Order Documents step only
- Frontend only unless a real API mismatch is discovered
- No backend changes expected
- No route changes
- No changes to Equipment/Requirement behavior
- No unrelated refactor
- Do not make documents mandatory

Required behavior:

A. Keep Order Documents optional
If the user has no documents:
- bottom Next must continue to Planning Record
- no API call should be made
- no error should be shown

If existing order attachments are already present:
- bottom Next must continue
- user should not be forced to add another document

B. Separate upload and link flows visually
Replace the mixed form with two clearly separated sections or modes:

Section 1: Upload new document
Fields:
- Document title
- Upload label
- File

Action:
- Attach uploaded document

Section 2: Link existing document
Fields:
- Existing document ID
- Link label

Action:
- Link existing document

Use clear section titles and helper text.

C. Add explicit Attach/Link buttons
Add inline actions:
- Attach uploaded document
- Link existing document
- Clear document draft

Rules:
- Attach uploaded document calls createOrderAttachment.
- Link existing document calls linkOrderAttachment.
- After successful attach/link:
  - refresh orderAttachments
  - clear the corresponding draft
  - clear persisted order-documents draft
  - stay on Order Documents
  - show success feedback
- The user can then add another document if needed.
- Bottom Next should no longer be the primary document-save action.

D. Bottom Next behavior
Update submitDocumentsStep():

- If there is no file/link draft:
  - return true and allow moving to Planning Record

- If there is a complete upload draft that the user has not attached yet:
  - block Next with a clear localized message:
    “Attach the current document or clear the document draft before continuing.”

- If there is a complete link draft that the user has not linked yet:
  - block Next with a clear localized message:
    “Link the current document or clear the document draft before continuing.”

- If there is a partial draft:
  - block Next with a clear localized message
  - do not silently discard user input

- If user clicks Clear document draft:
  - clear upload/link draft
  - clear persisted draft
  - allow Next afterward

E. Partial draft rules
Define helpers:
- hasOrderDocumentUploadDraftInput()
- hasCompleteOrderDocumentUploadDraft()
- hasOrderDocumentLinkDraftInput()
- hasCompleteOrderDocumentLinkDraft()
- hasAnyOrderDocumentDraftInput()

Suggested validation:
Upload is complete when:
- file content is present
- file_name is present
- title is present

Upload may have optional:
- label

Link is complete when:
- document_id is present

Link may have optional:
- label

Partial examples:
- title entered but no file
- label entered but no file
- file selected but title missing
- link label entered but no document_id

F. File safety and draft persistence
- Do not persist raw File objects.
- Do not persist large base64 content into sessionStorage.
- If the current branch already stores metadata only for file drafts, keep that.
- If the user refreshes after selecting a file, show that file must be reselected if needed.
- Keep document draft storage isolated by tenant/customer/order context.
- Clear draft after successful attach/link or Clear document draft.

G. Existing attachment list
Improve the existing attachments list if needed:
- show document title
- show document id or source label
- show current version/status if available
- keep it read-only unless the branch already has remove/download behavior
- do not invent delete/download behavior in this task

H. Styling
Use existing wizard/admin styling:
- field-stack
- cta-row
- cta-button
- cta-secondary
- sp-customer-plan-wizard-step__panel
- sp-customer-plan-wizard-step__list-row

Add stable test ids:
- customer-new-plan-order-document-upload-title
- customer-new-plan-order-document-upload-label
- customer-new-plan-order-document-file
- customer-new-plan-attach-order-document
- customer-new-plan-order-document-link-id
- customer-new-plan-order-document-link-label
- customer-new-plan-link-order-document
- customer-new-plan-clear-order-document-draft
- customer-new-plan-order-document-list

I. i18n
Add German-first and English fallback keys:
- Order documents are optional
- Upload new document
- Link existing document
- Attach uploaded document
- Link existing document
- Clear document draft
- Upload label
- Link label
- Existing document ID
- Attach or clear the current document before continuing
- Link or clear the current document before continuing
- Select a file and enter a title before attaching
- Enter a document ID before linking
- Document attached
- Document linked
- Document draft cleared

J. Tests
Add or update tests for:

1. Empty Order Documents step:
- no file
- no document_id
- no existing attachments
- Next proceeds to Planning Record
- no create/link API call is made

2. Existing attachments:
- existing orderAttachments render
- Next proceeds without requiring another document

3. Upload:
- file + title + Attach uploaded document calls createOrderAttachment
- stays on Order Documents
- refreshes orderAttachments
- clears draft
- allows adding another document

4. Link:
- document_id + Link existing document calls linkOrderAttachment
- stays on Order Documents
- refreshes orderAttachments
- clears link draft

5. Partial upload draft:
- title without file blocks Next
- file without title blocks Attach
- Clear document draft allows Next

6. Partial link draft:
- label without document_id blocks Next
- Clear document draft allows Next

7. Draft persistence:
- metadata-only draft behavior remains safe
- raw File object is not persisted
- draft clears after successful attach/link

8. Non-regression:
- Order Details selected/create order still works
- Equipment Lines Save/Update-vs-Next still works
- Requirement Lines Save/Update-vs-Next still works
- Planning Record step still receives order_id and remains next after Order Documents

Manual QA checklist:
- Reach Order Documents with no documents and click Next: moves to Planning Record.
- Upload a document using Attach uploaded document: remains on Order Documents and list updates.
- Attach multiple uploaded documents.
- Link an existing document ID: remains on Order Documents and list updates.
- Enter only title and click Next: blocked with clear message.
- Clear draft and click Next: moves to Planning Record.
- Refresh browser on Order Documents: no unsafe file content persisted.
- Confirm no backend call occurs when skipping empty documents.

Final output:
1. Validation summary
2. Whether the proposal was correct or adjusted
3. UX implemented
4. Files changed
5. Tests added/updated
6. Test results
7. Manual QA checklist
8. Remaining limitations

Keep this patch focused.
Avoid unrelated refactors.
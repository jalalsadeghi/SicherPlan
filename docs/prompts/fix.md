You are working in the SicherPlan monorepo.

Bug:
Creating a customer contact crashes in the backend with:

sqlalchemy.exc.DataError: (psycopg.errors.InvalidTextRepresentation)
invalid input syntax for type uuid: "Customer001"

Context:
- In the Contacts form inside:
  web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
  there is a field labeled "Portal user ID".
- The frontend currently allows arbitrary free-text input there.
- But backend/app/modules/customers/service.py validates payload.user_id by calling repository.get_user_account(tenant_id, payload.user_id).
- backend/app/modules/customers/repository.py then queries iam.user_account.id == user_id.
- iam.user_account.id is UUID-backed, and crm.customer_contact.user_id is a FK to iam.user_account.id.
- Therefore typing a value like "Customer001" causes PostgreSQL UUID parsing failure before the app can return a proper validation error.

Goal:
Fix this in the most correct and maintainable way.

Required solution principles:
1. Do NOT allow arbitrary free-text portal user IDs in the customer contact editor.
2. Portal user linkage must be managed by the dedicated portal-access provisioning flow, not by manual free-text entry in Contacts.
3. Backend must still be defensive and never leak a raw SQLAlchemy/psycopg DataError for invalid UUID input.
4. Keep backward compatibility where reasonable, but prefer a safe domain model.

Implement the fix in two layers:

A. Frontend fix
1. In:
   web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

2. Remove or disable manual editing of the "Portal user ID" input in the Contacts create/update editor.
   Preferred behavior:
   - Do not show an editable free-text field for user_id during contact creation.
   - If the contact already has a linked portal user, show it as a read-only info field or small status summary.
   - Add helper text that portal access is managed from the Portal tab, not from Contacts.

3. Ensure normalizeContactDraft() does not send arbitrary user_id text from the contact editor.
   Preferred:
   - On create: omit user_id entirely or send null.
   - On update from contact editor: preserve existing linkage unless there is a deliberate unlink flow elsewhere.
   - Do not silently overwrite an existing valid user_id with junk.

4. Update any labels/help text accordingly.
   For example:
   - rename “Portal user ID” display to “Linked portal user”
   - add help text like “Portal credentials are managed in the Portal tab.”

B. Backend hardening
1. In:
   backend/app/modules/customers/service.py
   and, if helpful,
   backend/app/modules/customers/repository.py

2. Make _validate_contact_constraints() robust:
   - If payload.user_id is provided, first validate that it is a syntactically valid UUID before querying the database.
   - If it is not a valid UUID, raise a clean ApiException 400 with a customer-contact-specific message key, e.g.:
     - code: customers.validation.portal_user_id_format
     - message_key: errors.customers.contact.invalid_user_id_format

3. Do not rely on the database cast error for validation.

4. Ensure repository.get_user_account() is only called with validated UUID values, or defensively handle invalid UUID there too.
   Prefer validation in the service layer.

5. Preserve the existing semantic validation:
   - if UUID format is valid but no matching user exists in this tenant, return the existing invalid scope/not found style business error.

C. Behavioral intent
1. Contacts are customer master data.
2. Portal account creation/linking belongs to the Portal tab / portal-access workflow.
3. The Contacts screen should not be a second, confusing provisioning path.

D. Tests
Add or update tests to cover at least:
1. creating a contact with no user_id succeeds
2. creating a contact with a non-UUID user_id returns a clean 400 ApiException, not a raw DataError
3. updating a contact with invalid non-UUID user_id returns a clean 400
4. existing linked contact remains displayable after frontend changes
5. portal-access flow still owns linking behavior

E. Output format
Before changing code, summarize:
- exact root cause
- frontend files to change
- backend files to change
- chosen UX behavior for the contact form
- validation strategy

Then implement the fix.
After implementation, verify:
- contact creation no longer crashes when the field is filled incorrectly
- no raw SQLAlchemy DataError leaks to the UI
- portal access creation remains in the Portal tab
- frontend builds successfully
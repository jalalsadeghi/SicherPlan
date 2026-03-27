You are working in the SicherPlan monorepo.

Goal:
Redesign the Employees > App access tab so it behaves professionally, clearly, and consistently with the real one-user-per-employee domain model.

Important context from current code:
- Frontend file:
  web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- Backend router:
  backend/app/modules/employees/router.py
- Backend service:
  backend/app/modules/employees/ops_service.py
- Backend service:
  backend/app/modules/employees/service.py
- Backend repository:
  backend/app/modules/employees/repository.py

Current behavior problems:
1. The UI shows a “Create app user” form even when the employee is already linked to an app user.
2. But backend create_access_user() returns the existing link immediately when employee.user_id already exists, so the create form becomes misleading instead of useful.
3. The UI shows current username/email at the top, but there is no way to properly edit the linked IAM user’s username/email or reset the password.
4. The “Existing user” box is technically valid but confusing for normal users. It is really an advanced attach/reconcile tool, not the main happy path.
5. The App access tab should enforce and communicate the rule:
   one employee = at most one linked app user.

Business intent to preserve:
- Each employee can have at most one linked app-access user.
- The main workflow should be:
  a) create access user if none is linked
  b) manage the linked user if one is already linked
- Existing-user attachment should remain possible, but only as an advanced/admin scenario.
- The tab must feel explicit, safe, and hard to misuse.

Required redesign:

A. UX / Information Architecture
1. Split the tab into two clear states:
   State A: no linked app user
   State B: linked app user exists

2. State A (no linked user):
   - Show a primary section:
     “Create app access”
   - Include fields:
     - username
     - email
     - initial password
   - Prefill email from employee.work_email when available.
   - Suggest username intelligently if possible from personnel_no / name, but keep it editable.
   - Show one concise sentence that this creates the single login for this employee.
   - Hide all edit/manage actions that only make sense after a link exists.

3. State B (linked user exists):
   - Replace the create form with a read-only summary card showing:
     - username
     - email
     - full name
     - access enabled
     - role assignment active
   - Add a primary “Manage linked access” section with explicit actions:
     - Update username/email/full_name
     - Reset password
     - Enable/disable access if relevant
     - Detach access (danger action)
   - Do NOT show the create form in this state.
   - Make it impossible in the normal UI to think a second user can be created.

4. “Existing user” section:
   - Keep the functionality, but move it into an advanced/collapsible section.
   - Rename it clearly, for example:
     “Link already-existing IAM account”
   - Add helper text explaining when it should be used:
     migration, recovery, or reconciling an existing account.
   - Make it collapsed by default.
   - Keep the rule that exactly one of:
     user_id / username / email
     must be provided.

5. “Reconcile” section:
   - Keep it only if it has real value.
   - If kept, rewrite the copy so users understand what it does.
   - If it is mostly for repair scenarios, move it next to the advanced section.
   - Do not present it as a normal day-to-day action.

B. Backend capability gap to fix
The current backend supports:
- get_access_link
- create_access_user
- attach_existing_user
- detach_access_user
- reconcile_access_user

But it does NOT support proper management of an already linked user.

Implement backend support for professional access management:
1. Add an endpoint to update the linked access user fields:
   - username
   - email
   - full_name
   Prefer something like:
   PATCH /api/employees/tenants/{tenant_id}/employees/{employee_id}/access-link/user

2. Add an endpoint to reset/set a new password for the linked access user.
   Prefer something like:
   POST /api/employees/tenants/{tenant_id}/employees/{employee_id}/access-link/reset-password

3. If access enable/disable should be controlled separately from detach, add an endpoint for that as well.
   Only do this if the current domain model supports it cleanly.
   Otherwise clarify in UI that detach/remove is the supported deactivation path.

4. Enforce uniqueness properly:
   - username unique per tenant
   - email unique per tenant
   - one employee cannot get a second linked user
   - one user cannot be linked to multiple employees

5. For update/reset flows, add clear business errors and avoid silent no-op behavior.

C. Frontend behavior changes
In EmployeeAdminView.vue:
1. Use accessLink existence to switch between “Create” state and “Manage existing access” state.
2. Do not render the Create form when accessLink.user_id exists.
3. Add a dedicated edit form for the linked user.
4. Add a reset-password form or action.
5. Keep detach as a clearly marked destructive action.
6. Move Existing user attach into an advanced collapsible block.
7. Improve labels and explanatory text for all sections.

D. Copy and labels
Use clear operator-facing language.
Examples:
- “Create app access”
- “Linked app account”
- “Reset password”
- “Link already-existing IAM account”
- “Detach linked account”
- “Advanced repair and migration tools”

Avoid vague labels like:
- “Creation”
- “Existing user”
- “Reconcile”
unless they are accompanied by precise explanations.

E. Validation and UX details
1. When linked access already exists, prevent duplicate-creation paths in the UI.
2. After successful create/update/reset/detach/attach, reload accessLink and employee detail.
3. Show explicit success and error messages.
4. If email is invalid or already taken, surface the exact backend message.
5. Keep the layout visually consistent with the rest of the employee detail tabs.

F. Tests
Add/adjust tests for:
1. employee with no linked user -> create form visible
2. employee with linked user -> manage form visible, create form hidden
3. update linked username/email/full_name
4. reset password for linked user
5. cannot create second linked user for same employee
6. attach-existing flow works only when one identifier is provided
7. duplicate username/email conflicts are handled cleanly
8. detach removes link and UI returns to create state

Output format before coding:
1. summarize current root UX problems
2. list backend endpoints to add/change
3. list frontend sections to remove/replace
4. describe final UX for:
   - no linked user
   - linked user exists
   - advanced attach/reconcile

Then implement the full redesign.
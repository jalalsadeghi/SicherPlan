You are working in the SicherPlan monorepo.

Goal:
Refine the Customer Portal so that a customer portal user can clearly understand:
- what they are allowed to view
- what they are allowed to do
- what is not yet available
- what is intentionally hidden by release/scope/privacy rules

Current issue:
The portal loads, but the user still cannot tell what their real permissions are.
The page currently shows context and dataset cards, but not a clear capability model.
This creates confusion about whether the customer can only view data, can download documents, can add watchbook entries, or should expect more actions.

Relevant files to inspect:
Backend:
- backend/app/modules/customers/portal_router.py
- backend/app/modules/customers/portal_service.py
- backend/app/modules/customers/repository.py
- backend/app/modules/customers/schemas.py
- backend/app/modules/iam/seed_permissions.py

Frontend:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerPortalAccessView.vue
- customer portal API files used there
- portal helper files used there

Product intent to preserve:
Customer Portal User is an external customer-side role.
They should only see their own customer-scoped, released outputs.
They must not see internal staffing detail, hidden personal names by default, or other customers’ data.
They should be able to review released orders, schedules, watchbooks, timesheets, invoices, reports, and history.
Customer-side watchbook entry should only be possible if explicitly enabled by policy.

Required work:

A. Make capabilities explicit in backend
1. Extend the customer portal context response to include a structured capabilities object.
   Add something like:
   - can_view_orders
   - can_view_schedules
   - can_view_watchbooks
   - can_add_watchbook_entries
   - can_view_timesheets
   - can_download_timesheet_documents
   - can_view_invoices
   - can_download_invoice_documents
   - can_view_reports
   - can_view_history
   - personal_names_visible
   - released_only
   - customer_scoped_only

2. Also include availability/reason metadata where useful, for example:
   - availability_status per dataset
   - why something is empty/pending/not connected/not released

3. Ensure the capabilities are derived from real backend logic, not hardcoded UI guesses.

B. Enforce optional write behavior correctly
1. Review customer watchbook entry creation:
   POST /api/portal/customer/watchbooks/{watchbook_id}/entries
2. The handbook says customer-side watchbook entries are optional and should only work if explicitly enabled by the tenant.
3. Add a proper backend policy/capability gate for this action.
4. Do not rely only on whether the UI happens to show a form.
5. If no explicit setting exists yet, introduce a safe capability source and default it conservatively.

C. Improve frontend clarity
In CustomerPortalAccessView.vue:
1. Add a visible “Your portal access” / “What you can do here” section near the top.
2. Show a concise capability summary for the current customer user:
   - View released orders
   - View released schedules
   - View released watchbooks
   - Download released timesheets
   - Download released invoices
   - View released reports
   - Review customer-visible history
   - Add watchbook entries (only if enabled)
3. Show these as clear status rows or badges:
   - Available
   - Read-only
   - Enabled
   - Not enabled
   - Pending integration
   - No released data yet

4. Replace raw technical UUID-heavy summary fields where they are not useful to the end user.
   For example, do not prominently show raw tenant UUID and raw allowed customer scope UUID as primary business information.
   Keep technical details only in an advanced/debug area if needed.

5. For each dataset card, improve the empty/pending copy:
   - distinguish “no released data yet”
   - distinguish “module not connected yet”
   - distinguish “feature not enabled for your portal”
   - distinguish “documents available for download” vs “view only”

6. Only render the watchbook entry form if can_add_watchbook_entries is true.
   Otherwise show a short explanation that customer-side watchbook entries are not enabled for this portal.

D. Align implementation with docs and API surface
1. Verify the Customer Portal matches the intended scope from the uploaded docs:
   - own customer only
   - released outputs only
   - personal names hidden by default
   - history visible
   - watchbook entries optional
2. Do not add internal/customer-admin features into the portal.

E. Tests
Add or adjust tests for:
1. customer portal context returns capabilities
2. read-only customer portal user can access released datasets
3. watchbook entry is blocked when not enabled
4. watchbook entry is allowed only when explicitly enabled
5. customer portal never exposes other customers’ data
6. personal names remain hidden unless release policy allows them

F. Output format before coding
1. summarize current gap between intended customer portal access and current UI
2. list backend schema/router/service changes
3. list frontend UI changes
4. define final customer-visible capability model

Then implement the improvement.
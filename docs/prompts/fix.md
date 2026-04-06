You are working in the public repository:
jalalsadeghi/SicherPlan

Goal:
Bring the "Create new address" workflow from admin/customers into admin/planning for all planning entities that use the "Address record ID (optional)" select/search field.

Context:
In the current planning admin page, the user can select an existing customer address via the address select/search component, which is good.
However, there is no way to create a new address inline when the required address does not yet exist.
This must be fixed by reusing the UX pattern already implemented in admin/customers:
- a button next to the address-link editor
- opening a dialog/modal
- creating a new shared address for the currently selected customer
- refreshing the planning address options
- auto-selecting the newly created address after success

Reference implementations to inspect first:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/components/planning/PlanningAddressSelect.vue
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/customers.ts

Primary planning entities that must support this:
- site
- event_venue
- trade_fair
- patrol_route

Important constraint:
Do not invent a second address-creation workflow.
Reuse the customer-address creation flow and API pattern already used in admin/customers.

What to implement:

1) Add "Create new address" action in planning
In PlanningOpsAdminView.vue, for every address-using planning form:
- site -> address_id
- event_venue -> address_id
- trade_fair -> address_id
- patrol_route -> meeting_address_id and/or address-related selector used there

Add a secondary button near the address select field:
- label: "Create new address"
- disabled when no customer is selected
- disabled while create-address action is in progress

The action must open a modal dialog, not navigate away.

2) Reuse the existing customers-style modal pattern
Mirror the existing admin/customers address create modal UX as closely as possible:
- modal backdrop
- modal card
- address fields:
  - street_line_1
  - street_line_2
  - postal_code
  - city
  - state
  - country_code
- primary action: create address
- secondary action: cancel

Do not make the user leave admin/planning to create an address.

3) Create address for the currently selected customer
When the modal opens:
- it must know which customer is currently selected in the planning draft
- if there is no selected customer, the action must stay disabled or show a clear validation/help message

On submit:
- use the same shared-address create API already used in admin/customers
- create the address under the currently selected customer
- keep the implementation tenant-scoped and access-token aware
- after success:
  - refresh the planning address options for that customer
  - set the newly created address as the selected value in the relevant planning field
  - close the modal
  - show success feedback using the shared toast system, not a fixed inline alert

4) Keep PlanningAddressSelect focused
Do not overload PlanningAddressSelect.vue with full modal/business logic unless there is a very clean reason.
Prefer one of these approaches:
- keep PlanningAddressSelect as the select/search field only, and render the "Create new address" button + modal in PlanningOpsAdminView.vue
OR
- create a thin wrapper component around PlanningAddressSelect if that results in cleaner code

But avoid duplicating large chunks of address-create code multiple times.

5) Make the flow entity-aware
The new address creation must work correctly in these cases:
- creating a new site
- editing an existing site
- creating a new event venue
- editing an existing event venue
- creating a new trade fair
- editing an existing trade fair
- creating a new patrol route
- editing an existing patrol route

It must always write back to the correct field:
- address_id for site/event_venue/trade_fair
- meeting_address_id (or whichever field is actually used) for patrol_route

6) Validation and UX requirements
- If no customer is selected, the button must not open a broken modal.
- Show a clear helper text or disabled reason when customer selection is required first.
- Preserve the existing select/search behavior.
- Keep layout and styling consistent with the legacy admin workspace design.
- Preserve mobile/responsive behavior.
- Do not regress existing create/edit flows.

7) Feedback behavior
Use the existing shared toast feedback pattern already used by admin/customers:
- success toast after address creation
- error toast on failure
- bottom-right placement
- auto-dismiss
Do not introduce a persistent fixed alert banner.

8) Code cleanup
- Extract shared address-create draft/reset helpers if needed
- Avoid copy-pasting large customer-page blocks verbatim without adaptation
- Keep the planning page readable
- Remove dead code if any temporary address-create attempts already exist

9) Tests
Add or update tests covering at least:
- "Create new address" button appears for address-enabled planning entities
- button is disabled when no customer is selected
- clicking the button opens the modal
- submitting valid address data calls the shared-address create API
- after success, the address options refresh and the new address becomes selected
- modal closes after successful create
- error path shows toast feedback and keeps modal open if appropriate

10) Deliverables
Return:
- code changes
- updated tests
- a short summary of which planning entity forms now support inline address creation
- any assumptions made about patrol-route address field mapping

Technical guidance:
- Prefer reusing the same API method already used in CustomerAdminView for shared customer addresses
- Keep tenant scope and access token handling consistent with the existing planning page conventions
- Reuse the same modal field structure and address payload shape from admin/customers where possible
- Do not change unrelated planning business logic
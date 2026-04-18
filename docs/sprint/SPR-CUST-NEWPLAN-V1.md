Sprint Brief for Codex
Sprint ID: SPR-CUST-NEWPLAN-V1
Sprint Name: Customer New Plan Wizard V1

Context
You are working in the SicherPlan repository.

This sprint introduces a new customer-scoped guided creation flow called "New Plan" inside Customer > Plans.
The purpose is to make plan creation much easier for the Tenant Administrator by guiding them from Planning Setup through Order/Planning creation, Shift Planning, and finally into Staffing Coverage, without changing or removing the existing canonical Operations & Planning workspaces.

Important:
This sprint is additive only.
Do NOT replace, remove, or redesign the existing Operations & Planning routes or workspaces.
The canonical workspaces must remain intact and usable:
- Planning Setup
- Orders & Planning Records
- Shift Planning
- Staffing Coverage

This wizard is a customer-scoped orchestration layer, not a replacement for those modules.

Critical operating assumption
The checked-out branch may not exactly match public main.
Before coding, validate the actual branch state first.
Do NOT assume GitHub main is the source of truth for the current working branch.

At the beginning of this sprint, validate:
1. whether Customer > Plans already exists in the checked-out branch
2. which file currently renders the Plans tab
3. whether a Customer Dashboard tab is already wired in the branch
4. what the actual route and component structure is for:
   - Customers
   - Planning Setup
   - Orders & Planning Records
   - Shift Planning
   - Staffing Coverage
5. which existing APIs and forms are already reusable for this flow

Output a short validation summary before implementation begins.

Business intent
The Tenant Administrator should be able to start from one selected customer, click "New Plan", and complete the major setup path in one guided flow:
Planning Setup -> Order -> Planning Record -> Shift Plan -> Series Generation -> redirected Staffing Coverage.

Do not force the user to manually navigate through multiple unrelated pages during this flow.

Role scope for V1
This sprint is for Tenant Administrator only.
Treat "Admin Tenant" as the Tenant Administrator role.
Do not broaden this feature to other roles in V1 unless the existing branch already has a tightly controlled compatible permission pattern.

Core domain rule
A "Plan" is not a single table or a single aggregate.
In this project, "Plan" is business shorthand for a guided creation flow across multiple existing aggregates:
customer -> order/project -> planning record -> shift plan / series -> staffing coverage

Do not collapse this into one fake monolithic backend object.

Non-negotiable architecture rules
1. Preserve canonical module ownership and aggregate boundaries.
2. Reuse the existing APIs, services, and forms wherever possible.
3. Do NOT create a giant backend endpoint like "create_full_plan_in_one_call".
4. Save real records step by step.
5. Each Next action should persist the current step before moving forward.
6. Previous must allow the user to return and edit already-saved earlier steps.
7. The wizard must remain customer-scoped.
8. The existing Operations & Planning menu and routes must remain untouched.
9. The final staffing work must still happen in the canonical Staffing Coverage page.
10. Use "Previous" for backward navigation, not "Preview".

Primary sprint goal
Add a Customer-scoped New Plan Wizard, launched from Customer > Plans, that allows a Tenant Administrator to complete the guided creation flow from Planning Setup to Generate Series, and then redirects them into the existing Staffing Coverage page prefiltered to the newly created planning context.

Recommended route model
Use a hidden route under Customers, for example:
- /admin/customers/new-plan?customer_id=<id>

If the checked-out branch uses a different but consistent route convention, adapt to that convention.
Do not add a new sidebar item.
Do not expose a new top-level menu group.

Wizard UX model
Build a dedicated full-page wizard view, not a giant inline expansion inside the existing Plans tab.
The Plans tab should remain the entry point.
The wizard page should contain:
- breadcrumb
- page title
- selected customer summary
- stepper/progress indicator
- step content area
- bottom action bar with:
  - Cancel
  - Previous
  - Next
- in the final step:
  - Generate Series & Continue

From step 2 onward, Previous must be available.
Cancel should protect against accidental exit if there are unsaved local changes.

Required wizard steps
Implement the guided flow as these steps:

Step 1: Planning
- User selects one planning entity family:
  - Sites
  - Event Venues
  - Trade Fairs
  - Patrol Routes
- Recommended UX:
  - Use Existing
  - Create New
- The step must remain customer-scoped where applicable.
- Persist:
  - planning_entity_type
  - planning_entity_id
  - planning_mode_code derived from the selected entity family

Step 2: Order Details
- Create or edit the customer order/project details
- customer_id must come from the selected customer context and must not be freely changed
- Persist:
  - order_id

Step 3: Equipment Lines
- Add equipment lines to the order
- Include a "New Equipment" action
- New Equipment must open a dialog and create a canonical equipment item in the Planning Setup domain, not a fake local-only record
- After successful creation, refresh the selection source and continue in the wizard

Step 4: Requirement Lines
- Add requirement lines to the order
- Include a "New Requirement" action
- New Requirement must open a dialog and create a canonical requirement type in the Planning Setup domain if that is how the checked-out branch models this concept
- Validate the actual branch semantics before finalizing this mapping
- After successful creation, refresh the selection source and continue in the wizard

Step 5: Order Documents
- Add or link documents to the order
- Keep order documents clearly separate from planning-record documents

Step 6: Planning Record Overview
- Create or edit the planning record
- It must be linked to the existing order_id
- planning_mode_code should remain consistent with the entity selected in Step 1
- Persist:
  - planning_record_id

Step 7: Planning Record Documents
- Add or link planning-record documents
- Keep these separate from order documents

Step 8: Shift Plan
- Create or edit the shift plan
- Persist:
  - shift_plan_id

Step 9: Series and Exceptions
- Create or edit the series configuration and any exception-related inputs
- Include a "New Template" action
- New Template must open a dialog and create a canonical shift template in the Shift Planning domain
- On the final action, "Next" becomes:
  - Generate Series & Continue
- This action must save the series step and trigger the existing generate-series behavior
- Persist:
  - series_id
  - generated shift context, if available

Final step / handoff behavior
After successful Generate Series:
- Redirect the user to the existing Staffing Coverage page
- Do NOT embed Staffing Coverage inside the wizard
- Do NOT create a new staffing page

The destination page must be prefiltered to the newly created plan context using the most truthful existing filters available in the checked-out branch.
Prefer:
- planning_record_id
- date_from
- date_to
- planning_mode_code

Do not invent a fake customer-only staffing page.
The goal is to land the user inside the real Staffing Coverage workspace with a narrowed scope.

State model requirements
Create a wizard state model that persists the working IDs and allows previous-step editing without re-creating records.

Minimum state contract:
- customer_id
- planning_entity_type
- planning_entity_id
- planning_mode_code
- order_id
- planning_record_id
- shift_plan_id
- series_id
- current_step
- completion state by step

Behavior rules:
- Step entry must be guarded by completed prerequisites
- Returning to a previous step must load the saved record and update it, not create duplicates
- Switching customers must reset the wizard state safely
- Direct route access without a valid customer context must show a controlled invalid-state UI

UI and design rules
1. Reuse existing project layout and design patterns
2. Reuse the nearest consistent Customers / Planning / Vben / Ant Design patterns already present in the branch
3. No new UI library
4. No broad visual redesign of existing Planning pages
5. Keep the wizard responsive
6. Support both light and dark mode if the branch supports both
7. Use stable test IDs for new major controls and step containers

Dialog requirements
You must implement three quick-create dialogs in V1:
- New Equipment
- New Requirement
- New Template

Rules for dialogs:
- Open in-place without leaving the wizard
- Validate required fields
- Save through the canonical module/domain
- Refresh the source selector after success
- Return focus cleanly to the wizard step
- Do not create fake temporary data that never persists

Permissions and access
V1 must be restricted to Tenant Administrator.
Implement:
- button visibility guard for "New Plan"
- route guard for the wizard route
- guard behavior for quick-create dialogs
- safe unauthorized handling

If the checked-out branch already has a more granular compatible permission model that is clearly aligned with Tenant Administrator access, you may reuse it.
Do not broaden access casually.

Internationalization
All new strings must be i18n-driven.
Use:
- German first
- English fallback
Follow the branch’s existing i18n structure and naming style.

Suggested i18n groups:
- customerPlansWizard.title
- customerPlansWizard.steps.*
- customerPlansWizard.actions.*
- customerPlansWizard.dialogs.*
- customerPlansWizard.errors.*
- customerPlansWizard.success.*
- customerPlansWizard.handoff.*

Implementation strategy
Implement this sprint in the following execution order:

Phase 1
- Validate checked-out branch state
- Identify reusable forms, APIs, and route patterns
- Confirm the current file map

Phase 2
- Add New Plan entry point in Customer > Plans
- Add hidden wizard route
- Build wizard shell, stepper, and footer action bar

Phase 3
- Build wizard state/orchestration layer
- Add step guards and previous-step edit behavior

Phase 4
- Implement Planning + Order + Equipment + Requirement + Order Documents

Phase 5
- Implement Planning Record + Planning Record Documents + Shift Plan + Series and Exceptions

Phase 6
- Implement Generate Series handoff into Staffing Coverage

Phase 7
- Apply permission guard, i18n, non-regression checks, and tests

Definition of done
This sprint is complete only if all of the following are true:
1. A Tenant Administrator can open Customer > Plans and click New Plan
2. The wizard opens in a customer-scoped route
3. The step flow works from Planning through Series Generation
4. Each Next persists the current step
5. Previous allows editing already-saved earlier steps
6. New Equipment / New Requirement / New Template dialogs work and return to the wizard
7. Generate Series executes and redirects into the existing Staffing Coverage page
8. The destination staffing page is correctly prefiltered to the newly created planning context
9. No canonical Operations & Planning workspace is removed or regressed
10. Tests cover the critical happy path and key non-regression scenarios

Testing expectations
Add or update tests for at least:
- New Plan button visibility for Tenant Administrator
- Hidden route access and invalid customer handling
- Step navigation
- Save-on-next behavior
- Previous and edit flow
- New Equipment dialog
- New Requirement dialog
- New Template dialog
- Generate Series redirect/handoff
- Unauthorized access behavior
- Non-regression for existing Customers and Planning pages

Required final output from Codex for this sprint
When reporting progress or completion, always include:
1. Branch validation summary
2. Architecture choices and reuse strategy
3. Changed files
4. What was intentionally not changed
5. Test results
6. Any real blockers or limitations still present

Guardrails
- Avoid unrelated refactors
- Avoid endpoint redesign unless a truly blocking mismatch is discovered
- Do not delete or replace existing Planning routes
- Do not invent new business semantics for “plan”
- Do not merge unrelated Customers and Planning ownership rules
- Keep the wizard thin, guided, and orchestration-focused

This sprint brief is the governing source of truth for V1.
Subsequent task prompts should implement this sprint story by story, not as one uncontrolled broad rewrite.
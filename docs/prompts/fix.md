You are working on the SicherPlan repo.

Task:
Validate and, if needed, implement planning-level team creation and assignment-to-team linking in the Planning Staffing workspace.

Important:
Before changing code, first validate the proposal below against:
1) current repo code,
2) current OpenAPI/backend contracts,
3) the uploaded project source-of-truth docs:
   - SicherPlan_Implementation_Data_Model_Spec.pdf
   - SicherPlan API.pdf
   - SicherPlan_User_Manual_Operational_Handbook.pdf
   - SicherPlan_Role_Based_Page_Coverage_Map.pdf
   - SicherPlan_Proposal.pdf

Expected validation points:
- P-04 / Staffing Board & Coverage is the canonical workspace for teams, team members, assignments, validations, and coverage.
- A planning-level team is valid when ops.team uses planning_record_id and leaves shift_id null.
- role_label belongs to ops.team_member, not to ops.team.
- notes must NOT be assumed on ops.team unless the real backend schema/OpenAPI currently supports it.
- assignments should be linkable to a team via team_id without breaking existing validation and audit behavior.

What I need from you:
Phase A — Validation summary
1. Inspect the current implementation and print a short validation summary:
   - confirmed assumptions
   - rejected assumptions
   - missing backend or frontend pieces
   - exact files/pages currently responsible for planning staffing
2. If an equivalent team-management UI already exists somewhere else, DO NOT duplicate it. Reuse and integrate it into the correct workflow.

Phase B — Implement the missing capability if validation confirms it is absent
Implement planning-level team management in the current staffing workspace.

Target workspace:
- the current planning staffing route / module used for Staffing Board & Coverage
- keep it aligned with the current shell/module-registry structure

Required behavior:
1. Add team CRUD wiring
   - list teams
   - create team
   - read team
   - update team

2. Add team-member CRUD wiring
   - list team members
   - create team member
   - update team member

3. Support planning-level team creation
   - required: name
   - required: planning_record_id
   - optional: shift_id (null for planning-level team)
   - optional: team_lead_employee_id OR team_lead_worker_id
   - exactly one team lead actor max
   - DO NOT place role_label on the team payload unless backend explicitly requires it
   - DO NOT send notes unless backend schema confirms support

4. Add UI affordance in the staffing page
   - a visible action like “Create team” or “Create planning team”
   - when the user is already filtered by planning_record_id, prefill that value
   - allow shift to remain empty/null for planning-level teams
   - show existing teams relevant to the selected planning record
   - clearly distinguish planning-level teams from shift-level teams

5. Add team-member editor
   - actor must be either employee OR subcontractor_worker
   - support role_label on team member
   - support valid_from / valid_to if backend supports them
   - prevent invalid mixed actor payloads

6. Add assignment-to-team linking
   - from the staffing board / assignment detail, allow assigning or changing team_id
   - preserve all existing assignment validations and override logic
   - do not bypass qualification/document/customer-block/double-booking rules

7. Preserve guardrails
   - tenant scoping
   - role-scoped visibility
   - audit-safe behavior
   - no changes that bypass finance.actual_record workflow
   - no schema invention

Likely code areas to inspect first:
- current module registry / shell registration for planning staffing
- current PlanningStaffingCoverageView.vue
- current planning staffing API wrapper / typed client
- any legacy planning staffing view still in use
- any backend DTO/router/schema for planning teams, team members, and assignments

Implementation details:
- prefer small, localized changes
- reuse existing composables, modal patterns, form patterns, and action guards
- keep naming consistent with existing SicherPlan modules
- if backend DTOs already exist but frontend wrappers are missing, only add missing wrappers
- if backend endpoints are missing fields needed for planning-level team UX, propose the smallest backend change set and implement it only if clearly necessary

Tests:
Add or update focused tests for:
- planning-level team creation with planning_record_id and null shift_id
- team-member creation with role_label
- linking assignment.team_id
- rejecting invalid dual-actor team-member payloads
- preserving existing assignment validation flows

Deliverables:
1. Validation summary first
2. Then implementation
3. Then a final report containing:
   - changed files
   - what was missing before
   - what was added
   - any backend/schema mismatch found
   - any field that was intentionally NOT implemented because it was not validated in schema/OpenAPI
   - short manual test steps

Acceptance criteria:
- A dispatcher in Staffing Board & Coverage can create a planning-level team for a selected planning record.
- The dispatcher can add team members with role_label.
- Assignments can be linked to that team.
- Existing staffing coverage, validations, outputs, and dispatch behavior keep working.
- No unsupported fields are invented.
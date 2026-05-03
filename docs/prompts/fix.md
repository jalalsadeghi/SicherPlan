You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

You must investigate and design a new 8th step for the customer order workspace wizard:
`Assignments`

Context:
- The customer detail page at `admin/customers?customer_id=...` has an order workspace wizard used to create/edit orders.
- The wizard currently has 7 steps:
  1. Order details
  2. Order scope & documents
  3. Planning record
  4. Planning documents
  5. Shift plan
  6. Series & exceptions
  7. Demand groups
- A new step must be added after `Demand groups`:
  8. Assignments
- This new step should be inspired by the existing staffing logic in `admin/planning-staffing`, but it is not a copy-paste of that page.
- The goal is to let the user prepare staffing assignments for the generated shifts of the order in a much more user-friendly, calendar-first workflow.

High-level UX target:
- Left side: a narrow, scrollable candidate list of workers.
- Right side: a calendar grid that covers the project execution dates.
- Users should be able to assign a candidate very easily, ideally via drag-and-drop from the left list into the calendar area.
- The left list must show only suitable candidates for the currently selected demand-group context and other active filters.
- The calendar must visually communicate daily staffing state using the same business meaning as `Total shifts`, `Fully covered`, `Warning state`, and `Blocked` from `admin/planning-staffing`.

Your first task is investigation and solution design only. Do not immediately implement before validating the architecture and dependencies.

You must inspect at least these areas:
- Existing order workspace / customer order wizard UI and step infrastructure.
- Existing demand-groups step implementation.
- Existing staffing-coverage / planning-staffing screens, APIs, models, and assignment logic.
- Existing concepts for:
  - demand groups
  - staffing actions / assignments
  - actor kind
  - workforce scope
  - employee qualifications / function types
  - availability / leave / absences
  - partner releases / subcontractor handling
  - project execution date ranges
  - editability / locking rules after later workflow steps
- Existing API contracts and DTOs related to planning staffing and assignments.
- Existing localization keys and reusable UI components.

Business requirements for the new Assignments step:
1. Add a new wizard step `Assignments` after `Demand groups`.
2. The step works on generated shifts that belong to the current order / selected shift plan / selected series scope.
3. Left candidate rail:
   - narrow width
   - vertically scrollable
   - each row shows at least profile/avatar, personnel number, first name + last name
   - may also show badges such as actor kind, team/group, qualification match, availability quality, and suitability score if helpful
4. Candidate filtering and ranking logic:
   - candidates must be filtered by suitability for the selected demand group
   - they must satisfy required qualifications / permissions / function-type compatibility
   - they must respect actor kind and workforce scope
   - if a user selects a group/team filter, only candidates in that group/team should be shown
   - ranking must prefer workers who can cover more of the project’s required dates
   - ranking must also consider other relevant priorities from project logic, such as fewer conflicts, better qualification fit, availability, and similar factors you find in the codebase
5. Right calendar area:
   - default visible month = project start month
   - previous/next month navigation
   - only the dates inside the project execution window are active; all other dates are visually disabled
   - days must be color-coded based on staffing state derived from the same semantics as planning-staffing summary states
   - calendar cells should present assignment-related information in a compact and elegant way
6. Assignment interaction:
   - the user can drag a candidate onto the calendar / day cells to create assignments for eligible days
   - the system should only place the candidate on days where they are eligible and available
   - days where the worker is on leave, unavailable, already booked on conflicting work, or otherwise ineligible must not accept the drop, or must clearly block it
   - this should be as simple and user-friendly as possible
7. Because the user described only the core idea, you must identify missing details and propose the most standard, scalable, and beautiful solution.
8. The design must be consistent with the project’s existing patterns, not a disconnected one-off screen.

You must produce a discovery report before implementation covering:
A. Current relevant files/modules/components/routes/apis.
B. Reusable existing backend logic and frontend components that should be leveraged.
C. Gaps that require new backend endpoints / DTOs / services.
D. Gaps that require new frontend components / composables / stores.
E. Recommended UX structure for the Assignments step.
F. Recommended data model / API contract for candidate list, calendar summary, and drag-drop assignment mutations.
G. Suggested editability/locking rules for the new step relative to previous steps.
H. Suggested validations, conflict handling, and empty states.
I. Suggested test plan.
J. Whether implementation should be split into multiple tasks/commits.

Important design expectations:
- Prefer reuse of existing staffing domain logic rather than inventing a second staffing system.
- Reuse existing summary semantics and assignment concepts from `admin/planning-staffing` whenever reasonable.
- Keep the UI compact and professional.
- Make the calendar understandable at a glance.
- Make candidate suitability explainable.
- Avoid heavy or fragile interactions if the codebase already has a simpler robust pattern.
- If direct drag-and-drop should be complemented by click-based assignment for accessibility or reliability, propose that too.

Deliverable for this task:
1. A concise but concrete implementation plan.
2. A list of files likely to change.
3. Proposed API additions/changes.
4. Proposed UI structure.
5. Risks and assumptions.
6. A recommended split into the next implementation tasks.

Output format:
- Rooted findings
- Current reusable building blocks
- Missing pieces
- Proposed solution architecture
- Proposed UX behavior
- Proposed editability / lock behavior
- Proposed API contract
- Proposed task split
- Files likely to change
- Risks / open questions
- Recommendation on whether to proceed exactly as proposed or adjust the design

Do not make product-code changes in this task until the investigation is complete and the proposal is self-validated.

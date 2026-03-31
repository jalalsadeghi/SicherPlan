You are working in the SicherPlan repository.

Task title:
Fix Planning Orders > Planning records form so UUID/reference fields use proper selectors instead of raw text inputs.

Problem:
In the Planning Orders page (`/admin/planning-orders`), the "Planning records for order" form still uses plain text inputs for several reference/ID fields that users cannot realistically enter by hand.

Current problematic fields in `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`:
- dispatcher_user_id
- parent_planning_record_id
- status
- event_detail.event_venue_id
- site_detail.site_id
- trade_fair_detail.trade_fair_id
- trade_fair_detail.trade_fair_zone_id
- patrol_detail.patrol_route_id

Observed issue:
These fields currently expect UUID-like IDs or internal references, but are rendered as raw `<input>` fields.
This is poor UX and leads to invalid/manual entry patterns.

Important backend context:
From `backend/app/modules/planning/schemas.py`:
- PlanningRecordCreate:
  - parent_planning_record_id: str | None
  - dispatcher_user_id: str | None
  - planning_mode_code: str
  - event_detail.event_venue_id is required for event mode
  - site_detail.site_id is required for site mode
  - trade_fair_detail.trade_fair_id is required for trade_fair mode
  - patrol_detail.patrol_route_id is required for patrol mode
- PlanningRecordUpdate:
  - status exists here
- PlanningRecordCreate does NOT define a `status` field
- release_state is already modeled separately for order/planning release workflows

Existing repo assets that should be reused:
- `web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts`
  already provides list endpoints for:
  - requirement_type
  - equipment_item
  - site
  - event_venue
  - trade_fair
  - patrol_route
- `PlanningOrdersAdminView.vue` already uses good lookup UI patterns for:
  - customer_id
  - requirement_type_id
  - patrol_route_id
  via Select / search-select style controls
- `PlanningOpsAdminView.vue` confirms those planning setup entities are real and listable through the planning admin API.

Goal:
Refactor the Planning records form so reference fields are selected from valid records instead of manually typed as IDs.

Implementation requirements

A) Replace UUID/manual reference fields with selectors
1. In `PlanningOrdersAdminView.vue`, replace these raw text inputs with controlled selectors:

- dispatcher_user_id
- parent_planning_record_id
- event_detail.event_venue_id
- site_detail.site_id
- trade_fair_detail.trade_fair_id
- trade_fair_detail.trade_fair_zone_id
- patrol_detail.patrol_route_id

2. Preferred control type:
- searchable select / combobox when option lists may grow
- normal select only if a searchable select is too heavy for the current local setup

3. Display labels must be human-friendly, not UUID-only.
Examples:
- event venue: `VENUE_NO — Name`
- site: `SITE_NO — Name`
- trade fair: `FAIR_NO — Name`
- patrol route: `ROUTE_NO — Name`
- parent planning record: `Planning name · YYYY-MM-DD - YYYY-MM-DD`
- dispatcher: `Full name · username/email` or best available readable label

B) Reuse existing planning setup APIs where possible
4. For planning setup entities, reuse `planningAdmin.ts` list APIs instead of inventing duplicate lookup sources:
- event_venue
- site
- trade_fair
- patrol_route

5. Filter these options by selected customer when appropriate.

6. For `trade_fair_zone_id`, make it dependent on selected `trade_fair_id`:
- no free text
- disabled until a trade fair is selected
- load/select zones only for the selected trade fair

C) Parent planning-record selector
7. Replace `parent_planning_record_id` with a select/search-select.
8. The option set should be filtered at least by:
- same tenant
- ideally same order_id
9. Exclude the currently edited planning record from the parent options to avoid self-parenting.
10. Keep backend validation as source of truth for any remaining parent constraints.

D) Dispatcher selector
11. Replace `dispatcher_user_id` with a search-select.
12. First inspect the repo for an existing user/employee lookup source that can be safely reused.
13. If a suitable existing lookup already exists, use it.
14. If no suitable lookup exists, add a minimal read-only lookup path for dispatcher candidates.
Requirements for this lookup:
- tenant-scoped
- returns readable labels for users
- does not expose unrelated private HR data
- suitable for assignment in planning records

E) Status field cleanup
15. The `status` field is currently misleading:
- frontend includes it in the form and payload
- backend `PlanningRecordCreate` does not define it
- release workflow already uses `release_state` separately

16. Fix this properly:
- remove `status` from the create form
- do not send it in create payload
- if lifecycle editing is actually needed for existing records, only show it in edit mode
- if shown in edit mode, render it as a dropdown, not free text

17. Do not confuse `status` with `release_state`.
Release state remains handled separately by the existing release actions/workflow.

F) UX details
18. Add proper placeholders like:
- “Select dispatcher”
- “Select parent planning record”
- “Select event venue”
- “Select site”
- “Select trade fair”
- “Select trade fair zone”
- “Select patrol route”

19. Disable dependent selectors when prerequisites are missing:
- disable event venue until customer is chosen
- disable site until customer is chosen
- disable trade fair until customer is chosen
- disable trade fair zone until trade fair is chosen
- disable parent planning record until order exists / is selected
- disable dispatcher selector while loading

20. Show inline helper text or empty-state hints when no options exist, instead of leaving a confusing empty selector.

G) Payload correctness
21. Keep backend payload field names unchanged.
22. Ensure selectors submit actual IDs, not labels.
23. Remove any create-payload status field that backend does not support.
24. Keep existing release-state behavior intact.

H) Testing
25. Add/update frontend tests for:
- event venue field is no longer a raw text input
- parent planning-record field is no longer a raw text input
- status field is hidden in create mode or rendered correctly in edit mode
- selectors load options from the correct sources
- trade fair zone selector depends on selected trade fair
- payload submission sends IDs correctly
- create payload no longer includes unsupported free-text status

Acceptance criteria
- Users no longer need to type UUIDs manually for planning-record references.
- Planning record reference fields use selectors with readable labels.
- Status is not a free-text field in create mode.
- Existing planning setup entities are reused as option sources where appropriate.
- No backend business logic is weakened.
- UX is consistent with the already improved selectors elsewhere in Planning Orders.

Before coding:
Briefly summarize:
1. which files you will change
2. which lookup sources already exist
3. whether dispatcher lookup needs a new endpoint or can reuse an existing one

After coding:
Provide:
1. files changed
2. selector mappings for each field
3. payload changes
4. any new lookup endpoint added
5. test coverage summary
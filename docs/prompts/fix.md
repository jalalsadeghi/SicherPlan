You are working in the SicherPlan repository.

This task follows the previous patch for:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Goal:
Do a focused QA and hardening pass after adding Create new address and Pick on map to the Customer New Plan Wizard Planning step.

Do not add unrelated features.
Only fix issues directly related to the Planning step modal parity with canonical Planning Setup.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/components/planning/PlanningLocationPickerModal.vue
- web/apps/web-antd/src/sicherplan-legacy/api/customers.ts
- related tests for Customer New Plan Wizard

Validation checklist:

1. Address creation
Confirm:
- Create new address appears only when relevant
- address creation uses the selected wizard customer_id
- required address fields are validated before submit
- API errors are shown cleanly
- created address is added to the address dropdown
- created address is selected automatically
- canceling address creation does not dirty or corrupt the planning create modal

2. Address target correctness
Confirm:
- site uses address_id
- event_venue uses address_id
- trade_fair uses address_id
- patrol_route uses meeting_address_id only if supported by the branch
- no address is written into the wrong payload field

3. Map picker
Confirm:
- Pick on map appears only for planning families with latitude/longitude support
- map modal opens correctly
- choosing a point updates latitude and longitude
- canceling the map modal keeps previous coordinates unchanged
- map load failure shows the localized error
- map modal does not break when coordinates are empty

4. Payload validation
Confirm the final create payload sent by submitPlanningCreateModal includes the correct address and coordinate fields:
- site: address_id, latitude, longitude, timezone, watchbook_enabled, status
- event_venue: address_id, latitude, longitude, timezone, status
- trade_fair: venue_id, address_id, latitude, longitude, timezone, start_date, end_date, status
- patrol_route: site_id, meeting_address_id, start_point_text, end_point_text, travel_policy_code, status

Do not include unsupported fields.
If the branch API rejects any field, adjust to the canonical PlanningOpsAdmin behavior.

5. UX and styling
Confirm:
- new buttons match wizard/admin styling
- nested address modal is styled
- map modal is usable
- focus states are visible
- narrow viewport is usable
- dark mode remains readable if supported

6. i18n
Confirm:
- no new hard-coded user-facing English strings remain
- German and English messages exist
- labels are consistent with the rest of the wizard

7. Non-regression
Confirm:
- Use Existing flow still works
- Create Planning Entry still saves for all supported families
- New Equipment/New Requirement/New Template dialogs still work
- Order Details and later steps are not impacted
- canonical /admin/planning page is not changed or regressed

Tests:
Add or update tests for any missing validation coverage:
- address creation success
- address creation validation failure
- map picker confirm
- map picker cancel
- family-specific field visibility
- family-specific payload correctness
- i18n key existence where practical

Final output:
1. QA validation summary
2. Issues found
3. Fixes made
4. Changed files
5. Tests added/updated
6. Test results
7. Manual QA checklist result
8. Clear statement: Ready / Not ready for real data entry

Before finalizing, explicitly confirm whether the implemented solution matches the proposal or required adjustment.
Avoid unrelated refactors.
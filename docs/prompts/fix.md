You are working in the SicherPlan repository.

Task title:
Fix Planning Orders > Planning records create UX so users get precise validation and cannot submit obviously invalid planning records.

Problem:
In `/admin/planning-orders`, creating a planning record currently fails with a generic frontend error:
- "The action could not be completed."

But backend validation is more specific. In the current implementation, create can fail because:
1) planning_from / planning_to are outside the selected order service window
2) event mode requires a valid event_detail.event_venue_id
3) other mode-specific detail references may be missing or invalid
4) dispatcher_user_id may be invalid if manually supplied

Current backend behavior:
In `backend/app/modules/planning/planning_record_service.py`, `create_planning_record()` validates, in this order:
- planning mode is valid
- order exists
- planning window is valid
- planning window stays within order.service_from / order.service_to
- dispatcher (if provided) exists
- parent record (if provided) is valid
- detail payload matches the selected mode
- mode-specific referenced entity exists and belongs to the same customer

Important frontend issue:
In `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
the planning record form currently:
- allows submission even when planning dates are outside the selected order window
- allows submission in event mode even when no event venue exists / is selected
- maps many backend errors to the generic fallback "error"

This creates a poor UX and hides the real reason.

Goal:
Make Planning record creation safe and self-explanatory on the frontend, while preserving backend validation as source of truth.

Files likely involved:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningOrders.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/i18n/planningOrders.messages.ts

Do NOT change backend business rules unless absolutely necessary.
Assume backend behavior is correct.

Implementation requirements

A) Add frontend validation for planning record date window
1. Introduce a frontend validation helper for planning record create/update.
2. It must enforce:
   - planning_from is required
   - planning_to is required
   - planning_to >= planning_from
   - if a selectedOrder exists:
     - planning_from >= selectedOrder.service_from
     - planning_to <= selectedOrder.service_to
3. If the planning window is outside the order window, show a specific validation message before submit.

B) Add min/max constraints to planning date inputs
4. In the planning record form:
   - `Planning from` input min must be `selectedOrder.service_from`
   - `Planning from` input max must be `selectedOrder.service_to`
   - `Planning to` input min must be max(planning_from, selectedOrder.service_from)
   - `Planning to` input max must be `selectedOrder.service_to`
5. Add a helper text below the planning date row that clearly shows:
   - "Allowed window: {service_from} → {service_to}"

C) Enforce mode-specific required selectors before submit
6. If `planning_mode_code === "event"`:
   - require `planningDraft.event_detail.event_venue_id`
   - if event venue options are empty, block submit and show a specific hint
7. If `planning_mode_code === "site"`:
   - require `planningDraft.site_detail.site_id`
8. If `planning_mode_code === "trade_fair"`:
   - require `planningDraft.trade_fair_detail.trade_fair_id`
9. If `planning_mode_code === "patrol"`:
   - require `planningDraft.patrol_detail.patrol_route_id`

D) Improve empty-state guidance
10. When event mode is selected and there are no event venues for the selected customer:
   - show a clear helper message
   - add a direct CTA/button/link to open Planning Setup for `event_venue`
11. Do the same pattern for site / trade fair / patrol route when relevant.

E) Improve error mapping
12. Extend `mapPlanningOrderApiMessage()` in `planningOrders.helpers.js` to handle at least:
- errors.planning.planning_record.order_window_mismatch
- errors.planning.planning_record.invalid_window
- errors.planning.planning_record.detail_mismatch
- errors.planning.planning_record.detail_customer_mismatch
- errors.planning.event_venue.not_found
- errors.planning.site.not_found
- errors.planning.trade_fair.not_found
- errors.planning.trade_fair_zone.not_found
- errors.planning.patrol_route.not_found
- errors.planning.dispatcher_user.not_found
- errors.planning.planning_record.parent_mismatch
- errors.planning.planning_record.parent_not_allowed

13. Add corresponding message keys in `planningOrders.messages.ts` for both DE and EN.
14. Do not fall back to the generic error message for these common validation cases.

F) Submit behavior
15. In `submitPlanningRecord()`:
   - run the new frontend validation before POST/PATCH
   - if invalid, show specific feedback and do not submit
16. Preserve existing backend validation and error handling.

G) UX consistency
17. Keep Dispatcher optional.
18. Keep Parent planning record optional.
19. Do not force users to enter values that backend allows to be null.
20. Do not change release workflow in this task.

Acceptance criteria
- Users cannot submit a planning record with dates outside the selected order window without seeing a specific frontend validation message first.
- Users cannot submit event mode without selecting a valid event venue.
- The planning record form visibly communicates the allowed date window from the selected order.
- Backend validation remains unchanged.
- Common planning-record errors no longer collapse into the generic "The action could not be completed."

Before coding:
Briefly summarize:
1. which files you will change
2. which frontend validations you will add
3. which backend message keys you will explicitly map

After coding:
Provide:
1. files changed
2. validation logic summary
3. added message keys
4. UX improvements
5. confirmation that backend business rules were not changed
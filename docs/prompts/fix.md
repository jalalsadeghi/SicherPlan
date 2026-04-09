You are working in the SicherPlan monorepo.

Goal:
Fix the 500 error when updating an existing planning record from P-02 (`/admin/planning-orders`, Planning records > Overview).

Observed backend failure:
PATCH /api/planning/tenants/{tenant_id}/ops/planning-records/{planning_record_id}
raises:
AttributeError: 'dict' object has no attribute '_sa_instance_state'

Root cause to fix:
- Frontend sends nested mode detail payloads on update (`event_detail`, `site_detail`, `trade_fair_detail`, `patrol_detail`).
- `PlanningRecordService.update_planning_record()` passes the full `PlanningRecordUpdate` payload into `repository.update_planning_record(...)`.
- `repository._update_row()` blindly iterates through `payload.model_dump(...)` and does `setattr(row, key, value)`.
- On `PlanningRecord`, the detail fields are SQLAlchemy relationships, so assigning a plain dict to them crashes.

Relevant files:
1. `backend/app/modules/planning/planning_record_service.py`
2. `backend/app/modules/planning/repository.py`
3. `backend/app/modules/planning/models.py`
4. `backend/app/modules/planning/schemas.py`
5. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`

Required fix:
1. Ensure update of an existing planning record never sends nested detail dictionaries into the generic ORM row updater.
2. Keep the current create flow intact.
3. Preserve the existing specialized detail update methods:
   - `update_event_plan_detail`
   - `update_site_plan_detail`
   - `update_trade_fair_plan_detail`
   - `update_patrol_plan_detail`

Recommended implementation approach:
A) In `PlanningRecordService.update_planning_record()`:
- Split the incoming payload into:
  - core/scalar planning record fields
  - mode-specific detail fields
- Only pass the scalar/core payload to `repository.update_planning_record(...)`
- Then call `_update_detail_for_mode(...)` with the original detail payload
- Re-read the record before returning, as the current code already intends

The scalar/core update payload should include only supported top-level fields such as:
- `dispatcher_user_id`
- `name`
- `planning_from`
- `planning_to`
- `notes`
- `status`
- `archived_at`
- `version_no`

It must exclude:
- `event_detail`
- `site_detail`
- `trade_fair_detail`
- `patrol_detail`

B) Optionally harden repository layer:
- Add an `exclude_fields` parameter to `_update_row(...)`
- Use it for `PlanningRecord` updates so relationship payloads can never be assigned by mistake
- This is optional but preferred as defensive design

C) Add regression tests
Add backend tests that prove:
1. Updating a site-mode planning record with `site_detail` no longer crashes
2. Updating an event-mode planning record with `event_detail` no longer crashes
3. Updating a trade-fair-mode planning record with `trade_fair_detail` no longer crashes
4. Updating a patrol-mode planning record with `patrol_detail` no longer crashes
5. Scalar fields like `name`, `planning_from`, `planning_to`, `notes`, `status`, and `dispatcher_user_id` still persist correctly
6. The specialized detail rows are actually updated, not ignored

Important side observation:
- The current frontend update payload includes `planning_mode_code` and `parent_planning_record_id`
- But `PlanningRecordUpdate` in `schemas.py` does not currently support those fields
- Do NOT silently broaden behavior unless intended
- Either:
  - keep them unsupported and make the update path ignore them safely, or
  - explicitly add full backend support if you determine that existing-record editing of those fields is required
- If you do not add backend support, ensure the frontend does not misleadingly imply that these fields are editable on existing records

Non-goals:
- Do not redesign P-02
- Do not change planning record create semantics
- Do not change release-state behavior
- Do not change commercial-link logic
- Do not touch unrelated planning modules

Acceptance criteria:
1. PATCH update for existing planning records no longer returns 500
2. Nested mode detail updates persist correctly
3. No dict is assigned to SQLAlchemy relationship attributes in generic row update
4. Existing create flow still works
5. Tests cover the regression

Deliverables:
- updated service/repository code
- regression tests
- short summary of the root cause and the fix
- note whether `planning_mode_code` / `parent_planning_record_id` remain unsupported on update or were explicitly implemented
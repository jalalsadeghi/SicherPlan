You are working in the SicherPlan monorepo.

Goal:
Improve the Planning Record edit experience in P-02 (`/admin/planning-orders`) so the UI clearly reflects the intended domain behavior.

Current situation:
- Existing planning records can be edited in `Planning records > Overview`
- But `Planning mode` is disabled for existing records
- There is no explicit UI action for:
  - deactivate
  - reactivate
  - archive
- There is also no explanatory UX telling the user why `Planning mode` is locked
- Users can mistakenly assume this is a broken form

Important domain rule to preserve:
- `Planning mode` must remain immutable after creation
- Do NOT enable in-place editing of `planning_mode_code` for existing planning records
- Current backend contract (`PlanningRecordUpdate`) does not support updating `planning_mode_code`
- Existing mode controls which detail structure is valid:
  - `event_detail`
  - `site_detail`
  - `trade_fair_detail`
  - `patrol_detail`

Relevant files:
1. `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
2. `backend/app/modules/planning/schemas.py`
3. `backend/app/modules/planning/router.py`
4. `backend/app/modules/planning/planning_record_service.py`
5. any related i18n/test files

Required implementation:

A) Keep Planning mode immutable
- Leave `Planning mode` disabled when editing an existing planning record
- Do NOT implement backend support for changing `planning_mode_code` on update
- Add inline helper text below the disabled field explaining why:
  Example intent:
  - “Planning mode cannot be changed after creation. If you selected the wrong mode, deactivate/archive this planning record and create a new one.”
- Add i18n keys for this explanation

B) Add explicit lifecycle actions for planning records
Currently `status` is editable via a dropdown, but the UX is weak.
Improve this by adding clear action buttons for existing planning records:
- Deactivate (sets `status = inactive`)
- Reactivate (sets `status = active`)
- Archive (sets `archived_at` to now, ideally via PATCH update)
Place these in a clear action row in the planning-record overview or a dedicated lifecycle section.

Implementation notes:
- Reuse existing PATCH `/planning-records/{id}` update flow
- For deactivate/reactivate:
  - update `status`
- For archive:
  - update `archived_at`
- Refresh the selected planning record and list after each action
- Show toast feedback on success/failure

C) Do NOT add hard delete in this task
- There is currently no DELETE endpoint for planning records
- Do not introduce destructive hard-delete behavior here
- If a future delete flow is needed, it should be a separate constrained feature with dependency checks

D) Optional but recommended UX improvement
Add a secondary CTA for mistaken mode selection:
- “Create replacement planning”
This should:
- start a new planning record draft for the same order
- prefill safe fields like:
  - name
  - planning_from
  - planning_to
  - dispatcher_user_id
  - notes
- but allow selecting a fresh `Planning mode`
Do NOT auto-copy incompatible mode-specific detail fields.

E) Tests
Update/add tests to verify:
1. Existing planning records still show `Planning mode` as disabled
2. Helper text explains why the field is locked
3. Deactivate action updates status to `inactive`
4. Reactivate action updates status to `active`
5. Archive action updates `archived_at`
6. No hard delete action is exposed
7. Existing save/release/document flows are not broken

Acceptance criteria:
1. Users understand that `Planning mode` is intentionally immutable
2. Users can explicitly deactivate/reactivate/archive an existing planning record
3. Wrong-mode correction follows a safe workflow (replace, not mutate)
4. No hard delete is introduced
5. Tests pass

Deliverables:
- updated `PlanningOrdersAdminView.vue`
- any minimal backend support needed for archive via existing PATCH contract
- updated i18n strings
- updated tests
- short summary of the UX and lifecycle changes
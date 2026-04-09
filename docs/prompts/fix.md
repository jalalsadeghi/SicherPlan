You are working in the repository `jalalsadeghi/SicherPlan`.

Goal:
Harden and complete `P-03 / Shift Planning` so that a Tenant Administrator can safely enter, edit, validate, and prepare shift-planning data for UAT without losing existing field values or bypassing intended release controls.

Context:
- The backend already exposes shift-planning APIs for:
  - shift templates
  - shift plans
  - shift series
  - shift series exceptions
  - shifts
  - release diagnostics
  - release-state transitions
  - visibility updates
  - copy slice
  - board preview
- The current frontend page is:
  - `web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue`
- The current frontend API wrapper is:
  - `web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts`
- The current helper file is:
  - `web/apps/web-antd/src/sicherplan-legacy/features/planning/planningShifts.helpers.js`
- The current backend service is:
  - `backend/app/modules/planning/shift_service.py`

Problems to fix:
1. Unsafe editing of existing records:
   - Existing templates, series, and shifts are currently edited from list-item data instead of full read models.
   - This can overwrite fields that are not present in list responses (for example notes, meeting_point, location_text, default_break_minutes, shift_type_code).
2. Missing release workflow controls in the UI:
   - The page does not expose release diagnostics, dedicated release-state transitions, or dedicated visibility updates.
   - Release/visibility is currently mixed into the generic shift edit form.
3. Incomplete exception management:
   - The UI can create series exceptions but does not list existing exceptions or support selecting/editing them properly.
4. Missing initial data loading:
   - The view does not reliably load templates / planning records / board data on initial mount.
   - Templates tab has no refresh action.
5. Missing backend window validation for manual shifts:
   - Manual shift create/update must be validated against the owning shift plan window (and parent planning record window if applicable).
6. Broken “Copy Week” behavior:
   - Current UI copy logic uses a single source day even for the “Copy Week” button.
7. Visibility rules must be enforced consistently:
   - A shift must not become customer-visible or subcontractor-visible unless it is in `released` state and passes release diagnostics.

Required changes:

A. Frontend API wrapper (`planningShifts.ts`)
Add missing typed API functions for:
- `getShiftTemplate`
- `getShiftSeries`
- `listShiftSeriesExceptions`
- `getShift`
- `getShiftReleaseDiagnostics`
- `setShiftReleaseState`
- `updateShiftVisibility`

Keep existing naming and error-handling conventions.

B. Frontend view (`PlanningShiftsAdminView.vue`)
1. Initial loading:
   - Load templates, planning records, and initial board data on mount.
   - Add a refresh action to the Templates tab.
2. Safe editing:
   - When selecting an existing template, fetch full template detail via `getShiftTemplate`.
   - When selecting an existing series, fetch full series detail via `getShiftSeries`.
   - When selecting an existing shift, fetch full shift detail via `getShift`.
   - Populate the edit drafts from full read models, not list items.
3. Series exceptions:
   - Show the current exception list for the selected series.
   - Allow selecting an exception and updating it through the existing update endpoint.
4. Release workflow:
   - Add a dedicated “Release & Visibility” section for the selected shift.
   - Show `release diagnostics` (blocking/warning counts and issue list).
   - Use dedicated `setShiftReleaseState` actions instead of only editing `release_state` inline.
   - Use dedicated `updateShiftVisibility` actions instead of silently persisting visibility flags through generic update.
5. Copy logic:
   - Replace the current day/week copy shortcuts with correct behavior.
   - “Copy Day” should copy exactly one source day.
   - “Copy Week” should copy a 7-day slice.
   - Make source range and target start explicit in the UI.
   - Disable copy actions when required inputs are missing.
6. Keep the page usable for tenant_admin role and preserve existing styling patterns.

C. Backend service (`shift_service.py`)
1. Add explicit validation that manual shift create/update stays within:
   - owning `shift_plan.planning_from/planning_to`
   - and, where relevant, the parent `planning_record` window
2. Add the same window validation to `copy_shift_slice` for target shifts.
3. Enforce visibility rules consistently:
   - if `customer_visible_flag` or `subcontractor_visible_flag` is true, the shift must already be `released`
   - otherwise reject with a validation error
4. Do not break generated-series behavior.

D. Tests
Add or update tests to cover:
1. Editing an existing template preserves `meeting_point`, `location_text`, and `notes`
2. Editing an existing series preserves `default_break_minutes`, `shift_type_code`, `meeting_point`, `location_text`, and `notes`
3. Editing an existing shift preserves `notes`
4. Existing series exceptions are listed and can be updated
5. Release diagnostics are shown before release actions
6. Manual shift outside plan window is rejected
7. Copy Week copies a 7-day slice, not a single day shifted by +7
8. Draft shifts cannot be made customer-visible/subcontractor-visible

Acceptance criteria:
- P-03 remains mounted and passes existing smoke tests
- Tenant Admin can:
  - create template
  - create shift plan
  - create series
  - generate shifts
  - create/edit manual shifts safely
  - inspect diagnostics
  - change release state through dedicated actions
  - manage visibility through dedicated actions
  - list and edit exceptions
  - copy day/week slices correctly
- No existing detail fields are lost when editing previously saved template/series/shift rows

Implementation notes:
- Follow existing repository conventions
- Prefer minimal, targeted changes over broad rewrites
- Preserve current route paths, naming style, and feedback-toast behavior
- After coding, update or add tests and ensure they pass
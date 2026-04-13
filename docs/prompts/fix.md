You are working in the SicherPlan monorepo on the latest main branch.

Task:
Fix the incomplete `Series exceptions` form in Planning -> Shift planning -> Series and exceptions.

Problem:
The current UI only renders:
- Occurrence date
- Exception action
- Override local start time (only when action = override)
- Override local end time (only when action = override)
- Notes

But the project model/API for shift series exceptions already support additional fields:
- `override_break_minutes`
- `override_shift_type_code`
- `override_meeting_point`
- `override_location_text`
- `customer_visible_flag`
- `subcontractor_visible_flag`
- `stealth_mode_flag`

So the current form appears incomplete relative to the actual contract.

What you must verify first:
1. Confirm that these fields are real supported fields in both backend and frontend API types.
2. Confirm whether they should be available in the UI.
3. Validate whether they should be shown:
   - always, or
   - only when `action_code === 'override'`

Known facts already observed:
- Backend shift series exception schemas include the additional override and visibility fields.
- Frontend `planningShifts.ts` also includes those fields in `ShiftSeriesExceptionRead`.
- Current `PlanningShiftsAdminView.vue` form does not render most of them.

Files to inspect first:
Frontend
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts`
- `@/features/planning/planningShifts.helpers` if relevant
- planning-shifts i18n/messages files

Backend
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/models.py`
- any shift-series-exception service/router/repository files if needed

Your job:
1. Validate the intended UX logic.
2. Complete the form so it matches the real contract.
3. Keep the UX clean and logically conditional.

Preferred UX logic unless validation disproves it:
- If `action_code === 'skip'`:
  - keep the form minimal
  - override-specific fields may remain hidden or collapsed
  - their values should be cleared/reset safely
- If `action_code === 'override'`:
  - show all override-capable fields:
    - Override Local Start Time
    - Override Local End Time
    - Override Break Minutes
    - Override Shift Type Code
    - Override Meeting Point
    - Override Location Text
    - Customer Visible Flag
    - Subcontractor Visible Flag
    - Stealth Mode Flag
    - Notes

Important implementation details:
A. Reuse existing shift-type option loading instead of inventing a new source.
   The override shift type field should use the same option source/pattern already used elsewhere in Shift planning.
B. Preserve edit round-trip for all fields.
C. Do not break current `skip` behavior.
D. Do not force users to fill override-only fields when action is `skip`.

Critical UX requirement for visibility flags:
The following fields are nullable booleans in the contract:
- `customer_visible_flag`
- `subcontractor_visible_flag`
- `stealth_mode_flag`

Because they are nullable, do NOT model them as simple two-state checkboxes if that would lose the `null` / “inherit” state.

Instead, validate and implement a proper nullable UI, for example:
- `inherit`
- `yes`
- `no`

This is important because `null` means “no exception-level override”.

Validation questions you must answer:
1. Are the missing fields truly part of the supported exception contract?
2. Should they appear only for `override` exceptions?
3. How did you preserve nullable behavior for the three visibility fields?
4. Did you reuse existing shift type option loading?

Acceptance criteria:
1. The `Series exceptions` form matches the real supported exception contract.
2. For `skip`, the form remains minimal and valid.
3. For `override`, the missing fields are available.
4. `override_shift_type_code` uses the existing shift type option source.
5. Nullable visibility flags are represented safely without losing `null`.
6. Existing create/edit/get round-trip still works.
7. No unrelated shift-planning behavior is changed.

Tests to add/update:
- frontend test for `skip` mode showing only the appropriate fields
- frontend test for `override` mode showing the full override field set
- frontend test for nullable visibility flag behavior
- round-trip test for edit mode hydrating all exception fields
- backend/integration test only if needed to align with the actual API contract

What not to do:
- Do not expose all override fields unconditionally if the UX becomes confusing and the model clearly distinguishes `skip` vs `override`
- Do not use simple checkboxes for nullable visibility flags if that destroys the inherit state
- Do not add new data sources for shift types
- Do not refactor unrelated shift-planning tabs

Required output:
1. Confirmed root cause
2. Confirmed UI rule: always visible vs override-only
3. Files changed
4. Exact fields added
5. How nullable visibility flags were implemented
6. Tests added/updated
7. Final self-check confirming you validated the proposal against the real contract instead of assuming
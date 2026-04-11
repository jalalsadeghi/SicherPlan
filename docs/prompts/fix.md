You are working in the latest SicherPlan repository state.

Task goal:
Fix the backend 500 error that breaks `/admin/planning-staffing` by aligning the staffing-board / coverage filter contract across router, schemas, service, and repository.

Read first:
1. `AGENTS.md`
2. the relevant `docs/sprint/*.md` and `docs/prompts/*.md` item for planning staffing / coverage if it exists
3. keep the change set narrow and traceable to the correct task/story; if no matching task exists, say so explicitly in your summary

Files to inspect first:
- `backend/app/modules/planning/router.py`
- `backend/app/modules/planning/staffing_service.py`
- `backend/app/modules/planning/repository.py`
- `backend/app/modules/planning/schemas.py`
- tests covering planning staffing / coverage / board endpoints
- only for context, inspect:
  - `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
  - `web/apps/web-antd/src/sicherplan-legacy/views/PlanningStaffingCoverageView.vue`

Bug to verify:
The current backend crashes on:
- `GET /api/planning/tenants/{tenant_id}/ops/coverage?...`
- `GET /api/planning/tenants/{tenant_id}/ops/staffing-board?...`

Observed traceback shows:
- `coverage()` calls `staffing_board()`
- `staffing_board()` calls `repository.list_board_shifts(...)`
- inside `list_board_shifts`, code dereferences `filters.visibility_state`
- but the current `StaffingBoardFilter` contract is not aligned, so `filters.visibility_state` is missing and raises `AttributeError`

What to verify carefully:
1. Whether `visibility_state` is missing from `StaffingBoardFilter`
2. Whether `visibility_state` is missing from `CoverageFilter`
3. Whether `_staffing_board_filters` and `_coverage_filters` expose that query param
4. Whether `coverage()` passes visibility through when constructing `StaffingBoardFilter`
5. Whether there are any other similar filter-field drifts, e.g. fields referenced in repository/service but not guaranteed by the Pydantic filter models

Required implementation outcome:
A. Make `visibility_state` a safe, optional, contract-defined filter field for staffing-board logic.
   - Prefer a constrained type if the repo already uses a pattern for narrow code values, e.g. `Literal["customer", "subcontractor"] | None`
   - If there is an existing enum / lookup convention already used in this module, follow that instead

B. Ensure both endpoints work when `visibility_state` is omitted.
   - Current UI does not send `visibility_state`
   - Omitted `visibility_state` must NOT crash
   - The default behavior should be the current internal/unfiltered staffing board behavior, not a silent semantic change

C. If the product/API should support visibility filtering explicitly, expose it consistently:
   - add it to `StaffingBoardFilter`
   - add it to `CoverageFilter` if coverage should support the same pass-through
   - add optional query params in router helpers
   - pass it through in `coverage()` when building `StaffingBoardFilter`

D. Make repository-side access robust.
   - Do not blindly dereference a field that the contract may not provide
   - Use a clear local variable and guard the visibility predicate cleanly
   - Preserve existing customer/subcontractor visibility semantics if that filtering is already implemented

E. Audit the rest of the staffing filter contract.
   - Compare all fields used in repository/service against:
     - `StaffingBoardFilter`
     - `CoverageFilter`
     - `_staffing_board_filters`
     - `_coverage_filters`
   - Fix any additional mismatches found in the same narrow change set if they are part of the same root cause
   - Do NOT do unrelated refactors

Important product guardrails:
- Keep tenant scoping intact
- Keep role-scoped visibility intact
- Do not change finance bridging or anything around `finance.actual_record`
- Do not broaden portal/customer/subcontractor data visibility
- Do not require frontend changes just to stop the backend crash unless a tiny type alignment is absolutely necessary

Tests and validation required:
1. Add/update backend tests for:
   - `/ops/staffing-board` without `visibility_state` -> returns 200, no AttributeError
   - `/ops/coverage` without `visibility_state` -> returns 200, no AttributeError
   - `/ops/staffing-board?visibility_state=customer` -> returns 200 and applies expected visibility predicate
   - `/ops/staffing-board?visibility_state=subcontractor` -> returns 200 and applies expected visibility predicate
   - if coverage is meant to support pass-through visibility filtering, test that too
2. Add at least one regression test specifically proving this bug no longer occurs
3. Run the relevant test suite / targeted tests / lint or type checks available in the repo

Preferred fix shape:
- small schema change
- small router change
- small service pass-through change
- robust repository guard
- regression tests

Self-check before finalizing:
- Confirm the bug is fixed for both endpoints, not just one
- Confirm current UI requests without `visibility_state` now work
- Confirm you did not remove legitimate visibility filtering capability
- Confirm tenant/role visibility semantics did not broaden
- Confirm there are no other obvious filter-model mismatches left in this staffing path

Final response format:
1. Short implementation summary
2. Exact files changed
3. Root cause confirmed
4. What was changed in schemas/router/service/repository
5. Tests run and results
6. Any additional filter-contract mismatches found
7. Self-validation summary
You are working in the SicherPlan repository on the current main branch.

Goal:
Fix the backend bug that causes POST /api/planning/tenants/{tenant_id}/ops/shift-plans to fail with HTTP 500 during audit-event creation, and make sure valid Shift Plan creation succeeds cleanly so the UI can continue into Shift Series creation without false follow-on errors.

Observed behavior:
- The UI later shows “The series falls outside the shift-plan window.”
- But the backend traceback clearly shows a 500 in create_shift_plan, inside:
  backend/app/modules/planning/shift_service.py
  -> ShiftPlanningService.create_shift_plan()
  -> self._record_event(... after_json=self._snapshot(row))
  -> backend/app/modules/iam/audit_service.py
  -> backend/app/modules/iam/audit_repository.py
  -> session.commit()
  -> psycopg JSON serialization crash
- This strongly suggests the audit payload contains non-JSON-serializable values (date/datetime/time/UUID/etc.).

Important code references:
- backend/app/modules/planning/shift_service.py
- backend/app/modules/planning/order_service.py
- backend/app/modules/planning/planning_record_service.py
- backend/app/modules/iam/audit_models.py
- backend/app/modules/iam/audit_repository.py
- backend/app/modules/planning/repository.py
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningShiftsAdminView.vue

Root-cause hypothesis to verify and fix:
- ShiftPlanningService._snapshot() currently returns raw row.__dict__ values.
- AuditEvent.before_json / after_json / metadata_json are JSONB fields.
- Raw SQLAlchemy model attributes can include Python date/datetime/time/UUID/Enum or other non-JSON-safe values.
- CustomerOrderService._snapshot() already contains a safer recursive serializer. Reuse that approach or extract a shared helper.

What to do:
1. Reproduce the failing path for Shift Plan creation.
2. Fix backend/app/modules/planning/shift_service.py so audit snapshots are JSON-safe.
   - Replace the current _snapshot() implementation with a recursive serializer that converts:
     - datetime/date/time -> ISO 8601 strings
     - UUID -> string
     - Decimal -> string
     - Enum -> its value (then serialize recursively)
     - dict/list/tuple/set -> recursively JSON-safe structures
   - Skip SQLAlchemy internals and any non-serializable relationship objects.
3. Prefer a small shared helper if it improves consistency.
   - If practical, extract a reusable JSON-safe snapshot helper and use it in:
     - backend/app/modules/planning/shift_service.py
     - backend/app/modules/planning/planning_record_service.py
   - Keep the scope tight; do not refactor unrelated modules.
4. Keep business validation semantics unchanged.
   - Do NOT relax the actual “shift plan window must fit planning record window” rule.
   - The fix is for the false 500/audit crash, not for bypassing domain validation.
5. Add regression tests.
   At minimum add tests that prove:
   - creating a valid Shift Plan no longer returns 500 when audit is enabled
   - the resulting audit event is stored successfully with JSON-safe after_json
   - date/datetime values in the snapshot are serialized as strings
   - planning_record_service audit snapshots are also safe if you touched that file
6. Make sure the API now returns the correct domain error only when the window is genuinely invalid.
7. Run the relevant tests and provide a short report with:
   - changed files
   - root cause
   - why the fix works
   - exact test commands and results

Implementation constraints:
- Preserve existing API contracts.
- Preserve current release/validation rules.
- Do not disable audit logging.
- Do not add broad try/except wrappers that hide real errors.
- Keep the patch production-grade and minimal.

Suggested acceptance criteria:
- POST /ops/shift-plans with a valid payload succeeds without HTTP 500.
- Audit rows are created successfully.
- No psycopg JSON serialization error occurs during audit commit.
- Creating a Shift Series afterwards is no longer blocked by this backend failure.
- Real window-mismatch errors still behave as proper business validation, not as 500s.

Before coding:
- Briefly summarize the root cause and list the files you will touch.

After coding:
- Show the exact tests you ran and whether they passed.
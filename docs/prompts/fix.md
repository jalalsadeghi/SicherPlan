You are working in the SicherPlan repository.

Bug to fix
----------
Creating a second Trade Fair zone returns HTTP 500, but the zone is actually persisted.
Observed backend error:
TypeError: Object of type TradeFair is not JSON serializable

Relevant files
--------------
- backend/app/modules/planning/service.py
- backend/app/modules/planning/models.py
- backend/app/modules/planning/repository.py
- backend/app/modules/iam/audit_repository.py
- backend/tests/modules/planning/test_ops_master_foundation.py

Diagnosis
---------
`PlanningService.create_trade_fair_zone()` creates the row successfully, then records an audit event using:
    after_json=self._snapshot(row)

`_snapshot()` currently builds a dict from `row.__dict__` and excludes only a hard-coded set of relationship names.
For `TradeFairZone`, the SQLAlchemy relationship `trade_fair` is not excluded.
That means the audit payload can contain a live ORM object (`TradeFair`), which later fails JSON serialization when the audit repository writes the JSON column.

Additionally, the planning repository commits the new zone before the audit repository commits the audit row, so the API returns 500 even though the zone was already saved.

What to implement
-----------------
1. Fix `PlanningService._snapshot()` so it is generic and JSON-safe:
   - Do NOT build the snapshot from `row.__dict__`.
   - Use SQLAlchemy inspection to include only mapped column attributes, never relationship attributes.
   - Serialize values recursively into JSON-safe primitives:
     - Decimal -> string
     - datetime/date/time -> ISO string
     - UUID -> string
     - Enum -> value or string
     - dict/list/tuple -> recurse
     - None/bool/int/float/str -> keep as-is
   - The helper must work for all planning models, not only TradeFairZone.

2. Keep the current API behavior and response schema unchanged.
   - Successful zone creation must return success instead of 500.
   - Do not change endpoint contracts unless strictly necessary.

3. Add regression tests in:
   `backend/tests/modules/planning/test_ops_master_foundation.py`
   Include at least:
   - a test that creates a trade fair and then creates a trade fair zone with audit enabled, asserting:
     - no exception
     - one audit event is recorded
     - `after_json` contains only JSON-safe values
     - `trade_fair` relationship object is not present in `after_json`
   - a second test for another relationship-bearing planning entity that uses the same snapshot path, preferably patrol checkpoint, to prevent the same bug class from returning.

4. Keep the fix minimal and production-safe.
   - Avoid broad refactors of transaction boundaries in this patch unless required for the tests.
   - Focus on the serialization bug and regression coverage first.

Acceptance criteria
-------------------
- POST /ops/trade-fairs/{trade_fair_id}/zones returns success for valid payloads.
- No `TypeError: Object of type TradeFair is not JSON serializable`.
- Audit rows are still written.
- Existing tests pass.
- New regression tests pass.

After coding
------------
Run the most relevant tests and report:
- what changed
- which tests were run
- whether any follow-up transaction-hardening work is still recommended
You are working in the jalalsadeghi/SicherPlan repository.

Task:
Make the “Latest plans” list in the customer dashboard visually easier to scan by giving each plan status a colored badge/chip/tag based on its real status.

Before coding:
- Validate what latest_plans[].status actually represents in the current backend contract (for example release_state or another canonical planning status).
- Inspect whether the repo already has a reusable status->color helper/pattern for planning/order/dashboard lists. Reuse it if it exists; otherwise add a very small local helper.
- Summarize the validated status mapping before coding.

Relevant files to inspect first:
- web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerDashboardTab.vue
- backend/app/modules/customers/dashboard_service.py
- any existing status badge/helper pattern in:
  - web/apps/web-antd/src/views/sicherplan/dashboard/index.vue
  - planning/order-related views if they already color statuses

Desired outcome:
- Each latest plan row should show a small status badge/tag with consistent color semantics.
- The rest of the row layout should stay compact and readable.

Implementation rules:
- Prefer Ant Design Tag or the nearest existing badge pattern already used in this repo.
- Map only real statuses that the backend actually returns.
- Suggested truthful mapping after validation:
  - released / approved / confirmed -> success / teal/green
  - draft / pending -> warning / gold
  - cancelled / archived / rejected -> error / red
  - unknown / fallback -> default / neutral
- Do not hard-code statuses that do not exist in the current contract.
- Keep the raw status text readable; do not replace it with icons only.
- Keep row layout and click behavior unchanged.
- Ensure the badge remains legible in dark mode.
- Expose a stable class/data attribute for testing instead of asserting literal CSS colors.

Tests:
- status badge renders for populated latest plans
- different statuses produce different tones
- unknown status falls back safely
- empty state unchanged

Validation request:
Before finalizing, compare your chosen status mapping against actual values produced by the current latest_plans serializer and explain any adjustment you made.

Output:
- chosen status mapping
- changed files
- test results
Avoid unrelated refactors.
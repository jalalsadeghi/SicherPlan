Add regression coverage for the real remaining browser bug, not only the previous simple remount/draft tests.

Target:
Customer New Plan Wizard, Step 2 Order Details must keep unsaved values when browser focus returns and both visibilitychange and focus trigger auth/session refresh behavior.

Files to inspect/update:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.test.ts
- any test utilities for auth/session/router/fetch mocks
- auth-session-lifecycle tests, create them if missing

Required test 1 — lifecycle coalescing:
1. Initialize auth session lifecycle.
2. Simulate document.visibilityState = 'visible' and dispatch visibilitychange.
3. Immediately dispatch window.focus.
4. Mock /api/auth/refresh.
5. Assert only one refresh request occurs or the second call reuses the in-flight promise.
6. Assert no duplicate destructive session state transitions happen.

Required test 2 — same-context accessToken churn:
1. Mount /admin/customers/new-plan with:
   - customer_id=84bad50d-209c-491e-b86b-13c7788c7620
   - planning_entity_id=bfe2eaba-0a95-4918-9f11-5e46fd4043e3
   - planning_entity_type=site
   - planning_mode_code=site
   - step=order-details
2. Type values into:
   - order_no
   - title
   - service_from
   - service_to
   - service_category_code
   - notes
   - security_concept_text
3. Change accessToken in the auth store twice, quickly.
4. Assert:
   - customer-new-plan-step-content remains mounted
   - no loading state replaces the form
   - all typed values remain visible
   - sessionStorage order-details draft still contains the typed values

Required test 3 — overlapping reload race:
1. Mock customer/reference/catalog API calls with controllable promises.
2. Trigger two lifecycle refresh waves:
   - wave A starts first but resolves last
   - wave B starts second but resolves first
3. While both are in flight, type or update Order Details fields.
4. Resolve wave B.
5. Resolve wave A.
6. Assert stale wave A does not overwrite:
   - orderDraft
   - selectedOrder
   - dirty state
   - sessionStorage draft
7. Assert no saveWizardDraft(..., null) occurs for order-details during this process.

Required test 4 — incomplete draft key guard:
1. Mount with route containing planning_entity_id.
2. Simulate a temporary wizardState where planning_entity_id is empty during hydration.
3. Trigger auth refresh/reference reload.
4. Assert no order-details draft is saved or cleared under a key containing the "_" empty segment when the route already has a planning_entity_id.
5. Assert the real key draft survives.

Required test 5 — actual browser/E2E if Playwright/Cypress exists:
If this repo has Playwright or another browser E2E setup, add a browser-level test:
1. Open the exact URL.
2. Fill Order Details fields.
3. Dispatch visibility/focus or use page.bringToFront after switching away.
4. Wait for mocked or real auth refresh/reference reload.
5. Click another field.
6. Assert values remain.

If no browser E2E setup exists, add a manual QA checklist to the final output and explain why Vitest covers the race deterministically.

Run:
- pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/customers/new-plan.test.ts src/views/sicherplan/customers/new-plan-epic3.smoke.test.ts src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts src/views/sicherplan/customers/new-plan-wizard.test.ts
- any new auth-session-lifecycle test file
- pnpm --dir web/apps/web-antd exec vue-tsc --noEmit --skipLibCheck --pretty false

Final output must include:
- exact tests added
- why previous tests missed the bug
- proof that double focus/visibility refresh does not clear Order Details
- proof that stale async reloads cannot overwrite active dirty form data
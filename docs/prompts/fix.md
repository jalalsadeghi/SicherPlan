The focus-triggered refresh/reset bug still occurs on /admin/customers/new-plan.

Please perform a deeper instrumentation pass.

Tasks:
1. Add temporary diagnostics locally, not committed unless useful behind a dev flag:
   - log route changes
   - log component mount/unmount/activated/deactivated
   - log wizard initialization calls
   - log modal open/close state changes
   - log calls to fetch/bootstrap customer/planning data
   - log window/document focus/blur/visibilitychange handlers
   - log beforeunload/pagehide/pageshow events

2. Reproduce the bug:
   - open the route with an existing customer_id
   - select Create new
   - open Create planning entry
   - switch away from browser/app
   - return and click a modal field

3. Identify exactly which event first causes the reset:
   - full browser navigation
   - Vite/HMR reload
   - router navigation
   - Vben tab refresh
   - component remount
   - destructive bootstrap
   - form submit
   - query refetch overwriting local state

4. Remove temporary logs after identifying the cause.

5. Implement the smallest durable fix:
   - no implicit reload on focus
   - no destructive reinitialization for the same customer_id
   - prevent default submit/navigation
   - preserve local wizard/modal state

6. Add or update the regression test from the previous task.

Report:
- root cause
- changed files
- why the fix is safe
- how it was tested
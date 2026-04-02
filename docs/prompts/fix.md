You are working in the latest SicherPlan repository.

Goal
Replace the current fixed inline “Alert Message” / feedback banner pattern in SicherPlan legacy admin form pages with standard bottom-right toast notifications that:
- appear as floating notifications in the bottom-right corner
- auto-dismiss after a few seconds
- use standard semantic styles for success / info / warning / error
- do not require the user to click “Dismiss notice”
- fit the current vben admin + ant-design stack

Important repo context
- The app is based on the vben admin monorepo and the web-antd app already uses ant-design-vue.
- In web/apps/web-antd/src/adapter/component/index.ts, ant-design-vue `notification` is already imported and used with `placement: 'bottomRight'`.
- Therefore, prefer reusing `notification` from ant-design-vue instead of building a custom toast system from scratch.
- Do not introduce a second competing notification framework unless there is a strong repo-local reason.

Current problem pattern
- Pages like:
  - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
  - web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
  currently keep a reactive `feedback` object and render a persistent inline banner near the top of the workspace.
- The banner remains visible until the user manually dismisses it.
- Similar feedback/setFeedback usage likely exists in other SicherPlan legacy views, including planning, subcontractor, recruiting, finance, and core admin pages.

Implementation objective
Refactor the feedback UX so that:
1. Business result messages are shown as bottom-right toast notifications instead of inline fixed banners.
2. Success/info/warning/error toasts auto-close after a sensible duration.
3. The notification style is consistent with ant-design-vue / vben admin.
4. Existing business logic and API flows remain intact.
5. Existing `setFeedback(...)` calls should not require large business-logic rewrites.

Preferred architecture
Create a small reusable helper/composable for SicherPlan legacy pages, for example:
- web/apps/web-antd/src/sicherplan-legacy/composables/useSicherPlanFeedback.ts
or a similarly named file

This helper should:
- expose a function like `showFeedbackToast(...)`
- map existing tone values such as:
  - success
  - error
  - warning
  - info / neutral
  to the proper ant-design-vue notification API
- use `placement: 'bottomRight'`
- set a consistent duration, for example:
  - success/info: around 3 to 4 seconds
  - warning/error: around 4 to 6 seconds
- optionally support a stable notification key to avoid duplicate stacking during rapid repeat actions when appropriate

Refactor strategy
1. Identify all SicherPlan legacy pages/components that currently use the inline feedback banner pattern.
   Look for:
   - reactive `feedback` object
   - `setFeedback(...)`
   - `clearFeedback()`
   - template sections like `v-if="feedback.message"`

2. Replace the inline banner rendering with toast notifications.
   - Remove the fixed top-of-form feedback banner markup where appropriate.
   - Remove “Dismiss notice” UX from these pages if it is no longer needed.
   - Keep any real validation-inline field errors in forms. Only replace the global action/result feedback banner.

3. Preserve the current success/error semantics.
   For example:
   - after successful save/create/update/import/export:
     show success toast
   - after failed API call:
     show error toast
   - for neutral/informational messages:
     show info toast
   - if warning semantics exist, use warning toast

4. First migrate these pages explicitly:
   - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   - web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

5. Then migrate the other SicherPlan legacy views/components that use the same global feedback-banner pattern, as long as the change is mechanical and safe.
   Likely candidates include files such as:
   - FinanceActualApprovalView.vue
   - PlanningShiftsAdminView.vue
   - SubcontractorAdminView.vue
   - PlanningOrdersAdminView.vue
   - PlanningOpsAdminView.vue
   - RecruitingAdminView.vue
   - FinancePayrollAdminView.vue
   - CoreAdminView.vue
   - any other legacy component/view with the same feedback banner pattern
   Do not refactor unrelated UI.

Behavior requirements
- Notifications must appear in the bottom-right corner.
- Notifications must auto-dismiss after a few seconds.
- Standard semantic colors/icons must be used from the existing ant-design-vue notification system.
- Notifications should not block the page.
- Do not replace inline field-level validation messages.
- Do not change API payloads or business rules.
- Do not break tests by changing unrelated text or structure more than necessary.

Testing
Add or update focused tests so that:
- success actions trigger toast notifications
- error paths trigger error notifications
- the old inline persistent feedback banner is no longer rendered on the migrated pages
Mock ant-design-vue notification APIs where appropriate.

Implementation guardrails
- Keep the patch clean and minimal.
- Reuse existing stack primitives.
- Do not invent a global event bus unless really required.
- Avoid duplicating notification mapping code in every page; centralize it in a helper/composable.

Output format
Before changing code, briefly summarize:
- which files currently use the inline feedback banner pattern
- the chosen migration strategy
- why ant-design-vue notification is the right fit here

After the change, report:
- changed files
- which pages were migrated
- duration/placement rules used
- whether any legacy pages still remain on the old banner pattern
- test results
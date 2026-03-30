You are working in the SicherPlan repository.

Task title:
Fix contradictory Commercial readiness messaging in Planning Orders detail view.

Problem:
In /admin/planning-orders, the Commercial tab can show contradictory messages at the same time:

- positive headline:
  "Commercial setup is complete. This order is commercially ready for release."
- but also a fix hint:
  "Please open Customers -> ... -> Commercial and complete the missing commercial master data there."

This creates a misleading UX because the page tells the user both:
- the order is commercially ready
- and that commercial master data is still missing

Repository context:
The affected file is:
- web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue

Relevant supporting files:
- web/apps/web-antd/src/sicherplan-legacy/i18n/planningOrders.messages.ts
- web/apps/web-antd/src/sicherplan-legacy/features/planning/planningOrders.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts

Current behavior:
In the Commercial tab panel of PlanningOrdersAdminView.vue:
- the headline uses commercialSummaryKey
- the context line uses commercialContextKey
- but the fix hint paragraph (commercialFixHint / commercialFixHintFallback)
  is rendered unconditionally
- and the "Open customer commercial settings" CTA also appears unconditionally

This means the fix hint is shown even when:
- selectedOrderCommercial.is_release_ready === true
- blocking_issues is empty
- warning_issues is empty

Goal:
Make the Commercial tab messaging consistent with the actual commercial readiness state.

Required behavior:
1. If commercial readiness is fully satisfied:
   - show the positive headline
   - show the positive context line
   - DO NOT show the "complete missing commercial master data" hint
   - DO NOT show the "Open customer commercial settings" CTA unless there is a real warning/blocking reason to act

2. If commercial readiness is blocked:
   - show the blocked headline/context
   - show the fix hint
   - show the CTA to open customer commercial settings
   - show blocking issues list if present

3. If commercial readiness has warnings but is not blocked:
   - show the warning headline/context
   - optionally show a softer review-oriented hint
   - only show CTA if user action is actually useful
   - do not use wording that says data is missing if readiness is still true

Implementation guidance:
A. In PlanningOrdersAdminView.vue:
- introduce computed booleans such as:
  - hasCommercialBlockingIssues
  - hasCommercialWarningIssues
  - showCommercialFixHint
  - showCommercialSettingsCta
- derive them from:
  - selectedOrderCommercial?.is_release_ready
  - orderCommercialBlockingIssues
  - orderCommercialWarningIssues

B. Suggested logic:
- showCommercialFixHint = orderCommercialBlockingIssues.length > 0
- showCommercialSettingsCta = orderCommercialBlockingIssues.length > 0 || orderCommercialWarningIssues.length > 0
- if is_release_ready === true and there are no blocking issues and no warning issues:
  - do not show fix hint
  - do not show CTA

C. If you want a separate hint for warnings:
- add a new i18n key such as:
  - commercialReviewHint
- wording should be review-oriented, not “missing data” oriented

D. Keep the existing summary/context key mechanism if it is already correct.
Only fix the contradictory unconditional hint/CTA rendering.

E. Do not change backend business logic.
This is a frontend display/conditional-rendering fix only.

F. Do not alter unrelated tabs or order/planning APIs.

Acceptance criteria:
- The Commercial tab no longer shows contradictory “ready” and “missing data” messages together.
- When the order is commercially ready, only ready-state messaging is shown.
- The fix hint appears only when blocking issues really exist.
- The CTA appears only when there is a meaningful next action.
- No backend files are changed.

Before coding:
Briefly summarize which computed properties and template conditions you will add/change.

After coding:
Provide:
1. files changed
2. old vs new rendering logic summary
3. confirmation that backend behavior was not changed
4. any optional follow-up UX improvements
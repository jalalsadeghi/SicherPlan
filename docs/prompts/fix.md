You are working on the latest main branch of the public repository `jalalsadeghi/SicherPlan`.

Task
Fix a UX bug in the admin customers workspace so that after saving or updating data from a non-Overview tab, the UI stays on the same active tab instead of jumping back to the first tab (`Overview`).

Inspect first
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.layout.test.js
- any nearby Vitest / Vue Test Utils helpers already used by the web workspace
- optionally inspect small nearby helper files already imported by CustomerAdminView if they are the right place for tiny tab-validation helpers

Observed problem
- The customers admin page has multiple detail tabs:
  - overview
  - contacts
  - addresses
  - commercial
  - portal
  - history
  - employee_blocks
- The commercial tab also has nested tabs:
  - billing_profile
  - invoice_parties
  - pricing_rules
- The pricing_rules tab has another nested level:
  - rate_cards
  - rate_lines
  - surcharges
- The currently selected tabs are controlled in the view layer by:
  - activeDetailTab
  - activeCommercialTab
  - activePricingRulesTab
  - and selectedRateCardId for the selected pricing context
- After successful save/update flows, the page often reloads the selected customer detail through selectCustomer(...) or equivalent refresh logic.
- During that reload, the tab state is reset:
  - activeDetailTab goes back to `overview`
  - activeCommercialTab goes back to `billing_profile`
  - pricing context may also be lost
- As a result, the user loses context and must manually reopen the same tab/subtab to verify the saved data.

Required behavior
1. When the user saves/updates data from a non-Overview detail tab, keep the same detail tab active after the refresh.
2. If the user is inside `commercial`, preserve:
   - the active commercial sub-tab
   - and if relevant, the active pricing sub-tab
3. If the user is inside `commercial -> pricing_rules`, preserve:
   - activeDetailTab = `commercial`
   - activeCommercialTab = `pricing_rules`
   - activePricingRulesTab = the previously active one
   - selectedRateCardId when still valid
4. Preserve tab state only for “reload the same selected customer after mutation/refresh” flows.
5. Keep the existing “new customer” create flow safe:
   - while creating a brand-new customer, `Overview` may remain the only valid/active tab
   - after first creation, fallback to a valid tab if needed
6. If any previously active tab/subtab becomes invalid after reload, fall back safely:
   - invalid detail tab -> `overview`
   - invalid commercial tab -> `billing_profile`
   - invalid pricing tab -> `rate_cards`
   - invalid selectedRateCardId -> first valid rate card or empty state
7. Do not add localStorage, route-query persistence, or unrelated global state unless absolutely necessary.
8. Do not change backend APIs or business rules.

Implementation guidance
- Make the smallest safe front-end change.
- Refactor the customer reload/select flow so it can preserve the current tab context when appropriate.
- A good approach is to refactor `selectCustomer(...)` to accept an options object, for example:
  - preserveDetailTab?: boolean
  - fallbackDetailTab?: string
  - preferredDetailTab?: string
  - preserveCommercialTab?: boolean
  - fallbackCommercialTab?: string
  - preferredCommercialTab?: string
  - preservePricingRulesTab?: boolean
  - fallbackPricingRulesTab?: string
  - preferredPricingRulesTab?: string
  - preserveSelectedRateCard?: boolean
  - preferredRateCardId?: string
- Add tiny helpers that validate:
  - desired detail tab against currently available detail tabs
  - desired commercial tab against allowed commercial tabs
  - desired pricing tab against allowed pricing tabs
  - desired selectedRateCardId against current commercialProfile.rate_cards
- Use tab preservation in post-save/post-update reload paths for the same selected customer.
- It is acceptable to keep explicit manual “start create customer” behavior on `overview`.

Important constraints
- Keep the fix local to the customers admin page unless a tiny shared helper is clearly better.
- Avoid unrelated refactors, renames, formatting churn, or permission-model changes.
- Preserve the current tab only when it is still valid in the current UI state.
- Do not break permission-gated tabs, especially `commercial`.
- Do not break the nested pricing tabs or the selected rate-card behavior.

Acceptance criteria
- Editing data in `Contacts` and saving keeps the user on `Contacts`.
- Editing data in `Addresses` and saving keeps the user on `Addresses`.
- Editing data in `Commercial -> Billing Profile` and saving keeps the user on `Commercial -> Billing Profile`.
- Editing data in `Commercial -> Invoice Parties` and saving keeps the user on `Commercial -> Invoice Parties`.
- Editing data in `Commercial -> Pricing Rules -> Rate Cards` and saving keeps the user on the same pricing context.
- Editing data in `Commercial -> Pricing Rules -> Rate Lines` and saving keeps the user on `Rate Lines`.
- Editing data in `Commercial -> Pricing Rules -> Surcharges` and saving keeps the user on `Surcharges`.
- Editing data in `Portal`, `History`, or `Employee Blocks` and saving keeps the user on the same tab after save/update.
- If a tab becomes unavailable after reload, the UI falls back safely without errors.
- Starting a brand-new customer still behaves safely and does not expose invalid tabs before the record exists.

Search hints
Look for:
- `activeDetailTab`
- `activeCommercialTab`
- `activePricingRulesTab`
- `selectedRateCardId`
- `overview`
- `billing_profile`
- `rate_cards`
- `selectCustomer(`
- post-submit success handlers that reload the selected customer
- refresh logic that re-selects the current customer
- anywhere that resets nested tabs during reload

Likely places to audit carefully
- selectCustomer(...)
- refreshCustomers()
- submitCustomer()
- submitContact()
- submitAddress()
- submitBillingProfile()
- submitInvoiceParty()
- submitRateCard()
- submitRateLine()
- submitSurchargeRule()
- submitPortalPrivacy()
- submitCustomerPortalAccess()
- submitCustomerPortalAccessPasswordReset()
- unlinkCustomerPortalAccount()
- submitHistoryAttachmentLink()
- submitEmployeeBlock()
- any success handler that calls selectCustomer(...) or refreshCustomers() for the same customer

Testing
- Add regression test(s) for this bug.
- Prefer a real component behavior test if practical.
- At minimum, add focused regression coverage that proves:
  1. the customer admin view can preserve a non-Overview detail tab after a successful same-customer reload
  2. the customer admin view can preserve nested commercial tab state
  3. invalid tab state falls back safely
- If the existing test harness makes a full behavior test impractical, add the smallest focused regression test around the tab-preservation logic and explain the limitation in the final summary.

Deliverables
- Code change
- Regression test(s)
- Final summary including:
  - root cause
  - files changed
  - why the fix works
  - which tab levels are preserved
  - any edge cases intentionally handled
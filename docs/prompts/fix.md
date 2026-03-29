You are working in the SicherPlan web admin frontend/backend.

Task:
Fix three issues in the Customer → Addresses tab address-link workflow on `/admin/customers`.

Current problems observed:

1. A shared address can only be used once and then disappears from the `Address` selector, even when the user wants to use the same address for a different `Address type`.
   This is incorrect.
   A single address should be reusable for multiple address types for the same customer.
   Only exact duplicate links of the same `(customer, address_id, address_type)` should be prevented.

2. Addresses created/linked in one customer context are appearing in the `Address` selector for a different customer.
   This is incorrect for the intended UX.
   The address selector for a customer should only show addresses that are valid/available for that specific customer workflow.

3. The `Address type` field is visually misaligned because the `Create new address` button is placed inside the same field stack as the `Address` selector.
   The layout needs to be cleaned up.

Important:
- Fix the active runtime path, not just docs/tests.
- Preserve the domain model unless clearly broken.
- Do not weaken duplicate protection entirely.
- Do not introduce fake data.
- Keep backend validation strict but correct.
- Keep the ability to create a new shared address from the current flow if it already exists.

Domain intent to preserve:
- `common.address` is the shared/master address record.
- customer address linking should be done through a customer-address link entity with `address_type`.
- The same physical/shared address should be reusable for multiple address types for the same customer.
- What must be blocked is only a duplicate of the same address for the same customer and same address_type.

Required fixes:

A) Fix duplicate filtering logic for address reuse
Investigate both frontend and backend rules.

Desired behavior:
- For the current customer, if address `X` is already linked as `mailing`, it must still remain selectable when the user chooses `billing`, `service`, or `registered`.
- The selector should only exclude address options that already exist for the same customer AND the currently selected `address_type`.
- If editing an existing link, keep the current address selectable as well.

Do not:
- globally remove duplicate protection
- allow duplicate `(customer_id, address_id, address_type)` rows

B) Fix customer scoping of address selector options
Investigate how the current `Address` selector options are loaded.

Observed bad behavior:
- addresses associated with customer `TestCus` appear for customer `Customer02`

Desired behavior:
- the selector should not show cross-customer addresses unless the product explicitly intends a global cross-customer reusable address directory for this step
- based on current UX expectations, the selector should only show addresses relevant to the selected customer flow

Implement the correct source/filter so that:
- customer A does not see customer B’s linked-address candidates by default
- newly created address options become available in the current customer flow appropriately
- if shared address records remain global in storage, the selector still needs customer-scoped filtering in this workflow

If necessary, separate:
- shared address creation
- customer-specific eligible address options

C) Clean up layout of `Address` and `Address type`
Current issue:
- `Create new address` is placed inside the `Address` field stack and breaks alignment of the row

Desired layout:
- `Address` selector and `Address type` should align cleanly in one row on desktop
- `Create new address` should not distort field height or grid alignment

Preferred UX:
- move `Create new address` into a clean header/action row for the address selector field
- for example:
  - a small field-header row above the Address selector with:
    - label on the left
    - action button on the right
- or place it in the form-section header / dedicated inline action row
- keep the CTA close to the Address selector, but not inside the select field stack in a way that breaks layout

D) Keep empty-state behavior clear
When no selectable addresses are available for the current customer and selected address type:
- show a clear empty-state hint
- keep the `Create new address` CTA visible and useful
- make the hint customer-specific and workflow-specific

E) Verify downstream impact
After fixing this flow:
- address linking should create clean linked-address rows
- invoice-party billing-address selection should continue to work correctly from the customer’s linked addresses
- no cross-customer leakage should appear there either

Required investigation steps:
1. Inspect the active `/admin/customers` Addresses tab implementation.
2. Inspect how address options are loaded and filtered.
3. Inspect backend/customer repository and service duplicate rules for customer addresses.
4. Confirm whether the issue is:
   - frontend filtering bug
   - backend uniqueness/duplicate bug
   - customer scoping bug
   - or a combination

Acceptance criteria:

1. The same address can be linked to the same customer under different address types.
   Example:
   - same address allowed for `billing`
   - and also allowed for `mailing`
   - but not duplicated twice for `billing`

2. Address selector options are properly customer-scoped.
   Customer02 should not see TestCus-specific linked addresses in this workflow.

3. `Address` and `Address type` appear visually aligned and clean.
   `Create new address` no longer breaks the layout.

4. Existing create/edit/cancel flows continue to work.

5. Tests are added/updated for:
   - duplicate same-address different-type allowed
   - duplicate same-address same-type blocked
   - customer-scoped selector options
   - layout selectors/test IDs if appropriate

Work process:
1. Identify active frontend and backend files
2. Summarize root cause for each of the 3 problems
3. Implement the smallest clean fix
4. Add/update tests
5. Provide a concise summary:
   - files changed
   - duplicate rule behavior after fix
   - customer scoping behavior after fix
   - layout adjustment made for Create new address / Address type
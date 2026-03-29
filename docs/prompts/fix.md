You are working in the SicherPlan project.

Task:
Investigate and fix the `400 Bad Request` problem when saving the Customer Commercial → Billing profile form, and improve the frontend so the user sees the exact reason instead of a vague generic message.

Observed behavior:
- Frontend shows:
  `Billing profile could not be saved due to an unexpected error. Please try again or contact support.`
- Backend returns:
  `PUT /api/customers/tenants/{tenant_id}/customers/{customer_id}/billing-profile` -> `400 Bad Request`

Current form values indicate that the issue is likely NOT the previously discussed e-invoice / Leitweg rule.
Based on the current entered values, the most likely cause is lookup validation for one of these code-backed fields:
- invoice_layout_code
- shipping_method_code
- dunning_policy_code

In backend commercial validation, these fields are validated against lookup domains:
- `invoice_layout`
- `invoice_delivery_method`
- `dunning_policy`

Likely current UI values:
- invoice layout = `standard`
- dispatch method = `email_pdf`
- dunning policy = `standard`

Potential root cause:
The frontend dropdown options are present, but one or more of these codes are not actually available in backend lookup data / database seed data, causing a 400 validation failure.

Required work:

1. Investigate the exact backend error
- Inspect the real response body returned by the billing-profile save endpoint.
- Identify the actual `message_key` / error payload for this 400.
- Confirm whether the cause is lookup validation (`errors.customers.lookup.not_found` or related field-specific lookup validation).

2. Fix the frontend error handling
- The frontend must stop collapsing this into a generic unexpected error.
- Surface the real backend validation message clearly.
- If the problem is one of the lookup-backed dropdowns, show a user-facing message like:
  - `The selected Invoice layout is not available in the system configuration.`
  - `The selected Dispatch method is not available in the system configuration.`
  - `The selected Dunning policy is not available in the system configuration.`

3. Verify the actual source of dropdown options
- Inspect the active customer commercial form implementation.
- Determine whether `Invoice layout`, `Dispatch method`, and `Dunning policy` are currently:
  - hardcoded in the frontend, or
  - loaded from real backend lookup/reference data.
- If they are hardcoded but backend requires real lookup-backed values, fix this mismatch.

4. Preferred fix strategy
Use the real source of truth.
- If lookup/reference-data endpoints or existing frontend sources already exist, load those values dynamically.
- Do not keep static frontend dropdown options if they can drift from backend validation.
- If the repo expects these lookup values to exist in seed/bootstrap data, add/repair the required seed/setup entries.
- Do not invent random codes; align exactly with backend-supported lookup codes.

5. Keep UX clear
- If a dropdown has no valid lookup-backed options, the user should be told that system configuration is missing.
- Do not let the user pick values that backend will reject.
- Show field-level error state for the affected dropdown.

6. Acceptance criteria
- Saving billing profile no longer fails because of frontend/backend lookup mismatch.
- Known 400 validation errors are shown clearly to the user.
- Dropdown options for invoice layout / dispatch method / dunning policy are aligned with backend-supported lookup values.
- No vague “unexpected error” message is shown for known validation failures.
- No backend business rule is weakened.

Work process:
1. Inspect the active customer commercial form implementation.
2. Inspect the billing-profile save API response handling.
3. Inspect lookup-loading or seed data for:
   - invoice_layout
   - invoice_delivery_method
   - dunning_policy
4. Summarize root cause.
5. Implement the smallest clean fix.
6. Report:
   - files changed
   - exact root cause
   - whether the issue was static frontend options, missing lookup data, or both
   - how the new error message is shown to the user
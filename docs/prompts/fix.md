You are working in the SicherPlan repository.

Task:
Fix the frontend bug in Customer Admin > Commercial > Pricing rules > Rate lines where submitting the form fails silently when "Minimum quantity" is filled, but succeeds when that field is empty.

Observed behavior:
- Clicking "Create rate line" with Minimum quantity filled does not create any network request.
- No backend POST is triggered.
- The UI only shows the generic fallback message "The customer action failed."
- Leaving Minimum quantity empty allows the form to submit successfully.

Root cause hypothesis:
The submit path is doing string-style normalization on a value that may be a number.
In Vue, input[type="number"] can bind as a number, while an empty field becomes an empty string.
So any helper that assumes `.trim()` is always available will break at runtime before the request is sent.

Primary target:
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue

Secondary targets if needed:
- any nearby customer commercial helper file if the normalization logic should be extracted
- relevant customer admin frontend tests

Important constraints:
- Do NOT change backend API contracts.
- Do NOT change backend validation, database models, or migrations.
- Preserve current request payload semantics for customer pricing APIs.
- The fix must be frontend-only unless you find a proven blocker that absolutely requires backend change.

What to change:
1. Inspect the Rate line submit path in CustomerAdminView.vue, especially:
   - submitRateLine()
   - normalizeRateLineDraft()
   - emptyToNull() or any equivalent normalization helper
   - the reactive draft fields used for:
     - unit_price
     - minimum_quantity
     - sort_order
     - any other numeric commercial inputs that may pass through string-only helpers

2. Fix the normalization bug so optional scalar form values are safe when they are:
   - string
   - number
   - null
   - undefined
   - empty string

3. Replace any helper that currently assumes string-only input with a safer helper, for example:
   - normalizeOptionalScalar(value)
   or equivalent naming
   Requirements:
   - null/undefined => null
   - empty string / whitespace-only string => null
   - number => String(value)
   - non-empty string => trimmed string
   - never call .trim() directly on a number

4. Update normalizeRateLineDraft() so:
   - minimum_quantity is normalized safely
   - unit_price is normalized safely
   - function_type_id / qualification_type_id / planning_mode_code / notes still work correctly
   - the payload sent to createCustomerRateLine / updateCustomerRateLine remains compatible with the existing API client expectations

5. Review the rest of CustomerAdminView.vue for the same bug pattern.
   Search for all uses of:
   - emptyToNull(...)
   - .trim()
   on values coming from form inputs
   Especially check numeric commercial fields such as:
   - billing payment_terms_days
   - rate card numeric/date-adjacent normalization
   - surcharge numeric fields
   Only fix places that are genuinely vulnerable; avoid unrelated refactors.

6. Keep the current user flow unchanged:
   - Minimum quantity filled => submit works
   - Minimum quantity empty => submit still works
   - No extra confirmation dialogs
   - No behavior change in successful backend payload handling

7. Improve resilience of the submit path:
   - ensure submitRateLine does not fail before the request due to scalar normalization
   - preserve existing error handling for actual API errors
   - do not swallow runtime errors silently in a way that hides regressions from tests

Tests to add/update:
1. Add or update focused frontend tests covering:
   - submitting a Rate line with minimum_quantity = 4 succeeds and triggers the create request
   - submitting a Rate line with minimum_quantity empty succeeds and sends null/empty-compatible payload
   - normalization helper handles string, number, empty string, null, undefined correctly
   - no runtime TypeError occurs when numeric fields are filled

2. Prefer targeted tests over snapshot-heavy tests.
3. If there is already a customer admin test file, extend it.
4. If needed, add a small unit test around the normalization helper.

Acceptance criteria:
- Filling "Minimum quantity" no longer blocks submission.
- A real network request is triggered when the form is valid.
- Leaving "Minimum quantity" empty still works.
- No `.trim is not a function`-style runtime failure remains in the Rate line submit path.
- Existing backend payload shape is preserved.
- Relevant regression tests pass.

Implementation guidance:
- Keep the patch minimal and localized.
- Prefer one reusable safe normalization helper over ad hoc fixes.
- Avoid broad refactors unrelated to this bug.

Before coding:
Briefly state:
- which file(s) you will edit
- where the failing normalization happens
- what helper strategy you will use

After coding:
Provide:
1. files changed
2. exact root cause confirmed
3. summary of the fix
4. tests added/updated
5. any remaining similar-risk spots you noticed
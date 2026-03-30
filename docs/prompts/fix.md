You are working in the SicherPlan repository.

Task title:
Fix customer dropdown labels so select options show only human-readable names/labels, not code + label.

Problem:
In the Customer Admin UI, dropdown options currently render values like:
- "standard - Standardkunde"
- "test-branch - Test Breanch"
But in user-facing dropdowns they should display only:
- "Standardkunde"
- "Test Breanch"

Current root cause:
In:
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.js

the helper:
- formatCustomerReferenceLabel(record)

currently formats records as:
- code + " - " + name
or
- code + " - " + label

This helper is then reused by CustomerAdminView.vue for select option labels, which makes dropdowns show technical codes to end users.

Important constraint:
Do NOT change the underlying select values.
The option value must remain the existing UUID / stored value.
Only the visible text in dropdowns should change.

Relevant files to inspect:
- web/apps/web-antd/src/sicherplan-legacy/features/customers/customerAdmin.helpers.js
- web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/customers.ts
- relevant tests in the customer frontend area

Goal:
Make all customer-facing dropdowns in Customer Admin show only human-readable labels/names, while keeping internal values unchanged.

Implementation requirements:

A) Refactor formatting helpers
1. Do not keep using one shared formatter for both:
   - user-facing select options
   - summary/debug/internal display labels

2. Introduce separate helpers, for example:
   - formatCustomerReferenceOptionLabel(record)
     -> returns only record.name or record.label
   - formatCustomerReferenceDisplayLabel(record)
     -> may preserve code + label if still needed elsewhere
   Use naming consistent with repo style.

3. For option label behavior:
   - if record has "name", show only record.name
   - else if record has "label", show only record.label
   - fallback to record.code only if label/name is truly missing

B) Apply to CustomerAdminView
4. Update all customer dropdowns in CustomerAdminView.vue to use the option-only formatter.
   This includes at least:
   - customer filters:
     - default branch
     - default mandate
   - customer overview form:
     - legal form
     - classification
     - ranking
     - customer status metadata
     - default branch
     - default mandate
   - any other selects in this view currently using formatReferenceLabel(...) for option text

5. Keep the select value attribute exactly as it is today.
   Only visible text should change.

C) Preserve non-dropdown displays carefully
6. Review where formatCustomerReferenceLabel() is used for:
   - summary cards
   - selected-customer summary labels
   - read-only metadata
7. Decide carefully:
   - if those should also become label-only for consistency, update them
   - if they are meant to remain code + label, switch them to a display-specific formatter
8. Do not accidentally degrade other UI contexts.

D) UX consistency
9. Ensure dropdown placeholders like "Not set" remain unchanged.
10. Do not show technical codes in normal user selection controls unless no label/name exists.

E) Tests
11. Add or update frontend tests to verify:
   - legal form dropdown option renders "GmbH", not "gmbh - GmbH"
   - classification dropdown option renders "Standardkunde", not "standard - Standardkunde"
   - branch dropdown option renders "Test Breanch", not "test-branch - Test Breanch"
   - select option values still remain the same UUIDs / stored identifiers
12. Avoid brittle snapshot-only coverage if more direct assertions are possible.

Acceptance criteria:
- Customer-facing dropdown options show only human-readable names/labels.
- Technical codes are no longer visible in select option text.
- Underlying submitted values are unchanged.
- Any summary/read-only display remains intentional and not accidentally broken.

Before coding:
Provide a short plan listing:
- which helper functions you will introduce or change
- which selects in CustomerAdminView will be updated
- whether summary/read-only labels will stay code+label or become label-only

After coding:
Provide:
1. files changed
2. exact root cause
3. exact fix
4. examples before/after
5. test evidence
6. any follow-up items
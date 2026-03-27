Important visual correction for /admin/subcontractors:

Please compare the current `/admin/subcontractors` page carefully against `/admin/customers`.

The left panel on `/admin/subcontractors` ("Partner list") is currently too narrow and too small.
It must be increased so that it matches the left panel on `/admin/customers` ("Customer list") in width, visual footprint, spacing rhythm, and overall card proportions.

Required correction:
- The left "Partner list" card must have the same width as the left "Customer list" card on `/admin/customers`.
- It must no longer appear narrower or more compressed than the customer list panel.
- It should still remain smaller than the right detail panel, exactly like the master-detail balance on the customer page.

Target layout rule:
- Reuse the same master-detail column proportions used by `/admin/customers`.
- If possible, reuse the same grid definition, shared layout class, or width token used by the customer page.
- Do not invent a new narrower width for subcontractors.

Visual expectations:
- "Partner list" should align with "Customer list" in:
  - width
  - card padding
  - header spacing
  - filter field spacing
  - checkbox spacing
  - CTA row spacing
  - result-list area rhythm
- The right "Detail view" must remain the dominant workspace, but the left card should feel equally substantial as the customer page’s left card.

Implementation guidance:
- Inspect the exact grid/container styles used by the customer admin page.
- Apply the same left-column sizing logic to the subcontractor page.
- Prefer shared styling or shared layout composition over one-off values.
- If the customer page uses a fixed or constrained left column width, mirror that exactly.

Do NOT do this:
- Do not keep the subcontractor left panel narrower than the customer left panel
- Do not make both columns equal width
- Do not shrink the left card just because the subcontractor list is currently empty

Important:
- This is a frontend-only UI/layout correction.
- No backend changes
- No API changes
- No state-management or business-logic changes

Acceptance criteria:
- The left "Partner list" panel on `/admin/subcontractors` has the same width and visual scale as the left "Customer list" panel on `/admin/customers`
- The right detail panel remains wider than the left panel
- The overall page balance now matches the customer page much more closely
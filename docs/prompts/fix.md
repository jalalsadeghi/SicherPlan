You are working in the SicherPlan web admin frontend.

Task:
Refactor the `Customers -> Commercial -> Pricing rules` workspace so that `Rate cards`, `Rate lines`, and `Surcharges` are organized as three separate tabs instead of being shown stacked in one long page.

Goal:
Make the Pricing Rules area cleaner and easier to use.

Current problem:
Inside the current `Pricing rules` panel:
- `Rate cards` is shown first
- after a rate card exists, `Rate lines` and `Surcharges` appear below it in the same page
- this makes the workspace too long and visually crowded

Desired UX:
- `Rate cards`, `Rate lines`, and `Surcharges` should become three sub-tabs inside the Pricing Rules area
- before any rate card exists, only the `Rate cards` tab should be visible
- after at least one rate card exists, the other two tabs should become visible:
  - `Rate lines`
  - `Surcharges`

Important scope:
- Frontend only
- No backend changes
- No API changes
- No schema/model changes
- No business-logic changes
- No permission/auth/session changes
- No unrelated refactors

Critical instruction:
First inspect the ACTUAL active component that powers:
`/admin/customers` -> `Commercial` -> `Pricing rules`

Do not edit an inactive file unless you confirm it is the real active path.

Reference pattern:
Reuse the same UI/UX idea already used elsewhere in the customer workspace:
- top-level tabs in `Customer detail`
- sub-tabs in `Commercial`
Keep styling aligned with existing `customer-admin-tabs` / `customer-admin-tab--sub` patterns.

Required behavior:

1) Introduce sub-tabs inside Pricing Rules
Inside the current `Pricing rules` panel, add a second tab level for:
- `Rate cards`
- `Rate lines`
- `Surcharges`

Use stable internal IDs such as:
- `rate_cards`
- `rate_lines`
- `surcharges`

2) Visibility rules
Before any rate card exists:
- show only the `Rate cards` tab
- do NOT show the `Rate lines` and `Surcharges` tabs yet
- do NOT show disabled dead tabs if that makes the UI cluttered
- the screen should make it obvious that the user must first create a rate card

After at least one rate card exists:
- show all three tabs
- allow switching between them
- default to:
  - `Rate cards` when first entering the area
  - keep current/active sub-tab stable during normal interaction when possible

3) Content mapping
Map the current content into the new tabs as follows:

Tab: `Rate cards`
Contains:
- Rate cards header
- Add rate card button
- rate card list/selector
- rate card create/edit form

Tab: `Rate lines`
Contains:
- Rate lines header
- Add rate line button
- rate lines list
- rate line create/edit form

Tab: `Surcharges`
Contains:
- Surcharges header
- Add surcharge rule button
- surcharge rules list
- surcharge rule create/edit form

4) Dependency behavior
`Rate lines` and `Surcharges` depend on a selected rate card.

Therefore:
- these tabs should only appear when at least one rate card exists
- inside those tabs, if a rate card exists but none is selected, automatically select the current/default one
- do not break the current selectedRateCard behavior
- preserve existing create/edit/cancel flows for rate lines and surcharge rules

5) Preserve existing functionality
Do not break:
- rate card creation
- rate card selection
- rate line creation/edit
- surcharge creation/edit
- current selected rate card state
- existing loading states
- existing validation behavior
- current success/error feedback behavior

6) Improve readability
The current UI is visually too dense.
After the refactor:
- only one pricing-rules subsection should be visible at a time
- spacing and panel rhythm should remain aligned with the customer admin design
- avoid nesting too many stacked sections in the same visible panel

7) Implementation guidance
- Reuse existing `customer-admin-tabs customer-admin-tabs--sub` styling if possible
- Prefer a minimal clean diff
- Add a local sub-tab state for the pricing-rules workspace
- Gate tab visibility using the real existence of `commercialProfile.rate_cards.length`
- Avoid broad restructuring outside the Pricing Rules area

8) Acceptance criteria
- Pricing Rules is split into three sub-tabs:
  - Rate cards
  - Rate lines
  - Surcharges
- Before any rate card exists:
  - only Rate cards tab is visible
- After a rate card exists:
  - Rate lines and Surcharges tabs appear
- Only the active pricing-rules sub-tab content is visible
- Existing pricing logic and form behavior remain intact
- No backend code is touched

Work process:
1. Identify the active frontend file(s)
2. Summarize which file(s) you will change
3. Implement the smallest clean refactor
4. Run relevant frontend checks if available
5. Provide a concise summary of:
   - files changed
   - pricing-rules sub-tab structure introduced
   - visibility logic for the tabs
   - confirmation that no backend code was touched
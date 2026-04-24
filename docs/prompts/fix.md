Add/update regression tests for the Customers > Contacts & Access left-nav layout bug.

Goal:
The left-side section navigation must stay sticky/visible without collapsing the page layout during scroll or click-to-scroll.

Required coverage:

Test 1 — Stable two-column structure
1. Mount /admin/customers with Contacts & Access tab active.
2. Assert the main layout has:
   - left nav container
   - right content container
3. Assert the content container is a sibling of the nav container, not nested incorrectly.
4. Assert the layout wrapper keeps its intended grid/flex classes.

Test 2 — Sticky/fixed behavior does not remove layout width
If the implementation uses fixed fallback:
1. Simulate the scroll state where nav becomes fixed.
2. Assert the nav shell gets the fixed/sticky class/state.
3. Assert the layout still keeps a reserved nav column / placeholder width.
4. Assert the content wrapper width/layout classes remain intact.

Test 3 — Click-to-scroll does not collapse layout
1. Mock scrollIntoView.
2. Click Addresses link.
3. Assert scrollIntoView is called for Addresses section.
4. Assert no layout-collapse class/state is introduced.
5. Assert the content wrapper remains present and structurally separate from the nav.

Test 4 — Active link behavior still works
1. Mock IntersectionObserver or the current section-detection logic.
2. Simulate Contacts active, then Addresses active, then Portal & Access active.
3. Assert the active nav item changes correctly.
4. Assert layout structure remains unchanged during those state changes.

Test 5 — No regression to Employees Overview pattern
1. If a shared helper/composable is used, assert the Customers page uses the same pattern safely.
2. Do not regress Employees Overview behavior.

Test 6 — Responsive fallback
1. Assert narrow-screen layout still behaves safely.
2. The nav may become static/horizontal on small screens, but layout must not collapse.

Commands:
- run the relevant customer admin/frontend vitest suites
- run vue-tsc --noEmit --skipLibCheck
- include exact commands in final output

Manual QA checklist:
1. Open /admin/customers
2. Go to Contacts & Access
3. Confirm layout looks correct initially
4. Scroll down
5. Confirm left nav stays visible and page layout does NOT collapse
6. Click Addresses
7. Confirm scroll works and layout still does NOT collapse
8. Click Portal & Access
9. Confirm same result
10. Confirm no console errors

Final output must include:
- files changed
- tests added/updated
- commands run
- root cause of the collapse
- proof the sticky nav works without reflow/collapse
You have already implemented the new customer Plans tab in the SicherPlan repository.

Now do a focused hardening + validation pass.

IMPORTANT:
First validate the implementation against the current checked-out branch, not against assumptions from GitHub main.
Explicitly verify whether the final implementation matches the following proposal:
- tab id is `plans`
- tab placement is immediately after Portal and before History
- same /admin/customers route + query-tab contract is preserved
- the chosen "plan" source is the correct canonical entity for this branch
- search is truthful
- sorting is truthful
- color semantics are validated against actual serialized values

Scope:
Do NOT add unrelated features.
Only fix correctness, UX, typing, data-contract, and maintainability issues around the Plans tab.

Validation and hardening checklist:

1. Domain correctness
- Re-check whether "plan" in this branch is truly PlanningRecord or CustomerOrder.
- If your first implementation picked the wrong domain object, correct it now and explain why.
- Ensure the user-facing list and filters match the actual business meaning already used by the current branch.

2. Data truthfulness
- Re-check that registration-date sorting is based on a real created_at field, not an approximation.
- Re-check that execution-date sorting uses planning_from / planning_to (or the canonical equivalents if the branch uses orders).
- Re-check that search uses the intended backend filter and not only client-side fuzzy filtering.

3. Status and colors
- Compare the status/display-state mapping against actual values returned by the real serializer in this branch.
- Reuse existing repo color patterns where possible.
- Ensure the colored card/row styles are subtle, accessible, and work in light + dark themes.
- Expose stable classes or data attributes for testing. Do NOT make tests depend on literal CSS colors.

4. Routing and tab behavior
- Deep-link `tab=plans` must work.
- Switching between customers must not leave stale plan data behind.
- Create mode must still hide the Plans tab.
- Existing dashboard/overview/portal/history flows must not regress.

5. Performance and DX
- Ensure no N+1 detail fetching was introduced for the list.
- If request caching exists, key it correctly by tenant + customer + search + sort.
- Keep the component reasonably focused; extract tiny helpers/composables if needed, but avoid broad refactors.

6. Permission safety
- Re-verify that users without the canonical planning read permission cannot see plan data.
- Ensure the customer workspace does not accidentally broaden access just because the tab sits under Customers.

7. Tests
Add/fix tests for:
- permission-restricted state
- no created_at regression
- no stale results after switching customer
- search debounce behavior
- sort stability
- unknown status fallback
- no visual overflow on long titles
- dark-mode legibility if the branch already has theme tests/patterns

Deliverables:
- short validation report comparing the final code to the proposal above
- bug list of what you fixed in the hardening pass
- changed files
- test results
- any real remaining limitation
Avoid unrelated refactors.
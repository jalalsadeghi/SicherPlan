You have already implemented the customer dashboard tab feature in the SicherPlan repository.

Now do a focused hardening pass.
Do NOT add new features.
Only fix integration issues, typing gaps, edge cases, permission leaks, and UX rough edges around this feature.

Review and improve:

1. Backend
- endpoint naming consistency
- schema consistency
- tenant isolation
- authorization correctness
- null/empty handling
- truthful semantics for the finance aggregate
- stable ordering and hard limit for latest 5 plans

2. Frontend
- create vs existing customer tab behavior
- default tab selection logic
- deep-link tab behavior
- loading / empty / error states
- permission-aware finance visibility
- responsive layout and no visual overflow
- date / currency formatting consistency
- i18n completeness
- test-id consistency

3. Shared calendar reuse
- ensure the reused/extracted calendar did not regress the main dashboard
- keep customer filtering strict and explicit
- verify no unrelated calendar behavior changed

4. Tests
- fill missing tests
- remove brittle assertions
- add coverage for:
  - no plans
  - no finance data
  - restricted finance user
  - no calendar items
  - selected customer switch
  - create mode reset back to overview only

Output:
- a short bug list of what you fixed
- changed files
- any remaining known limitation that is real and grounded in current repo constraints
- avoid unrelated refactors
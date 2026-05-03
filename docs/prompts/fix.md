You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Review the newly implemented `Assignments` step in the customer order workspace wizard and validate that it is correct, coherent, and aligned with the intended business workflow.

Context:
- The order-workspace wizard now has 8 steps, with `Assignments` added after `Demand groups`.
- The feature is intended to provide a user-friendly staffing workflow for generated shifts of the current order.
- It should reuse the project’s existing staffing semantics from `admin/planning-staffing` while fitting naturally into the order-workspace wizard.

You must review both backend and frontend.

Review goals:
1. Confirm the new step is placed correctly and wired correctly.
2. Confirm the step only works on the intended order/shift-plan/generated-shift scope.
3. Confirm the candidate rail behavior is correct:
   - compact and scrollable
   - shows profile/avatar, personnel number, name
   - filters candidates by true suitability
   - considers qualification/function-type fit
   - considers actor kind and workforce scope
   - respects group/team filtering if available
   - prioritizes candidates reasonably
4. Confirm the calendar behavior is correct:
   - defaults to project start month
   - supports previous/next month navigation
   - disables dates outside project execution range
   - colors dates using the correct staffing-state semantics
5. Confirm the assignment interaction is correct:
   - easy to use
   - does not assign workers to blocked/ineligible days
   - handles conflicts/leave/other-project occupancy safely
   - produces understandable feedback
6. Confirm persistence/reload behavior:
   - revisiting the step shows the correct current state
   - loading states and empty states are sensible
7. Confirm workflow/editability behavior:
   - respects backend lock rules
   - does not allow unauthorized editing in locked situations
   - does not break earlier/later wizard-step assumptions
8. Confirm localization, code quality, and maintainability.

You must actively look for issues such as:
- missing edge cases
- accidental duplication of staffing business logic
- inconsistent state labels between planning-staffing and assignments step
- incorrect candidate eligibility
- incorrect month/date boundary logic
- insufficient handling of no generated shifts / no demand groups / no candidates
- broken drag-and-drop fallback behavior
- stale or incomplete persisted state
- visual crowding or unreadable day cells
- lock behavior gaps

Required actions:
A. Inspect changed files.
B. Run the most relevant tests/builds/checks.
C. Trace at least one realistic end-to-end scenario mentally or with available tests:
   - order has generated shifts
   - demand groups exist
   - candidates are filtered
   - assignments are applied
   - step is reopened
D. Identify any defects or risks.
E. If issues are found, fix them.
F. Re-run verification after fixes.

Output format:
- Review scope
- What is working correctly
- Defects found
- Fixes applied
- Verification commands and results
- Final assessment against requirements
- Remaining risks / recommended next improvements

Final self-check:
Explicitly answer whether the implemented feature now satisfies the business request in a standard, scalable, and user-friendly way. If not, say what remains and fix anything reasonably fixable before finalizing.

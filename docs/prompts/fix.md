You are working in the SicherPlan repository.

This task is EPIC 5 from:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Treat that sprint document as the governing source of truth for this implementation.
Read it first before changing any code.

EPIC 5 title:
Permissions, i18n, Hardening, and Non-Regression

Goal
Harden the Customer New Plan Wizard V1 after the earlier epics are implemented.
This epic is not for adding new major features.
It is for:
- role/permission enforcement
- i18n completeness
- UX polish
- error handling
- non-regression coverage
- final review against the sprint brief

Important constraints
- Build on top of EPIC 1 through EPIC 4.
- Do NOT expand the scope of the sprint.
- Do NOT add unrelated new features.
- Do NOT redesign canonical Planning pages.
- Do NOT change business semantics unless a real correctness bug requires it.
- Do NOT assume public GitHub main exactly matches the checked-out branch.

Before coding
Validate the current post-EPIC-4 branch state and output a short summary covering:
1. whether the full wizard path now exists end-to-end
2. whether the New Plan entry point is correctly scoped to Tenant Administrator only
3. whether all new labels are already i18n-driven
4. which major tests already exist and where the gaps are
5. whether there are any obvious regressions in:
   - Customer > Plans
   - canonical Planning Setup
   - Orders & Planning Records
   - Shift Planning
   - Staffing Coverage

Scope for this epic

A. Permission hardening
- Re-check that V1 is truly restricted to Tenant Administrator
- Verify:
  - New Plan button visibility
  - wizard route access
  - quick-create dialog access
  - unauthorized fallback behavior
- Reuse existing role/permission patterns in the branch rather than inventing a parallel auth model

B. i18n completion
- Move any remaining hard-coded UI strings into i18n
- Keep:
  - German first
  - English fallback
- Ensure step labels, dialog labels, button labels, error messages, invalid states, and success/handoff messages are all localized

C. UX polish
- Verify visual consistency of:
  - wizard header
  - stepper
  - footer action bar
  - dialogs
  - loading / empty / invalid states
- Ensure Previous/Next/Cancel behavior is clear
- Ensure responsive behavior remains clean
- Ensure dark mode remains readable if the branch supports it

D. Data-flow hardening
- Re-check that no duplicate records are created when editing previous steps
- Re-check that customer changes reset the wizard safely
- Re-check that failed saves keep the user in the correct step with clear feedback
- Re-check that Generate Series failures do not leave the wizard in a misleading state

E. Non-regression
- Verify no existing Customers behavior was broken
- Verify the canonical Planning pages still behave as before
- Verify the staffing handoff does not broaden or leak data unexpectedly
- Verify no hidden route/menu regressions were introduced

F. Tests
Add or improve tests for:
- unauthorized access
- localized label rendering
- missing customer context
- duplicate-prevention on previous-step edits
- final redirect/handoff correctness
- no regression in the existing Plans tab list
- no regression in canonical Planning routes
- no layout break on narrow widths
- dark mode readability if the branch already tests/themes that area

G. Final sprint review
Compare the implemented feature directly against /docs/sprint/SPR-CUST-NEWPLAN-V1.md and explicitly report:
- what is fully complete
- what is partially complete
- what remains intentionally out of scope for V1
- any real known limitation

Implementation guidance
- Prefer focused fixes over broad refactors
- Reuse existing test helpers and patterns
- Reuse existing i18n naming conventions
- If the branch already has a QA/checklist or implementation-notes convention, you may add a small note, but do not rewrite the sprint brief itself

Output format
At the end, provide:
1. validation summary
2. hardening checklist with pass/fail status
3. changed files
4. tests added/updated
5. test results
6. explicit comparison against /docs/sprint/SPR-CUST-NEWPLAN-V1.md
7. real known limitations still present, if any

Avoid unrelated refactors.
This epic should improve correctness, safety, and readiness, not widen the sprint scope.
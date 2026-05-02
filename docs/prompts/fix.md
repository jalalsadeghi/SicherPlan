/review Please review the implementation for compact applied demand-group cards and edit flows in the customer order wizard `demand-groups` step.

Business requirement:
The `demand-groups` step must show already-applied demand groups in compact, clear cards. Each applied aggregate card must provide:
1. an aggregate Edit action that edits the demand-group definition across all matching generated shifts
2. a per-shift/day edit action that lists individual shifts and allows editing each persisted demand group separately

Review against:
- AGENTS.md
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningShifts.ts`
- `/admin/planning-staffing` behavior
- German default / English secondary localization rules
- existing demand-group bulk apply and applied summary behavior

Review focus:
1. Compact card UI
   - Cards are significantly more compact than before.
   - Fields are readable and not overly tall.
   - Status and applied shift count are visible.
   - Buttons are on the left side as requested.
   - UI follows SicherPlan/Vben/Ant style and does not hardcode one-off colors.

2. Aggregate Edit
   - Opens a modal with correct prefilled values.
   - Updates all matching persisted demand groups safely.
   - Uses a backend aggregate update if available, or a justified safe alternative.
   - Avoids partial-update risks or reports them clearly.
   - Reloads persisted summary after save.
   - Handles mixed/variant aggregates safely.

3. Per-shift/day edit
   - Opens a modal listing all matching shifts/days sorted by start date/time.
   - Shows useful shift context.
   - Allows editing individual rows.
   - Uses the correct single-demand-group update API.
   - Reloads summary after a row edit.
   - Handles locked rows safely.

4. Data correctness
   - Persisted demand groups remain normalized per concrete shift.
   - No shadow persisted template model is introduced.
   - The summary keeps enough underlying row ids and shift metadata.
   - Repeated visits do not duplicate demand groups.
   - Applying new templates still works.

5. Editability / locking
   - Edit actions are disabled or read-only when downstream assignments/releases/field/actual/finance locks exist.
   - If full backend mutation guards are missing, this is called out as follow-up.
   - Previous wizard steps remain navigable for review.

6. Localization and tests
   - New strings are localized in German and English.
   - No hardcoded user-facing strings.
   - Tests cover compact cards, aggregate edit, per-shift edit, validation, lock state, and no regression in New/Apply demand group flows.
   - Build/tests pass.

Required review output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.

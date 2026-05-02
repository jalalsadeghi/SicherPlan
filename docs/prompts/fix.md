You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Task:
Move the `Edit shifts` and `Edit` actions for applied demand-group summary cards into the card header/title row on the right side.

Observed UI problem:
In `/admin/customers?tab=orders&customer_id=...&orderWorkspace=edit&...&step=demand-groups`, the applied demand-group cards now show persisted demand groups correctly, but the action buttons are displayed in a separate left-side column:
- `Edit shifts`
- `Edit`

This creates an awkward layout and wastes vertical/horizontal space. The requested layout is:
- each applied demand-group card should have its title/summary row
- `Edit shifts` and `Edit` should appear together on the right side of that same header/title row
- `Edit shifts` should appear before `Edit`
- the `Complete` status indicator should remain below the title/action row, not behind or mixed with the buttons

Current repo facts to validate:
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue` contains the customer order wizard Demand groups step.
- This component imports and uses planning staffing APIs such as `bulkUpdateDemandGroups`, `listDemandGroups`, `bulkApplyDemandGroups`, and `updateDemandGroup`.
- The current applied demand-group summary UI is in this component.
- The current layout has action buttons positioned on the left side of each applied summary card.
- The `Edit shifts` action opens the per-shift/day edit flow.
- The `Edit` action opens the aggregate edit flow.
- The underlying edit behavior should not change in this task.

Goal:
Make a layout-only UI refinement:
1. Move `Edit shifts` and `Edit` into the applied demand-group card header.
2. Place them on the far right of the header row.
3. Keep `Edit shifts` before `Edit`.
4. Keep the demand-group title/function type and qualification label on the left of the header row.
5. Keep the status indicator such as `Complete`, `Partial`, or `Mixed` in a clear row below the header, or as a separate compact badge that does not collide with the buttons.
6. Keep the card compact and visually clean.

Files to inspect:
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-epic4.smoke.test.ts`
- locale files under:
  - `web/apps/web-antd/src/locales/langs/de-DE`
  - `web/apps/web-antd/src/locales/langs/en-US`

Implementation requirements:
1. Do not change business logic.
2. Do not change backend APIs.
3. Do not change `bulkUpdateDemandGroups`, `bulkApplyDemandGroups`, `listDemandGroups`, or `updateDemandGroup` behavior.
4. Do not change how applied demand groups are aggregated.
5. Do not change how aggregate edit and per-shift edit modals work.
6. Only adjust markup/CSS/tests as needed for the requested layout.
7. The card header layout should be responsive:
   - desktop: title/qualification on the left, actions on the right
   - narrow widths: actions may wrap below the title but should remain grouped and aligned cleanly
8. Preserve accessibility:
   - buttons remain real buttons
   - labels remain localized
   - existing data-testid values should be preserved if possible
   - if test IDs are missing, add stable test IDs
9. Preserve existing visual theme:
   - do not hardcode unrelated colors
   - use existing SicherPlan/Vben card/button classes or local scoped CSS consistent with the existing component
10. Keep the visual hierarchy:
   - header row: title + actions
   - status row: Complete / Partial / Mixed indicator
   - detail row: min/target/sort/mandatory/applied shift count
11. Ensure the `Complete` status does not appear behind, above, or visually mixed with the action buttons.

Suggested DOM structure:
```vue
<div class="sp-customer-plan-wizard-step__demand-summary-card">
  <div class="sp-customer-plan-wizard-step__demand-summary-header">
    <div class="sp-customer-plan-wizard-step__demand-summary-title">
      <strong>Schichtleiter</strong>
      <span>Sachkunde §34a GewO</span>
    </div>

    <div class="sp-customer-plan-wizard-step__demand-summary-actions">
      <button ...>Edit shifts</button>
      <button ...>Edit</button>
    </div>
  </div>

  <div class="sp-customer-plan-wizard-step__demand-summary-status">
    Complete
  </div>

  <div class="sp-customer-plan-wizard-step__demand-summary-details">
    ...
  </div>
</div>
```

Suggested CSS intent:
```css
.sp-customer-plan-wizard-step__demand-summary-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.sp-customer-plan-wizard-step__demand-summary-title {
  min-width: 0;
}

.sp-customer-plan-wizard-step__demand-summary-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 0.5rem;
  justify-content: flex-end;
}

@media (max-width: ... ) {
  .sp-customer-plan-wizard-step__demand-summary-header {
    flex-direction: column;
  }

  .sp-customer-plan-wizard-step__demand-summary-actions {
    justify-content: flex-start;
  }
}
```

Testing requirements:
Update or add tests for:
1. Applied demand-group card renders action buttons inside the card header.
2. `Edit shifts` appears before `Edit`.
3. Both buttons remain clickable and call/open the existing flows.
4. The status label such as `Complete` remains visible and separate from the button group.
5. Existing aggregate edit tests still pass.
6. Existing per-shift edit tests still pass.
7. Existing New demand group and Apply demand groups tests still pass.

Verification:
Run and report exact results:
```bash
cd web
nvm use 22
pnpm -F @vben/web-antd run build
pnpm test:unit -- --runInBand
```

If the repo uses a different test command, use the existing command and report it.

Output format:
- Design validation: accepted / adjusted / rejected
- Root layout issue
- Files changed
- Markup/CSS changes
- Tests added/updated
- Verification commands and results
- Remaining risks or follow-ups

You are working in the public repo `jalalsadeghi/SicherPlan`.

Task:
Make a very small, scoped CSS refinement to the dashboard calendar item marker style in the SicherPlan dashboard.

Scope:
Only adjust the shared calendar item marker selector.
Do NOT redesign the dashboard.
Do NOT target generated Vue scope hash selectors like `[data-v-99cca3be]` in source code.
Use the real source selector in the Vue file.

Target page:
`/admin/dashboard`

Likely file:
`web/apps/web-antd/src/views/sicherplan/dashboard/index.vue`

What to change:
For the base selector:
`.sp-dashboard__calendar-item-marker`

change only these properties to:
- `width: 0.35rem;`
- `height: 0.35rem;`

Important constraints:
- Apply this to the shared base `.sp-dashboard__calendar-item-marker`, not a rendered `[data-v-...]` selector
- Do not change other properties unless needed to keep valid CSS formatting
- Do not change marker colors or state-specific styling
- Do not change markup or behavior
- Keep the patch CSS-only

What to inspect first:
1. The current `<style scoped>` block in `dashboard/index.vue`
2. The existing `.sp-dashboard__calendar-item-marker` selector
3. Any variant-specific overrides that might conflict

What to do:
1. Update the base `.sp-dashboard__calendar-item-marker` selector
2. Change only:
   - `width`
   - `height`
3. Leave all other calendar marker styling intact
4. Do not introduce extra overrides unless necessary

Validation requirements:
After implementing, verify:
1. `.sp-dashboard__calendar-item-marker` now uses:
   - `width: 0.35rem`
   - `height: 0.35rem`
2. All calendar item variants still inherit the updated marker size correctly
3. Color/state styling remains unchanged
4. No build/lint errors are introduced

At the end, provide a concise validation report with:
1. Which file was changed
2. Which selector was updated
3. Confirmation that only the requested properties were changed
4. Confirmation that variant-specific marker colors were left unchanged
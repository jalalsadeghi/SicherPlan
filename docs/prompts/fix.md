You are working in the latest public SicherPlan repository.

Target route:
admin/customers/order-workspace?customer_id=<id>&order_id=<id>&order_mode=edit&step=shift-plan

Target step:
Shift plan

Observed UI:
In the Shift plan step, after a shift plan is selected, the page shows an extra box/row with the text:
"Selected shift plan: <shift plan name>"

User request:
Remove this "Selected shift plan:" box/row from the UI because it adds visual clutter and does not provide useful information.

Important:
This is a UI-only cleanup.
Do not change the actual selected shift plan state.
Do not change the shift plan editor behavior.
Do not change API calls.
Do not change wizard route/query synchronization.
Do not change save/update/next/previous behavior.
Do not remove the existing shift plan list item above it.
Do not remove the editor fields below it.

Files to inspect:
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- any extracted Shift plan step component if it exists
- related tests such as new-plan-epic4.smoke.test.ts or closest new-plan test file

Required investigation:
1) Find the markup that renders the "Selected shift plan:" box/row.
2) Confirm whether it is purely informational or used as a clickable/control element.
3) If it is purely informational, remove it from the rendered template.
4) If any test depends on that text, update the test to assert the selected shift plan behavior through the actual selected card/editor instead of this redundant label.

Implementation rules:
- Keep selected shift plan card highlighting unchanged.
- Keep selected shift plan editor fields unchanged.
- Keep internal state variables unchanged unless they are only used for this removed visual label.
- Do not remove useful accessibility labels from the actual selected card/editor.
- Preserve layout spacing after removal so there is no awkward gap.

Validation:
Please validate my suggestion critically before changing code.
If the "Selected shift plan:" box is used for something important, explain it and propose a safer alternative.
If it is purely redundant display text, remove it.

Acceptance criteria:
- The text/box "Selected shift plan:" no longer appears in the Shift plan step.
- The selected shift plan remains visibly selected in the existing shift plan list/card.
- The editor still shows the selected shift plan data.
- Save/update behavior still works.
- Next/Previous navigation still works.
- No unrelated wizard steps are changed.

Deliverables:
1) Apply the code change.
2) Update tests if needed.
3) Summarize:
   - changed files
   - exact UI element removed
   - why it was safe to remove
   - validation performed
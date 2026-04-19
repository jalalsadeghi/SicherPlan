You are working in the SicherPlan repository.

This task is part of the Customer New Plan Wizard work:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md

Important current product decision:
- Order Details is the first wizard step.
- Planning is not a separate first step.
- Planning context is selected or created inside the Planning Record step.
- Do NOT reintroduce a separate Planning step.

Current user-visible problems in Step 5 “Planning record”:

1. The two options:
   - Use existing planning entry
   - Create new planning entry
   are visually broken / poorly aligned.
   They currently look like raw radio controls or stretched layout rows and do not match the rest of the SicherPlan wizard UI.

2. When the user selects an existing planning entry, the page appears to refresh/reload.
   Backend logs show repeated GETs such as:
   - GET /ops/orders/{order_id}
   - GET /ops/orders/{order_id}/equipment-lines
   - GET /ops/orders/{order_id}/requirement-lines
   - GET /ops/orders/{order_id}/attachments
   - GET /ops/sites?customer_id=...
   - GET /ops/event-venues?customer_id=...
   - GET /ops/trade-fairs?customer_id=...
   - GET /ops/patrol-routes?customer_id=...

Expected behavior:
- Selecting an existing planning entry should be instant and local.
- It should highlight/select the chosen planning entry.
- It should reveal or update the Planning Record detail form.
- It should NOT trigger a full step reload.
- It should NOT reload order/equipment/requirement/attachment/reference data.
- The wizard should commit planning context to route/state only on explicit submit/Next, or in a carefully idempotent way that does not trigger refresh loops.

Relevant files to inspect first:
- /docs/sprint/SPR-CUST-NEWPLAN-V1.md
- web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue
- web/apps/web-antd/src/views/sicherplan/customers/use-customer-new-plan-wizard.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.steps.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard.types.ts
- web/apps/web-antd/src/views/sicherplan/customers/new-plan-wizard-drafts.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts
- web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
- related tests under web/apps/web-antd/src/views/sicherplan/customers/

Before coding, validate this proposal:
1. Confirm how the current Planning Record step renders “Use existing planning entry” and “Create new planning entry”.
2. Confirm whether the current selector uses raw radio controls or an unstyled layout.
3. Confirm what happens when an existing planning entry is clicked:
   - Does it update planningEntityId locally?
   - Does it emit saved-context?
   - Does it update route query?
   - Does it trigger refreshStepData?
4. Confirm whether stepRefreshContextKey includes planning_entity_id/type/mode and therefore causes refreshStepData when those values are committed.
5. Confirm whether refreshStepData for planning-record-overview calls both loadOrderState and loadPlanningRecordState.
6. Confirm whether loadPlanningRecordState loads all planning reference lists again.
7. State clearly whether my diagnosis is correct, partially correct, or needs adjustment before changing code.

Goal:
Make Planning Record context selection visually clean and non-destructive.

Scope:
- Frontend only
- No backend changes
- No canonical /admin/planning changes
- No step-order change
- No unrelated refactor

Required behavior:

A. Replace the broken “Use existing / Create new” UI
Implement a clean toggle/segmented control or two selectable cards inside the Planning Record step.

The control should show:
- Use existing planning entry
- Create new planning entry

Requirements:
- visually aligned
- compact
- same height
- clear selected state
- keyboard accessible
- responsive on narrow screens
- matches the existing wizard/admin styling
- no raw, stretched radio-line look

Use existing classes/design tokens where possible:
- planning-admin-checkbox if still appropriate
- cta-button / cta-secondary
- sp-customer-plan-wizard-step__toggle-row
- or add a small local class such as:
  - sp-customer-plan-wizard-step__mode-toggle
  - sp-customer-plan-wizard-step__mode-option

B. Existing planning entry list styling
For “Use existing planning entry”:
- show planning entries as clear selectable rows/cards
- selected entry should be visually highlighted
- row should show meaningful label/name and optionally id/code
- do not show a raw select if the current branch already uses card rows here
- if a select is used, style it consistently and keep it from stretching awkwardly

C. Selection must be local first
When the user clicks an existing planning entry:
- set local planningEntityId
- keep planningFamily/planningModeCode local
- update visible selected state
- update Planning Record form fields as needed
- do NOT emit saved-context immediately
- do NOT call router.replace immediately
- do NOT trigger refreshStepData
- do NOT reload order data
- do NOT reload all planning families again

The selected planning context should be committed later by the Planning Record submit/Next action.

D. Build Planning Record payload from local selected context
Because selected planning context is local until submit:
- update buildPlanningRecordModePayload and validation helpers so they can use the local selected context:
  - planningFamily
  - planningEntityId
  - derived planningModeCode
instead of relying only on props.wizardState.planning_entity_id/type/mode.

On successful Planning Record submit:
- emit saved-context with:
  - planning_entity_id
  - planning_entity_type
  - planning_mode_code
  - planning_record_id
- then parent can update route/state once.

E. Hydration from route/state must be idempotent
If the user returns to Planning Record with existing planning context in route/state:
- hydrate local planningFamily/planningEntityId once
- do not emit saved-context during hydration
- do not reload repeatedly
- do not overwrite active local selection unnecessarily

F. Create new planning entry
For “Create new planning entry”:
- opening the create modal must not reload the step
- creating a new entry should:
  - create via canonical planning setup API
  - refresh only the relevant planning family options once
  - set the created entry as local selected planningEntityId
  - switch to Use existing mode if that is the branch UX pattern
  - keep user on Planning Record
  - not full-refresh order state

Do not remove:
- Create new address
- Pick on map
- family-specific create fields

G. Prevent refresh loops and over-fetching
Review watchers:
- planningFamily watcher
- planningEntityId watcher
- main props/wizardState watcher
- refreshStepData
- loadPlanningRecordReferenceOptions
- loadPlanningEntityOptions

Ensure:
- changing local planningEntityId does not trigger global refreshStepData
- only planningFamily change should fetch options for that family
- selecting an option should not fetch all families again
- same values do not trigger route sync or step reload
- loading/hydration is guarded with draftSyncPaused or a more specific isHydratingPlanningContext flag

H. Tests
Add or update tests for:

1. Toggle UI:
- Use existing / Create new renders as styled controls
- selected mode is visually indicated
- responsive classes exist

2. Existing entry selection:
- clicking an existing planning entry selects it locally
- no saved-context is emitted on selection
- no router.replace is called on selection
- refreshStepData is not called again on selection
- order GET is not called again on selection

3. Form unlock:
- after selecting an existing planning entry, Planning Record detail fields are shown/enabled
- validation uses local context

4. Submit:
- clicking Next with selected context and valid form creates PlanningRecord
- saved-context emits planning_entity_id/type/mode and planning_record_id only on submit
- then wizard moves to Planning Documents

5. Hydration:
- route/state planning context hydrates local state once
- hydration does not emit saved-context repeatedly
- hydration does not trigger repeated GET loop

6. Create new planning entry:
- creates the entity
- refreshes only relevant options
- selects created entry locally
- no full reload loop starts

7. Non-regression:
- Order Details first-step behavior still works
- Equipment/Requirement steps still work
- Order Documents optional behavior still works
- Planning Record missing context still blocks Next with a clear message

Manual QA checklist:
- Open Planning Record step.
- Confirm Use existing / Create new controls look clean and aligned.
- Select an existing Site entry.
- Confirm row is selected instantly.
- Confirm backend logs do not show a full reload sequence.
- Confirm Planning Record fields remain visible.
- Switch to Create new planning entry and back.
- Create a new Site and confirm it becomes selected.
- Fill Planning Record and click Next.
- Confirm it creates Planning Record and moves to Planning Documents.
- Refresh page after selecting context and confirm stable hydration.

Final output:
1. Validation summary
2. Root cause found
3. Styling changes implemented
4. Selection behavior changes implemented
5. Files changed
6. Tests added/updated
7. Test results
8. Manual QA checklist
9. Remaining limitations

Before finalizing, explicitly state whether my proposal was correct or adjusted.
Avoid unrelated refactors.
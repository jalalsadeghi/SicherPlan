You are working in the SicherPlan repository.

This is a focused follow-up requirement for the Planning record step refactor in:

/admin/customers/order-workspace
step=planning-record-overview

Important clarification:
The button "Create new planning entry" must be positioned specifically at the TOP-RIGHT of the "Planning record details" box/subsection.

It must NOT be:
- at the top-right of the whole step
- inside the Existing planning records subsection
- floating above both subsections
- placed below the editor fields

Correct placement:
Inside the header row of the "Planning record details" subsection:
- subsection title on the left
- "Create new planning entry" button on the right

Expected subsection structure:
<div class="sp-customer-plan-wizard-step__subsection">
  <div class="sp-customer-plan-wizard-step__subsection-header sp-customer-plan-wizard-step__subsection-header--with-action">
    <div class="sp-customer-plan-wizard-step__subsection-title">
      <strong>Planning record details</strong>
      <p class="field-help">...</p>
    </div>

    <button
      type="button"
      class="cta-button cta-secondary"
      data-testid="customer-new-plan-planning-record-create-entry"
      @click="openPlanningCreateModal()"
    >
      Create new planning entry
    </button>
  </div>

  <!-- planning record editor fields here -->
</div>

Implementation requirements:
1. Put the button in the header of the Planning record details subsection only.
2. Align it to the top-right on desktop/wide screens.
3. On smaller screens, allow it to stack below the title/help text cleanly.
4. Do not place it in the Existing planning records subsection.
5. Do not move the actual modal logic; continue reusing:
   openPlanningCreateModal()
6. Keep all existing editor fields and actions unchanged.

Suggested CSS behavior:
.sp-customer-plan-wizard-step__subsection-header--with-action {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
  flex-wrap: wrap;
}

On narrow screens:
- button may wrap below the title block
- but it should remain inside the Planning record details subsection header

Validation:
After implementation, confirm visually that:
- Existing planning records subsection has no Create new planning entry button
- Planning record details subsection has the button in its own top-right corner
- mobile layout still looks clean
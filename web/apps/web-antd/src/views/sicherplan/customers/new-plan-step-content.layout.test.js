import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue"),
  "utf8",
);
const employeeSource = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue"),
  "utf8",
);

test("wizard step content uses wizard field wrappers across implemented steps", () => {
  assert.match(source, /data-testid="customer-new-plan-step-panel-planning-record-overview"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-order-details"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-equipment-lines"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-requirement-lines"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-order-documents"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-planning-record-overview"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-planning-record-documents"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-shift-plan"/);
  assert.match(source, /data-testid="customer-new-plan-step-panel-series-exceptions"/);
  assert.match(source, /class="field-stack"/);
  assert.match(source, /class="field-stack field-stack--wide"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-address-id"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-address-action"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-timezone"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-latitude"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-longitude"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-pick-on-map"/);
  assert.match(source, /data-testid="customer-new-plan-planning-address-dialog"/);
  assert.match(source, /data-testid="customer-new-plan-planning-create-status"/);
  assert.match(source, /data-testid="customer-new-plan-trade-fair-zone"/);
});

test("wizard step content defines local form-control styling instead of relying on scoped planning views", () => {
  assert.match(source, /\.field-stack \{/);
  assert.match(source, /\.field-stack span \{/);
  assert.match(source, /\.field-stack input,/);
  assert.match(source, /\.field-stack select,/);
  assert.match(source, /\.field-stack textarea \{/);
  assert.match(source, /\.field-help \{/);
  assert.match(source, /\.cta-row \{/);
  assert.match(source, /\.cta-button \{/);
  assert.match(source, /\.cta-button\.cta-secondary \{/);
  assert.match(source, /\.planning-admin-checkbox \{/);
  assert.match(source, /\.planning-admin-checkbox input\[type='checkbox'\],/);
  assert.match(source, /\.sp-customer-plan-wizard-step__grid \{/);
  assert.match(source, /\.sp-customer-plan-wizard-step__panel \{/);
  assert.match(source, /\.sp-customer-plan-wizard-step__list-row \{/);
});

test("teleported modal content gets explicit wizard styling hooks", () => {
  assert.match(source, /wrap-class-name="sp-customer-plan-wizard-modal"/);
  assert.match(source, /:deep\(\.sp-customer-plan-wizard-modal \.field-stack\)/);
  assert.match(source, /:deep\(\.sp-customer-plan-wizard-modal \.field-stack input\)/);
  assert.match(source, /data-testid="customer-new-plan-new-equipment-dialog"/);
  assert.match(source, /data-testid="customer-new-plan-new-requirement-dialog"/);
  assert.match(source, /data-testid="customer-new-plan-new-template-dialog"/);
});

test("wizard step operational feedback uses bottom-right toast notifications instead of a top banner", () => {
  assert.match(source, /useSicherPlanFeedback/);
  assert.match(source, /const \{ showFeedbackToast \} = useSicherPlanFeedback\(\);/);
  assert.match(source, /function setFeedback\(tone: 'error' \| 'neutral' \| 'success', message = ''\) \{[\s\S]*showFeedbackToast\(\{[\s\S]*key: 'customer-new-plan-step-feedback'/);
  assert.doesNotMatch(source, /const stepFeedback = reactive/);
  assert.doesNotMatch(source, /v-if="stepFeedback\.message"/);
  assert.match(source, /v-if="draftRestoreMessage"[\s\S]*data-testid="customer-new-plan-draft-restored"/);
});

test("wizard planning step uses canonical branch-backed selectors and tenant catalog scope", () => {
  assert.match(source, /listCustomerAddresses/);
  assert.match(source, /createCustomerAvailableAddress/);
  assert.match(source, /PlanningLocationPickerModal/);
  assert.match(source, /resolveInitialMapCenter/);
  assert.match(source, /listTradeFairZones/);
  assert.match(source, /planningCreateAddressOptions/);
  assert.match(source, /planningCreateStagedAddresses/);
  assert.match(source, /tradeFairZoneSelectOptions/);
  assert.match(source, /createPlanningSetupRecord\('requirement_type'/);
  assert.match(source, /createPlanningSetupRecord\('equipment_item'/);
  const requirementCreateBlock = source.slice(
    source.indexOf("createPlanningSetupRecord('requirement_type'"),
    source.indexOf('resetRequirementModal();'),
  );
  const equipmentCreateBlock = source.slice(
    source.indexOf("createPlanningSetupRecord('equipment_item'"),
    source.indexOf('resetEquipmentModal();'),
  );
  assert.equal(requirementCreateBlock.includes('customer_id: props.customer.id'), false);
  assert.equal(equipmentCreateBlock.includes('customer_id: props.customer.id'), false);
  assert.match(source, /planningCreateSupportsLocationPicker = computed/);
  assert.match(source, /planningFamily\.value === 'site' \|\| planningFamily\.value === 'event_venue' \|\| planningFamily\.value === 'trade_fair'/);
});

test("wizard form grid keeps responsive stacking rules", () => {
  assert.match(source, /grid-template-columns: repeat\(auto-fit, minmax\(14rem, 1fr\)\);/);
  assert.match(source, /@media \(max-width: 960px\)/);
  assert.match(source, /\.sp-customer-plan-wizard-step__grid \{\s*grid-template-columns: 1fr;/);
});

test("order scope documents step uses employee-overview style sticky section navigation", () => {
  assert.match(source, /v-else-if="orderScopeDocumentsStepActive"[\s\S]*data-testid="customer-order-scope-onepage"/);
  assert.match(source, /data-testid="customer-order-scope-nav"/);
  assert.match(source, /customer-order-scope-nav-link-equipment/);
  assert.match(source, /customer-order-scope-nav-link-requirements/);
  assert.match(source, /customer-order-scope-nav-link-documents/);
  assert.match(source, /IconifyIcon class="sp-customer-order-scope-nav__icon"/);
  assert.match(source, /id="customer-order-scope-section-equipment"/);
  assert.match(source, /id="customer-order-scope-section-requirements"/);
  assert.match(source, /id="customer-order-scope-section-documents"/);
  assert.match(source, /scrollIntoView\(\{\s*behavior: 'smooth',\s*block: 'start'/);
  assert.match(source, /new IntersectionObserver/);
  assert.match(source, /const EXTRA_SECTION_NAV_TOP_OFFSET = 25;/);
  assert.match(source, /const orderScopeVisibleEntries = new Map<OrderScopeSectionId, IntersectionObserverEntry>\(\);/);
  assert.match(source, /resolveActiveOrderScopeSection/);
  assert.match(source, /activeOrderScopeSection\.value = sectionId/);
  assert.match(source, /\.sp-customer-order-scope-nav-shell \{[\s\S]*position: sticky;/);
  assert.match(source, /\.sp-customer-order-scope-nav-shell--fixed \{[\s\S]*position: fixed;/);
  assert.match(source, /\.sp-customer-order-scope-nav-shell--pinned \{[\s\S]*position: absolute;/);
  assert.match(source, /\.sp-customer-order-scope-nav__link--active \{[\s\S]*border-left-color: var\(--sp-color-primary\);/);
  assert.match(source, /--customer-order-scope-sticky-top: calc\(var\(--sp-sticky-offset, 6\.5rem\) \+ 25px\);/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-card \{[\s\S]*scroll-margin-top: var\(--customer-order-scope-sticky-top, 6\.5rem\);/);
});

test("order scope layout keeps action rows spaced and flattens document subsections", () => {
  assert.match(source, /sp-customer-plan-wizard-step__scope-action-row[\s\S]*data-testid="customer-new-plan-new-equipment"/);
  assert.match(source, /sp-customer-plan-wizard-step__scope-action-row[\s\S]*data-testid="customer-new-plan-new-requirement"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-subsection"[\s\S]*data-testid="customer-new-plan-new-equipment"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-subsection"[\s\S]*data-testid="customer-new-plan-new-requirement"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-saved-list"[\s\S]*customer-new-plan-equipment-line-select/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-saved-list"[\s\S]*customer-new-plan-requirement-line-select/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-editor"[\s\S]*customer-new-plan-equipment-item/);
  assert.match(source, /class="sp-customer-plan-wizard-step__scope-editor"[\s\S]*customer-new-plan-requirement-type/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-action-row \{[\s\S]*margin-bottom: 0;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-subsection \{[\s\S]*gap: 0\.65rem;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-saved-list \{[\s\S]*margin: 0\.15rem 0 0\.35rem;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-editor \{[\s\S]*gap: 0\.85rem;/);
  assert.match(source, /class="sp-customer-plan-wizard-step__document-subsection"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__document-divider" aria-hidden="true"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__document-list"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__list-action sp-customer-plan-wizard-step__list-action--compact sp-customer-plan-wizard-step__list-action--document-remove"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static sp-customer-plan-wizard-step__list-row--document"/);
  assert.match(source, /\.sp-customer-plan-wizard-step__document-list \{[\s\S]*margin: 0\.7rem 0 1rem;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__document-subsection \{[\s\S]*display: grid;[\s\S]*gap: 1rem;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__document-divider \{[\s\S]*height: 1px;[\s\S]*margin: 0\.85rem 0 0\.45rem;[\s\S]*background: var\(--sp-color-border-soft\);/);
  assert.match(source, /\.sp-customer-plan-wizard-step__list-row--document \{[\s\S]*align-items: flex-start;/);
  assert.match(source, /\.sp-customer-plan-wizard-step__list-action--document-remove \{[\s\S]*min-height: 1\.85rem;[\s\S]*padding: 0\.32rem 0\.6rem;/);
  assert.match(source, /customer-new-plan-order-scope-documents-card[\s\S]*customer-new-plan-order-document-upload-title/);
  assert.doesNotMatch(source, /customer-new-plan-order-document-link-id/);
  const documentsCardSource = source.slice(
    source.indexOf('data-testid="customer-new-plan-order-scope-documents-card"'),
    source.indexOf('v-else-if="planningRecordStepActive"'),
  );
  assert.doesNotMatch(documentsCardSource, /class="sp-customer-plan-wizard-step__panel"/);
  assert.doesNotMatch(documentsCardSource, /manualDocumentId/);
  assert.doesNotMatch(documentsCardSource, /documentSummary\(selectedOrderLinkDocument, orderAttachmentLink\.document_id\)/);
  assert.match(documentsCardSource, /documentCustomerSummary\(selectedOrderLinkDocument\)/);
  assert.match(documentsCardSource, /data-testid="customer-new-plan-attach-order-document"[\s\S]*v-if="hasOrderDocumentUploadDraftInput\(\)"[\s\S]*data-testid="customer-new-plan-clear-order-document-draft"/);
  assert.match(documentsCardSource, /data-testid="customer-new-plan-link-order-document"[\s\S]*v-if="hasOrderDocumentLinkDraftInput\(\)"[\s\S]*data-testid="customer-new-plan-clear-order-document-draft"/);
  assert.doesNotMatch(source, /documentSummary\(document, document\.id\)/);
  assert.match(source, /documentCustomerSummary\(document\)/);
});

test("order scope prevents duplicate equipment and requirement selections locally", () => {
  assert.match(source, /const availableEquipmentItemSelectOptions = computed/);
  assert.match(source, /line\.id !== selectedEquipmentLineId\.value[\s\S]*line\.equipment_item_id === equipmentLineDraft\.equipment_item_id/);
  assert.match(source, /const requirementLineDuplicateActive = computed\(\(\) =>\s*hasDuplicateActiveRequirementLine/);
  assert.match(source, /v-for="option in availableEquipmentItemSelectOptions"/);
  assert.match(source, /data-testid="customer-new-plan-equipment-all-assigned"/);
  assert.match(source, /data-testid="customer-new-plan-equipment-duplicate"/);
  assert.match(source, /data-testid="customer-new-plan-requirement-duplicate"/);
  assert.match(source, /data-testid="customer-new-plan-save-equipment-line"[\s\S]*:disabled="stepLoading \|\| equipmentLineDuplicateActive"/);
  assert.match(source, /data-testid="customer-new-plan-save-requirement-line"[\s\S]*:disabled="stepLoading \|\| requirementLineDuplicateActive"/);
  assert.match(source, /if \(!equipmentLineDraft\.equipment_item_id \|\| equipmentLineDraft\.required_qty < 1 \|\| equipmentLineDuplicateActive\.value\)/);
  assert.match(source, /requirementLineDuplicateActive\.value[\s\S]*setFeedback\('error', \$t\('sicherplan\.customerPlansWizard\.errors\.requirementLineInvalid'\)\)/);
});

test("order scope next-validation uses section-aware results, inline field errors, and invalid card styling", () => {
  assert.match(source, /interface OrderScopeSectionValidationResult/);
  assert.match(source, /const orderScopeSectionErrors = reactive<Record<OrderScopeSectionId, string>>/);
  assert.match(source, /const orderScopeFieldErrors = reactive<Record<OrderScopeValidationFieldKey, string>>/);
  assert.match(source, /function validateEquipmentStep\(\): OrderScopeSectionValidationResult \| null/);
  assert.match(source, /function validateRequirementStep\(\): OrderScopeSectionValidationResult \| null/);
  assert.match(source, /function validateDocumentsStep\(\): OrderScopeSectionValidationResult \| null/);
  assert.match(source, /function applyOrderScopeValidationResults\(results: OrderScopeSectionValidationResult\[\]\)/);
  assert.match(source, /function revealOrderScopeValidationResult\(result: OrderScopeSectionValidationResult\)/);
  assert.match(source, /focusOrderScopeValidationTarget\(result\.focusSelector\)/);
  assert.match(source, /data-testid="customer-new-plan-order-scope-equipment-error"/);
  assert.match(source, /data-testid="customer-new-plan-order-scope-requirements-error"/);
  assert.match(source, /data-testid="customer-new-plan-order-scope-documents-error"/);
  assert.match(source, /data-testid="customer-new-plan-order-document-file-error"/);
  assert.match(source, /data-testid="customer-new-plan-order-document-selection-error"/);
  assert.match(source, /field-stack--invalid': Boolean\(orderScopeFieldErrors\.equipmentItem\)/);
  assert.match(source, /field-stack--invalid': Boolean\(orderScopeFieldErrors\.requirementsType\)/);
  assert.match(source, /field-stack--invalid': Boolean\(orderScopeFieldErrors\.documentsUploadTitle\)/);
  assert.match(source, /sp-customer-plan-wizard-step__scope-card--invalid/);
  assert.match(source, /\.sp-customer-plan-wizard-step__scope-card--invalid \{/);
  assert.match(source, /\.cta-button--invalid \{/);
});

test("employee overview uses the same section nav offset and deterministic active-section tracking", () => {
  assert.match(employeeSource, /const EXTRA_SECTION_NAV_TOP_OFFSET = 25;/);
  assert.match(employeeSource, /const employeeOverviewVisibleEntries = new Map<EmployeeOverviewSectionId, IntersectionObserverEntry>\(\);/);
  assert.match(employeeSource, /resolveActiveEmployeeOverviewSection/);
  assert.match(employeeSource, /--employee-overview-sticky-top: calc\(var\(--sp-sticky-offset, 6\.5rem\) \+ 25px\);/);
  assert.match(employeeSource, /\.employee-admin-overview-section-card \{[\s\S]*scroll-margin-top: var\(--employee-overview-sticky-top, 6\.5rem\);/);
});

test("wizard step content exposes non-disruptive local loading indicators for saved data areas", () => {
  assert.match(source, /LocalLoadingIndicator/);
  assert.match(source, /type StepLoadKey/);
  assert.match(source, /beginStepLoads/);
  assert.match(source, /finishStepLoads/);
  assert.match(source, /stepLoadState = reactive/);
  assert.match(source, /test-id="customer-new-plan-order-loading"/);
  assert.match(source, /test-id="customer-new-plan-step-local-loading"/);
  assert.match(source, /test-id="customer-new-plan-equipment-lines-loading"/);
  assert.match(source, /test-id="customer-new-plan-equipment-options-loading"/);
  assert.match(source, /test-id="customer-new-plan-requirement-lines-loading"/);
  assert.match(source, /test-id="customer-new-plan-requirement-options-loading"/);
  assert.match(source, /test-id="customer-new-plan-order-documents-loading"/);
  assert.match(source, /test-id="customer-new-plan-planning-reference-loading"/);
  assert.match(source, /test-id="customer-new-plan-planning-record-loading"/);
  assert.match(source, /test-id="customer-new-plan-planning-record-detail-loading"/);
  assert.match(source, /test-id="customer-new-plan-planning-documents-loading"/);
  assert.match(source, /test-id="customer-new-plan-shift-plan-loading"/);
  assert.match(source, /test-id="customer-new-plan-shift-plan-detail-loading"/);
  assert.match(source, /test-id="customer-new-plan-shift-options-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-context-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-loading"/);
  assert.match(source, /data-testid="customer-new-plan-series-detail-loading"/);
  assert.match(source, /data-order-workspace-testid="customer-order-workspace-series-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-exceptions-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-options-loading"/);
  assert.doesNotMatch(source, /sp-customer-plan-wizard-step--loading/);
});

test("series exceptions keeps generation options compact and saved-series loading above fields", () => {
  assert.match(source, /const seriesEditMode = computed\(\(\) => Boolean\(selectedSeries\.value\?\.id\)\);/);
  assert.match(source, /class="sp-customer-plan-wizard-step__series-loading-row"[\s\S]*data-order-workspace-testid="customer-order-workspace-series-loading"/);
  assert.match(source, /class="sp-customer-plan-wizard-step__series-loading-row"[\s\S]*<LocalLoadingIndicator :label="\$t\('sicherplan\.customerPlansWizard\.forms\.loadingSavedSeries'\)" \/>[\s\S]*<\/div>\s*<div class="sp-customer-plan-wizard-step__grid">/);
  assert.match(source, /:data-order-workspace-testid="seriesEditMode \? 'customer-order-workspace-series-update' : 'customer-order-workspace-series-save'"/);
  assert.match(source, /seriesEditMode[\s\S]*\$t\('sicherplan\.customerPlansWizard\.actions\.updateSeries'\)[\s\S]*\$t\('sicherplan\.customerPlansWizard\.actions\.saveSeries'\)/);
  assert.match(source, /class="sp-customer-plan-wizard-step__generation-grid"[\s\S]*data-order-workspace-testid="customer-order-workspace-generation-options"/);
  assert.match(source, /data-order-workspace-testid="customer-order-workspace-generate-from"[\s\S]*data-order-workspace-testid="customer-order-workspace-generate-to"[\s\S]*data-order-workspace-testid="customer-order-workspace-regenerate-existing"/);
  assert.match(source, /\.sp-customer-plan-wizard-step__generation-grid \{[\s\S]*grid-template-columns: minmax\(10rem, 14rem\) minmax\(10rem, 14rem\) minmax\(12rem, max-content\);/);
  assert.match(source, /\.sp-customer-plan-wizard-step__generation-date-field \{[\s\S]*max-width: 14rem;/);
});

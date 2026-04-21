import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue"),
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
  assert.match(source, /test-id="customer-new-plan-series-detail-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-exceptions-loading"/);
  assert.match(source, /test-id="customer-new-plan-series-options-loading"/);
  assert.doesNotMatch(source, /sp-customer-plan-wizard-step--loading/);
});

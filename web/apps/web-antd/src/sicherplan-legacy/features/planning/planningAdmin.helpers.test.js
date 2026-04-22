import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPlanningDirtySnapshot,
  buildPlanningImportTemplate,
  derivePlanningActionState,
  isPlanningChildEntity,
  PLANNING_ENTITY_OPTIONS,
  PLANNING_MODE_OPTIONS,
  normalizePlanningEditorEntity,
  formatPlanningAddressOption,
  filterPlanningCustomerOptions,
  formatPlanningCustomerOption,
  mapPlanningApiMessage,
  resolvePlanningBrowseEntity,
  parseOptionalCoordinate,
  resolvePlanningRouteContext,
  resolveInitialMapCenter,
  validatePlanningCreateDraft,
} from "./planningAdmin.helpers.js";

test("derivePlanningActionState grants dispatcher planning write access", () => {
  const state = derivePlanningActionState("dispatcher", "site", { id: "1" });
  assert.equal(state.canRead, true);
  assert.equal(state.canWrite, true);
  assert.equal(state.canManageChildren, false);
});

test("planning setup entity order groups service categories with tenant catalogs", () => {
  assert.deepEqual(
    PLANNING_ENTITY_OPTIONS.slice(0, 3),
    ["requirement_type", "service_category", "equipment_item"],
  );
});

test("derivePlanningActionState enables child editing for fair and route records", () => {
  assert.equal(derivePlanningActionState("tenant_admin", "trade_fair", { id: "1" }).canManageChildren, true);
  assert.equal(derivePlanningActionState("tenant_admin", "patrol_route", { id: "1" }).canManageChildren, true);
});

test("buildPlanningImportTemplate returns stable CSV headers", () => {
  assert.equal(
    buildPlanningImportTemplate("site"),
    "customer_id,site_no,name,address_id,timezone,latitude,longitude,watchbook_enabled,notes,status",
  );
  assert.equal(
    buildPlanningImportTemplate("requirement_type"),
    "code,label,default_planning_mode_code,notes,status",
  );
  assert.equal(
    buildPlanningImportTemplate("equipment_item"),
    "code,label,unit_of_measure_code,notes,status",
  );
  assert.equal(
    buildPlanningImportTemplate("service_category"),
    "code,label,sort_order,notes,status",
  );
});

test("equipment item import template keeps unit_of_measure_code as the canonical controlled field", () => {
  assert.match(buildPlanningImportTemplate("equipment_item"), /^code,label,unit_of_measure_code,notes,status$/);
});

test("planning mode options expose exactly the four canonical downstream planning values", () => {
  assert.deepEqual(
    PLANNING_MODE_OPTIONS.map((option) => option.value),
    ["event", "site", "trade_fair", "patrol"],
  );
});

test("mapPlanningApiMessage maps import and duplicate errors", () => {
  assert.equal(mapPlanningApiMessage("errors.planning.import.invalid_headers"), "invalidImportHeaders");
  assert.equal(mapPlanningApiMessage("errors.planning.patrol_checkpoint.duplicate_sequence"), "duplicateChild");
  assert.equal(
    mapPlanningApiMessage("errors.planning.equipment_item.invalid_unit_of_measure_code"),
    "validationUnitInvalid",
  );
});

test("formatPlanningCustomerOption renders customer number and name together", () => {
  assert.equal(
    formatPlanningCustomerOption({ customer_number: "CUS-200", name: "Messe Nord" }),
    "CUS-200 — Messe Nord",
  );
});

test("filterPlanningCustomerOptions matches across the combined customer label", () => {
  const customers = [
    { customer_number: "CUS-100", name: "Alpha Security" },
    { customer_number: "CUS-200", name: "Messe Nord" },
  ];

  assert.deepEqual(filterPlanningCustomerOptions(customers, "nord"), [customers[1]]);
  assert.deepEqual(filterPlanningCustomerOptions(customers, "cus-100"), [customers[0]]);
});

test("formatPlanningAddressOption renders a readable postal label", () => {
  assert.equal(
    formatPlanningAddressOption({
      address_id: "address-1",
      address: {
        street_line_1: "Musterstrasse 12",
        postal_code: "50667",
        city: "Koeln",
        country_code: "DE",
      },
    }),
    "Musterstrasse 12 · 50667 Koeln · DE",
  );
});

test("parseOptionalCoordinate keeps blank values unset instead of coercing to zero", () => {
  assert.equal(parseOptionalCoordinate(""), null);
  assert.equal(parseOptionalCoordinate("   "), null);
  assert.equal(parseOptionalCoordinate(undefined), null);
  assert.equal(parseOptionalCoordinate(null), null);
  assert.equal(parseOptionalCoordinate("0"), 0);
});

test("resolveInitialMapCenter ignores blank form coordinates and falls back truthfully", () => {
  const center = resolveInitialMapCenter({
    currentLatitude: "",
    currentLongitude: "",
    customerCoordinates: null,
    customerGeocode: null,
    fallback: { lat: 51.662973, lng: 8.174013 },
  });

  assert.deepEqual(center, {
    lat: 51.662973,
    lng: 8.174013,
    source: "fallback",
  });
});

test("resolveInitialMapCenter uses existing form coordinates only when both values are present", () => {
  const center = resolveInitialMapCenter({
    currentLatitude: "51.5",
    currentLongitude: "8.1",
    customerCoordinates: { lat: 52.1, lng: 13.1 },
    customerGeocode: { lat: 53.1, lng: 9.1 },
    fallback: { lat: 51.662973, lng: 8.174013 },
  });

  assert.deepEqual(center, {
    lat: 51.5,
    lng: 8.1,
    source: "existing-record",
  });
});

test("resolvePlanningRouteContext keeps only supported entity and customer query context", () => {
  assert.deepEqual(
    resolvePlanningRouteContext({ entity: "requirement_type", customer_id: "customer-1" }),
    { entity: "requirement_type", customerId: "customer-1" },
  );
  assert.deepEqual(
    resolvePlanningRouteContext({ entity: "service_category" }),
    { entity: "service_category", customerId: "" },
  );
  assert.deepEqual(
    resolvePlanningRouteContext({ entity: "unknown", customer_id: 7 }),
    { entity: null, customerId: "" },
  );
});

test("planning editor entity normalization maps child create flows back to their browse parent", () => {
  assert.equal(normalizePlanningEditorEntity("trade_fair_zone"), "trade_fair_zone");
  assert.equal(resolvePlanningBrowseEntity("trade_fair_zone"), "trade_fair");
  assert.equal(resolvePlanningBrowseEntity("patrol_checkpoint"), "patrol_route");
  assert.equal(isPlanningChildEntity("trade_fair_zone"), true);
  assert.equal(isPlanningChildEntity("site"), false);
});

test("planning create validation blocks child entities without parents and fair date regressions", () => {
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "trade_fair_zone",
      draft: {},
      zoneDraft: { zone_type_code: "security", zone_code: "A1", label: "North", notes: "" },
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationTradeFairParentRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "patrol_checkpoint",
      draft: {},
      zoneDraft: {},
      checkpointDraft: {
        sequence_no: 0,
        checkpoint_code: "",
        label: "",
        latitude: "",
        longitude: "",
        scan_type_code: "",
        minimum_dwell_seconds: -1,
      },
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationPatrolRouteParentRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "trade_fair",
      draft: {
        customer_id: "customer-1",
        fair_no: "FAIR-1",
        name: "Expo",
        start_date: "2026-05-10",
        end_date: "2026-05-09",
      },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationTradeFairDateRange",
  );
});

test("planning create validation covers top-level entities with entity-specific required fields", () => {
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "requirement_type",
      draft: { customer_id: "", code: "", label: "", default_planning_mode_code: "" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationCodeRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "requirement_type",
      draft: { customer_id: "", code: "REQ-1", label: "Guard", default_planning_mode_code: "legacy_mode" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationDefaultPlanningModeInvalid",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "equipment_item",
      draft: { customer_id: "", code: "RADIO", label: "", unit_of_measure_code: "" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationLabelRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "service_category",
      draft: { customer_id: "", code: "OBJ", label: "" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationLabelRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "site",
      draft: { customer_id: "customer-1", site_no: "", name: "" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationSiteNoRequired",
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "patrol_route",
      draft: { customer_id: "customer-1", route_no: "ROUTE-1", name: "" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    "validationNameRequired",
  );
});

test("planning create validation accepts valid site and valid child drafts", () => {
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "site",
      draft: { customer_id: "customer-1", site_no: "SITE-1", name: "North Gate" },
      zoneDraft: {},
      checkpointDraft: {},
      parentTradeFairId: "",
      parentPatrolRouteId: "",
    }),
    null,
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "trade_fair_zone",
      draft: {},
      zoneDraft: { zone_type_code: "hall", zone_code: "A1", label: "Hall A", notes: "" },
      checkpointDraft: {},
      parentTradeFairId: "fair-1",
      parentPatrolRouteId: "",
    }),
    null,
  );
  assert.equal(
    validatePlanningCreateDraft({
      editorEntityKey: "patrol_checkpoint",
      draft: {},
      zoneDraft: {},
      checkpointDraft: {
        sequence_no: 1,
        checkpoint_code: "CP-1",
        label: "Front Gate",
        latitude: "51.5",
        longitude: "8.1",
        scan_type_code: "qr",
        minimum_dwell_seconds: 0,
      },
      parentTradeFairId: "",
      parentPatrolRouteId: "route-1",
    }),
    null,
  );
});

test("planning dirty snapshot changes when create context changes", () => {
  const initial = buildPlanningDirtySnapshot({
    editorEntityKey: "site",
    isCreatingRecord: true,
    selectedRecordId: "",
    parentTradeFairId: "",
    parentPatrolRouteId: "",
    draft: { customer_id: "", site_no: "" },
    zoneDraft: { zone_code: "" },
    checkpointDraft: { checkpoint_code: "" },
  });
  const changed = buildPlanningDirtySnapshot({
    editorEntityKey: "site",
    isCreatingRecord: true,
    selectedRecordId: "",
    parentTradeFairId: "",
    parentPatrolRouteId: "",
    draft: { customer_id: "customer-1", site_no: "" },
    zoneDraft: { zone_code: "" },
    checkpointDraft: { checkpoint_code: "" },
  });

  assert.notEqual(initial, changed);
});
